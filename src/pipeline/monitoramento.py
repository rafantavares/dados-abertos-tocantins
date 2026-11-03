"""Compara a contagem de linhas desta carga com a anterior e detecta anomalias.

Uso:
    python -m pipeline.monitoramento <contagens.json> [--anterior <anteriores.json>]
        [--banco <banco.duckdb>] [--historico <historico.jsonl>] [--resumo <resumo.md>]

Regras (por tabela presente na carga anterior):
- tabela que sumiu ou ficou vazia -> **erro**;
- queda maior que ``QUEDA_MAXIMA`` -> **erro** (as fontes só acumulam anos;
  perder linhas indica falha de extração ou mudança de formato);
- crescimento maior que ``CRESCIMENTO_MAXIMO`` -> **erro** (ex.: filtro de UF
  quebrado trazendo o Brasil inteiro);
- tabelas novas -> aviso.
Além disso, extratores que falharam nesta execução (``raw._cargas``) geram aviso.
O processo termina com código 1 se houver algum erro.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

#: Variação relativa tolerada entre duas cargas consecutivas.
QUEDA_MAXIMA = 0.05
CRESCIMENTO_MAXIMO = 0.50
#: Tabelas de controle, que crescem a cada execução por definição.
IGNORADAS = {"raw._cargas"}


@dataclass(frozen=True)
class Achado:
    nivel: str  # "erro" ou "aviso"
    tabela: str
    anterior: int | None
    atual: int | None
    mensagem: str


def _pct(fracao: float) -> str:
    return f"{100 * fracao:.1f}%".replace(".", ",")


def comparar(
    atual: dict[str, int],
    anterior: dict[str, int],
    queda_maxima: float = QUEDA_MAXIMA,
    crescimento_maximo: float = CRESCIMENTO_MAXIMO,
) -> list[Achado]:
    """Achados da comparação entre duas contagens ``{tabela: linhas}``."""
    achados: list[Achado] = []
    for tabela, antes in sorted(anterior.items()):
        if tabela in IGNORADAS:
            continue
        agora = atual.get(tabela)
        if agora is None:
            achados.append(Achado("erro", tabela, antes, None, "tabela sumiu"))
        elif agora == 0 and antes > 0:
            achados.append(Achado("erro", tabela, antes, 0, "tabela ficou vazia"))
        elif antes > 0:
            variacao = (agora - antes) / antes
            if variacao < -queda_maxima:
                achados.append(Achado("erro", tabela, antes, agora, f"queda de {_pct(-variacao)}"))
            elif variacao > crescimento_maximo:
                achados.append(
                    Achado("erro", tabela, antes, agora, f"crescimento de {_pct(variacao)}")
                )
    for tabela in sorted(set(atual) - set(anterior) - IGNORADAS):
        achados.append(Achado("aviso", tabela, None, atual[tabela], "tabela nova"))
    return achados


def falhas_de_extracao(banco: Path) -> list[Achado]:
    """Avisos para extratores cuja execução mais recente falhou (ver ``raw._cargas``)."""
    import duckdb

    if not banco.exists():
        return []
    with duckdb.connect(str(banco), read_only=True) as con:
        try:
            linhas = con.execute(
                "select extrator, arg_max(erro, finalizado_em) from raw._cargas "
                "group by extrator having not arg_max(sucesso, finalizado_em)"
            ).fetchall()
        except duckdb.CatalogException:
            return []
    return [
        Achado(
            "aviso", f"extrator {nome}", None, None, f"falhou; mantida a carga anterior ({erro})"
        )
        for nome, erro in linhas
    ]


def resumo_markdown(achados: list[Achado], atual: dict[str, int], anterior: dict[str, int]) -> str:
    erros = [a for a in achados if a.nivel == "erro"]
    titulo = "❌ Anomalias na carga" if erros else "✅ Carga dentro do esperado"
    linhas = [f"## {titulo}", ""]
    if achados:
        linhas += ["| Nível | Tabela | Anterior | Atual | Detalhe |", "|---|---|---:|---:|---|"]
        for a in achados:
            linhas.append(
                f"| {a.nivel} | `{a.tabela}` | {a.anterior if a.anterior is not None else '—'} "
                f"| {a.atual if a.atual is not None else '—'} | {a.mensagem} |"
            )
        linhas.append("")
    linhas += [
        "<details><summary>Contagens desta carga</summary>",
        "",
        "| Tabela | Anterior | Atual |",
        "|---|---:|---:|",
    ]
    for tabela in sorted(atual):
        linhas.append(f"| `{tabela}` | {anterior.get(tabela, '—')} | {atual[tabela]} |")
    linhas += ["", "</details>", ""]
    return "\n".join(linhas)


def _ler(caminho: Path | None) -> dict:
    if caminho is None or not caminho.exists():
        return {}
    return json.loads(caminho.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detecta anomalias na contagem de linhas.")
    parser.add_argument("contagens", type=Path)
    parser.add_argument("--anterior", type=Path)
    parser.add_argument("--banco", type=Path, help="banco DuckDB (para ler raw._cargas)")
    parser.add_argument("--historico", type=Path, help="acrescenta esta carga a um JSONL")
    parser.add_argument("--resumo", type=Path, help="grava o resumo em Markdown")
    args = parser.parse_args(argv)

    atual_doc = _ler(args.contagens)
    atual = atual_doc.get("tabelas", {})
    anterior = _ler(args.anterior).get("tabelas", {})
    achados = comparar(atual, anterior) if anterior else []
    if args.banco:
        achados += falhas_de_extracao(args.banco)

    texto = resumo_markdown(achados, atual, anterior)
    print(texto)
    if args.resumo:
        with args.resumo.open("a", encoding="utf-8") as f:
            f.write(texto)
    if args.historico:
        args.historico.parent.mkdir(parents=True, exist_ok=True)
        registro = {
            "gerado_em": atual_doc.get("gerado_em"),
            "tabelas": atual,
            "erros": sum(a.nivel == "erro" for a in achados),
            "avisos": sum(a.nivel == "aviso" for a in achados),
        }
        with args.historico.open("a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    if not anterior:
        print("Sem carga anterior para comparar; nada a verificar.")
    return 1 if any(a.nivel == "erro" for a in achados) else 0


if __name__ == "__main__":
    sys.exit(main())

"""Definição dos indicadores do painel e formatação em português (pt-BR).

Separado da interface para poder ser testado sem o Streamlit.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

ETAPAS = {
    "anos_iniciais": "Anos iniciais (1º ao 5º)",
    "anos_finais": "Anos finais (6º ao 9º)",
    "ensino_medio": "Ensino médio",
}
REDES = {"publica": "Pública (todas)", "municipal": "Municipal", "estadual": "Estadual"}


def ausente(valor) -> bool:
    """Verdadeiro para None, NaN e pd.NA."""
    try:
        return bool(pd.isna(valor))
    except (TypeError, ValueError):
        return False


def numero(valor: float | None, casas: int = 0) -> str:
    """Formata no padrão brasileiro: 1.234.567,89."""
    if ausente(valor):
        return "—"
    valor = float(valor)
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def reais(valor: float | None, curto: bool = False) -> str:
    if ausente(valor):
        return "—"
    valor = float(valor)
    if curto:
        for limite, sufixo in ((1e9, "bi"), (1e6, "mi"), (1e3, "mil")):
            if abs(valor) >= limite:
                return f"R$ {numero(valor / limite, 1)} {sufixo}"
    return f"R$ {numero(valor, 2)}"


@dataclass(frozen=True)
class Indicador:
    fonte: str
    coluna: str
    rotulo_curto: str
    formato_plotly: str
    formato_hover: str
    formatar: Callable[[float | None], str]


INDICADORES: dict[str, Indicador] = {
    "IDEB": Indicador("ideb", "ideb", "IDEB", ":.1f", ":.1f", lambda v: numero(v, 1)),
    "Investimento por aluno (rede municipal)": Indicador(
        "investimento",
        "investimento_por_aluno",
        "Investimento por aluno",
        ":,.0f",
        ":,.0f",
        reais,
    ),
    "Despesa em Educação por habitante": Indicador(
        "despesa",
        "despesa_educacao_per_capita",
        "Despesa por habitante",
        ":,.0f",
        ":,.0f",
        reais,
    ),
    "Parcela da despesa total destinada à Educação (%)": Indicador(
        "despesa",
        "percentual_educacao",
        "Parcela da despesa (%)",
        ":.1f",
        ":.1f",
        lambda v: f"{numero(v, 1)}%",
    ),
}


def serie(
    d: dict[str, pd.DataFrame], nome: str, etapa: str | None = None, rede: str | None = None
) -> pd.DataFrame:
    """Série (cod_municipio, nome_municipio, ano, valor) do indicador escolhido."""
    definicao = INDICADORES[nome]
    base = d[definicao.fonte]
    if definicao.fonte == "ideb":
        base = base[(base["etapa"] == etapa) & (base["rede"] == rede)]
    resultado = base[["cod_municipio", "nome_municipio", "ano", definicao.coluna]].rename(
        columns={definicao.coluna: "valor"}
    )
    resultado = resultado.dropna(subset=["valor"])
    resultado["valor"] = resultado["valor"].astype(float)
    return resultado.reset_index(drop=True)


def comparativo(d: dict[str, pd.DataFrame], nomes: list[str]) -> pd.DataFrame:
    """Tabela lado a lado com o valor mais recente de cada indicador."""
    linhas = {}
    pop = d["municipios"].set_index("nome_municipio")["populacao_censo_2022"]
    linhas["População (Censo 2022)"] = {n: numero(pop.get(n)) for n in nomes}
    for etapa, rotulo in ETAPAS.items():
        s = serie(d, "IDEB", etapa=etapa, rede="publica")
        linhas[f"IDEB {rotulo} – rede pública"] = _mais_recente(s, nomes, lambda v: numero(v, 1))
    for nome, definicao in INDICADORES.items():
        if definicao.fonte != "ideb":
            linhas[nome] = _mais_recente(serie(d, nome), nomes, definicao.formatar)
    return pd.DataFrame(linhas).T[nomes]


def _mais_recente(s: pd.DataFrame, nomes: list[str], formatar) -> dict[str, str]:
    saida = {}
    for n in nomes:
        linhas = s[s["nome_municipio"] == n].sort_values("ano")
        if linhas.empty:
            saida[n] = "—"
        else:
            ultimo = linhas.iloc[-1]
            saida[n] = f"{formatar(ultimo['valor'])} ({int(ultimo['ano'])})"
    return saida

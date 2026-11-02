"""Valida o acesso às fontes públicas candidatas e gera amostras pequenas.

Roda no GitHub Actions (o ambiente de desenvolvimento não alcança os sites do
governo). Para cada fonte, registra status HTTP, tipo de conteúdo, tamanho e
hash, e salva uma amostra filtrada para o Tocantins em ``saida/amostras``.

Uso: python scripts/validar_fontes.py saida
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
import time
import urllib.error
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path

UA = "dados-abertos-tocantins/0.1 (+https://github.com/rafantavares/dados-abertos-tocantins)"

FONTES: list[dict] = [
    {
        "id": "ibge_localidades_municipios_to",
        "url": "https://servicodados.ibge.gov.br/api/v1/localidades/estados/17/municipios",
    },
    {
        "id": "ibge_sidra_censo2022_populacao",
        "url": "https://apisidra.ibge.gov.br/values/t/4709/n6/in%20n3%2017/v/93/p/all",
    },
    {
        "id": "ibge_sidra_estimativas_populacao",
        "url": "https://apisidra.ibge.gov.br/values/t/6579/n6/in%20n3%2017/v/9324/p/all",
    },
    {
        "id": "ibge_malha_municipios_to",
        "url": "https://servicodados.ibge.gov.br/api/v3/malhas/estados/17"
        "?intrarregiao=municipio&formato=application/vnd.geo%2Bjson&qualidade=minima",
    },
    {
        "id": "inep_ideb_anos_iniciais_municipios_2023",
        "url": "https://download.inep.gov.br/ideb/resultados/divulgacao_anos_iniciais_municipios_2023.zip",
    },
    {
        "id": "inep_ideb_anos_finais_municipios_2023",
        "url": "https://download.inep.gov.br/ideb/resultados/divulgacao_anos_finais_municipios_2023.zip",
    },
    {
        "id": "inep_ideb_ensino_medio_municipios_2023",
        "url": "https://download.inep.gov.br/ideb/resultados/divulgacao_ensino_medio_municipios_2023.zip",
    },
    {
        "id": "inep_censo_escolar_2023",
        "url": "https://download.inep.gov.br/dados_abertos/microdados_censo_escolar_2023.zip",
    },
    {
        "id": "inep_censo_escolar_2024",
        "url": "https://download.inep.gov.br/dados_abertos/microdados_censo_escolar_2024.zip",
    },
    {
        "id": "siconfi_entes",
        "url": "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/entes",
    },
    {
        "id": "siconfi_dca_anexo_ie_palmas_2023",
        "url": "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca"
        "?an_exercicio=2023&no_anexo=DCA-Anexo%20I-E&id_ente=1721000",
    },
    {
        "id": "siconfi_dca_anexo_ie_estado_to_2023",
        "url": "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca"
        "?an_exercicio=2023&no_anexo=DCA-Anexo%20I-E&id_ente=17",
    },
    {
        "id": "siconfi_rreo_anexo08_estado_to_2023",
        "url": "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/rreo"
        "?an_exercicio=2023&nr_periodo=6&co_tipo_demonstrativo=RREO"
        "&no_anexo=RREO-Anexo%2008&id_ente=17",
    },
    {
        "id": "transparencia_to_portal",
        "url": "https://www.transparencia.to.gov.br/",
    },
    {
        "id": "transparencia_to_dados_abertos",
        "url": "https://www.transparencia.to.gov.br/dados-abertos",
    },
    {
        "id": "dados_gov_br_portal",
        "url": "https://dados.gov.br/",
    },
    {
        "id": "dados_gov_br_api_publica",
        "url": "https://dados.gov.br/dados/api/publico/conjuntos-dados?isPrivado=false&pagina=1&nomeConjuntoDados=tocantins",
    },
]

LIMITE_BYTES = 600 * 1024 * 1024


def baixar(
    url: str, tentativas: int = 3, timeout: int = 120
) -> tuple[int, dict, bytes]:
    ultimo_erro: Exception | None = None
    for tentativa in range(1, tentativas + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                corpo = resp.read(LIMITE_BYTES)
                return resp.status, dict(resp.headers), corpo
        except urllib.error.HTTPError as erro:
            return erro.code, dict(erro.headers or {}), erro.read()[:2000]
        except Exception as erro:  # noqa: BLE001 - registramos qualquer falha de rede
            ultimo_erro = erro
            time.sleep(2**tentativa)
    raise RuntimeError(f"falha após {tentativas} tentativas: {ultimo_erro!r}")


def amostrar(fonte_id: str, corpo: bytes, destino: Path) -> dict:
    """Gera amostra pequena e um resumo da estrutura do arquivo."""
    import pandas as pd

    resumo: dict = {}
    if corpo[:2] == b"PK":
        zf = zipfile.ZipFile(io.BytesIO(corpo))
        resumo["arquivos_zip"] = [(i.filename, i.file_size) for i in zf.infolist()]
        for info in zf.infolist():
            nome = info.filename.lower()
            if nome.endswith(".xlsx"):
                bruto = pd.read_excel(zf.open(info), header=None, dtype=str)
                resumo["xlsx_primeiras_linhas"] = (
                    bruto.head(12).fillna("").values.tolist()
                )
                linha_cab = next(
                    i for i, row in bruto.iterrows() if "SG_UF" in row.values
                )
                df = bruto.iloc[linha_cab + 1 :].copy()
                df.columns = bruto.iloc[linha_cab].values
                df = df[df["SG_UF"] == "TO"]
                resumo["linhas_to"] = len(df)
                df.to_csv(destino / f"{fonte_id}_TO.csv", index=False)
            elif nome.endswith(".csv") and "ed_basica" in nome:
                df = pd.read_csv(
                    zf.open(info),
                    sep=";",
                    encoding="latin-1",
                    dtype=str,
                    low_memory=False,
                )
                resumo["colunas"] = list(df.columns)
                resumo["linhas_total"] = len(df)
                df = df[df["SG_UF"] == "TO"]
                resumo["linhas_to"] = len(df)
                colunas = [
                    c
                    for c in df.columns
                    if c
                    in {
                        "NU_ANO_CENSO",
                        "SG_UF",
                        "CO_MUNICIPIO",
                        "NO_MUNICIPIO",
                        "CO_ENTIDADE",
                        "NO_ENTIDADE",
                        "TP_DEPENDENCIA",
                        "TP_LOCALIZACAO",
                        "TP_SITUACAO_FUNCIONAMENTO",
                    }
                    or c.startswith("QT_MAT_")
                ]
                df[colunas].to_csv(destino / f"{fonte_id}_TO.csv", index=False)
    else:
        texto = corpo.decode("utf-8", errors="replace")
        (destino / f"{fonte_id}.txt").write_text(texto[:200_000], encoding="utf-8")
        try:
            dado = json.loads(texto)
            if isinstance(dado, dict):
                resumo["chaves"] = list(dado.keys())
                itens = dado.get("items")
                if isinstance(itens, list):
                    resumo["n_items"] = len(itens)
                    resumo["has_more"] = dado.get("hasMore")
                    resumo["exemplo"] = itens[:3]
            elif isinstance(dado, list):
                resumo["n_registros"] = len(dado)
                resumo["exemplo"] = dado[:2]
        except json.JSONDecodeError:
            resumo["inicio_texto"] = texto[:500]
    return resumo


def main(saida: str) -> None:
    base = Path(saida)
    amostras = base / "amostras"
    amostras.mkdir(parents=True, exist_ok=True)
    relatorio = []
    for fonte in FONTES:
        registro: dict = {
            "id": fonte["id"],
            "url": fonte["url"],
            "acessado_em": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        try:
            status, cabecalhos, corpo = baixar(fonte["url"])
            registro.update(
                status=status,
                content_type=cabecalhos.get("Content-Type"),
                last_modified=cabecalhos.get("Last-Modified"),
                bytes=len(corpo),
                sha256=hashlib.sha256(corpo).hexdigest(),
            )
            if status == 200:
                registro["resumo"] = amostrar(fonte["id"], corpo, amostras)
            else:
                registro["inicio_resposta"] = corpo[:300].decode(
                    "utf-8", errors="replace"
                )
        except Exception as erro:  # noqa: BLE001
            registro["erro"] = repr(erro)
        print(json.dumps(registro, ensure_ascii=False, default=str)[:4000], flush=True)
        relatorio.append(registro)
    (base / "relatorio.json").write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "saida")

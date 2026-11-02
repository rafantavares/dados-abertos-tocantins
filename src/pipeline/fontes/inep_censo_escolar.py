"""Matrículas por escola do Censo Escolar (INEP), filtradas para o Tocantins.

Usa a tabela de escolas dos microdados (``microdados_ed_basica_<ano>.csv``),
que já traz as quantidades de matrícula por etapa. Grava em
``raw.inep_censo_escolas`` particionado por ano. Anos já carregados não são
baixados de novo (exceto os dois mais recentes, que o INEP pode republicar).
"""

from __future__ import annotations

import io
import logging
import zipfile
from datetime import date

import duckdb
import pandas as pd

from pipeline.carga import gravar_particao, particoes_existentes
from pipeline.config import CODIGO_UF_TO, PASTA_FIXTURES, pasta_cache
from pipeline.http import ErroDownload, baixar_com_cache

log = logging.getLogger(__name__)

TABELA = "raw.inep_censo_escolas"
URL = "https://download.inep.gov.br/dados_abertos/microdados_censo_escolar_{ano}.zip"
PRIMEIRO_ANO = 2019

COLUNAS = [
    "NU_ANO_CENSO",
    "SG_UF",
    "CO_UF",
    "CO_MUNICIPIO",
    "NO_MUNICIPIO",
    "CO_ENTIDADE",
    "NO_ENTIDADE",
    "TP_DEPENDENCIA",
    "TP_LOCALIZACAO",
    "TP_SITUACAO_FUNCIONAMENTO",
    "QT_MAT_BAS",
    "QT_MAT_INF",
    "QT_MAT_FUND",
    "QT_MAT_MED",
    "QT_MAT_PROF",
    "QT_MAT_EJA",
    "QT_MAT_ESP",
]


def anos_candidatos(hoje: date | None = None) -> list[int]:
    """Do primeiro ano até o ano anterior ao atual (o Censo sai no ano seguinte)."""
    hoje = hoje or date.today()
    return list(range(PRIMEIRO_ANO, hoje.year))


def ler_escolas(conteudo_zip: bytes) -> pd.DataFrame:
    """Lê a tabela de escolas do ZIP e mantém só as escolas do Tocantins."""
    with zipfile.ZipFile(io.BytesIO(conteudo_zip)) as zf:
        nome = next(
            n
            for n in zf.namelist()
            if "microdados_ed_basica" in n.lower() and n.lower().endswith(".csv")
        )
        with zf.open(nome) as arquivo:
            partes = pd.read_csv(
                arquivo,
                sep=";",
                encoding="latin-1",
                dtype=str,
                usecols=lambda c: c in COLUNAS,
                chunksize=50_000,
            )
            return pd.concat(
                [p[p["CO_UF"] == str(CODIGO_UF_TO)] for p in partes], ignore_index=True
            )


def extrair(con: duckdb.DuckDBPyConnection, usar_fixtures: bool = False) -> int:
    if usar_fixtures:
        arquivo = PASTA_FIXTURES / "inep" / "censo_escolas.csv"
        df = pd.read_csv(arquivo, dtype=str)
        total = 0
        for ano, parte in df.groupby("NU_ANO_CENSO"):
            total += gravar_particao(
                con,
                TABELA,
                parte,
                coluna_particao="NU_ANO_CENSO",
                valor_particao=str(ano),
                fonte_url=f"fixture:{arquivo.name}",
            )
        return total

    carregados = particoes_existentes(con, TABELA, "NU_ANO_CENSO")
    anos = anos_candidatos()
    recentes = set(anos[-2:])
    total = 0
    for ano in anos:
        if str(ano) in carregados and ano not in recentes:
            log.info("censo %s já carregado; pulando", ano)
            continue
        url = URL.format(ano=ano)
        try:
            conteudo = baixar_com_cache(url, pasta_cache() / "inep_censo")
        except ErroDownload as erro:
            log.warning("censo %s indisponível: %s", ano, erro)
            continue
        df = ler_escolas(conteudo)
        if "QT_MAT_BAS" not in df.columns:
            log.warning("censo %s sem contagem de matrículas na tabela de escolas", ano)
            continue
        total += gravar_particao(
            con, TABELA, df, coluna_particao="NU_ANO_CENSO", valor_particao=str(ano), fonte_url=url
        )
    return total

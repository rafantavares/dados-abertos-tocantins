"""IPCA mensal (IBGE/SIDRA, tabela 1737), usado para corrigir valores pela inflação.

Baixa o número-índice do IPCA (variável 2266, base dez/1993 = 100) para o
Brasil, todos os meses. Grava em ``raw.ibge_sidra_ipca`` (partição = número da
tabela). A série inteira é pequena e muda todo mês, por isso é sempre
recarregada.
"""

from __future__ import annotations

import duckdb
import pandas as pd

from pipeline.carga import gravar_particao
from pipeline.config import PASTA_FIXTURES
from pipeline.fontes.ibge import ler_sidra
from pipeline.http import baixar

TABELA = "raw.ibge_sidra_ipca"
TABELA_SIDRA = "1737"
URL = f"https://apisidra.ibge.gov.br/values/t/{TABELA_SIDRA}/n1/all/v/2266/p/all"


def extrair(con: duckdb.DuckDBPyConnection, usar_fixtures: bool = False) -> int:
    if usar_fixtures:
        arquivo = PASTA_FIXTURES / "ibge" / "ibge_sidra_ipca.csv"
        df = pd.read_csv(arquivo, dtype=str).drop(columns=["_referencia"], errors="ignore")
        url = f"fixture:{arquivo.name}"
    else:
        df, url = ler_sidra(baixar(URL)), URL
    return gravar_particao(
        con, TABELA, df, coluna_particao="_referencia", valor_particao=TABELA_SIDRA, fonte_url=url
    )

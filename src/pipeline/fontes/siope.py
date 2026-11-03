"""Indicadores oficiais de educação do SIOPE (FNDE), Estado e municípios do Tocantins.

Usa a API OData de dados abertos do FNDE (``DADOS_ABERTOS_SIOPE``, plataforma
Olinda), função ``Indicadores_Siope``: uma linha por ente e indicador, com o
percentual aplicado em Manutenção e Desenvolvimento do Ensino (MDE), os
indicadores do Fundeb e o investimento por aluno declarados pelo próprio ente.
Considera o 6º bimestre (dados anuais). Grava em ``raw.siope_indicadores``,
particionado por ano.

Anos já carregados não são consultados de novo, exceto os dois mais recentes
(os entes entregam e retificam a declaração com atraso).
"""

from __future__ import annotations

import json
import logging
import urllib.parse
from datetime import date

import duckdb
import pandas as pd

from pipeline.carga import gravar_particao, particoes_existentes
from pipeline.config import PASTA_FIXTURES, SIGLA_UF_TO
from pipeline.http import baixar

log = logging.getLogger(__name__)

BASE = "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata"
TABELA = "raw.siope_indicadores"
PRIMEIRO_ANO = 2015
#: 6º bimestre = declaração anual consolidada.
PERIODO_ANUAL = 6
TAMANHO_PAGINA = 10_000


def anos_candidatos(hoje: date | None = None) -> list[int]:
    hoje = hoje or date.today()
    return list(range(PRIMEIRO_ANO, hoje.year))


def url_indicadores(ano: int, skip: int = 0) -> str:
    parametros = {
        "@Ano_Consulta": ano,
        "@Num_Peri": PERIODO_ANUAL,
        "@Sig_UF": f"'{SIGLA_UF_TO}'",
        "$format": "json",
        "$top": TAMANHO_PAGINA,
        "$skip": skip,
    }
    funcao = "Indicadores_Siope(Ano_Consulta=@Ano_Consulta,Num_Peri=@Num_Peri,Sig_UF=@Sig_UF)"
    return f"{BASE}/{funcao}?{urllib.parse.urlencode(parametros, safe='@$')}"


def indicadores(ano: int) -> pd.DataFrame:
    """Todos os indicadores do ano para o Estado e os municípios do Tocantins."""
    registros: list[dict] = []
    skip = 0
    while True:
        pagina = json.loads(baixar(url_indicadores(ano, skip), timeout=120)).get("value", [])
        registros.extend(pagina)
        if len(pagina) < TAMANHO_PAGINA:
            break
        skip += TAMANHO_PAGINA
    # dtype=object preserva os valores como vieram: com o Estado tendo COD_MUNI
    # nulo, o pandas converteria a coluna para float ("172100.0").
    return pd.DataFrame(registros, dtype=object)


def extrair(con: duckdb.DuckDBPyConnection, usar_fixtures: bool = False) -> int:
    if usar_fixtures:
        arquivo = PASTA_FIXTURES / "siope" / "siope_indicadores.csv"
        df = pd.read_csv(arquivo, dtype=str)
        total = 0
        for ano, parte in df.groupby("NUM_ANO"):
            total += gravar_particao(
                con,
                TABELA,
                parte,
                coluna_particao="NUM_ANO",
                valor_particao=str(ano),
                fonte_url=f"fixture:{arquivo.name}",
            )
        return total

    carregados = particoes_existentes(con, TABELA, "NUM_ANO")
    anos = anos_candidatos()
    recentes = set(anos[-2:])
    total = 0
    for ano in anos:
        if str(ano) in carregados and ano not in recentes:
            log.info("SIOPE %s já carregado; pulando", ano)
            continue
        df = indicadores(ano)
        if df.empty:
            log.warning("SIOPE %s: nenhum indicador publicado ainda", ano)
            continue
        log.info(
            "SIOPE %s: %d indicadores de %d entes",
            ano,
            len(df),
            df["COD_MUNI"].nunique(dropna=False),
        )
        total += gravar_particao(
            con,
            TABELA,
            df,
            coluna_particao="NUM_ANO",
            valor_particao=str(ano),
            fonte_url=url_indicadores(ano),
        )
    return total

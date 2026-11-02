"""Despesa por função (DCA - Anexo I-E) do SICONFI, para o Estado e os municípios.

Usa a API aberta do Tesouro Nacional. Para cada exercício, consulta o Estado do
Tocantins e cada município do estado (lista obtida em ``/entes``) e guarda só
as linhas necessárias ao projeto: os totais da despesa e as contas da função
12 - Educação. Grava em ``raw.siconfi_dca_despesa_funcao`` particionado por
exercício e a lista de entes em ``raw.siconfi_entes``.

Exercícios já carregados não são consultados de novo, exceto os dois mais
recentes (municípios entregam ou retificam a declaração com atraso).
"""

from __future__ import annotations

import json
import logging
import time
import urllib.parse
from datetime import date

import duckdb
import pandas as pd

from pipeline.carga import gravar_particao, particoes_existentes
from pipeline.config import CODIGO_UF_TO, PASTA_FIXTURES, SIGLA_UF_TO
from pipeline.http import baixar

log = logging.getLogger(__name__)

BASE = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
ANEXO = "DCA-Anexo I-E"
TABELA = "raw.siconfi_dca_despesa_funcao"
TABELA_ENTES = "raw.siconfi_entes"
PRIMEIRO_ANO = 2015
#: Pausa entre requisições para não sobrecarregar a API pública.
PAUSA_SEGUNDOS = 0.2


def anos_candidatos(hoje: date | None = None) -> list[int]:
    """Do primeiro exercício ao anterior ao atual (o DCA é entregue até 30/04)."""
    hoje = hoje or date.today()
    return list(range(PRIMEIRO_ANO, hoje.year))


def conta_relevante(conta: str) -> bool:
    """Totais da despesa e contas da função 12 - Educação."""
    conta = conta.strip()
    return conta.startswith(("Despesas ", "12 ", "12.", "FU12 "))


def consultar(caminho: str, parametros: dict[str, str | int]) -> list[dict]:
    """Consulta paginada da API do SICONFI (campos ``items``/``hasMore``)."""
    itens: list[dict] = []
    offset = 0
    while True:
        query = urllib.parse.urlencode(
            {**parametros, "offset": offset}, quote_via=urllib.parse.quote
        )
        dados = json.loads(baixar(f"{BASE}/{caminho}?{query}", timeout=90))
        itens.extend(dados.get("items", []))
        if not dados.get("hasMore"):
            return itens
        offset += int(dados.get("limit") or len(dados.get("items", [])) or 5000)


def entes_tocantins() -> pd.DataFrame:
    entes = pd.DataFrame(consultar("entes", {}))
    entes = entes[(entes["uf"] == SIGLA_UF_TO) | (entes["cod_ibge"] == CODIGO_UF_TO)]
    return entes.reset_index(drop=True)


def dca_ente(ano: int, cod_ibge: int) -> pd.DataFrame:
    itens = consultar("dca", {"an_exercicio": ano, "no_anexo": ANEXO, "id_ente": cod_ibge})
    df = pd.DataFrame(itens)
    if df.empty:
        return df
    return df[df["conta"].map(conta_relevante)].reset_index(drop=True)


def _extrair_fixtures(con: duckdb.DuckDBPyConnection) -> int:
    pasta = PASTA_FIXTURES / "siconfi"
    entes = pd.read_csv(pasta / "siconfi_entes.csv", dtype=str)
    total = gravar_particao(
        con,
        TABELA_ENTES,
        entes,
        coluna_particao="_uf_consulta",
        valor_particao=SIGLA_UF_TO,
        fonte_url="fixture:siconfi_entes.csv",
    )
    dca = pd.read_csv(pasta / "siconfi_dca_despesa_funcao.csv", dtype=str)
    for ano, parte in dca.groupby("exercicio"):
        total += gravar_particao(
            con,
            TABELA,
            parte,
            coluna_particao="exercicio",
            valor_particao=str(ano),
            fonte_url="fixture:siconfi_dca_despesa_funcao.csv",
        )
    return total


def extrair(con: duckdb.DuckDBPyConnection, usar_fixtures: bool = False) -> int:
    if usar_fixtures:
        return _extrair_fixtures(con)

    entes = entes_tocantins()
    total = gravar_particao(
        con,
        TABELA_ENTES,
        entes,
        coluna_particao="_uf_consulta",
        valor_particao=SIGLA_UF_TO,
        fonte_url=f"{BASE}/entes",
    )
    codigos = sorted(int(c) for c in entes["cod_ibge"])
    carregados = particoes_existentes(con, TABELA, "exercicio")
    anos = anos_candidatos()
    recentes = set(anos[-2:])
    for ano in anos:
        if str(ano) in carregados and ano not in recentes:
            log.info("DCA %s já carregado; pulando", ano)
            continue
        partes = []
        sem_declaracao = 0
        for cod in codigos:
            df = dca_ente(ano, cod)
            if df.empty:
                sem_declaracao += 1
            else:
                partes.append(df)
            time.sleep(PAUSA_SEGUNDOS)
        if not partes:
            log.warning("DCA %s: nenhum ente declarou ainda", ano)
            continue
        log.info("DCA %s: %d entes sem declaração", ano, sem_declaracao)
        total += gravar_particao(
            con,
            TABELA,
            pd.concat(partes, ignore_index=True),
            coluna_particao="exercicio",
            valor_particao=str(ano),
            fonte_url=f"{BASE}/dca?no_anexo={ANEXO}",
        )
    return total

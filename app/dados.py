"""Acesso aos dados do painel.

O painel lê o banco DuckDB publicado na branch ``dados`` pelo pipeline:

- ``DADOS_DUCKDB_URL``: URL do arquivo (padrão: raw.githubusercontent.com da
  branch ``dados`` deste repositório). O arquivo é baixado para um cache local
  e reaproveitado por ``DADOS_CACHE_HORAS`` horas (padrão 6).
- ``DADOS_DUCKDB_PATH``: caminho de um banco local; tem prioridade sobre a URL
  (útil para desenvolvimento e para as capturas de tela).
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

import duckdb
import httpx
import pandas as pd

URL_PADRAO = (
    "https://raw.githubusercontent.com/rafantavares/dados-abertos-tocantins/dados/tocantins.duckdb"
)
PASTA_CACHE = Path(os.environ.get("DADOS_CACHE_DIR", Path.home() / ".cache" / "dados-tocantins"))


def caminho_banco() -> Path:
    """Devolve o caminho de um banco local, baixando-o da URL se necessário."""
    local = os.environ.get("DADOS_DUCKDB_PATH")
    if local:
        return Path(local)
    url = os.environ.get("DADOS_DUCKDB_URL", URL_PADRAO)
    destino = PASTA_CACHE / "tocantins.duckdb"
    validade = float(os.environ.get("DADOS_CACHE_HORAS", "6")) * 3600
    if destino.exists() and time.time() - destino.stat().st_mtime < validade:
        return destino
    PASTA_CACHE.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=120, follow_redirects=True) as cliente:
        resposta = cliente.get(url)
        resposta.raise_for_status()
    with tempfile.NamedTemporaryFile(dir=PASTA_CACHE, delete=False) as tmp:
        tmp.write(resposta.content)
    Path(tmp.name).replace(destino)
    return destino


def consultar(banco: Path, sql: str, parametros: list | None = None) -> pd.DataFrame:
    with duckdb.connect(str(banco), read_only=True) as con:
        return con.execute(sql, parametros or []).df()


def municipios(banco: Path) -> pd.DataFrame:
    return consultar(
        banco,
        "select cod_municipio, nome_municipio, regiao_intermediaria, populacao_censo_2022, "
        "eh_capital from marts.dim_municipio order by nome_municipio",
    )


def geojson_municipios(banco: Path) -> dict:
    """FeatureCollection com ``id`` = código IBGE do município."""
    linhas = consultar(banco, "select cod_municipio, geojson from marts.dim_municipio_geometria")
    return {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "id": int(cod), "properties": {}, "geometry": json.loads(geo)}
            for cod, geo in linhas.itertuples(index=False)
        ],
    }


def ideb(banco: Path) -> pd.DataFrame:
    return consultar(
        banco,
        "select f.*, m.nome_municipio from marts.fct_ideb f "
        "join marts.dim_municipio m using (cod_municipio) where f.ideb is not null",
    )


def despesa_municipal(banco: Path) -> pd.DataFrame:
    return consultar(
        banco,
        "select f.*, m.nome_municipio from marts.fct_despesa_educacao f "
        "join marts.dim_municipio m on f.cod_ente = m.cod_municipio "
        "where f.esfera = 'municipal'",
    ).rename(columns={"cod_ente": "cod_municipio"})


def investimento_aluno(banco: Path) -> pd.DataFrame:
    return consultar(
        banco,
        "select i.*, m.nome_municipio from marts.mart_investimento_aluno i "
        "join marts.dim_municipio m using (cod_municipio)",
    )


COLUNAS_SIOPE = [
    "cod_municipio",
    "nome_municipio",
    "ano",
    "percentual_mde",
    "cumpre_minimo_mde",
    "investimento_por_aluno_educacao_basica",
]


def mde_siope(banco: Path) -> pd.DataFrame:
    """Indicadores oficiais do SIOPE dos municípios.

    Devolve uma tabela vazia se o banco ainda não tiver o mart (banco publicado
    antes da integração do SIOPE).
    """
    try:
        return consultar(
            banco,
            "select s.cod_ente as cod_municipio, m.nome_municipio, s.ano, s.percentual_mde, "
            "s.cumpre_minimo_mde, s.investimento_por_aluno_educacao_basica "
            "from marts.mart_mde_siope s "
            "join marts.dim_municipio m on s.cod_ente = m.cod_municipio",
        )
    except duckdb.CatalogException:
        return pd.DataFrame(columns=COLUNAS_SIOPE)


def matriculas(banco: Path) -> pd.DataFrame:
    return consultar(
        banco,
        "select f.*, m.nome_municipio from marts.fct_matriculas f "
        "join marts.dim_municipio m using (cod_municipio)",
    )


def resumo_estadual(banco: Path) -> pd.DataFrame:
    return consultar(banco, "select * from marts.mart_resumo_estadual order by ano")


def ultima_carga(banco: Path) -> pd.DataFrame:
    return consultar(
        banco,
        "select extrator as fonte, max(finalizado_em) as ultima_execucao, "
        "arg_max(sucesso, finalizado_em) as ultima_execucao_ok, "
        "max(finalizado_em) filter (where sucesso) as ultima_carga_com_sucesso "
        "from raw._cargas group by extrator order by extrator",
    )

"""Referência de municípios do IBGE: DTB, população (SIDRA) e malha municipal.

- ``raw.ibge_dtb_municipios``: Divisão Territorial Brasileira (códigos, nomes
  e regiões geográficas) dos municípios do Tocantins.
- ``raw.ibge_sidra_populacao``: população residente do Censo 2022 (tabela
  4709) e estimativas anuais (tabela 6579), por município.
- ``raw.ibge_malha_municipios``: contorno de cada município em GeoJSON,
  simplificado para uso no mapa do painel.

A API ``servicodados.ibge.gov.br`` não responde a partir do GitHub Actions
(ver docs/fontes.md), por isso usamos o geoftp e o SIDRA.
"""

from __future__ import annotations

import io
import json
import logging
import zipfile

import duckdb
import pandas as pd

from pipeline.carga import gravar_particao
from pipeline.config import CODIGO_UF_TO, PASTA_FIXTURES, pasta_cache
from pipeline.http import baixar, baixar_com_cache

log = logging.getLogger(__name__)

ANO_DTB = 2022
URL_DTB = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/"
    "divisao_territorial/{ano}/DTB_{ano}.zip"
)
URL_MALHA = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/"
    "malhas_municipais/municipio_{ano}/UFs/TO/TO_Municipios_{ano}.zip"
)
URL_SIDRA = "https://apisidra.ibge.gov.br/values/t/{tabela}/n6/in%20n3%2017/v/{variavel}/p/all"
#: Tabelas do SIDRA: (tabela, variável) -> descrição.
TABELAS_SIDRA = {
    ("4709", "93"): "Censo 2022 - população residente",
    ("6579", "9324"): "Estimativas - população residente estimada",
}
#: Tolerância de simplificação da malha, em graus (~100 m).
TOLERANCIA_GRAUS = 0.001


def ler_dtb(conteudo_zip: bytes) -> pd.DataFrame:
    """Lê a planilha de municípios da DTB e mantém os do Tocantins.

    A planilha começa com linhas de título; o cabeçalho é a primeira linha
    totalmente preenchida.
    """
    with zipfile.ZipFile(io.BytesIO(conteudo_zip)) as zf:
        nome = next(
            n
            for n in zf.namelist()
            if n.upper().endswith("MUNICIPIO.XLS") or n.upper().endswith("MUNICIPIO.XLSX")
        )
        bruto = pd.read_excel(zf.open(nome), header=None, dtype=str)
    cabecalho = next(i for i, linha in bruto.iterrows() if linha.notna().all())
    df = bruto.iloc[cabecalho + 1 :].copy()
    df.columns = [str(c).strip() for c in bruto.iloc[cabecalho].values]
    primeira = df.columns[0]
    return df[df[primeira].str.strip() == str(CODIGO_UF_TO)].reset_index(drop=True)


def ler_sidra(conteudo_json: bytes) -> pd.DataFrame:
    """A primeira linha da resposta do SIDRA descreve as colunas; o resto são dados."""
    registros = json.loads(conteudo_json)
    return pd.DataFrame(registros[1:])


def ler_malha(conteudo_zip: bytes, tolerancia: float = TOLERANCIA_GRAUS) -> pd.DataFrame:
    """Converte o shapefile em GeoJSON simplificado (uma linha por município)."""
    import shapefile
    from shapely.geometry import mapping, shape

    with zipfile.ZipFile(io.BytesIO(conteudo_zip)) as zf:
        base = next(n for n in zf.namelist() if n.lower().endswith(".shp"))[:-4]
        leitor = shapefile.Reader(
            shp=io.BytesIO(zf.read(base + ".shp")),
            shx=io.BytesIO(zf.read(base + ".shx")),
            dbf=io.BytesIO(zf.read(base + ".dbf")),
            encoding="utf-8",
        )
        campos = [f[0] for f in leitor.fields[1:]]
        linhas = []
        for registro in leitor.iterShapeRecords():
            atributos = dict(zip(campos, registro.record, strict=True))
            geometria = shape(registro.shape.__geo_interface__).simplify(
                tolerancia, preserve_topology=True
            )
            atributos["geojson"] = json.dumps(mapping(geometria), separators=(",", ":"))
            linhas.append(atributos)
    return pd.DataFrame(linhas)


def _gravar(con, tabela, df, valor, url):
    return gravar_particao(
        con, tabela, df, coluna_particao="_referencia", valor_particao=valor, fonte_url=url
    )


def extrair(con: duckdb.DuckDBPyConnection, usar_fixtures: bool = False) -> int:
    total = 0
    if usar_fixtures:
        pasta = PASTA_FIXTURES / "ibge"
        for tabela in ("ibge_dtb_municipios", "ibge_sidra_populacao", "ibge_malha_municipios"):
            df = pd.read_csv(pasta / f"{tabela}.csv", dtype=str)
            referencia = "_referencia"
            for valor, parte in df.groupby(referencia):
                total += _gravar(
                    con,
                    f"raw.{tabela}",
                    parte.drop(columns=[referencia]),
                    str(valor),
                    f"fixture:{tabela}.csv",
                )
        return total

    cache = pasta_cache() / "ibge"
    url = URL_DTB.format(ano=ANO_DTB)
    total += _gravar(
        con, "raw.ibge_dtb_municipios", ler_dtb(baixar_com_cache(url, cache)), str(ANO_DTB), url
    )

    for (tabela, variavel), descricao in TABELAS_SIDRA.items():
        url = URL_SIDRA.format(tabela=tabela, variavel=variavel)
        log.info("SIDRA %s (%s)", tabela, descricao)
        # Sem cache: as estimativas ganham um ano novo a cada divulgação.
        total += _gravar(con, "raw.ibge_sidra_populacao", ler_sidra(baixar(url)), tabela, url)

    url = URL_MALHA.format(ano=ANO_DTB)
    total += _gravar(
        con, "raw.ibge_malha_municipios", ler_malha(baixar_com_cache(url, cache)), str(ANO_DTB), url
    )
    return total

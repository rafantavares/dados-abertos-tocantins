import io
import json
import zipfile

import duckdb
import pandas as pd
import shapefile

from pipeline.config import PASTA_FIXTURES
from pipeline.fontes import ibge


def _zip(arquivos: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for nome, conteudo in arquivos.items():
            zf.writestr(nome, conteudo)
    return buffer.getvalue()


def test_ler_dtb_encontra_cabecalho_e_filtra_tocantins():
    real = pd.read_csv(PASTA_FIXTURES / "ibge" / "ibge_dtb_municipios.csv", dtype=str)
    real = real.drop(columns=["_referencia"]).head(3)
    largura = real.shape[1]
    titulo = pd.DataFrame([["TÍTULO : BET"] + [None] * (largura - 1)])
    cabecalho = pd.DataFrame([list(real.columns)])
    outra_uf = real.head(1).copy()
    outra_uf.iloc[0, 0] = "52"  # caso de teste: linha de outra UF deve ser descartada
    corpo = pd.DataFrame(pd.concat([real, outra_uf]).values)
    planilha = pd.concat([titulo, cabecalho, corpo], ignore_index=True)
    xlsx = io.BytesIO()
    planilha.to_excel(xlsx, header=False, index=False)

    df = ibge.ler_dtb(_zip({"RELATORIO_DTB_BRASIL_MUNICIPIO.xlsx": xlsx.getvalue()}))
    assert list(df.columns) == list(real.columns)
    assert len(df) == 3


def test_ler_sidra_descarta_linha_de_descricao():
    resposta = [
        {"V": "Valor", "D1C": "Município (Código)"},
        {"V": "2576", "D1C": "1700251"},
    ]
    df = ibge.ler_sidra(json.dumps(resposta).encode())
    assert df.to_dict("records") == [{"V": "2576", "D1C": "1700251"}]


def test_ler_malha_gera_geojson_simplificado():
    shp, shx, dbf = io.BytesIO(), io.BytesIO(), io.BytesIO()
    with shapefile.Writer(shp=shp, shx=shx, dbf=dbf, shapeType=shapefile.POLYGON) as w:
        w.field("CD_MUN", "C")
        # quadrado de teste com um vértice quase colinear, que some na simplificação
        w.poly(
            [
                [
                    [-48.0, -10.0],
                    [-48.0, -10.5],
                    [-48.0001, -10.75],
                    [-48.0, -11.0],
                    [-47.0, -11.0],
                    [-47.0, -10.0],
                    [-48.0, -10.0],
                ]
            ]
        )
        w.record("1721000")
    conteudo = _zip({"TO.shp": shp.getvalue(), "TO.shx": shx.getvalue(), "TO.dbf": dbf.getvalue()})
    df = ibge.ler_malha(conteudo, tolerancia=0.01)
    assert df.loc[0, "CD_MUN"] == "1721000"
    geometria = json.loads(df.loc[0, "geojson"])
    assert geometria["type"] == "Polygon"
    assert len(geometria["coordinates"][0]) == 5


def test_extrair_com_fixtures_e_idempotente():
    with duckdb.connect() as con:
        n1 = ibge.extrair(con, usar_fixtures=True)
        n2 = ibge.extrair(con, usar_fixtures=True)
        assert n1 == n2 > 0
        assert con.execute("select count(*) from raw.ibge_dtb_municipios").fetchone() == (139,)

import duckdb
import pandas as pd
import pytest

from pipeline.carga import gravar_particao, particoes_existentes


@pytest.fixture
def con():
    with duckdb.connect() as conexao:
        yield conexao


def _gravar(con, df, valor):
    return gravar_particao(
        con, "raw.t", df, coluna_particao="ano", valor_particao=valor, fonte_url="u"
    )


def test_gravar_particao_e_idempotente(con):
    df = pd.DataFrame({"x": [1, 2]})
    assert _gravar(con, df, "2023") == 2
    _gravar(con, df, "2023")
    assert con.execute("select count(*) from raw.t").fetchone() == (2,)
    assert particoes_existentes(con, "raw.t", "ano") == {"2023"}


def test_gravar_particao_preserva_outras_particoes(con):
    _gravar(con, pd.DataFrame({"x": [1]}), "2022")
    _gravar(con, pd.DataFrame({"x": [2, 3]}), "2023")
    _gravar(con, pd.DataFrame({"x": [4]}), "2023")
    linhas = con.execute("select ano, x from raw.t order by ano").fetchall()
    assert linhas == [("2022", "1"), ("2023", "4")]


def test_gravar_particao_aceita_colunas_novas(con):
    _gravar(con, pd.DataFrame({"x": [1]}), "2022")
    _gravar(con, pd.DataFrame({"x": [2], "y": ["b"]}), "2023")
    linhas = con.execute("select ano, x, y from raw.t order by ano").fetchall()
    assert linhas == [("2022", "1", None), ("2023", "2", "b")]


def test_gravar_particao_guarda_texto_e_metadados(con):
    _gravar(con, pd.DataFrame({"x": [1]}), "2023")
    tipos = dict(con.execute("select column_name, column_type from (describe raw.t)").fetchall())
    assert set(tipos.values()) == {"VARCHAR"}
    assert {"_fonte_url", "_carregado_em"} <= set(tipos)


def test_particoes_de_tabela_inexistente(con):
    assert particoes_existentes(con, "raw.nao_existe", "ano") == set()

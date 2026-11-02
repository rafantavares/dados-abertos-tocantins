import duckdb
import pytest

from pipeline import extrair


@pytest.fixture
def banco(monkeypatch, tmp_path):
    caminho = tmp_path / "t.duckdb"
    monkeypatch.setenv("DUCKDB_PATH", str(caminho))
    return caminho


def test_executar_cria_schema_raw_e_registra_carga(monkeypatch, banco):
    chamados = []

    def falso(con, usar_fixtures):
        chamados.append(usar_fixtures)
        con.execute("create or replace table raw.teste_x as select 1 as x")
        return 1

    monkeypatch.setattr(extrair, "EXTRATORES", {"teste": falso})
    assert extrair.executar(usar_fixtures=True) == {"teste": 1}
    assert chamados == [True]
    with duckdb.connect(str(banco)) as con:
        assert con.execute("select x from raw.teste_x").fetchone() == (1,)
        assert con.execute("select extrator, sucesso, linhas from raw._cargas").fetchall() == [
            ("teste", True, 1)
        ]


def test_executar_filtra_por_nome(monkeypatch, banco):
    monkeypatch.setattr(extrair, "EXTRATORES", {"a": lambda c, f: 1, "b": lambda c, f: 2})
    assert extrair.executar(["b"]) == {"b": 2}


def _quebra(con, usar_fixtures):
    raise TimeoutError("fonte fora do ar")


def test_falha_sem_dados_anteriores_interrompe(monkeypatch, banco):
    monkeypatch.setattr(extrair, "EXTRATORES", {"ok": lambda c, f: 1, "fonte": _quebra})
    with pytest.raises(RuntimeError, match="fonte"):
        extrair.executar()
    with duckdb.connect(str(banco)) as con:
        registros = con.execute("select extrator, sucesso, erro from raw._cargas").fetchall()
    assert registros[0] == ("ok", True, None)
    assert registros[1][:2] == ("fonte", False)
    assert "fonte fora do ar" in registros[1][2]


def test_falha_com_dados_anteriores_segue(monkeypatch, banco):
    with duckdb.connect(str(banco)) as con:
        con.execute("create schema raw")
        con.execute("create table raw.fonte_dados as select 1 as x")
    monkeypatch.setattr(extrair, "EXTRATORES", {"fonte": _quebra, "ok": lambda c, f: 3})
    monkeypatch.setattr(extrair, "PREFIXOS", {"fonte": "fonte_"})
    assert extrair.executar() == {"ok": 3}
    with duckdb.connect(str(banco)) as con:
        assert con.execute("select x from raw.fonte_dados").fetchone() == (1,)

import duckdb

from pipeline import extrair


def test_executar_cria_schema_raw(monkeypatch, tmp_path):
    banco = tmp_path / "t.duckdb"
    monkeypatch.setenv("DUCKDB_PATH", str(banco))
    chamados = []

    def falso(con, usar_fixtures):
        chamados.append(usar_fixtures)
        con.execute("create or replace table raw.teste as select 1 as x")
        return 1

    monkeypatch.setattr(extrair, "EXTRATORES", {"teste": falso})
    assert extrair.executar(usar_fixtures=True) == {"teste": 1}
    assert chamados == [True]
    with duckdb.connect(str(banco)) as con:
        assert con.execute("select x from raw.teste").fetchone() == (1,)


def test_executar_filtra_por_nome(monkeypatch, tmp_path):
    monkeypatch.setenv("DUCKDB_PATH", str(tmp_path / "t.duckdb"))
    monkeypatch.setattr(extrair, "EXTRATORES", {"a": lambda c, f: 1, "b": lambda c, f: 2})
    assert extrair.executar(["b"]) == {"b": 2}

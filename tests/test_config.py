from pathlib import Path

from pipeline import config


def test_caminho_banco_padrao(monkeypatch):
    monkeypatch.delenv("DUCKDB_PATH", raising=False)
    assert config.caminho_banco() == Path("data/tocantins.duckdb")


def test_caminho_banco_por_variavel(monkeypatch, tmp_path):
    destino = tmp_path / "x.duckdb"
    monkeypatch.setenv("DUCKDB_PATH", str(destino))
    assert config.caminho_banco() == destino


def test_pasta_fixtures_existe():
    assert config.PASTA_FIXTURES.is_dir()

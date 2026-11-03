import os
import sys
from pathlib import Path

import duckdb
import httpx
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

import dados
import indicadores as ind


def test_numero_e_reais_no_padrao_brasileiro():
    assert ind.numero(1234567.891, 2) == "1.234.567,89"
    assert ind.numero(5.4, 1) == "5,4"
    assert ind.reais(15775.52) == "R$ 15.775,52"
    assert ind.reais(2.3e9, curto=True) == "R$ 2,3 bi"
    assert ind.reais(4.5e6, curto=True) == "R$ 4,5 mi"


@pytest.mark.parametrize("vazio", [None, float("nan"), pd.NA])
def test_valores_ausentes_viram_travessao(vazio):
    assert ind.numero(vazio) == "—"
    assert ind.reais(vazio) == "—"


def _dados_falsos():
    municipios = pd.DataFrame({"nome_municipio": ["A", "B"], "populacao_censo_2022": [100, 200]})
    ideb = pd.DataFrame(
        {
            "cod_municipio": [1, 1, 2],
            "nome_municipio": ["A", "A", "B"],
            "ano": [2021, 2023, 2023],
            "etapa": ["anos_iniciais"] * 3,
            "rede": ["publica", "publica", "municipal"],
            "ideb": [5.0, 5.5, 6.0],
        }
    )
    despesa = pd.DataFrame(
        {
            "cod_municipio": [1, 2],
            "nome_municipio": ["A", "B"],
            "ano": [2023, 2023],
            "despesa_educacao_per_capita": [1000.0, None],
            "percentual_educacao": [25.0, 30.0],
        }
    )
    investimento = pd.DataFrame(
        {
            "cod_municipio": [1],
            "nome_municipio": ["A"],
            "ano": [2023],
            "investimento_por_aluno": [12000.0],
        }
    )
    return {
        "municipios": municipios,
        "ideb": ideb,
        "despesa": despesa,
        "investimento": investimento,
    }


def test_serie_filtra_etapa_rede_e_descarta_nulos():
    d = _dados_falsos()
    s = ind.serie(d, "IDEB", etapa="anos_iniciais", rede="publica")
    assert s["valor"].tolist() == [5.0, 5.5]
    s = ind.serie(d, "Despesa em Educação por habitante")
    assert s["nome_municipio"].tolist() == ["A"]


def test_comparativo_usa_valor_mais_recente():
    tabela = ind.comparativo(_dados_falsos(), ["A", "B"])
    linha = tabela.loc["IDEB Anos iniciais (1º ao 5º) – rede pública"]
    assert linha["A"] == "5,5 (2023)"
    assert linha["B"] == "—"


def test_caminho_banco_prefere_arquivo_local(monkeypatch, tmp_path):
    monkeypatch.setenv("DADOS_DUCKDB_PATH", str(tmp_path / "x.duckdb"))
    assert dados.caminho_banco() == tmp_path / "x.duckdb"


def test_caminho_banco_baixa_da_url_e_usa_cache(monkeypatch, tmp_path):
    monkeypatch.delenv("DADOS_DUCKDB_PATH", raising=False)
    monkeypatch.setenv("DADOS_DUCKDB_URL", "https://exemplo/tocantins.duckdb")
    monkeypatch.setattr(dados, "PASTA_CACHE", tmp_path)
    chamadas = []
    cliente_real = httpx.Client

    def handler(request):
        chamadas.append(str(request.url))
        return httpx.Response(200, content=b"banco")

    def cliente(**kwargs):
        return cliente_real(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(dados.httpx, "Client", cliente)
    caminho = dados.caminho_banco()
    assert caminho.read_bytes() == b"banco"
    dados.caminho_banco()
    assert chamadas == ["https://exemplo/tocantins.duckdb"]  # segunda chamada usa o cache


def _banco_com_marts() -> str | None:
    caminho = os.environ.get("DADOS_DUCKDB_PATH") or os.environ.get("DUCKDB_PATH")
    if not caminho or not Path(caminho).exists():
        return None
    try:
        with duckdb.connect(caminho, read_only=True) as con:
            con.execute("select 1 from marts.mart_investimento_aluno limit 1")
    except duckdb.Error:
        return None
    return caminho


@pytest.mark.skipif(_banco_com_marts() is None, reason="requer banco com os marts (dbt build)")
def test_painel_renderiza_todas_as_abas(monkeypatch):
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("DADOS_DUCKDB_PATH", _banco_com_marts())
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app" / "painel.py"))
    app.run(timeout=60)
    assert not app.exception, app.exception
    assert len(app.tabs) == 7
    for indicador in ind.INDICADORES:
        app.selectbox(key=None)
        app.selectbox[0].set_value(indicador).run(timeout=60)
        assert not app.exception, (indicador, app.exception)

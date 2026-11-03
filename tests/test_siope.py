import json
import urllib.parse
from datetime import date

import duckdb

from pipeline.fontes import siope


def test_url_indicadores_usa_parametros_odata():
    url = siope.url_indicadores(2024, skip=10)
    assert "Indicadores_Siope(Ano_Consulta=@Ano_Consulta,Num_Peri=@Num_Peri,Sig_UF=@Sig_UF)" in url
    query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
    assert query["@Ano_Consulta"] == ["2024"]
    assert query["@Num_Peri"] == ["6"]
    assert query["@Sig_UF"] == ["'TO'"]
    assert query["$skip"] == ["10"]


def test_indicadores_pagina_e_preserva_codigos(monkeypatch):
    # Estado com COD_MUNI nulo e município com código inteiro, como na API
    paginas = [
        [{"TIPO": "Estadual", "COD_MUNI": None, "VAL_INDI": "25.21"}] * 2,
        [{"TIPO": "Municipal", "COD_MUNI": 172100, "VAL_INDI": "25.11"}],
    ]
    monkeypatch.setattr(siope, "TAMANHO_PAGINA", 2)
    monkeypatch.setattr(
        siope, "baixar", lambda url, **kw: json.dumps({"value": paginas.pop(0)}).encode()
    )
    df = siope.indicadores(2024)
    assert len(df) == 3
    with duckdb.connect() as con:
        siope.gravar_particao(
            con, "raw.t", df, coluna_particao="NUM_ANO", valor_particao="2024", fonte_url="u"
        )
        codigos = [c for (c,) in con.execute('select "COD_MUNI" from raw.t').fetchall()]
    assert codigos == [None, None, "172100"]  # e não "172100.0"


def test_anos_candidatos():
    assert siope.anos_candidatos(date(2026, 11, 3)) == list(range(2015, 2026))


def test_extrair_com_fixtures_e_idempotente():
    with duckdb.connect() as con:
        n1 = siope.extrair(con, usar_fixtures=True)
        n2 = siope.extrair(con, usar_fixtures=True)
        assert n1 == n2 == 454
        anos = con.execute(
            'select distinct "NUM_ANO" from raw.siope_indicadores order by 1'
        ).fetchall()
        assert [a for (a,) in anos] == ["2019", "2024", "2025"]

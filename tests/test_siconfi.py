import json
from datetime import date

import duckdb
import pytest

from pipeline.fontes import siconfi_dca


@pytest.mark.parametrize(
    ("conta", "esperado"),
    [
        ("Despesas Exceto Intraorçamentárias", True),
        ("Despesas Intraorçamentárias", True),
        ("12 - Educação", True),
        ("12.361 - Ensino Fundamental", True),
        ("FU12 - Demais Subfunções", True),
        ("10 - Saúde", False),
        ("10.122 - Administração Geral", False),
        ("FU10 - Demais Subfunções", False),
        ("01.122 - Administração Geral", False),
    ],
)
def test_conta_relevante(conta, esperado):
    assert siconfi_dca.conta_relevante(conta) is esperado


def test_consultar_percorre_paginas(monkeypatch):
    paginas = {
        0: {"items": [{"a": 1}, {"a": 2}], "hasMore": True, "limit": 2},
        2: {"items": [{"a": 3}], "hasMore": False, "limit": 2},
    }
    urls = []

    def falso(url, **kwargs):
        urls.append(url)
        offset = int(url.rsplit("offset=", 1)[1])
        return json.dumps(paginas[offset]).encode()

    monkeypatch.setattr(siconfi_dca, "baixar", falso)
    itens = siconfi_dca.consultar("dca", {"no_anexo": "DCA-Anexo I-E", "id_ente": 17})
    assert [i["a"] for i in itens] == [1, 2, 3]
    assert "no_anexo=DCA-Anexo%20I-E" in urls[0]


def test_anos_candidatos():
    assert siconfi_dca.anos_candidatos(date(2026, 11, 2))[-1] == 2025


def test_extrair_com_fixtures_e_idempotente():
    with duckdb.connect() as con:
        n1 = siconfi_dca.extrair(con, usar_fixtures=True)
        n2 = siconfi_dca.extrair(con, usar_fixtures=True)
        assert n1 == n2 > 0
        entes = con.execute("select count(*) from raw.siconfi_entes").fetchone()[0]
        assert entes == 4  # 3 municípios de amostra + Estado
        contas = con.execute(
            "select distinct conta from raw.siconfi_dca_despesa_funcao"
        ).fetchall()
        assert all(siconfi_dca.conta_relevante(c) for (c,) in contas)

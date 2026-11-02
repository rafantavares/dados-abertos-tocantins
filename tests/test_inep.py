import io
import zipfile
from datetime import date

import duckdb
import pandas as pd

from pipeline.config import PASTA_FIXTURES
from pipeline.fontes import inep_censo_escolar, inep_ideb


def _zip(nome: str, conteudo: bytes) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr(nome, conteudo)
    return buffer.getvalue()


def test_ler_planilha_ideb_pula_cabecalho_e_rodape():
    real = pd.read_csv(PASTA_FIXTURES / "inep" / "ideb_ensino_medio.csv", dtype=str)
    # Reproduz o leiaute da planilha do INEP: linhas de título, linha de códigos,
    # dados e nota de rodapé sem UF.
    titulo = pd.DataFrame([["Ministério da Educação"] + [None] * (real.shape[1] - 1)])
    codigos = pd.DataFrame([list(real.columns)])
    rodape = pd.DataFrame([[None, "Fonte: MEC/Inep."] + [None] * (real.shape[1] - 2)])
    corpo = pd.DataFrame(real.values)
    planilha = pd.concat([titulo, codigos, corpo, rodape], ignore_index=True)
    xlsx = io.BytesIO()
    planilha.to_excel(xlsx, header=False, index=False)

    df = inep_ideb.ler_planilha(_zip("pasta/divulgacao.xlsx", xlsx.getvalue()))
    assert list(df.columns) == list(real.columns)
    assert len(df) == len(real)
    assert df.loc[0, "CO_MUNICIPIO"] == real.loc[0, "CO_MUNICIPIO"]


def test_filtrar_tocantins():
    df = pd.DataFrame({"SG_UF": ["TO", "GO", "TO "]})
    assert len(inep_ideb.filtrar_tocantins(df)) == 2


def test_ler_escolas_filtra_tocantins_e_colunas():
    real = pd.read_csv(PASTA_FIXTURES / "inep" / "censo_escolas.csv", dtype=str).head(3)
    real["CO_UF"] = "17"
    real["COLUNA_DESCARTADA"] = "x"
    outra_uf = real.head(1).copy()
    outra_uf["CO_UF"] = "52"  # caso de teste: linha de outra UF deve ser descartada
    entrada = pd.concat([real, outra_uf]).to_csv(sep=";", index=False).encode("latin-1")

    df = inep_censo_escolar.ler_escolas(_zip("x/dados/microdados_ed_basica_2023.csv", entrada))
    assert len(df) == 3
    assert "COLUNA_DESCARTADA" not in df.columns
    assert set(df["CO_UF"]) == {"17"}


def test_anos_candidatos():
    assert inep_censo_escolar.anos_candidatos(date(2026, 11, 2)) == list(range(2019, 2026))


def test_extrair_com_fixtures_e_idempotente():
    with duckdb.connect() as con:
        n1 = inep_ideb.extrair(con, usar_fixtures=True)
        n2 = inep_ideb.extrair(con, usar_fixtures=True)
        assert n1 == n2 == 9 + 7 + 7
        assert con.execute("select count(*) from raw.inep_ideb_anos_iniciais").fetchone() == (9,)

        inep_censo_escolar.extrair(con, usar_fixtures=True)
        inep_censo_escolar.extrair(con, usar_fixtures=True)
        anos = con.execute(
            "select NU_ANO_CENSO, count(*) from raw.inep_censo_escolas group by 1 order by 1"
        ).fetchall()
        assert [a for a, _ in anos] == ["2023", "2024"]
        assert sum(n for _, n in anos) == 411

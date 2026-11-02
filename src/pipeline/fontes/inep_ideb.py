"""IDEB por município (INEP), filtrado para o Tocantins.

O INEP publica, a cada edição, uma planilha por etapa com a série histórica
completa (2005 em diante). O extrator usa a edição mais recente disponível e
grava uma tabela bruta por etapa: ``raw.inep_ideb_<etapa>``.
"""

from __future__ import annotations

import io
import logging
import zipfile

import duckdb
import pandas as pd

from pipeline.carga import gravar_particao
from pipeline.config import PASTA_FIXTURES, SIGLA_UF_TO, pasta_cache
from pipeline.http import ErroDownload, baixar_com_cache

log = logging.getLogger(__name__)

ETAPAS = ("anos_iniciais", "anos_finais", "ensino_medio")
#: Edições tentadas, da mais recente para a mais antiga.
EDICOES = (2025, 2023)
URL = "https://download.inep.gov.br/ideb/resultados/divulgacao_{etapa}_municipios_{edicao}.zip"


def ler_planilha(conteudo_zip: bytes) -> pd.DataFrame:
    """Lê o XLSX de dentro do ZIP e devolve a tabela com os códigos de coluna.

    A planilha tem um cabeçalho descritivo de várias linhas; a linha que
    contém ``SG_UF`` traz os nomes técnicos das colunas. Linhas sem UF são
    notas de rodapé e são descartadas.
    """
    with zipfile.ZipFile(io.BytesIO(conteudo_zip)) as zf:
        nome = next(n for n in zf.namelist() if n.lower().endswith(".xlsx"))
        bruto = pd.read_excel(zf.open(nome), header=None, dtype=str)
    linha_cabecalho = next(i for i, linha in bruto.iterrows() if "SG_UF" in linha.values)
    df = bruto.iloc[linha_cabecalho + 1 :].copy()
    df.columns = [str(c) for c in bruto.iloc[linha_cabecalho].values]
    df = df.loc[:, [c for c in df.columns if c != "nan"]]
    return df[df["SG_UF"].notna()].reset_index(drop=True)


def filtrar_tocantins(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["SG_UF"].str.strip() == SIGLA_UF_TO].reset_index(drop=True)


def _baixar_edicao_recente(etapa: str) -> tuple[bytes, str, int]:
    ultimo: Exception | None = None
    for edicao in EDICOES:
        url = URL.format(etapa=etapa, edicao=edicao)
        try:
            return baixar_com_cache(url, pasta_cache() / "inep_ideb"), url, edicao
        except ErroDownload as erro:
            log.info("edição %s indisponível para %s: %s", edicao, etapa, erro)
            ultimo = erro
    raise ErroDownload(f"nenhuma edição do IDEB disponível para {etapa}") from ultimo


def extrair(con: duckdb.DuckDBPyConnection, usar_fixtures: bool = False) -> int:
    total = 0
    for etapa in ETAPAS:
        if usar_fixtures:
            arquivo = PASTA_FIXTURES / "inep" / f"ideb_{etapa}.csv"
            df, url, edicao = pd.read_csv(arquivo, dtype=str), f"fixture:{arquivo.name}", 2023
        else:
            conteudo, url, edicao = _baixar_edicao_recente(etapa)
            df = filtrar_tocantins(ler_planilha(conteudo))
        total += gravar_particao(
            con,
            f"raw.inep_ideb_{etapa}",
            df,
            coluna_particao="_edicao",
            valor_particao=str(edicao),
            fonte_url=url,
        )
        # Mantém só a edição mais recente: ela já contém toda a série histórica.
        con.execute(f"delete from raw.inep_ideb_{etapa} where _edicao <> ?", [str(edicao)])
    return total

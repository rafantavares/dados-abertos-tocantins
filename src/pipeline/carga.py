"""Gravação idempotente na camada bruta (schema ``raw`` do DuckDB).

Cada fonte grava em uma tabela particionada por uma coluna (em geral o ano).
Gravar uma partição apaga a versão anterior dela e insere a nova na mesma
transação, então rodar o mesmo extrator duas vezes produz o mesmo resultado.
As colunas da fonte são guardadas como texto, exatamente como vieram; tipos e
nomes são padronizados depois, no staging do dbt.
"""

from __future__ import annotations

from datetime import UTC, datetime

import duckdb
import pandas as pd

COLUNAS_METADADOS = ("_fonte_url", "_carregado_em")


def _identificador(nome: str) -> str:
    return '"' + nome.replace('"', '""') + '"'


def tabela_existe(con: duckdb.DuckDBPyConnection, tabela: str) -> bool:
    esquema, nome = tabela.split(".")
    return bool(
        con.execute(
            "select count(*) from information_schema.tables "
            "where table_schema = ? and table_name = ?",
            [esquema, nome],
        ).fetchone()[0]
    )


def particoes_existentes(con: duckdb.DuckDBPyConnection, tabela: str, coluna: str) -> set[str]:
    """Valores distintos de ``coluna`` já gravados em ``tabela``."""
    if not tabela_existe(con, tabela):
        return set()
    linhas = con.execute(f"select distinct {_identificador(coluna)} from {tabela}").fetchall()
    return {str(valor) for (valor,) in linhas}


def gravar_particao(
    con: duckdb.DuckDBPyConnection,
    tabela: str,
    df: pd.DataFrame,
    *,
    coluna_particao: str,
    valor_particao: str,
    fonte_url: str,
) -> int:
    """Substitui a partição ``coluna_particao = valor_particao`` por ``df``.

    Colunas novas na fonte são adicionadas à tabela (como texto); colunas que
    deixaram de existir ficam nulas na nova partição.
    """
    dados = df.astype("string").copy()
    dados[coluna_particao] = str(valor_particao)
    dados["_fonte_url"] = fonte_url
    dados["_carregado_em"] = datetime.now(UTC).isoformat(timespec="seconds")

    esquema = tabela.split(".")[0]
    con.execute(f"create schema if not exists {esquema}")
    con.register("_novos", dados)
    try:
        con.execute("begin transaction")
        if not tabela_existe(con, tabela):
            colunas = ", ".join(f"{_identificador(c)} varchar" for c in dados.columns)
            con.execute(f"create table {tabela} ({colunas})")
        else:
            atuais = {linha[0] for linha in con.execute(f"describe {tabela}").fetchall()}
            for coluna in dados.columns:
                if coluna not in atuais:
                    con.execute(f"alter table {tabela} add column {_identificador(coluna)} varchar")
        con.execute(
            f"delete from {tabela} where {_identificador(coluna_particao)} = ?",
            [str(valor_particao)],
        )
        con.execute(f"insert into {tabela} by name select * from _novos")
        con.execute("commit")
    except Exception:
        con.execute("rollback")
        raise
    finally:
        con.unregister("_novos")
    return len(dados)

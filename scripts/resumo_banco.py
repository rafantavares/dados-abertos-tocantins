"""Imprime e salva a contagem de linhas de cada tabela do banco DuckDB.

Uso: python scripts/resumo_banco.py <banco.duckdb> <saida.json>
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime

import duckdb


def contar(caminho: str) -> dict[str, int]:
    with duckdb.connect(caminho, read_only=True) as con:
        tabelas = con.execute(
            "select table_schema || '.' || table_name from information_schema.tables "
            "where table_schema not in ('information_schema', 'pg_catalog') order by 1"
        ).fetchall()
        return {t: con.execute(f"select count(*) from {t}").fetchone()[0] for (t,) in tabelas}


def main(banco: str, saida: str) -> None:
    contagens = contar(banco)
    for tabela, linhas in contagens.items():
        print(f"{tabela:60s} {linhas:>10,d}")
    documento = {"gerado_em": datetime.now(UTC).isoformat(timespec="seconds"), "tabelas": contagens}
    with open(saida, "w", encoding="utf-8") as f:
        json.dump(documento, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

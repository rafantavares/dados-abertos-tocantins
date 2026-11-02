"""Ponto de entrada da extração: ``python -m pipeline.extrair``.

Cada extrator registrado em ``EXTRATORES`` recebe uma conexão DuckDB e grava
suas tabelas no schema ``raw``. Com ``--fixtures`` os extratores leem as
amostras reais versionadas em ``tests/fixtures`` em vez de acessar a rede,
o que permite rodar o pipeline completo offline (CI e desenvolvimento).
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Callable

import duckdb

from pipeline.config import caminho_banco
from pipeline.fontes import inep_censo_escolar, inep_ideb, siconfi_dca

log = logging.getLogger("pipeline")

Extrator = Callable[[duckdb.DuckDBPyConnection, bool], int]

#: Extratores na ordem de execução: nome -> função(conexão, usar_fixtures) -> linhas.
EXTRATORES: dict[str, Extrator] = {
    "inep_ideb": inep_ideb.extrair,
    "inep_censo_escolar": inep_censo_escolar.extrair,
    "siconfi_dca": siconfi_dca.extrair,
}


def executar(nomes: list[str] | None = None, usar_fixtures: bool = False) -> dict[str, int]:
    """Roda os extratores pedidos (ou todos) e devolve as linhas gravadas por extrator."""
    destino = caminho_banco()
    destino.parent.mkdir(parents=True, exist_ok=True)
    resultado: dict[str, int] = {}
    with duckdb.connect(str(destino)) as con:
        con.execute("create schema if not exists raw")
        for nome, extrator in EXTRATORES.items():
            if nomes and nome not in nomes:
                continue
            log.info("extraindo %s", nome)
            resultado[nome] = extrator(con, usar_fixtures)
            log.info("%s: %d linhas", nome, resultado[nome])
    return resultado


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Extrai as fontes para a camada bruta.")
    parser.add_argument("extratores", nargs="*", help="extratores a rodar (padrão: todos)")
    parser.add_argument(
        "--fixtures", action="store_true", help="usa as amostras de tests/fixtures (offline)"
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    executar(args.extratores or None, usar_fixtures=args.fixtures)


if __name__ == "__main__":
    main()

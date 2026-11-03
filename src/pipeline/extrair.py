"""Ponto de entrada da extração: ``python -m pipeline.extrair``.

Cada extrator registrado em ``EXTRATORES`` recebe uma conexão DuckDB e grava
suas tabelas no schema ``raw``. Com ``--fixtures`` os extratores leem as
amostras reais versionadas em ``tests/fixtures`` em vez de acessar a rede,
o que permite rodar o pipeline completo offline (CI e desenvolvimento).

Uma fonte fora do ar não interrompe as demais: a falha é registrada em
``raw._cargas`` e os dados já carregados daquela fonte continuam no banco.
O processo termina com erro se algum extrator falhar e a fonte não tiver
nenhum dado anterior para aproveitar.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

import duckdb

from pipeline.config import caminho_banco
from pipeline.fontes import ibge, ibge_ipca, inep_censo_escolar, inep_ideb, siconfi_dca, siope

log = logging.getLogger("pipeline")

Extrator = Callable[[duckdb.DuckDBPyConnection, bool], int]

#: Extratores na ordem de execução: nome -> função(conexão, usar_fixtures) -> linhas.
EXTRATORES: dict[str, Extrator] = {
    "ibge": ibge.extrair,
    "ibge_ipca": ibge_ipca.extrair,
    "inep_ideb": inep_ideb.extrair,
    "inep_censo_escolar": inep_censo_escolar.extrair,
    "siconfi_dca": siconfi_dca.extrair,
    "siope": siope.extrair,
}


@dataclass
class Resultado:
    extrator: str
    sucesso: bool
    linhas: int = 0
    erro: str | None = None
    tem_dados_anteriores: bool = False


def _registrar(con: duckdb.DuckDBPyConnection, r: Resultado, inicio: datetime) -> None:
    con.execute(
        """
        create table if not exists raw._cargas (
            extrator varchar, iniciado_em timestamptz, finalizado_em timestamptz,
            sucesso boolean, linhas integer, erro varchar
        )
        """
    )
    con.execute(
        "insert into raw._cargas values (?, ?, ?, ?, ?, ?)",
        [r.extrator, inicio, datetime.now(UTC), r.sucesso, r.linhas, r.erro],
    )


#: Prefixo das tabelas brutas gravadas por cada extrator.
PREFIXOS: dict[str, str] = {
    "ibge": "ibge_",
    "ibge_ipca": "ibge_sidra_ipca",
    "inep_ideb": "inep_ideb_",
    "inep_censo_escolar": "inep_censo_",
    "siconfi_dca": "siconfi_",
    "siope": "siope_",
}


def _tem_dados(con: duckdb.DuckDBPyConnection, extrator: str) -> bool:
    """Verdadeiro se já existe alguma tabela bruta não vazia deste extrator."""
    prefixo = PREFIXOS.get(extrator, extrator + "_")
    tabelas = con.execute(
        "select table_name from information_schema.tables "
        "where table_schema = 'raw' and starts_with(table_name, ?)",
        [prefixo],
    ).fetchall()
    return any(
        con.execute(f'select exists (select 1 from raw."{t}")').fetchone()[0] for (t,) in tabelas
    )


def executar(nomes: list[str] | None = None, usar_fixtures: bool = False) -> dict[str, int]:
    """Roda os extratores pedidos (ou todos) e devolve as linhas gravadas por extrator.

    Levanta ``RuntimeError`` se algum extrator falhar sem ter dados anteriores.
    """
    destino = caminho_banco()
    destino.parent.mkdir(parents=True, exist_ok=True)
    resultados: list[Resultado] = []
    with duckdb.connect(str(destino)) as con:
        con.execute("create schema if not exists raw")
        for nome, extrator in EXTRATORES.items():
            if nomes and nome not in nomes:
                continue
            log.info("extraindo %s", nome)
            inicio = datetime.now(UTC)
            try:
                r = Resultado(nome, True, extrator(con, usar_fixtures))
                log.info("%s: %d linhas", nome, r.linhas)
            except Exception as erro:
                log.exception("falha em %s", nome)
                r = Resultado(nome, False, erro=f"{type(erro).__name__}: {erro}"[:2000])
                r.tem_dados_anteriores = _tem_dados(con, nome)
            _registrar(con, r, inicio)
            resultados.append(r)

    fatais = [r for r in resultados if not r.sucesso and not r.tem_dados_anteriores]
    for r in resultados:
        if not r.sucesso and r.tem_dados_anteriores:
            log.warning("%s falhou; mantidos os dados da carga anterior", r.extrator)
    if fatais:
        raise RuntimeError(
            "extratores sem dados após falha: " + ", ".join(r.extrator for r in fatais)
        )
    return {r.extrator: r.linhas for r in resultados if r.sucesso}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Extrai as fontes para a camada bruta.")
    parser.add_argument("extratores", nargs="*", help="extratores a rodar (padrão: todos)")
    parser.add_argument(
        "--fixtures", action="store_true", help="usa as amostras de tests/fixtures (offline)"
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    try:
        executar(args.extratores or None, usar_fixtures=args.fixtures)
    except RuntimeError as erro:
        log.error("%s", erro)
        sys.exit(1)


if __name__ == "__main__":
    main()

"""Configurações compartilhadas do pipeline (caminhos e constantes)."""

from __future__ import annotations

import os
from pathlib import Path

#: Código IBGE da unidade federativa do Tocantins.
CODIGO_UF_TO = 17
SIGLA_UF_TO = "TO"

#: Raiz do repositório (src/pipeline/config.py -> ../../).
RAIZ = Path(__file__).resolve().parents[2]
PASTA_FIXTURES = RAIZ / "tests" / "fixtures"


def caminho_banco() -> Path:
    """Caminho do arquivo DuckDB, configurável pela variável ``DUCKDB_PATH``."""
    return Path(os.environ.get("DUCKDB_PATH", "data/tocantins.duckdb"))


def pasta_cache() -> Path:
    """Pasta de cache dos downloads, configurável por ``PIPELINE_CACHE``."""
    return Path(os.environ.get("PIPELINE_CACHE", "data/cache"))

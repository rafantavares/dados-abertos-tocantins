"""Exporta recortes pequenos e reais da camada bruta para virar fixtures.

Para cada tabela de ``raw``, mantém só as linhas dos municípios de amostra
(e do Estado, quando a tabela tem entes estaduais) e grava um CSV com as
colunas originais. Usado nas execuções do pipeline em branches de
desenvolvimento; os CSVs gerados são copiados para ``tests/fixtures``.

Uso: python scripts/exportar_amostras.py <banco.duckdb> <pasta_saida>
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

#: Palmas, Abreulândia e Ananás (ver tests/fixtures/README.md) e o Estado (17).
CODIGOS = ("1721000", "1700251", "1701002", "17")

#: Coluna com o código do município/ente em cada tabela bruta.
COLUNA_CODIGO = {
    "inep_ideb_anos_iniciais": "CO_MUNICIPIO",
    "inep_ideb_anos_finais": "CO_MUNICIPIO",
    "inep_ideb_ensino_medio": "CO_MUNICIPIO",
    "inep_censo_escolas": "CO_MUNICIPIO",
    "siconfi_entes": "cod_ibge",
    "siconfi_dca_despesa_funcao": "cod_ibge",
    "ibge_sidra_populacao": "D1C",
}
#: Tabelas pequenas exportadas inteiras (dimensões completas do Tocantins).
COMPLETAS = {"ibge_dtb_municipios"}
#: Tabelas exportadas sem as colunas pesadas.
GEOMETRIA = {"ibge_malha_municipios": "CD_MUN"}


def main(banco: str, saida: str) -> None:
    destino = Path(saida)
    destino.mkdir(parents=True, exist_ok=True)
    lista = ", ".join(f"'{c}'" for c in CODIGOS)
    with duckdb.connect(banco, read_only=True) as con:
        tabelas = [
            t
            for (t,) in con.execute(
                "select table_name from information_schema.tables where table_schema = 'raw'"
            ).fetchall()
        ]
        for tabela in tabelas:
            colunas = [
                c
                for (c,) in con.execute(
                    "select column_name from information_schema.columns "
                    "where table_schema = 'raw' and table_name = ? order by ordinal_position",
                    [tabela],
                ).fetchall()
                if c not in ("_fonte_url", "_carregado_em")
            ]
            selecao = ", ".join(f'"{c}"' for c in colunas)
            if tabela == "siope_indicadores":
                # SIOPE usa o código IBGE sem o dígito verificador; Estado vem nulo
                seis = ", ".join(f"'{c[:6]}'" for c in CODIGOS if len(c) == 7)
                filtro = f'"COD_MUNI" in ({seis}) or "TIPO" = \'Estadual\''
            elif tabela in COMPLETAS:
                filtro = "true"
            elif tabela in GEOMETRIA:
                filtro = f'"{GEOMETRIA[tabela]}" in ({lista})'
            elif tabela in COLUNA_CODIGO:
                filtro = f'"{COLUNA_CODIGO[tabela]}" in ({lista})'
            else:
                print(f"pulando {tabela}: coluna de código desconhecida")
                continue
            arquivo = destino / f"{tabela}.csv"
            con.execute(
                f"copy (select {selecao} from raw.{tabela} where {filtro}) "
                f"to '{arquivo}' (header, delimiter ',')"
            )
            print(f"{tabela}: {arquivo.stat().st_size} bytes")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

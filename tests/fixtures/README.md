# Fixtures

Amostras **pequenas e reais** usadas nos testes e no modo offline
(`python -m pipeline.extrair --fixtures`). Nenhum valor foi inventado ou
alterado: as amostras são recortes de linhas e colunas dos arquivos oficiais
baixados pelo workflow `validar-fontes.yml` em 02/11/2026 (branch
`amostras-descoberta`).

Municípios incluídos: **Palmas** (1721000), **Abreulândia** (1700251) e
**Ananás** (1701002) — a capital, um município pequeno e um médio.

| Arquivo | Origem | Recorte |
|---|---|---|
| `inep/ideb_anos_iniciais.csv`, `inep/ideb_anos_finais.csv`, `inep/ideb_ensino_medio.csv` | INEP, `divulgacao_<etapa>_municipios_2025.zip` (edição 2025, exportada pelo pipeline real na branch `amostras-feat-6-municipios-ibge`) | Linhas dos 3 municípios; todas as colunas; `_edicao` indica a edição |
| `inep/censo_escolas.csv` | INEP, `microdados_censo_escolar_{2023,2024}.zip` (`microdados_ed_basica_<ano>.csv`) | Escolas dos 3 municípios; colunas de identificação, situação e matrículas |
| `siconfi/siconfi_entes.csv` | SICONFI, `/tt/entes` (02/11/2026) | Os 3 municípios e o Estado (cod. 17); a coluna técnica `_uf_consulta` é recriada na carga |
| `siconfi/siconfi_dca_despesa_funcao.csv` | SICONFI, `/tt/dca` Anexo I-E | Exercícios 2019–2025 dos 3 municípios e do Estado, só as contas guardadas pelo extrator (totais e função 12) |

As amostras do SICONFI vieram da execução do workflow `pipeline.yml` na branch
`feat/5-extrator-despesas` (exportadas por `scripts/exportar_amostras.py` para a
branch `amostras-feat-5-extrator-despesas`).
| `ibge/ibge_dtb_municipios.csv` | IBGE geoftp, `DTB_2022.zip` (`RELATORIO_DTB_BRASIL_MUNICIPIO.xls`) | Os 139 municípios do Tocantins; todas as colunas |
| `ibge/ibge_sidra_populacao.csv` | IBGE SIDRA, tabelas 4709 (Censo 2022) e 6579 (estimativas) | Linhas dos 3 municípios |
| `ibge/ibge_malha_municipios.csv` | IBGE geoftp, `TO_Municipios_2022.zip` | 3 municípios; geometria simplificada pelo extrator (tolerância de 0,001°) |

As amostras do IBGE vieram da execução do `pipeline.yml` na branch
`feat/6-municipios-ibge` (branch `amostras-feat-6-municipios-ibge`). A coluna
`_referencia` identifica a partição (ano da DTB/malha ou número da tabela SIDRA).
| `siope/siope_indicadores.csv` | FNDE, API OData `Indicadores_Siope` (6º bimestre, UF TO), anos 2019, 2024 e 2025 | Estado (`TIPO = Estadual`) e os 3 municípios (códigos de 6 dígitos 172100, 170025 e 170100); todas as colunas |

As amostras do SIOPE vieram da execução do `validar-fontes.yml` na branch
`feat/22-siope` (branch `amostras-validacao-feat-22-siope`), filtradas sem
alterar valores.
| `ibge/ibge_sidra_ipca.csv` | IBGE SIDRA, tabela 1737 (IPCA, número-índice), Brasil | Meses de jan/2015 a set/2026, exportados pelo `pipeline.yml` na branch `feat/23-ipca` (branch `amostras-feat-23-ipca`) |

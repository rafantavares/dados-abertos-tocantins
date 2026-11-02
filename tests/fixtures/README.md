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
| `inep/ideb_anos_iniciais.csv`, `inep/ideb_anos_finais.csv`, `inep/ideb_ensino_medio.csv` | INEP, `divulgacao_<etapa>_municipios_2023.zip` | Linhas dos 3 municípios; todas as colunas |
| `inep/censo_escolas.csv` | INEP, `microdados_censo_escolar_{2023,2024}.zip` (`microdados_ed_basica_<ano>.csv`) | Escolas dos 3 municípios; colunas de identificação, situação e matrículas |

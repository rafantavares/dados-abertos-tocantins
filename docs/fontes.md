# Fontes de dados

Inventário das fontes avaliadas na descoberta (issue #1). Todas são públicas e
oficiais. A validação foi feita em **02/11/2026** pelo workflow
[`validar-fontes.yml`](../.github/workflows/validar-fontes.yml), que roda nos
runners do GitHub Actions (o ambiente de desenvolvimento não alcança os sites do
governo). O relatório bruto de cada tentativa — status HTTP, tipo, tamanho,
SHA-256 e `Last-Modified` — está em
[`docs/validacao/relatorio_2026-11-02.json`](validacao/relatorio_2026-11-02.json),
e as amostras filtradas para o Tocantins foram publicadas na branch
[`amostras-descoberta`](https://github.com/rafantavares/dados-abertos-tocantins/tree/amostras-descoberta).

> **Sobre licenças.** Nenhum dos arquivos baixados traz um arquivo de licença
> próprio. Os dados são publicados por órgãos federais como dados abertos, sob a
> Política de Dados Abertos do Executivo Federal
> ([Decreto nº 8.777/2016](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2016/decreto/d8777.htm))
> e a Lei de Acesso à Informação (Lei nº 12.527/2011), que garantem a livre
> reutilização com citação da fonte. Quando o órgão declara termos próprios,
> eles estão indicados na tabela. O projeto sempre cita a fonte original.

## Fontes adotadas

| Fonte | Órgão | URL (padrão) | Formato | Atualização | Licença / termos | Acesso em 02/11/2026 |
|---|---|---|---|---|---|---|
| IDEB por município – anos iniciais, anos finais e ensino médio (série 2005–2023) | INEP | `https://download.inep.gov.br/ideb/resultados/divulgacao_{anos_iniciais,anos_finais,ensino_medio}_municipios_2023.zip` | ZIP com XLSX/ODS (cabeçalho em 9 linhas; códigos de coluna na 10ª) | Bienal (ano de SAEB) | Dados abertos (Decreto 8.777/2016); citar INEP | ✅ 200 – 23 MB, 23 MB, 7 MB |
| Microdados do Censo Escolar da Educação Básica 2023 e 2024 (tabela de escolas) | INEP | `https://download.inep.gov.br/dados_abertos/microdados_censo_escolar_{ano}.zip` | ZIP com CSV `;`, Latin-1, ~215 mil escolas × ~400 colunas | Anual | Dados abertos (Decreto 8.777/2016); citar INEP | ✅ 200 – 32 MB e 34 MB |
| Despesa por função/subfunção (DCA – Anexo I-E) do Estado e dos municípios | Tesouro Nacional (SICONFI) | `https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca?an_exercicio={ano}&no_anexo=DCA-Anexo%20I-E&id_ente={cod_ibge}` | API REST JSON paginada (`items`, `hasMore`, limite 5.000) | Anual (declaração até 30/04 do ano seguinte) | Dados abertos (Decreto 8.777/2016); citar Tesouro Nacional/SICONFI | ✅ 200 – Palmas 426 itens; Estado 579 itens |
| Lista de entes (código IBGE, população, CNPJ) | Tesouro Nacional (SICONFI) | `https://apidatalake.tesouro.gov.br/ords/siconfi/tt/entes` | API REST JSON | Anual | idem | ✅ 200 – 5.598 entes |
| População residente – Censo 2022 (tabela 4709) | IBGE (SIDRA) | `https://apisidra.ibge.gov.br/values/t/4709/n6/in%20n3%2017/v/93/p/all` | API REST JSON (1ª linha = cabeçalho) | Decenal | Termos do IBGE: reprodução permitida citando a fonte | ✅ 200 – 139 municípios |
| População residente estimada (tabela 6579) | IBGE (SIDRA) | `https://apisidra.ibge.gov.br/values/t/6579/n6/in%20n3%2017/v/9324/p/all` | API REST JSON | Anual | idem | ✅ 200 – 3.058 registros (2001–2025, sem anos de censo) |
| Divisão Territorial Brasileira 2022 (municípios, regiões geográficas) | IBGE (geoftp) | `https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/divisao_territorial/2022/DTB_2022.zip` | ZIP com XLS/ODS | Anual | idem | ✅ 200 – 139 municípios do TO |
| Malha municipal 2022 do Tocantins | IBGE (geoftp) | `https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2022/UFs/TO/TO_Municipios_2022.zip` | ZIP com Shapefile (SIRGAS 2000) | Anual | idem | ✅ 200 – 26 MB |

## Fontes inviáveis e alternativas

| Fonte candidata | Resultado da validação | Decisão / alternativa oficial |
|---|---|---|
| **Portal da Transparência do Tocantins** (`www.transparencia.to.gov.br`) | ❌ Timeout em todas as tentativas a partir dos runners do GitHub (dois endereços testados, 3 tentativas de 40 s cada). O portal não responde a clientes fora do país/da rede, e não foi possível localizar uma API documentada. | Usar o **SICONFI (DCA – Anexo I-E)** do Tesouro Nacional, que traz a despesa por função/subfunção declarada pelo próprio Estado **e** pelos 139 municípios, em API aberta e padronizada (MCASP). Vantagem extra: permite comparar municípios com a mesma metodologia. |
| **API de localidades e malhas do IBGE** (`servicodados.ibge.gov.br`) | ❌ Timeout a partir dos runners do GitHub (as APIs SIDRA e o geoftp do mesmo órgão funcionam). | Códigos e nomes de municípios vêm da **DTB 2022** (geoftp) e do SIDRA; o mapa usa a **malha municipal 2022** do geoftp, convertida para GeoJSON simplificado no pipeline. |
| **Portal Brasileiro de Dados Abertos** (`dados.gov.br`) | ⚠️ Página inicial responde (200), mas a API pública de catálogo retorna **401** — desde 2023 exige token de acesso pessoal. | Usado apenas como catálogo de referência, sem integração. Os conjuntos de interesse (INEP, Tesouro, IBGE) são baixados direto dos órgãos publicadores. |
| **SICONFI – RREO Anexo 08 (MDE)** | ⚠️ 200, mas sem itens para o Estado em 2023 com os filtros testados. | Não necessário: o DCA Anexo I-E cobre a função 12 – Educação. Fica registrado para investigação futura (indicador constitucional de 25% em MDE). |

## Observações técnicas encontradas na validação

- **Cadeia TLS incompleta no INEP.** `download.inep.gov.br` não envia o
  certificado intermediário, e clientes HTTP sem busca automática de emissores
  (Python/`urllib`, `httpx`) falham com `CERTIFICATE_VERIFY_FAILED`. O pipeline
  completa a cadeia buscando o emissor indicado no campo AIA do certificado do
  servidor — **sem desativar a verificação**.
- **IDEB:** valores ausentes vêm como `-` e `ND`; as últimas linhas da planilha
  são notas de rodapé (sem `SG_UF`). As redes por município são `Estadual`,
  `Municipal` e `Pública` (agregado), e a meta (`VL_PROJECAO_*`) só existe até
  2021, último ano do 1º ciclo de metas.
- **Censo Escolar:** o arquivo de escolas inclui escolas paralisadas e extintas
  (`TP_SITUACAO_FUNCIONAMENTO` ≠ 1), com matrículas vazias. Em 2024 a pasta
  interna do ZIP se chama `microdados_censo_escolar_2024_defeso`.
  `TP_DEPENDENCIA`: 1 federal, 2 estadual, 3 municipal, 4 privada.
- **SICONFI/DCA:** as contas vêm em texto (`"12 - Educação"`,
  `"12.361 - Ensino Fundamental"`, `"FU12 - Demais Subfunções"`); códigos de
  subfunção como `122 - Administração Geral` se repetem entre funções. Há cinco
  colunas por conta (empenhadas, liquidadas, pagas e inscrições de restos a
  pagar). O projeto usa **despesas liquidadas**.
- **SICONFI/DCA — rótulos variam entre exercícios** (carga real de 02/11/2026,
  exercícios 2015–2025): o total aparece como `Despesas Exceto
  Intraorçamentárias` ou `Despesas (Exceto Intraorçamentárias)`, e as
  "demais subfunções" da Educação como `FU12 - Demais Subfunções` ou
  `12.999 - Demais Subfunções Educação`. O staging normaliza os dois formatos.
- **SICONFI/entes:** o Estado do Tocantins (código 17) vem com `uf = "BR"`;
  o extrator o seleciona pelo código.

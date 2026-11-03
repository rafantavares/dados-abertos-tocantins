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
| População residente estimada (tabela 6579) | IBGE (SIDRA) | `https://apisidra.ibge.gov.br/values/t/6579/n6/in%20n3%2017/v/9324/p/all` | API REST JSON | Anual | idem | ✅ 200 – 3.058 registros (2001–2026, sem estimativa em 2007, 2010, 2022 e 2023) |
| Divisão Territorial Brasileira 2022 (municípios, regiões geográficas) | IBGE (geoftp) | `https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/divisao_territorial/2022/DTB_2022.zip` | ZIP com XLS/ODS | Anual | idem | ✅ 200 – 139 municípios do TO |
| Malha municipal 2022 do Tocantins | IBGE (geoftp) | `https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2022/UFs/TO/TO_Municipios_2022.zip` | ZIP com Shapefile (SIRGAS 2000) | Anual | idem | ✅ 200 – 26 MB |

### Adicionada no M6 (issue #22)

| Fonte | Órgão | URL (padrão) | Formato | Atualização | Licença / termos | Acesso em 03/11/2026 |
|---|---|---|---|---|---|---|
| Indicadores do SIOPE (aplicação em MDE, Fundeb, investimento por aluno) | FNDE (SIOPE) | `https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/Indicadores_Siope(Ano_Consulta=@Ano_Consulta,Num_Peri=@Num_Peri,Sig_UF=@Sig_UF)?@Ano_Consulta={ano}&@Num_Peri=6&@Sig_UF='TO'&$format=json` | API OData v4 (JSON), plataforma Olinda | Anual (6º bimestre), com retificações | Dados abertos do FNDE (Decreto 8.777/2016); citar FNDE/SIOPE | ✅ 200 – 4.479 a 5.598 indicadores por ano (140 entes); a API cobre **2017 em diante** (2015 e 2016 vêm vazios) |

| IPCA mensal, número-índice (tabela 1737, variável 2266) — issue #23 | IBGE (SIDRA) | `https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/all` | API REST JSON (1ª linha = cabeçalho) | Mensal | Termos do IBGE: reprodução permitida citando a fonte | ✅ 200 – série até set/2026 (carga de 03/11/2026) |

Validação feita com o workflow `validar-fontes.yml` (entrada `fontes`), branch
`amostras-validacao-feat-22-siope`. O catálogo CKAN do FNDE redireciona para o
dados.gov.br, e a página do programa no gov.br retornou 404; a API OData é o
acesso estável.

## Fontes inviáveis e alternativas

| Fonte candidata | Resultado da validação | Decisão / alternativa oficial |
|---|---|---|
| **Portal da Transparência do Tocantins** (`www.transparencia.to.gov.br`) | ❌ Inacessível a partir do GitHub Actions em 02/11/2026 e de novo em **03/11/2026** (issue #25). O DNS resolve (`128.201.16.168`, `191.223.64.251`), mas a **conexão TCP nas portas 443 e 80 expira**, com e sem `www`. O mesmo acontece com `www.to.gov.br` e `www.sefaz.to.gov.br`, o que indica bloqueio de rede da infraestrutura do Estado para os IPs dos runners (e não o portal fora do ar). `dados.to.gov.br` e `dadosabertos.to.gov.br` não existem no DNS. | Mantido o **SICONFI (DCA – Anexo I-E)**, que traz a despesa por função/subfunção declarada pelo próprio Estado **e** pelos 139 municípios, em API aberta e padronizada (MCASP), e permite comparar municípios com a mesma metodologia. Para usar o portal estadual no futuro, seria preciso rodar o extrator a partir de uma rede brasileira (ex.: *runner* auto-hospedado). Evidência: [`docs/validacao/relatorio_transparencia_to_2026-11-03.json`](validacao/relatorio_transparencia_to_2026-11-03.json). |
| **API de localidades e malhas do IBGE** (`servicodados.ibge.gov.br`) | ❌ Timeout a partir dos runners do GitHub (as APIs SIDRA e o geoftp do mesmo órgão funcionam). | Códigos e nomes de municípios vêm da **DTB 2022** (geoftp) e do SIDRA; o mapa usa a **malha municipal 2022** do geoftp, convertida para GeoJSON simplificado no pipeline. |
| **Portal Brasileiro de Dados Abertos** (`dados.gov.br`) | ⚠️ Página inicial responde (200), mas a API pública de catálogo retorna **401** — desde 2023 exige token de acesso pessoal. | Usado apenas como catálogo de referência, sem integração. Os conjuntos de interesse (INEP, Tesouro, IBGE) são baixados direto dos órgãos publicadores. |
| **SICONFI – RREO Anexo 08 (MDE)** | ⚠️ 200, mas sem itens para o Estado e para Palmas (2023 e 2024, com e sem `co_esfera`), embora o RREO do Estado tenha outros anexos (4.472 itens em 2024). | Substituído pelo **SIOPE** (indicadores oficiais de MDE declarados pelos entes). |

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

## Cobertura observada na primeira carga real (02/11/2026)

| Fonte | Cobertura carregada |
|---|---|
| IDEB (INEP) | **Edição 2025** (publicada após a validação inicial), série 2005–2025; 400 linhas (anos iniciais), 359 (anos finais), 283 (ensino médio) |
| Censo Escolar (INEP) | 2019–2024 (2.258 a 2.667 escolas por ano); o Censo 2025 ainda não foi publicado em microdados |
| DCA Anexo I-E (SICONFI) | Exercícios 2015–2025 do Estado e dos municípios |
| DTB / malha (IBGE) | 139 municípios, referência 2022 |
| População (SIDRA) | Censo 2022 + estimativas 2001–2026 (sem estimativa em 2007, 2010, 2022 e 2023) |

- **Instabilidade do INEP:** em uma das execuções o `download.inep.gov.br`
  deu timeout em todas as tentativas. Desde então, a falha de uma fonte é
  registrada em `raw._cargas` e a carga anterior dela é mantida, sem interromper
  as demais.
- **SIOPE:** o município é identificado pelo código IBGE de **6 dígitos** (sem
  o dígito verificador) e o Estado vem com `COD_MUNI` nulo; o staging converte
  para o código de 7 dígitos pela DTB. O mesmo indicador muda de `COD_INDI`
  entre versões da norma (ex.: 24 e 40 para o % de MDE), mas mantém o código de
  exibição `COD_EXIB` (1.1), usado como chave — único por ente e ano em 2019,
  2024 e 2025. Todos os indicadores vêm no grupo "Indicadores de Dispêndio com
  Pessoal", aparentemente um erro de rotulagem da fonte (o grupo é ignorado).
- **SIOPE — percentuais acima de 100%:** o % do Fundeb na remuneração (1.2) é
  calculado sobre a receita do Fundeb do próprio exercício e passa de 100% quando
  o ente aplica mais do que recebeu no ano (ex.: Araguaína 2024, 100,28%;
  Aguiarnópolis 2025, 101,66%; Miranorte 2025, 101,86%). O indicador 1.3 pode
  ser negativo (Araguaína 2024, −0,95). São tratados como válidos; acima de 105%
  o dbt emite aviso. A primeira execução real do pipeline falhou justamente por
  um teste que assumia o máximo de 100%.

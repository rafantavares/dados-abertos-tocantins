# Perguntas de negócio e dicionário de dados

## Perguntas que o painel responde

| # | Pergunta | Tabelas | Visualização no painel |
|---|---|---|---|
| P1 | Como evoluiu o IDEB de cada município (anos iniciais, anos finais e ensino médio) desde 2005, por rede? | `fct_ideb`, `dim_municipio` | Série temporal por município |
| P2 | Quais municípios atingiram a meta do IDEB e qual a distância para ela? | `fct_ideb` | Ranking com destaque para meta atingida |
| P3 | Como o IDEB se distribui no território do Tocantins? | `fct_ideb`, `dim_municipio`, `dim_municipio_geometria` | Mapa coroplético |
| P4 | Quanto cada município gasta com a função Educação, em valor total, per capita e como fatia da despesa total? | `fct_despesa_educacao`, `dim_municipio` | Mapa e ranking |
| P5 | Quanto cada rede municipal investe por aluno matriculado, e como isso evoluiu? | `mart_investimento_aluno` | Ranking e série temporal |
| P6 | Existe relação entre investimento por aluno e resultado no IDEB da rede municipal? | `mart_investimento_aluno` | Dispersão (investimento × IDEB) |
| P7 | Como as matrículas se dividem entre as redes estadual, municipal, federal e privada em cada município? | `fct_matriculas` | Barras empilhadas |
| P8 | Como dois municípios escolhidos se comparam em todos os indicadores acima? | todas | Comparativo lado a lado |
| P9 | Cada município aplicou o mínimo constitucional de 25% das receitas de impostos em MDE, segundo o SIOPE? | `mart_mde_siope` | Ranking com a linha dos 25% |

### Limites conhecidos das respostas

- **Despesa não é só MDE.** A função 12 – Educação do DCA inclui despesas que não
  entram no cálculo constitucional de Manutenção e Desenvolvimento do Ensino
  (MDE). O indicador "investimento por aluno" deste projeto é, portanto,
  *despesa liquidada na função Educação ÷ matrículas da rede própria* — uma
  aproximação, não o valor oficial do SIOPE.
- **IDEB é bienal** (anos ímpares) e a meta só existe até 2021.
- **Correlação não é causalidade.** A pergunta P6 descreve associação, sem
  controlar por renda, ruralidade ou porte do município.

## Convenções

- Camadas: `raw` (como veio da fonte, tudo texto) → `staging` (`stg_*`, nomes e
  tipos padronizados) → `intermediate` (`int_*`, regras de negócio) → `marts`
  (`dim_*`, `fct_*`, `mart_*`).
- Nomes em português, `snake_case`. Valores monetários em **reais correntes**
  (sem correção pela inflação), com duas casas decimais.
- `cod_municipio`: código IBGE de 7 dígitos (inteiro). O Estado do Tocantins usa
  o código de UF `17` quando aparece como ente.
- Redes: `federal`, `estadual`, `municipal`, `privada` e `publica` (agregado de
  federal + estadual + municipal, usado pelo INEP no IDEB).

## Dicionário das tabelas finais (schema `marts`)

### `dim_municipio`
Um registro por município do Tocantins (139).

| Coluna | Tipo | Descrição | Fonte |
|---|---|---|---|
| `cod_municipio` | integer | Código IBGE de 7 dígitos (chave) | DTB 2022 |
| `nome_municipio` | varchar | Nome oficial | DTB 2022 |
| `regiao_intermediaria` | varchar | Região geográfica intermediária | DTB 2022 |
| `regiao_imediata` | varchar | Região geográfica imediata | DTB 2022 |
| `populacao_censo_2022` | integer | População residente no Censo 2022 | SIDRA 4709 |
| `eh_capital` | boolean | Verdadeiro para Palmas | SICONFI entes |

### `dim_municipio_geometria`
| Coluna | Tipo | Descrição | Fonte |
|---|---|---|---|
| `cod_municipio` | integer | Código IBGE (chave, FK `dim_municipio`) | Malha 2022 |
| `geojson` | varchar | Geometria simplificada em GeoJSON (WGS84) | Malha 2022 |

### `fct_ideb`
Grão: município × ano × etapa × rede.

| Coluna | Tipo | Descrição |
|---|---|---|
| `cod_municipio` | integer | FK `dim_municipio` |
| `ano` | integer | Ano de referência (2005–2023, ímpares) |
| `etapa` | varchar | `anos_iniciais`, `anos_finais` ou `ensino_medio` |
| `rede` | varchar | `estadual`, `municipal` ou `publica` |
| `taxa_aprovacao` | double | Taxa de aprovação média da etapa (%) |
| `indicador_rendimento` | double | Indicador de rendimento (P), 0 a 1 |
| `nota_saeb_matematica` | double | Proficiência média em Matemática no SAEB |
| `nota_saeb_portugues` | double | Proficiência média em Língua Portuguesa no SAEB |
| `nota_saeb_padronizada` | double | Nota média padronizada (N), 0 a 10 |
| `ideb` | double | IDEB observado (N × P) |
| `meta_ideb` | double | Meta projetada pelo INEP (até 2021) |
| `atingiu_meta` | boolean | `ideb >= meta_ideb` (nulo sem meta ou sem IDEB) |

### `fct_matriculas`
Grão: município × ano × rede. Considera apenas escolas em atividade.

| Coluna | Tipo | Descrição |
|---|---|---|
| `cod_municipio` | integer | FK `dim_municipio` |
| `ano` | integer | Ano do Censo Escolar |
| `rede` | varchar | `federal`, `estadual`, `municipal` ou `privada` |
| `escolas_em_atividade` | integer | Número de escolas em atividade |
| `matriculas_educacao_basica` | integer | Total de matrículas na educação básica |
| `matriculas_infantil` | integer | Educação infantil (creche + pré-escola) |
| `matriculas_fundamental` | integer | Ensino fundamental |
| `matriculas_medio` | integer | Ensino médio |
| `matriculas_eja` | integer | Educação de jovens e adultos |
| `matriculas_especial` | integer | Educação especial (classes comuns e exclusivas) |

### `fct_despesa_educacao`
Grão: ente × ano. Ente = cada município (`esfera = municipal`) e o Estado
(`esfera = estadual`, `cod_ente = 17`).

| Coluna | Tipo | Descrição |
|---|---|---|
| `cod_ente` | integer | Código IBGE do município ou `17` para o Estado |
| `esfera` | varchar | `municipal` ou `estadual` |
| `ano` | integer | Exercício |
| `despesa_total` | decimal(18,2) | Despesa liquidada total, exceto intraorçamentária (R$) |
| `despesa_educacao` | decimal(18,2) | Despesa liquidada na função 12 – Educação (R$) |
| `despesa_ensino_fundamental` | decimal(18,2) | Subfunção 361 (R$) |
| `despesa_ensino_medio` | decimal(18,2) | Subfunção 362 (R$) |
| `despesa_educacao_infantil` | decimal(18,2) | Subfunção 365 (R$) |
| `percentual_educacao` | double | `despesa_educacao / despesa_total` × 100 |
| `populacao` | integer | População de referência do ano (ver nota abaixo) |
| `origem_populacao` | varchar | `censo`, `estimativa` ou `ultima_disponivel` |
| `despesa_educacao_per_capita` | decimal(18,2) | `despesa_educacao / populacao` (R$) |
| `dca_inconsistente` | boolean | Educação < 5% da despesa total: sinal de DCA declarado parcialmente; a linha fica fora do investimento por aluno |

População de referência (`int_populacao_anual`): Censo 2022 no próprio ano,
estimativa do IBGE quando existe e, nos anos sem publicação (2022–2023 para
estimativas), o último valor disponível. A do Estado é a soma dos municípios
(nula se faltar algum).

### `mart_investimento_aluno`
Grão: município × ano (rede municipal). Junta despesa municipal em Educação,
matrículas da rede municipal e IDEB da rede municipal.

| Coluna | Tipo | Descrição |
|---|---|---|
| `cod_municipio` | integer | FK `dim_municipio` |
| `ano` | integer | Ano |
| `despesa_educacao` | decimal(18,2) | Despesa municipal liquidada na função Educação (R$) |
| `matriculas_rede_municipal` | integer | Matrículas da rede municipal |
| `investimento_por_aluno` | decimal(18,2) | `despesa_educacao / matriculas_rede_municipal` (R$) |
| `ideb_anos_iniciais` | double | IDEB anos iniciais da rede municipal (anos ímpares) |
| `ideb_anos_finais` | double | IDEB anos finais da rede municipal (anos ímpares) |

### `mart_resumo_estadual`
Grão: ano. Visão do Estado (rede estadual).

| Coluna | Tipo | Descrição |
|---|---|---|
| `ano` | integer | Ano |
| `despesa_educacao_estado` | decimal(18,2) | Despesa estadual liquidada na função Educação (R$) |
| `matriculas_rede_estadual` | integer | Matrículas da rede estadual no Tocantins |
| `investimento_por_aluno_estado` | decimal(18,2) | Razão entre as duas colunas anteriores (R$) |
| `despesa_educacao_municipios` | decimal(18,2) | Soma da despesa em Educação dos municípios que declararam o DCA (R$) |
| `municipios_com_dca` | integer | Quantos municípios declararam o DCA no ano |

### `mart_mde_siope`
Grão: ente × ano (municípios e Estado, `cod_ente = 17`). Indicadores oficiais
declarados ao SIOPE (FNDE), 6º bimestre.

| Coluna | Tipo | Descrição |
|---|---|---|
| `cod_ente` | integer | Código IBGE do município ou `17` para o Estado |
| `esfera` | varchar | `municipal` ou `estadual` |
| `ano` | integer | Exercício |
| `percentual_mde` | double | % das receitas de impostos e transferências aplicado em MDE (indicador 1.1) |
| `cumpre_minimo_mde` | boolean | `percentual_mde >= 25` (art. 212 da Constituição) |
| `excecao_ec_119` | boolean | Anos 2020 e 2021: a EC 119/2022 afastou a responsabilização pelo descumprimento do mínimo (pandemia), com compensação até 2023 |
| `percentual_fundeb_remuneracao` | double | % do Fundeb na remuneração dos profissionais (1.2; mínimo 70%) |
| `percentual_educacao_despesa_total` | double | Despesa em educação ÷ despesa de todas as áreas (2.8) |
| `investimento_por_aluno_educacao_basica` | decimal(18,2) | Investimento por aluno da educação básica, R$ (4.8) |
| `investimento_por_aluno` | decimal(18,2) | Investimento por aluno, todas as etapas, R$ (4.9) |
| `valor_exigido_mde` | decimal(18,2) | Mínimo a aplicar em MDE, R$ (8.1) |
| `valor_aplicado_mde` | decimal(18,2) | Valor aplicado em MDE com receita de impostos, R$ (8.2) |

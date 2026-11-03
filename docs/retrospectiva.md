# Retrospectiva — MVP (M1 a M5)

Período: 02 e 03/11/2026. Todas as dez issues do backlog inicial foram
entregues, uma por PR, com merge *squash* na `main` depois do CI verde.

## O que foi entregue

| Milestone | Issue | PR | Entrega |
|---|---|---|---|
| M1 – Descoberta | #1 | [#11](https://github.com/rafantavares/dados-abertos-tocantins/pull/11) | Validação das fontes pelo GitHub Actions; `docs/fontes.md` |
| | #2 | [#12](https://github.com/rafantavares/dados-abertos-tocantins/pull/12) | 8 perguntas de negócio e dicionário das tabelas finais |
| | #3 | [#13](https://github.com/rafantavares/dados-abertos-tocantins/pull/13) | `pyproject`, Ruff, pytest, dbt-duckdb, CLI de extração, cliente HTTP, CI |
| M2 – Ingestão | #4 | [#14](https://github.com/rafantavares/dados-abertos-tocantins/pull/14) | IDEB e Censo Escolar; camada bruta idempotente; workflow que publica a branch `dados` |
| | #5 | [#15](https://github.com/rafantavares/dados-abertos-tocantins/pull/15) | Despesa por função (SICONFI DCA Anexo I-E) do Estado e dos 139 municípios |
| | #6 | [#16](https://github.com/rafantavares/dados-abertos-tocantins/pull/16) | DTB, população (SIDRA) e malha municipal do IBGE; falha de uma fonte não derruba as demais |
| M3 – Modelagem | #7 | [#17](https://github.com/rafantavares/dados-abertos-tocantins/pull/17) | 7 modelos de staging com testes genéricos e unitários |
| | #8 | [#18](https://github.com/rafantavares/dados-abertos-tocantins/pull/18) | 3 intermediários e 7 marts; `dbt docs` |
| M4 – Painel | #9 | [#19](https://github.com/rafantavares/dados-abertos-tocantins/pull/19) | Painel Streamlit (mapa, ranking, evolução, investimento × IDEB, matrículas, comparativo) |
| M5 – Automação | #10 | [#20](https://github.com/rafantavares/dados-abertos-tocantins/pull/20) | Alerta de anomalias de carga, issue automática e guia de operação |

Números da primeira carga completa: 139 municípios; IDEB 2005–2025 (3 etapas);
Censo Escolar 2019–2024 (14.610 registros de escolas); DCA 2015–2025 (34.190
linhas); 141 nós no `dbt build` (modelos, testes de dados e unitários); 55
testes Python.

## Decisões

- **Desenvolver offline e extrair no Actions.** O ambiente de desenvolvimento
  não alcança nenhum site do governo. Toda a extração real roda nos runners do
  GitHub. Localmente, o pipeline completo roda com `--fixtures` sobre amostras
  reais. As amostras são exportadas pelo próprio pipeline
  (`scripts/exportar_amostras.py` → branches `amostras-*`), o que garante que
  nenhuma fixture foi digitada à mão.
- **SICONFI no lugar do Portal da Transparência TO.** O portal estadual não
  respondeu a partir do Actions. O DCA Anexo I-E do Tesouro tem a mesma
  informação (despesa por função/subfunção) para o Estado **e** para todos os
  municípios, na mesma metodologia. Com isso, a comparação entre municípios
  ficou possível.
- **geoftp e SIDRA no lugar da API `servicodados` do IBGE**, pelo mesmo motivo.
- **Camada bruta como texto, exatamente como veio**, com partições substituídas
  em transação (idempotência) e colunas novas aceitas. Toda tipagem e limpeza
  fica no dbt, documentada e testada.
- **Banco publicado numa branch órfã `dados`**, recriada a cada carga com um
  único commit. O repositório não cresce, a `main` não recebe dados e o painel
  lê o arquivo pela URL raw.
- **"Investimento por aluno" é uma aproximação declarada:** despesa liquidada
  na função Educação ÷ matrículas da rede municipal. Não é o indicador de MDE do
  SIOPE, e isso está escrito no dicionário, no dbt docs e no painel.
- **Painel local**, sem publicação externa, como combinado. A decisão está
  registrada na issue #9 com o caminho para publicar no futuro.
- **Uma fonte fora do ar não derruba a carga:** a falha fica registrada em
  `raw._cargas` e a carga anterior daquela fonte é mantida. Já uma anomalia de
  contagem **bloqueia** a publicação.

## Problemas de dados encontrados

| Fonte | Problema | Tratamento |
|---|---|---|
| INEP | O servidor não envia o certificado intermediário (`CERTIFICATE_VERIFY_FAILED` em Python) | Cadeia completada via AIA, **sem** desligar a verificação TLS |
| INEP | Timeout intermitente em `download.inep.gov.br` (derrubou uma execução inteira) | Retry + resiliência por fonte |
| INEP/IDEB | Notas do SAEB de **2015 com vírgula decimal**; demais anos com ponto | Normalização no staging + teste unitário |
| INEP/IDEB | Ausência marcada como `-` e `ND`; notas de rodapé dentro da planilha | Nulo no staging; extrator localiza o cabeçalho e descarta linhas sem UF |
| INEP/IDEB | Edição 2025 publicada depois da validação inicial | O extrator tenta a edição mais recente primeiro |
| INEP/Censo | Escolas paralisadas/extintas no arquivo, com matrículas vazias; pasta interna `_defeso` em 2024 | Filtro por situação; busca do CSV por padrão de nome |
| SICONFI | Rótulos de contas e colunas mudam entre exercícios (`Despesas (Exceto Intraorçamentárias)` × sem parênteses; `FU12` × `12.999`; **`Inscrição de RP`** abreviado em 2015–2016) | Classificação por padrão; os testes de unicidade pegaram o caso de 2015–2016 no dado real; teste unitário cobre todos os rótulos |
| SICONFI | O Estado aparece com `uf = "BR"` na lista de entes | Seleção pelo código 17 |
| SICONFI | **DCAs declarados de forma parcial**: Tabocão (2015), Sampaio e Axixá do Tocantins (2016), Ipueiras (2017) com R$ 0 em Educação; Aragominas (2018) com 0,5%; Sampaio (2016) com despesa total de R$ 415 mil | Flag `dca_inconsistente` (< 5%), fora do investimento por aluno, teste em *warn* |
| SICONFI | Cobertura incompleta nos anos recentes: 133 de 139 municípios com DCA 2025 (Araguanã, Chapada de Areia, Muricilândia, Aragominas, Crixás do Tocantins e Tupirama sem declaração) | Mostrado no painel; os dois últimos exercícios são reconsultados a cada carga |
| IBGE | Sem estimativa de população em 2007, 2010, 2022 e 2023 | População de referência: Censo > estimativa > último valor disponível, com a origem registrada |
| Portal TO / `servicodados` / dados.gov.br | Inacessíveis a partir do Actions (timeout) ou exigindo token (401) | Alternativas oficiais documentadas em `docs/fontes.md` |

Checagem de sanidade: a soma da população do Censo 2022 em `dim_municipio`
(1.511.460) bate com o total oficial do Tocantins.

## Defeitos encontrados no próprio código (e corrigidos)

- Um `rm` de worktree apagou rascunhos não versionados da #3, que precisaram
  ser refeitos. Lição: versionar cedo, mesmo como rascunho.
- O CSV de entes foi exportado com inferência de tipos (`regiao = "NO"` virou
  `false`). Refeito com `all_varchar` e conferido byte a byte com a fonte.
- Afirmação errada na documentação (estimativas "até 2025"; o dado vai até
  2026). Corrigida depois de conferir no dado.
- Painel: `pd.NA` quebrava a formatação dos KPIs quando o ano escolhido não
  tinha Censo; o Spearman do pandas exige o scipy; o `px.choropleth` (d3-geo)
  não desenhava os polígonos e foi trocado por `choropleth_map`; a legenda
  ficava sobreposta ao eixo. Todos esses defeitos apareceram só ao rodar com
  dado real e capturar telas.

## Pendências e próximos passos

1. **MDE oficial (SIOPE/FNDE):** o RREO Anexo 08 do SICONFI voltou vazio para
   o Estado com os filtros testados. Investigar o SIOPE para ter o indicador
   constitucional de 25% e um investimento por aluno oficial.
2. **Censo Escolar 2025:** ainda não publicado em microdados; entra
   automaticamente quando o INEP publicar (o extrator tenta até o ano anterior
   ao atual).
3. **Valores reais (deflacionados):** hoje tudo está em reais correntes.
   Adicionar o IPCA (SIDRA) e um modo "valores de 2025" no painel.
4. **Portal da Transparência TO:** se ficar acessível, pode complementar o
   SICONFI com execução mensal do Estado.
5. **Ações do dono do repositório** (ver `docs/operacao.md`): conferir as
   permissões do token do Actions e as notificações de falha. Nenhuma é
   bloqueante hoje.
6. **Painel:** modo escuro validado e versão em tabela acessível para o mapa
   (hoje o ranking cumpre esse papel).
7. **Branches auxiliares** `amostras-descoberta` e `amostras-feat-*` podem ser
   apagadas quando não forem mais úteis. Elas guardam a origem das fixtures, por
   isso foram mantidas.

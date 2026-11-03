# Operação: atualização agendada e monitoramento

## Como a atualização funciona

O workflow [**Pipeline de dados**](../.github/workflows/pipeline.yml) roda toda
**segunda-feira às 06:17 (Brasília)** e também pode ser disparado manualmente
(Actions → Pipeline de dados → *Run workflow*). Ele:

1. restaura a carga anterior a partir da branch `dados` (banco, contagens e
   histórico) — os extratores são incrementais e só baixam o que mudou;
2. roda `python -m pipeline.extrair` (fonte que falhar mantém a carga
   anterior e fica registrada em `raw._cargas`);
3. roda `dbt build` (modelos + testes de qualidade) e `dbt docs generate`;
4. conta as linhas de cada tabela e compara com a carga anterior
   (`python -m pipeline.monitoramento`);
5. **só se tudo passar**, publica `tocantins.duckdb`, `contagens.json`,
   `historico_contagens.jsonl` e `documentacao_dbt.html` na branch `dados`.

## Regras do alerta de anomalia

Para cada tabela presente na carga anterior (`raw._cargas` é ignorada):

| Situação | Resultado |
|---|---|
| Tabela sumiu ou ficou vazia | ❌ erro |
| Queda maior que **5%** | ❌ erro — as fontes só acumulam anos; perder linhas indica falha de extração ou mudança de formato |
| Crescimento maior que **50%** | ❌ erro — ex.: filtro de UF quebrado trazendo o país inteiro |
| Tabela nova | ⚠️ aviso |
| Extrator cuja última execução falhou | ⚠️ aviso (a carga anterior da fonte foi mantida) |

Os limites ficam em `src/pipeline/monitoramento.py` (`QUEDA_MAXIMA`,
`CRESCIMENTO_MAXIMO`). O resultado aparece no **resumo do job** (aba *Summary*
da execução), em formato de tabela.

## Quando o pipeline falha

- Nada é publicado: o painel continua com a última carga boa.
- Uma issue com o rótulo **`alerta-carga`** é aberta (ou recebe um comentário,
  se já houver uma aberta) com o link da execução.
- O banco gerado fica disponível como artefato `banco-duckdb` da execução por
  14 dias, para investigação.

### Passo a passo para investigar

1. Abra a execução pelo link da issue e leia o resumo do job.
2. Se for **erro de extração** (fonte fora do ar), espere a próxima execução
   ou dispare manualmente mais tarde.
3. Se for **anomalia de contagem**, baixe o artefato `banco-duckdb` e compare
   a tabela citada com a carga anterior (`historico_contagens.jsonl` na branch
   `dados`).
4. Se a variação for legítima (ex.: o INEP republicou a série com menos
   linhas), rode o workflow manualmente com **`ignorar_anomalias = true`**.
   Para recomeçar do zero (descartando o banco anterior), use **`forcar = true`**.
5. Feche a issue `alerta-carga` quando a carga voltar ao normal.

## Ações que dependem do dono do repositório

Nenhuma é obrigatória para o pipeline funcionar hoje. Mesmo assim, vale conferir:

1. **Permissões do token do Actions** — *Settings → Actions → General →
   Workflow permissions*: o workflow declara `contents: write` e
   `issues: write`. Se a organização restringir o `GITHUB_TOKEN` a leitura, a
   publicação na branch `dados` e a abertura de issues falham; nesse caso
   selecione *Read and write permissions*.
2. **Notificações** — *Settings (do seu perfil) → Notifications → Actions*:
   marque "Send notifications for failed workflows only" para receber e-mail
   quando a execução agendada falhar. As issues `alerta-carga` também notificam
   quem acompanha o repositório.
3. **Agendamento em repositório parado** — o GitHub desativa workflows
   agendados depois de 60 dias sem atividade no repositório. Se isso
   acontecer, reative em *Actions → Pipeline de dados → Enable workflow*.
4. **Proteção da branch `dados`** — não proteja a branch `dados` contra
   *force push*: o workflow a recria a cada carga (um único commit, para o
   repositório não crescer com versões antigas do banco).
5. **Branches de trabalho** — em *Settings → General → Pull Requests*, marque
   *Automatically delete head branches*. As branches `amostras-*` criadas pelos
   runs de desenvolvimento podem ser apagadas depois que as fixtures forem
   copiadas; mantenha as citadas em `tests/fixtures/README.md` e
   `docs/fontes.md` (ver issue #29).

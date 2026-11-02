{% docs __overview__ %}
# Dados Abertos Tocantins

Modelo de dados de **educação e gastos públicos** dos 139 municípios do
Tocantins, construído com dbt + DuckDB a partir de fontes públicas oficiais
(INEP, Tesouro Nacional/SICONFI e IBGE).

## Camadas

| Camada | Schema | Conteúdo |
|---|---|---|
| Bruta | `raw` | Como veio da fonte, tudo texto, com `_fonte_url` e `_carregado_em` |
| Staging | `staging` | `stg_<fonte>__<entidade>`: nomes, tipos e códigos padronizados |
| Intermediária | `intermediate` | `int_*`: regras de negócio (população de referência, agregações) |
| Marts | `marts` | `dim_*`, `fct_*` e `mart_*`: tabelas prontas para o painel |

## Perguntas respondidas

Ver `docs/dicionario.md` no repositório: evolução e metas do IDEB, despesa em
Educação (total, por habitante e como parcela da despesa), investimento por
aluno da rede municipal, relação entre investimento e IDEB, matrículas por
rede e comparação entre municípios.

## Cuidados de leitura

- Valores em **reais correntes**, despesa **liquidada** na função 12 – Educação
  (não é o indicador constitucional de MDE).
- Linhas de DCA com Educação abaixo de 5% da despesa total são sinalizadas
  (`dca_inconsistente`) e ficam fora do investimento por aluno.
{% enddocs %}

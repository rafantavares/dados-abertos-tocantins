# 🗂️ Dados Abertos Tocantins

> Pipeline de dados que coleta informações públicas do Tocantins (educação e gastos públicos), trata, valida a qualidade e publica um painel aberto para qualquer cidadão consultar.

![status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow) ![python](https://img.shields.io/badge/python-3.12-blue) ![dbt](https://img.shields.io/badge/dbt-duckdb-orange) ![licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green)

## Por que este projeto existe

Os dados públicos do estado existem, mas estão espalhados em portais diferentes, em formatos variados e sem contexto. Este projeto junta essas fontes em um modelo único e responde perguntas como:

- Como evoluíram os indicadores de educação nos municípios do Tocantins?
- Quanto o estado e os municípios investem em educação por aluno?
- Existe relação entre investimento e resultado educacional?

## Arquitetura

```
Fontes públicas (APIs / CSV)
        │  extração agendada (GitHub Actions)
        ▼
  camada bruta (raw) ──► dbt: staging → intermediária → marts
                                        │   testes de qualidade
                                        ▼
                         DuckDB ──► painel público + dados exportados
```

Arquitetura em camadas (medalhão): **bruta** guarda o dado como veio; **staging** padroniza nomes e tipos; **marts** entrega tabelas prontas para análise.

## Fontes candidatas

A validação de disponibilidade e licença de cada fonte é a primeira tarefa do projeto (issue #1).

| Tema | Fonte candidata |
|---|---|
| Indicadores educacionais | INEP (Censo Escolar, IDEB) |
| Gastos públicos | Portal da Transparência do Tocantins |
| Dados municipais | IBGE (população, códigos de municípios) |
| Catálogo federal | Portal Brasileiro de Dados Abertos |

## Stack

Python 3.12 · httpx · DuckDB · dbt-duckdb · pandas · Streamlit · pytest · Ruff · GitHub Actions

## Qualidade de dados

- Testes do dbt: unicidade, não nulos, integridade referencial, faixas válidas
- Contagem de linhas por carga e alerta quando houver variação anormal
- Documentação das tabelas gerada pelo `dbt docs`

## Roadmap

| Milestone | Entrega | Status |
|---|---|---|
| **M1 – Descoberta** | Inventário das fontes, licenças e dicionário de dados | ⏳ |
| **M2 – Ingestão** | Extratores com carga incremental e camada bruta | ⏳ |
| **M3 – Modelagem** | Modelos dbt (staging → marts) com testes | ⏳ |
| **M4 – Painel** | Painel público com mapas e comparativos por município | ⏳ |
| **M5 – Automação** | Atualização agendada, monitoramento e documentação | ⏳ |

## Como rodar (em construção)

```bash
git clone https://github.com/rafantavares/dados-abertos-tocantins
cd dados-abertos-tocantins
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pipeline.extrair
dbt build --project-dir transform
streamlit run app/painel.py
```

## Autor

**Rafael Nunes Tavares** — estudante de Engenharia de Software (ULBRA Palmas)
[GitHub](https://github.com/rafantavares)

## Licença

Código sob [MIT](LICENSE). Os dados pertencem às suas fontes originais e seguem as licenças de cada uma.

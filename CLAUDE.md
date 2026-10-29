# Guia para sessões do Claude Code

Projeto de portfólio público do Rafael (engenharia de dados). Qualidade e clareza importam mais que velocidade.

## Como trabalhar
- Pegue uma issue aberta do milestone mais antigo, trabalhe em uma branch `feat/<numero>-<slug>` e abra PR com `Closes #N`.
- Uma issue por PR. Commits em português, padrão Conventional Commits.
- Atualize o README (Roadmap e Fontes) quando um milestone for concluído.

## Regras sobre dados
- Use apenas fontes públicas e oficiais. Registre URL, licença e data de acesso em `docs/fontes.md`.
- Se uma fonte candidata não estiver acessível, documente isso na issue e proponha alternativa — nunca invente dados.
- Não versione arquivos grandes de dados; versione apenas amostras pequenas em `tests/fixtures/`.

## Padrões técnicos
- Extração em `src/pipeline/`, transformações dbt em `transform/`, painel em `app/`.
- Extratores idempotentes e incrementais; requisições com retry e timeout.
- Todo modelo dbt de staging e mart precisa de testes e descrição em YAML.
- Textos e interface em português.

## Antes de abrir PR
```bash
ruff check . && ruff format --check . && pytest && dbt build --project-dir transform
```

-- Visão anual do Estado: despesa estadual em Educação por aluno da rede
-- estadual e soma da despesa municipal declarada.
with

anos as (
    select distinct ano from {{ ref('fct_despesa_educacao') }}
),

estado as (
    select ano, despesa_educacao
    from {{ ref('fct_despesa_educacao') }}
    where esfera = 'estadual'
),

municipios as (
    select ano, sum(despesa_educacao) as despesa_educacao, count(*) as municipios_com_dca
    from {{ ref('fct_despesa_educacao') }}
    where esfera = 'municipal'
    group by ano
),

matriculas_estaduais as (
    select ano, sum(matriculas_educacao_basica) as matriculas
    from {{ ref('fct_matriculas') }}
    where rede = 'estadual'
    group by ano
)

select
    a.ano,
    e.despesa_educacao as despesa_educacao_estado,
    cast(me.matriculas as integer) as matriculas_rede_estadual,
    cast(round(e.despesa_educacao / nullif(me.matriculas, 0), 2) as decimal(18, 2))
        as investimento_por_aluno_estado,
    cast(m.despesa_educacao as decimal(18, 2)) as despesa_educacao_municipios,
    cast(coalesce(m.municipios_com_dca, 0) as integer) as municipios_com_dca
from anos as a
left join estado as e on a.ano = e.ano
left join municipios as m on a.ano = m.ano
left join matriculas_estaduais as me on a.ano = me.ano

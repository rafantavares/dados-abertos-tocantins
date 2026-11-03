-- Investimento por aluno da rede municipal: despesa municipal liquidada na
-- função Educação dividida pelas matrículas da rede municipal, com o IDEB
-- da rede municipal no mesmo ano (anos ímpares).
-- Só entram anos com despesa declarada (e consistente) e Censo Escolar disponível.
with

despesa as (
    select cod_ente as cod_municipio, ano, despesa_educacao
    from {{ ref('fct_despesa_educacao') }}
    where esfera = 'municipal' and not dca_inconsistente
),

matriculas as (
    select cod_municipio, ano, matriculas_educacao_basica
    from {{ ref('fct_matriculas') }}
    where rede = 'municipal'
),

ideb as (
    select
        cod_municipio,
        ano,
        max(ideb) filter (where etapa = 'anos_iniciais') as ideb_anos_iniciais,
        max(ideb) filter (where etapa = 'anos_finais') as ideb_anos_finais
    from {{ ref('fct_ideb') }}
    where rede = 'municipal'
    group by cod_municipio, ano
)

select
    d.cod_municipio,
    d.ano,
    d.despesa_educacao,
    cast(m.matriculas_educacao_basica as integer) as matriculas_rede_municipal,
    cast(round(d.despesa_educacao / nullif(m.matriculas_educacao_basica, 0), 2) as decimal(18, 2))
        as investimento_por_aluno,
    i.ideb_anos_iniciais,
    i.ideb_anos_finais
from despesa as d
inner join matriculas as m on d.cod_municipio = m.cod_municipio and d.ano = m.ano
left join ideb as i on d.cod_municipio = i.cod_municipio and d.ano = i.ano

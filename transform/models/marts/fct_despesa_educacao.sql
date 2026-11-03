-- Despesa liquidada em Educação por ente (municípios e Estado) e ano.
with

despesa as (
    select * from {{ ref('int_despesa_educacao_ente_ano') }}
),

populacao_municipal as (
    select cod_municipio as cod_ente, ano, populacao, origem_populacao
    from {{ ref('int_populacao_anual') }}
),

-- população do Estado = soma dos municípios no ano; nula se faltar algum
populacao_estadual as (
    select
        17 as cod_ente,
        ano,
        case when count(populacao) = count(*) then sum(populacao) end as populacao,
        case
            when count(populacao) < count(*) then null
            when bool_and(origem_populacao = 'censo') then 'censo'
            when bool_and(origem_populacao = 'estimativa') then 'estimativa'
            else 'ultima_disponivel'
        end as origem_populacao
    from {{ ref('int_populacao_anual') }}
    group by ano
),

populacao as (
    select * from populacao_municipal
    union all
    select * from populacao_estadual
)

select
    d.cod_ente,
    d.esfera,
    d.ano,
    cast(d.despesa_total as decimal(18, 2)) as despesa_total,
    cast(d.despesa_educacao as decimal(18, 2)) as despesa_educacao,
    cast(d.despesa_ensino_fundamental as decimal(18, 2)) as despesa_ensino_fundamental,
    cast(d.despesa_ensino_medio as decimal(18, 2)) as despesa_ensino_medio,
    cast(d.despesa_educacao_infantil as decimal(18, 2)) as despesa_educacao_infantil,
    round(100.0 * d.despesa_educacao / nullif(d.despesa_total, 0), 2) as percentual_educacao,
    cast(p.populacao as integer) as populacao,
    p.origem_populacao,
    cast(round(d.despesa_educacao / nullif(p.populacao, 0), 2) as decimal(18, 2))
        as despesa_educacao_per_capita,
    -- valores corrigidos pelo IPCA médio do ano, em reais do ano-base do deflator
    cast(round(d.despesa_educacao * ipca.fator_correcao, 2) as decimal(18, 2))
        as despesa_educacao_real,
    cast(round(d.despesa_educacao * ipca.fator_correcao / nullif(p.populacao, 0), 2)
        as decimal(18, 2)) as despesa_educacao_per_capita_real,
    ipca.ano_base as ano_base_valores_reais,
    -- Menos de 5% da despesa total em Educação é implausível para um ente que
    -- precisa aplicar 25% da receita de impostos em MDE: indica DCA declarado
    -- de forma parcial (ex.: só a Câmara). A linha é mantida e sinalizada.
    coalesce(100.0 * d.despesa_educacao / nullif(d.despesa_total, 0) < 5, true)
        as dca_inconsistente
from despesa as d
left join populacao as p on d.cod_ente = p.cod_ente and d.ano = p.ano
left join {{ ref('dim_deflator_ipca') }} as ipca on d.ano = ipca.ano
where d.esfera = 'estadual'
    or d.cod_ente in (select cod_municipio from {{ ref('dim_municipio') }})

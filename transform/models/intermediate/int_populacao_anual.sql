-- População de referência de cada município em cada ano usado nos marts.
-- Prioridade: Censo (2022) > estimativa do ano > último valor disponível antes
-- do ano (o IBGE não publica estimativa em todo ano, ex.: 2022 e 2023).
with

populacao as (
    select * from {{ ref('stg_ibge__populacao') }}
),

anos as (
    select unnest(range(
        (select min(ano) from {{ ref('stg_siconfi__dca_despesa_funcao') }}),
        (select max(ano) from {{ ref('stg_siconfi__dca_despesa_funcao') }}) + 1
    )) as ano
),

grade as (
    select m.cod_municipio, a.ano
    from {{ ref('stg_ibge__municipios') }} as m
    cross join anos as a
),

-- se houver Censo e estimativa no mesmo ano, fica o Censo
uma_por_ano as (
    select *
    from populacao
    qualify row_number() over (
        partition by cod_municipio, ano
        order by case origem when 'censo' then 0 else 1 end
    ) = 1
)

select
    g.cod_municipio,
    g.ano,
    p.populacao,
    case when p.ano = g.ano then p.origem else 'ultima_disponivel' end as origem_populacao,
    p.ano as ano_populacao
from grade as g
asof left join uma_por_ano as p
    on g.cod_municipio = p.cod_municipio
    and g.ano >= p.ano

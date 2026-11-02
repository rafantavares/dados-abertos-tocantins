-- Dimensão de municípios do Tocantins (139).
with

municipios as (
    select * from {{ ref('stg_ibge__municipios') }}
),

censo as (
    select cod_municipio, populacao
    from {{ ref('stg_ibge__populacao') }}
    where origem = 'censo' and ano = 2022
),

entes as (
    select cod_ente, eh_capital from {{ ref('stg_siconfi__entes') }}
)

select
    m.cod_municipio,
    m.nome_municipio,
    m.regiao_intermediaria,
    m.regiao_imediata,
    c.populacao as populacao_censo_2022,
    coalesce(e.eh_capital, false) as eh_capital
from municipios as m
left join censo as c on m.cod_municipio = c.cod_municipio
left join entes as e on m.cod_municipio = e.cod_ente

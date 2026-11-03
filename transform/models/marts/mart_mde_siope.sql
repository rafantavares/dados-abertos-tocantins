-- Indicadores oficiais de financiamento da educação (SIOPE/FNDE) por ente e ano:
-- aplicação em MDE frente ao mínimo constitucional de 25%, uso do Fundeb e
-- investimento por aluno. Responde à pergunta P9 e complementa P5.
with indicadores as (
    select * from {{ ref('stg_siope__indicadores') }}
)

select
    cod_ente,
    any_value(esfera) as esfera,
    ano,
    max(valor) filter (where cod_indicador = '1.1') as percentual_mde,
    max(valor) filter (where cod_indicador = '1.1') >= 25 as cumpre_minimo_mde,
    max(valor) filter (where cod_indicador = '1.2') as percentual_fundeb_remuneracao,
    max(valor) filter (where cod_indicador = '2.8') as percentual_educacao_despesa_total,
    cast(max(valor) filter (where cod_indicador = '4.8') as decimal(18, 2))
        as investimento_por_aluno_educacao_basica,
    cast(max(valor) filter (where cod_indicador = '4.9') as decimal(18, 2))
        as investimento_por_aluno,
    cast(max(valor) filter (where cod_indicador = '8.1') as decimal(18, 2))
        as valor_exigido_mde,
    cast(max(valor) filter (where cod_indicador = '8.2') as decimal(18, 2))
        as valor_aplicado_mde
from indicadores
where esfera = 'estadual'
    or cod_ente in (select cod_municipio from {{ ref('dim_municipio') }})
group by cod_ente, ano

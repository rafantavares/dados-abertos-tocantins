-- Indicadores oficiais do SIOPE por ente, ano e indicador.
-- O SIOPE identifica o município pelo código IBGE de 6 dígitos (sem o dígito
-- verificador) e deixa o código nulo para o Estado; aqui os dois viram cod_ente
-- (7 dígitos para municípios, 17 para o Estado). O mesmo indicador muda de
-- COD_INDI conforme a versão da norma, mas mantém o código de exibição
-- (COD_EXIB, ex.: '1.1'), que é usado como chave.
with

fonte as (
    select * from {{ source('raw', 'siope_indicadores') }}
),

municipios as (
    select cod_municipio, cod_municipio // 10 as cod_municipio_6
    from {{ ref('stg_ibge__municipios') }}
)

select
    cast(f."NUM_ANO" as integer) as ano,
    case when f."TIPO" = 'Estadual' then 17 else m.cod_municipio end as cod_ente,
    case f."TIPO" when 'Estadual' then 'estadual' when 'Municipal' then 'municipal' end
        as esfera,
    trim(f."COD_EXIB") as cod_indicador,
    cast(f."COD_INDI" as integer) as cod_indicador_versao,
    trim(f."NOM_INDI") as nome_indicador,
    try_cast(f."VAL_INDI" as double) as valor
from fonte as f
left join municipios as m
    on try_cast(f."COD_MUNI" as integer) = m.cod_municipio_6

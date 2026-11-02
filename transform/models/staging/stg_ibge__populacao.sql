-- População residente por município e ano: Censo 2022 (SIDRA 4709) e
-- estimativas anuais (SIDRA 6579).
select
    cast("D1C" as integer) as cod_municipio,
    cast("D3C" as integer) as ano,
    try_cast("V" as integer) as populacao,
    case _referencia when '4709' then 'censo' when '6579' then 'estimativa' end as origem,
    cast(_referencia as integer) as tabela_sidra
from {{ source('raw', 'ibge_sidra_populacao') }}
where try_cast("V" as integer) is not null

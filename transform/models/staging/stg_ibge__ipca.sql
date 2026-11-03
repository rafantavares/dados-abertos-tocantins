-- IPCA mensal (número-índice, base dez/1993 = 100), Brasil, SIDRA tabela 1737.
-- O período vem como AAAAMM em D3C.
select
    cast(substr("D3C", 1, 4) as integer) as ano,
    cast(substr("D3C", 5, 2) as integer) as mes,
    cast("V" as double) as numero_indice
from {{ source('raw', 'ibge_sidra_ipca') }}
where try_cast("V" as double) is not null

-- Entes do Tocantins no SICONFI: o Estado (código 17) e os municípios.
select
    cast(cod_ibge as integer) as cod_ente,
    trim(ente) as nome_ente,
    case esfera when 'E' then 'estadual' when 'M' then 'municipal' end as esfera,
    trim(capital) = '1' as eh_capital,
    cast(exercicio as integer) as exercicio_referencia,
    cast(populacao as integer) as populacao_siconfi,
    cnpj
from {{ source('raw', 'siconfi_entes') }}

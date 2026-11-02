-- Municípios do Tocantins segundo a Divisão Territorial Brasileira (DTB) do IBGE.
select
    cast("Código Município Completo" as integer) as cod_municipio,
    trim("Nome_Município") as nome_municipio,
    cast("Região Geográfica Intermediária" as integer) as cod_regiao_intermediaria,
    trim("Nome Região Geográfica Intermediária") as regiao_intermediaria,
    cast("Região Geográfica Imediata" as integer) as cod_regiao_imediata,
    trim("Nome Região Geográfica Imediata") as regiao_imediata,
    cast(_referencia as integer) as ano_referencia
from {{ source('raw', 'ibge_dtb_municipios') }}

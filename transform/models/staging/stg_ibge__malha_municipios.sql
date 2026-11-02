-- Contorno de cada município (malha municipal 2022 do IBGE), já simplificado
-- pelo extrator e serializado em GeoJSON.
select
    cast("CD_MUN" as integer) as cod_municipio,
    trim("NM_MUN") as nome_municipio,
    cast("AREA_KM2" as double) as area_km2,
    geojson
from {{ source('raw', 'ibge_malha_municipios') }}

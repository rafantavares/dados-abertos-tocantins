-- Contorno simplificado de cada município, em GeoJSON (WGS84), para o mapa.
select cod_municipio, area_km2, geojson
from {{ ref('stg_ibge__malha_municipios') }}

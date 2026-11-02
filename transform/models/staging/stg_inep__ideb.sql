-- IDEB em formato longo: uma linha por município, rede, etapa e ano.
-- A planilha do INEP é larga (uma coluna por indicador e ano, ex.:
-- VL_OBSERVADO_2023); aqui ela é despivotada e os marcadores de ausência
-- ('-' e 'ND') viram nulo. As notas do SAEB de 2015 vêm com vírgula decimal.
{% set etapas = ['anos_iniciais', 'anos_finais', 'ensino_medio'] %}

with

longo as (
    {% for etapa in etapas %}
    select
        '{{ etapa }}' as etapa,
        "CO_MUNICIPIO" as co_municipio,
        "REDE" as rede,
        coluna,
        valor
    from (
        unpivot {{ source('raw', 'inep_ideb_' ~ etapa) }}
        on columns('^VL_')
        into name coluna value valor
    )
    {% if not loop.last %}union all{% endif %}
    {% endfor %}
),

partes as (
    select
        etapa,
        cast(co_municipio as integer) as cod_municipio,
        lower(strip_accents(trim(rede))) as rede,
        regexp_extract(coluna, '^VL_(.+?)_(\d{4})(_.*)?$', 1) as indicador,
        cast(regexp_extract(coluna, '^VL_(.+?)_(\d{4})(_.*)?$', 2) as integer) as ano,
        regexp_extract(coluna, '^VL_(.+?)_(\d{4})(_.*)?$', 3) as sufixo,
        try_cast(
            replace(nullif(nullif(trim(valor), '-'), 'ND'), ',', '.') as double
        ) as valor
    from longo
),

largo as (
    select
        cod_municipio,
        ano,
        etapa,
        rede,
        -- _SI_4 é a taxa da etapa inteira (ex.: 1º ao 5º ano)
        max(valor) filter (where indicador = 'APROVACAO' and sufixo = '_SI_4') as taxa_aprovacao,
        max(valor) filter (where indicador = 'INDICADOR_REND') as indicador_rendimento,
        max(valor) filter (where indicador = 'NOTA_MATEMATICA') as nota_saeb_matematica,
        max(valor) filter (where indicador = 'NOTA_PORTUGUES') as nota_saeb_portugues,
        max(valor) filter (where indicador = 'NOTA_MEDIA') as nota_saeb_padronizada,
        max(valor) filter (where indicador = 'OBSERVADO') as ideb,
        max(valor) filter (where indicador = 'PROJECAO') as meta_ideb
    from partes
    group by all
)

select *
from largo
where coalesce(
    taxa_aprovacao, indicador_rendimento, nota_saeb_matematica, nota_saeb_portugues,
    nota_saeb_padronizada, ideb, meta_ideb
) is not null

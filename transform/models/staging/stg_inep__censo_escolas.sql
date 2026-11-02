-- Escolas do Censo Escolar com rede, situação e matrículas tipadas.
with fonte as (
    select * from {{ source('raw', 'inep_censo_escolas') }}
)

select
    cast("NU_ANO_CENSO" as integer) as ano,
    cast("CO_ENTIDADE" as integer) as cod_escola,
    trim("NO_ENTIDADE") as nome_escola,
    cast("CO_MUNICIPIO" as integer) as cod_municipio,
    case "TP_DEPENDENCIA"
        when '1' then 'federal'
        when '2' then 'estadual'
        when '3' then 'municipal'
        when '4' then 'privada'
    end as rede,
    case "TP_LOCALIZACAO" when '1' then 'urbana' when '2' then 'rural' end as localizacao,
    case "TP_SITUACAO_FUNCIONAMENTO"
        when '1' then 'em_atividade'
        when '2' then 'paralisada'
        when '3' then 'extinta'
        when '4' then 'extinta_ano_anterior'
    end as situacao,
    "TP_SITUACAO_FUNCIONAMENTO" = '1' as em_atividade,
    try_cast("QT_MAT_BAS" as integer) as matriculas_educacao_basica,
    try_cast("QT_MAT_INF" as integer) as matriculas_infantil,
    try_cast("QT_MAT_FUND" as integer) as matriculas_fundamental,
    try_cast("QT_MAT_MED" as integer) as matriculas_medio,
    try_cast("QT_MAT_PROF" as integer) as matriculas_profissional,
    try_cast("QT_MAT_EJA" as integer) as matriculas_eja,
    try_cast("QT_MAT_ESP" as integer) as matriculas_especial
from fonte

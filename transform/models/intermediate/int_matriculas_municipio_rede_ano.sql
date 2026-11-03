-- Escolas em atividade e matrículas por município, rede e ano.
select
    cod_municipio,
    ano,
    rede,
    cast(count(*) as integer) as escolas_em_atividade,
    cast(coalesce(sum(matriculas_educacao_basica), 0) as integer) as matriculas_educacao_basica,
    cast(coalesce(sum(matriculas_infantil), 0) as integer) as matriculas_infantil,
    cast(coalesce(sum(matriculas_fundamental), 0) as integer) as matriculas_fundamental,
    cast(coalesce(sum(matriculas_medio), 0) as integer) as matriculas_medio,
    cast(coalesce(sum(matriculas_eja), 0) as integer) as matriculas_eja,
    cast(coalesce(sum(matriculas_especial), 0) as integer) as matriculas_especial
from {{ ref('stg_inep__censo_escolas') }}
where em_atividade
group by cod_municipio, ano, rede

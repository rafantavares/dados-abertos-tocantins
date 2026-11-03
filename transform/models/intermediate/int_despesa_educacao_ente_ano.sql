-- Despesa liquidada por ente e ano: total, função Educação e subfunções principais.
with liquidada as (
    select *
    from {{ ref('stg_siconfi__dca_despesa_funcao') }}
    where estagio = 'liquidada'
)

select
    cod_ente,
    any_value(esfera) as esfera,
    ano,
    sum(valor) filter (where tipo_conta = 'total_exceto_intra') as despesa_total,
    coalesce(sum(valor) filter (where tipo_conta = 'funcao_educacao'), 0) as despesa_educacao,
    coalesce(sum(valor) filter (where cod_subfuncao = 361), 0) as despesa_ensino_fundamental,
    coalesce(sum(valor) filter (where cod_subfuncao = 362), 0) as despesa_ensino_medio,
    coalesce(sum(valor) filter (where cod_subfuncao = 365), 0) as despesa_educacao_infantil
from liquidada
group by cod_ente, ano
-- ente sem o total declarado não tem DCA válido no ano
having sum(valor) filter (where tipo_conta = 'total_exceto_intra') is not null

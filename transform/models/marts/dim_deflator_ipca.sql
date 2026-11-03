-- Deflator anual pelo IPCA médio do ano (média dos 12 números-índice mensais),
-- adequado para corrigir fluxos que ocorrem ao longo do ano, como a despesa.
-- O ano-base é o último ano com os 12 meses publicados; valores reais ficam
-- "em reais de <ano_base>". Anos incompletos não entram.
with

anual as (
    select ano, avg(numero_indice) as ipca_medio, count(*) as meses
    from {{ ref('stg_ibge__ipca') }}
    group by ano
    having count(*) = 12
),

base as (
    select max(ano) as ano_base from anual
)

select
    a.ano,
    a.ipca_medio,
    b.ano_base,
    (select ipca_medio from anual where ano = b.ano_base) / a.ipca_medio as fator_correcao
from anual as a
cross join base as b

-- DCA Anexo I-E normalizado: uma linha por ente, ano, estágio da despesa e conta.
-- Os rótulos mudam entre exercícios (ex.: 'Despesas (Exceto Intraorçamentárias)'
-- e 'Despesas Exceto Intraorçamentárias'; 'FU12 - Demais Subfunções' e
-- '12.999 - Demais Subfunções Educação'), então a conta é classificada por padrão.
with fonte as (
    select * from {{ source('raw', 'siconfi_dca_despesa_funcao') }}
),

classificado as (
    select
        cast(exercicio as integer) as ano,
        cast(cod_ibge as integer) as cod_ente,
        trim(coluna) as coluna_origem,
        trim(conta) as conta_origem,
        case
            when trim(coluna) = 'Despesas Empenhadas' then 'empenhada'
            when trim(coluna) = 'Despesas Liquidadas' then 'liquidada'
            when trim(coluna) = 'Despesas Pagas' then 'paga'
            when trim(coluna) = 'Inscrição de Restos a Pagar Processados' then 'restos_a_pagar_processados'
            when trim(coluna) = 'Inscrição de Restos a Pagar Não Processados' then 'restos_a_pagar_nao_processados'
        end as estagio,
        case
            when conta ilike 'Despesas%Exceto%Intra%' then 'total_exceto_intra'
            when conta ilike 'Despesas%Intra%' then 'total_intra'
            when regexp_matches(conta, '^\s*12 - ') then 'funcao_educacao'
            when regexp_matches(conta, '^\s*(FU12|12\.999) ') then 'subfuncao'
            when regexp_matches(conta, '^\s*12\.\d{3} - ') then 'subfuncao'
        end as tipo_conta,
        case
            when regexp_matches(conta, '^\s*(FU12|12\.999) ') then 999
            else try_cast(regexp_extract(conta, '^\s*12\.(\d{3}) - ', 1) as integer)
        end as cod_subfuncao,
        cast(valor as decimal(18, 2)) as valor
    from fonte
)

select
    ano,
    cod_ente,
    case when cod_ente = 17 then 'estadual' else 'municipal' end as esfera,
    estagio,
    tipo_conta,
    cod_subfuncao,
    case
        when cod_subfuncao = 999 then 'Demais subfunções'
        when cod_subfuncao is not null then trim(regexp_extract(conta_origem, ' - (.+)$', 1))
    end as nome_subfuncao,
    valor,
    coluna_origem,
    conta_origem
from classificado

-- IDEB por município, ano, etapa e rede, com indicação de meta atingida.
select
    i.cod_municipio,
    i.ano,
    i.etapa,
    i.rede,
    i.taxa_aprovacao,
    i.indicador_rendimento,
    i.nota_saeb_matematica,
    i.nota_saeb_portugues,
    i.nota_saeb_padronizada,
    i.ideb,
    i.meta_ideb,
    case
        when i.ideb is null or i.meta_ideb is null then null
        else i.ideb >= i.meta_ideb
    end as atingiu_meta
from {{ ref('stg_inep__ideb') }} as i
inner join {{ ref('dim_municipio') }} as m on i.cod_municipio = m.cod_municipio

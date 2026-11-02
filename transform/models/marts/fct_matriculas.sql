-- Escolas em atividade e matrículas por município, ano e rede.
select i.*
from {{ ref('int_matriculas_municipio_rede_ano') }} as i
inner join {{ ref('dim_municipio') }} as m on i.cod_municipio = m.cod_municipio

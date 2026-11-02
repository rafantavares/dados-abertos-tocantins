{# Falha se a combinação das colunas não for única no modelo. #}
{% test combinacao_unica(model, colunas) %}
select {{ colunas | join(', ') }}, count(*) as repeticoes
from {{ model }}
group by {{ colunas | join(', ') }}
having count(*) > 1
{% endtest %}

{# Falha se algum valor não nulo estiver fora do intervalo [minimo, maximo]. #}
{% test entre(model, column_name, minimo=none, maximo=none) %}
select {{ column_name }}
from {{ model }}
where {{ column_name }} is not null
  and (
    false
    {% if minimo is not none %} or {{ column_name }} < {{ minimo }} {% endif %}
    {% if maximo is not none %} or {{ column_name }} > {{ maximo }} {% endif %}
  )
{% endtest %}

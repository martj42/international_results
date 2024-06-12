{% macro generate_database_name(custom_database_name=None, node=None) %}
    {%- set default_database = target.database -%}
    {%- if custom_database_name is none -%}
        {{ default_database }}
    {%- else -%}
        {{ custom_database_name | trim }}
    {%- endif -%}
{% endmacro %}

 
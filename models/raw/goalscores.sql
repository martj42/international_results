{{
  config({    
    "schema": 'DEV'
  })
}}

WITH goalscorers AS (

  SELECT * 
  
  FROM {{ ref('goalscorers')}}

)

SELECT *

FROM goalscorers

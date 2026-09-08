select
customer_id,
customer_name,
email,
age,
CASE
    WHEN age <25 THEN 'Gen Z'
    WHEN age <40 THEN 'Millennial'
    WHEN age <55 THEN 'Gen X'
    WHEN age IS NULL THEN 'Unknown'
    ELSE 'Boomer'
END AS age_segment,
gender,
marital_status,
occupation,
income_band,
education,
family_size
from {{ref('stg_users')}}


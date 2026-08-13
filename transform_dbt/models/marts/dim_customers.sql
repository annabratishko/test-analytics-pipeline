with product_customers as (
    select * from {{ ref('stg_product_customers') }}
),

stripe_customers as (
    select * from {{ ref('stg_stripe_customers') }}
)

select
    pc.customer_id,
    pc.email,
    pc.country,
    pc.signup_date,
    pc.stripe_customer_id,
    sc.created as stripe_signup_date,
    (pc.stripe_customer_id is not null) as is_paying_customer
from product_customers pc
left join stripe_customers sc
    on pc.stripe_customer_id = sc.id
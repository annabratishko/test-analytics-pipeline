with payments as (
    select * from {{ ref('stg_stripe_charges') }}
)

select
    id as payment_id, 
    amount as amount_cents,
    currency,
    customer as stripe_customer_id,
    description,
    statement_descriptor,
    status,
    created,
    round(amount / 100.0, 2) as amount_final,
    (status = 'succeeded') as is_successful
from payments
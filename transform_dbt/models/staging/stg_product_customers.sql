select
    customer_id,
    stripe_customer_id,
    email,
    country,
    signup_date
from {{ source('raw', 'product_customers') }}
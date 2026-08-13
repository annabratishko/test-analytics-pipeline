select
    id, 
    email, 
    created
from {{ source('raw', 'stripe_customers') }}
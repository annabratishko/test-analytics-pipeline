select
    id, 
    amount,
    currency,
    customer,
    description,
    statement_descriptor,
    status,
    created
from {{ source('raw', 'stripe_charges') }}
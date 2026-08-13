with orders as (
    select * from {{ ref('stg_product_orders') }}
)

select
    order_id,
    customer_id,
    document_type,
    status,
    price,
    created_at,
    updated_at,
    (status = 'completed') as is_completed,
    date_part('day', updated_at - created_at) as days_to_last_update
from orders
select
    order_id, 
    customer_id, 
    document_type, 
    status, 
    price, 
    created_at, 
    updated_at
from {{ source('raw', 'product_orders') }}
with amplitude_events as (
    select * from {{ ref('stg_amplitude_events') }}
)

select
    event_id,
    user_id,
    event_type,
    event_time,
    (event_properties->>'order_id')::integer as order_id,
    (event_properties->>'price')::numeric as price,
    event_properties->>'document_type' as document_type
from amplitude_events
where event_type in ('order_started', 'order_completed')
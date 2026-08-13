with amplitude_events as (
    select * from {{ ref('stg_amplitude_events') }}
)

select
    event_id,
    user_id,
    event_type,
    event_time,
    (event_properties->>'email') as email
from amplitude_events
where event_type in ('signup')
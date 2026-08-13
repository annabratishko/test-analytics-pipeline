select
    event_id, 
    user_id, 
    event_type, 
    event_time, 
    server_upload_time, 
    event_properties
from {{ source('raw', 'amplitude_events') }}
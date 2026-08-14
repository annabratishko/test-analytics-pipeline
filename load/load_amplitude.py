import os
import json
import glob
import psycopg2
from psycopg2.extras import Json

DB_CONN = "dbname=analytics_pipeline"
RAW_DIR = "data/raw/amplitude"
CUTOFF = "2026-08-12 11:00:00"  # anything before this is the corrupted pre-fix batch — never load it


def run():
    paths = glob.glob(os.path.join(RAW_DIR, "**", "*.json"), recursive=True)

    conn = psycopg2.connect(DB_CONN)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw.amplitude_events (
            event_id BIGINT PRIMARY KEY,
            user_id TEXT,
            event_type TEXT,
            event_time TIMESTAMP,
            server_upload_time TIMESTAMP,
            event_properties JSONB
        )
    """)

    total = 0
    skipped = 0
    for path in paths:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                event = json.loads(line)

                if event["server_upload_time"] < CUTOFF:
                    skipped += 1
                    continue

                cur.execute("""
                    INSERT INTO raw.amplitude_events
                        (event_id, user_id, event_type, event_time, server_upload_time, event_properties)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (event_id) DO UPDATE SET
                        event_properties = EXCLUDED.event_properties
                """, (
                    event["event_id"],
                    event["user_id"],
                    event["event_type"],
                    event["event_time"],
                    event["server_upload_time"],
                    Json(event.get("event_properties", {})),
                ))
                total += 1

        print(f"  processed {path}")

    conn.commit()
    conn.close()
    print(f"Loaded {total} events total ({skipped} skipped as pre-fix corrupted data)")


if __name__ == "__main__":
    run()
import os
import sqlite3
import csv
import json
from datetime import datetime

DB_PATH = "data/product.db"
OUTPUT_DIR = "data/raw/product"
STATE_DIR = "data/state"
STATE_FILE = os.path.join(STATE_DIR, "product_db_watermark.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(STATE_DIR, exist_ok=True)


def load_watermark():
    if not os.path.exists(STATE_FILE):
        return "1970-01-01T00:00:00"
    with open(STATE_FILE) as f:
        return json.load(f).get("orders_last_updated_at", "1970-01-01T00:00:00")


def save_watermark(timestamp):
    with open(STATE_FILE, "w") as f:
        json.dump({"orders_last_updated_at": timestamp}, f)


def run_query(conn, query, params=()):
    cur = conn.cursor()
    cur.execute(query, params)
    columns = [description[0] for description in cur.description]
    rows = cur.fetchall()
    return columns, rows


def save_csv(columns, rows, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
    print(f"Saved {len(rows)} records to {path}")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    run_date = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

    print("Extracting customers (full)...")
    columns, rows = run_query(conn, "SELECT * FROM customers")
    save_csv(columns, rows, f"customers_{run_date}.csv")

    watermark = load_watermark()
    print(f"Extracting orders updated after {watermark}...")
    columns, rows = run_query(
        conn,
        "SELECT * FROM orders WHERE updated_at > ? ORDER BY updated_at",
        (watermark,),
    )
    save_csv(columns, rows, f"orders_{run_date}.csv")

    if rows:
        updated_at_index = columns.index("updated_at")
        new_watermark = max(row[updated_at_index] for row in rows)
        save_watermark(new_watermark)
        print(f"Updated watermark to {new_watermark}")
    else:
        print("No new or updated orders — watermark unchanged")

    conn.close()
    print("Done.")
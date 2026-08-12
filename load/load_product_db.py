import os
import csv
import glob
import psycopg2

DB_CONN = "dbname=analytics_pipeline"

RAW_DIR = "data/raw/product"


def get_latest_file(pattern):
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"No files matching {pattern}")
    return max(files, key=os.path.getctime)


def load_customers(conn):
    path = get_latest_file(os.path.join(RAW_DIR, "customers_*.csv"))
    print(f"Loading customers from {path}")

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw.product_customers (
            customer_id INTEGER PRIMARY KEY,
            stripe_customer_id TEXT,
            email TEXT,
            country TEXT,
            signup_date TIMESTAMP
        )
    """)

    for row in rows:
        stripe_customer_id = row["stripe_customer_id"] or None
        cur.execute("""
            INSERT INTO raw.product_customers
                (customer_id, stripe_customer_id, email, country, signup_date)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (customer_id) DO UPDATE SET
                stripe_customer_id = EXCLUDED.stripe_customer_id,
                email = EXCLUDED.email,
                country = EXCLUDED.country,
                signup_date = EXCLUDED.signup_date
        """, (row["customer_id"], stripe_customer_id, row["email"], row["country"], row["signup_date"]))

    conn.commit()
    print(f"Loaded {len(rows)} customers")


def load_orders(conn):
    # Orders are extracted incrementally, so we load every orders_*.csv file,
    # not just the latest one — each file only contains that run's new/updated rows
    paths = sorted(glob.glob(os.path.join(RAW_DIR, "orders_*.csv")))

    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw.product_orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            document_type TEXT,
            status TEXT,
            price NUMERIC,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)

    total = 0
    for path in paths:
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        for row in rows:
            cur.execute("""
                INSERT INTO raw.product_orders
                    (order_id, customer_id, document_type, status, price, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (order_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    price = EXCLUDED.price,
                    updated_at = EXCLUDED.updated_at
            """, (
                row["order_id"], row["customer_id"], row["document_type"],
                row["status"], row["price"], row["created_at"], row["updated_at"]
            ))
        total += len(rows)
        print(f"  processed {path} ({len(rows)} rows)")

    conn.commit()
    print(f"Loaded {total} order records total (across all files)")


if __name__ == "__main__":
    conn = psycopg2.connect(DB_CONN)
    load_customers(conn)
    load_orders(conn)
    conn.close()
    print("Done.")
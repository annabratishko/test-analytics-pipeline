import os
import json
import glob
import psycopg2

DB_CONN = "dbname=analytics_pipeline"
RAW_DIR = "data/raw/stripe"

def run():
    def load_customers(conn):
        paths = sorted(glob.glob(os.path.join(RAW_DIR, "customers_*.json")))

        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.stripe_customers (
                id TEXT PRIMARY KEY,
                email TEXT,
                created TIMESTAMP
            )
        """)

        total = 0
        for path in paths:
            with open(path) as f:
                customers = json.load(f)

            for customer in customers:
                cur.execute("""
                    INSERT INTO raw.stripe_customers
                        (id, email, created)
                    VALUES (%s, %s, to_timestamp(%s))
                    ON CONFLICT (id) DO UPDATE SET
                        email = EXCLUDED.email,
                        created = EXCLUDED.created
                """, (customer["id"], customer["email"], customer["created"]))
            total += len(customers)
            print(f"  processed {path} ({len(customers)} rows)")

        conn.commit()
        print(f"Loaded {total} customer records total")


    def load_charges(conn):
        paths = sorted(glob.glob(os.path.join(RAW_DIR, "charges_*.json")))

        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.stripe_charges (
                id TEXT PRIMARY KEY,
                amount INTEGER,
                currency TEXT,
                customer TEXT,
                description TEXT,
                statement_descriptor TEXT,
                status TEXT,
                created TIMESTAMP
            )
        """)

        total = 0
        for path in paths:
            with open(path) as f:
                charges = json.load(f)

            for charge in charges:
                cur.execute("""
                    INSERT INTO raw.stripe_charges
                        (id, amount, currency, customer, description, statement_descriptor, status, created)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, to_timestamp(%s))
                    ON CONFLICT (id) DO UPDATE SET
                        amount = EXCLUDED.amount,
                        currency = EXCLUDED.currency,
                        customer = EXCLUDED.customer,
                        description = EXCLUDED.description,
                        statement_descriptor = EXCLUDED.statement_descriptor,
                        status = EXCLUDED.status,
                        created = EXCLUDED.created
                """, (charge["id"], charge["amount"], charge["currency"], charge["customer"], charge["description"], charge["statement_descriptor"], charge["status"], charge["created"]))
            total += len(charges)
            print(f"  processed {path} ({len(charges)} rows)")

        conn.commit()
        print(f"Loaded {total} charges records total")


    conn = psycopg2.connect(DB_CONN)
    load_customers(conn)
    load_charges(conn)
    conn.close()
    print("Done.")

if __name__ == "__main__":
    run()
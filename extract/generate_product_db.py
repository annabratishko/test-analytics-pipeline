import sqlite3
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

DB_PATH = "data/product.db"

NUM_CUSTOMERS = 200

STATUSES = [
    "submitted",
    "in_review",
    "approved",
    "rejected",
    "completed"
]

DOCUMENT_TYPES = [
    "passport_renewal",
    "visa_application",
    "id_card",
    "birth_certificate",
    "residence_permit"
]


# --------------------------------------------------
# REAL STRIPE CUSTOMERS
# --------------------------------------------------

stripe_customers = [
    {
        "customer_id": 1,
        "stripe_customer_id": "cus_V2wu6Zthov7tZG",
        "email": "test5@test.com",
        "stripe_created": 1786359894,
        "payment_amount": 10.00,
        "payment_created": 1786360489,
        "subscription_type": "monthly",
    },
    {
        "customer_id": 2,
        "stripe_customer_id": "cus_V2wujfVwxX259v",
        "email": "test4@test.com",
        "stripe_created": 1786359883,
        "payment_amount": 10.00,
        "payment_created": 1786360462,
        "subscription_type": "monthly",
    },
    {
        "customer_id": 3,
        "stripe_customer_id": "cus_V2wuBP4qfjgfn1",
        "email": "test3@test.com",
        "stripe_created": 1786359868,
        "payment_amount": 50.00,
        "payment_created": 1786360430,
        "subscription_type": "yearly",
    },
    {
        "customer_id": 4,
        "stripe_customer_id": "cus_V2wtjGxpNeD9ni",
        "email": "test2@test.com",
        "stripe_created": 1786359856,
        "payment_amount": 5.00,
        "payment_created": 1786360394,
        "subscription_type": "weekly",
    },
    {
        "customer_id": 5,
        "stripe_customer_id": "cus_V2wtmIHYsPHAX1",
        "email": "test1@test.com",
        "stripe_created": 1786359840,
        "payment_amount": 10.00,
        "payment_created": 1786360288,
        "subscription_type": "monthly",
    }
]


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Start completely from scratch
cur.execute("DROP TABLE IF EXISTS stripe_charges")
cur.execute("DROP TABLE IF EXISTS orders")
cur.execute("DROP TABLE IF EXISTS customers")


# --------------------------------------------------
# CUSTOMERS TABLE
# --------------------------------------------------

cur.execute("""
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    stripe_customer_id TEXT UNIQUE,
    email TEXT,
    country TEXT,
    signup_date TEXT
)
""")


# --------------------------------------------------
# ORDERS TABLE
# --------------------------------------------------

cur.execute("""
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    document_type TEXT,
    status TEXT,
    price REAL,
    created_at TEXT,
    updated_at TEXT,

    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
)
""")


# --------------------------------------------------
# STRIPE CHARGES TABLE
# --------------------------------------------------

cur.execute("""
CREATE TABLE stripe_charges (
    charge_id TEXT PRIMARY KEY,
    stripe_customer_id TEXT,
    amount INTEGER,
    currency TEXT,
    payment_intent TEXT,
    paid BOOLEAN,
    status TEXT,
    created INTEGER,
    description TEXT,

    FOREIGN KEY (stripe_customer_id)
        REFERENCES customers(stripe_customer_id)
)
""")


# --------------------------------------------------
# INSERT FIRST 5 STRIPE CUSTOMERS
# --------------------------------------------------

for customer in stripe_customers:

    signup_date = datetime.fromtimestamp(
        customer["stripe_created"]
    ).isoformat()

    cur.execute("""
        INSERT INTO customers (
            customer_id,
            stripe_customer_id,
            email,
            country,
            signup_date
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        customer["customer_id"],
        customer["stripe_customer_id"],
        customer["email"],
        fake.country(),
        signup_date
    ))


# --------------------------------------------------
# GENERATE REMAINING 195 CUSTOMERS
# --------------------------------------------------

for customer_id in range(6, NUM_CUSTOMERS + 1):

    signup_date = fake.date_time_between(
        start_date="-1y",
        end_date="now"
    )

    cur.execute("""
        INSERT INTO customers (
            customer_id,
            stripe_customer_id,
            email,
            country,
            signup_date
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        customer_id,
        None,
        fake.email(),
        fake.country(),
        signup_date.isoformat()
    ))


# --------------------------------------------------
# CREATE ORDERS
# --------------------------------------------------

order_id = 1


# First 5 customers:
# create an order corresponding to their Stripe payment

for customer in stripe_customers:

    payment_datetime = datetime.fromtimestamp(
        customer["payment_created"]
    )

    document_type = random.choice(DOCUMENT_TYPES)

    cur.execute("""
        INSERT INTO orders (
            order_id,
            customer_id,
            document_type,
            status,
            price,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        order_id,
        customer["customer_id"],
        document_type,
        "completed",
        customer["payment_amount"],
        payment_datetime.isoformat(),
        payment_datetime.isoformat()
    ))

    order_id += 1


# --------------------------------------------------
# GENERATE RANDOM ORDERS FOR ALL CUSTOMERS
# --------------------------------------------------

for customer_id in range(1, NUM_CUSTOMERS + 1):

    # First 5 already have one Stripe-related order.
    # Add 0-4 additional synthetic orders.
    additional_orders = random.randint(0, 4)

    for _ in range(additional_orders):

        customer_row = cur.execute("""
            SELECT signup_date
            FROM customers
            WHERE customer_id = ?
        """, (customer_id,)).fetchone()

        signup_date = datetime.fromisoformat(
            customer_row[0]
        )

        now = datetime.now()
        days_since_signup = max((now - signup_date).days, 0)
        max_offset = min(300, days_since_signup)

        created_at = signup_date + timedelta(
            days=random.randint(0, max_offset) if max_offset > 0 else 0
        )

        max_update_offset = min(14, (now - created_at).days)
        updated_at = created_at + timedelta(
            days=random.randint(0, max_update_offset) if max_update_offset > 0 else 0
        )

        cur.execute("""
            INSERT INTO orders (
                order_id,
                customer_id,
                document_type,
                status,
                price,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            order_id,
            customer_id,
            random.choice(DOCUMENT_TYPES),
            random.choice(STATUSES),
            round(random.uniform(15, 120), 2),
            created_at.isoformat(),
            updated_at.isoformat()
        ))

        order_id += 1


conn.commit()
conn.close()

print(
    f"Created {NUM_CUSTOMERS} customers "
    f"and {order_id - 1} orders in {DB_PATH}"
)
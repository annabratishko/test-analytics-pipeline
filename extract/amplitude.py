import os
import random
import sqlite3
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv


# Load variables from .env
load_dotenv()

AMPLITUDE_API_KEY = os.getenv("AMPLITUDE_API_KEY")

if not AMPLITUDE_API_KEY:
    raise ValueError("AMPLITUDE_API_KEY is not set in .env")


DB_PATH = "data/product.db"
AMPLITUDE_URL = "https://api2.amplitude.com/2/httpapi"


# ---------------------------------------------------------
# 1. Get customers and orders from our product database
# ---------------------------------------------------------

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

customers = conn.execute("""
    SELECT customer_id, email, signup_date
    FROM customers
""").fetchall()

orders = conn.execute("""
    SELECT order_id, customer_id, document_type, status, price, created_at
    FROM orders
""").fetchall()

conn.close()

print(f"Loaded {len(customers)} customers")
print(f"Loaded {len(orders)} orders")


# ---------------------------------------------------------
# 2. Create Amplitude events
# ---------------------------------------------------------

events = []

# Events related to customers
for customer in customers:

    customer_id = str(customer["customer_id"])
    amplitude_user_id = f"customer_{int(customer_id):06d}"
    signup_date = customer["signup_date"]

    # signup event
    events.append({
    "user_id": amplitude_user_id,
    "event_type": "signup",
    "time": int(
        datetime.fromisoformat(signup_date).timestamp() * 1000
    ),
    "event_properties": {
        "source": "product_db",
        "email": customer["email"]
    },
    "user_properties": {
        "customer_id": customer_id
    }
})

    # page_view event
    events.append({
        "user_id": amplitude_user_id,
        "event_type": "page_view",
        "time": int(
            (
                datetime.fromisoformat(signup_date)
                + timedelta(minutes=random.randint(1, 60))
            ).timestamp() * 1000
        ),
        "event_properties": {
            "page": "/home"
        },
    "user_properties": {
        "customer_id": customer_id
    }
    })


# Events related to orders
for order in orders:

    customer_id = str(order["customer_id"])
    amplitude_user_id = f"customer_{int(customer_id):06d}"

    created_at = datetime.fromisoformat(order["created_at"])

    # order_started
    events.append({
        "user_id": amplitude_user_id,
        "event_type": "order_started",
        "time": int(created_at.timestamp() * 1000),
        "event_properties": {
            "order_id": order["order_id"],
            "document_type": order["document_type"],
            "price": order["price"]
        },
    "user_properties": {
        "customer_id": customer_id
    }
    })

    # Sometimes user completes the order
    if order["status"] == "completed":

        events.append({
            "user_id": amplitude_user_id,
            "event_type": "order_completed",
            "time": int(
                (
                    created_at + timedelta(hours=random.randint(1, 48))
                ).timestamp() * 1000
            ),
            "event_properties": {
                "order_id": order["order_id"],
                "document_type": order["document_type"],
                "price": order["price"]
            },
            "user_properties": {
                "customer_id": customer_id
            }
        })


print(f"Generated {len(events)} Amplitude events")


# ---------------------------------------------------------
# 3. Send events to Amplitude
# ---------------------------------------------------------

payload = {
    "api_key": AMPLITUDE_API_KEY,
    "events": events
}

response = requests.post(
    AMPLITUDE_URL,
    json=payload
)

print("Status code:", response.status_code)
print("Response:", response.text)
import os
import json
import stripe
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

OUTPUT_DIR = "data/raw/stripe"
STATE_DIR = "data/state"
STATE_FILE = os.path.join(STATE_DIR, "stripe_watermark.json")

def run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(STATE_DIR, exist_ok=True)


    def load_watermark(key):
        if not os.path.exists(STATE_FILE):
            return 0
        with open(STATE_FILE) as f:
            return json.load(f).get(key, 0)


    def save_watermark(key, value):
        data = {}
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE) as f:
                data = json.load(f)
        data[key] = value
        with open(STATE_FILE, "w") as f:
            json.dump(data, f)


    def extract_customers(since):
        customers = stripe.Customer.list(limit=100, created={"gt": since})
        return [c.to_dict() for c in customers.auto_paging_iter()]


    def extract_charges(since):
        charges = stripe.Charge.list(limit=100, created={"gt": since})
        return [c.to_dict() for c in charges.auto_paging_iter()]


    def save_json(data, filename):
        path = os.path.join(OUTPUT_DIR, filename)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"Saved {len(data)} records to {path}")



    run_stamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

    customers_watermark = load_watermark("customers_last_created")
    print(f"Extracting customers created after {customers_watermark}...")
    customers = extract_customers(customers_watermark)
    save_json(customers, f"customers_{run_stamp}.json")
    if customers:
        save_watermark("customers_last_created", max(c["created"] for c in customers))

    charges_watermark = load_watermark("charges_last_created")
    print(f"Extracting charges created after {charges_watermark}...")
    charges = extract_charges(charges_watermark)
    save_json(charges, f"charges_{run_stamp}.json")
    if charges:
        save_watermark("charges_last_created", max(c["created"] for c in charges))

    print("Done.")

if __name__ == "__main__":
    run()
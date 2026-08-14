import os
import gzip
import shutil
import zipfile
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

AMPLITUDE_API_KEY = os.getenv("AMPLITUDE_API_KEY")
AMPLITUDE_SECRET_KEY = os.getenv("AMPLITUDE_SECRET_KEY")

AMPLITUDE_EXPORT_URL = "https://amplitude.com/api/2/export"
RAW_DIR = "data/raw/amplitude"
STATE_DIR = "data/state"
STATE_FILE = os.path.join(STATE_DIR, "amplitude_watermark.json")

SAFETY_BUFFER_HOURS = 3
DEFAULT_START = "20260810T00"  # covers our earliest test data; a real project would use go-live date


def run():
    if not AMPLITUDE_API_KEY:
        raise ValueError("AMPLITUDE_API_KEY is not set in .env")
    if not AMPLITUDE_SECRET_KEY:
        raise ValueError("AMPLITUDE_SECRET_KEY is not set in .env")

    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(STATE_DIR, exist_ok=True)

    def load_watermark():
        if not os.path.exists(STATE_FILE):
            return DEFAULT_START
        with open(STATE_FILE) as f:
            return json.load(f).get("last_extracted_end", DEFAULT_START)

    def save_watermark(value):
        with open(STATE_FILE, "w") as f:
            json.dump({"last_extracted_end": value}, f)

    start = load_watermark()
    safe_now = datetime.now() - timedelta(hours=SAFETY_BUFFER_HOURS)
    end = safe_now.strftime("%Y%m%dT%H")

    if start >= end:
        print(f"Nothing new to extract yet (watermark {start} is already caught up to the safe window).")
        return

    print(f"Extracting Amplitude events from {start} to {end}...")

    response = requests.get(
        AMPLITUDE_EXPORT_URL,
        params={"start": start, "end": end},
        auth=(AMPLITUDE_API_KEY, AMPLITUDE_SECRET_KEY),
        timeout=60,
    )

    print("Status code:", response.status_code)

    if response.status_code == 200:
        run_stamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        zip_path = os.path.join(RAW_DIR, f"export_{run_stamp}.zip")
        extract_dir = os.path.join(RAW_DIR, run_stamp)

        with open(zip_path, "wb") as f:
            f.write(response.content)
        print("Saved zip to:", zip_path)

        with zipfile.ZipFile(zip_path) as z:
            z.extractall(extract_dir)
        print("Unzipped to:", extract_dir)

        for root, _, files in os.walk(extract_dir):
            for name in files:
                if name.endswith(".gz"):
                    gz_path = os.path.join(root, name)
                    json_path = gz_path[:-3]
                    with gzip.open(gz_path, "rb") as f_in, open(json_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                    os.remove(gz_path)
                    print("Unpacked:", json_path)

        save_watermark(end)
        print(f"Updated watermark to {end}")

    elif response.status_code == 404:
        print("No Amplitude data available for this time range.")
        save_watermark(end)
        print(f"Updated watermark to {end} anyway — this window has been checked, future runs will move forward")

    else:
        print("Amplitude export failed.")
        print("Response:", response.text)


if __name__ == "__main__":
    run()
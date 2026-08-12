import os
import requests
from dotenv import load_dotenv


# Load variables from .env
load_dotenv()

AMPLITUDE_API_KEY = os.getenv("AMPLITUDE_API_KEY")
AMPLITUDE_SECRET_KEY = os.getenv("AMPLITUDE_SECRET_KEY")

if not AMPLITUDE_API_KEY:
    raise ValueError("AMPLITUDE_API_KEY is not set in .env")

if not AMPLITUDE_SECRET_KEY:
    raise ValueError("AMPLITUDE_SECRET_KEY is not set in .env")


AMPLITUDE_EXPORT_URL = "https://amplitude.com/api/2/export"


# ---------------------------------------------------------
# Export time range
# ---------------------------------------------------------
# We will change these dates after checking when
# our events were uploaded to Amplitude.

START = "20260812T10"
END = "20260812T19"


# ---------------------------------------------------------
# Request data from Amplitude
# ---------------------------------------------------------

response = requests.get(
    AMPLITUDE_EXPORT_URL,
    params={
        "start": START,
        "end": END
    },
    auth=(AMPLITUDE_API_KEY, AMPLITUDE_SECRET_KEY),
    timeout=60
)


print("Status code:", response.status_code)
print("Content-Type:", response.headers.get("Content-Type"))
print("Response size:", len(response.content), "bytes")


if response.status_code == 200:

    output_path = "data/raw/amplitude_export.zip"

    os.makedirs("data/raw", exist_ok=True)

    with open(output_path, "wb") as file:
        file.write(response.content)

    print("Export saved to:", output_path)

elif response.status_code == 404:

    print("No Amplitude data available for this time range.")
    print("Remember: Export API can have up to a 2-hour delay.")

else:

    print("Amplitude export failed.")
    print("Response:", response.text)
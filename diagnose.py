import requests
import os
from datetime import datetime

key = os.environ["DATA_GOV_API_KEY"]
headers = {"User-Agent": "Mozilla/5.0 (compatible; mandi-prices-fetcher/1.0)"}
today = datetime.now().strftime("%d/%m/%Y")

r_no_filter = requests.get(
    "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24",
    params={"api-key": key, "format": "json", "limit": 3},
    headers=headers,
    timeout=30,
)
print("no date filter status:", r_no_filter.status_code)

for i in range(5):
    r = requests.get(
        "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24",
        params={
            "api-key": key,
            "format": "json",
            "limit": 1000,
            "offset": 0,
            "filters[Arrival_Date]": today,
        },
        headers=headers,
        timeout=30,
    )
    print(f"WITH date filter attempt {i+1} status:", r.status_code, r.text[:120] if r.status_code != 200 else "OK")

import requests
import os

key = os.environ["DATA_GOV_API_KEY"]
print("egress IP (python requests):", requests.get("https://api.ipify.org", timeout=15).text)

headers = {"User-Agent": "Mozilla/5.0 (compatible; mandi-prices-fetcher/1.0)"}
r1 = requests.get(
    "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24",
    params={"api-key": key, "format": "json", "limit": 3},
    headers=headers,
    timeout=30,
)
print("simple request (no date filter, custom UA) status:", r1.status_code)

r2 = requests.get(
    "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24",
    params={"api-key": key, "format": "json", "limit": 3},
    timeout=30,
)
print("simple request (no date filter, default UA) status:", r2.status_code)

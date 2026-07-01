"""
Fetches daily mandi (market) price data from data.gov.in's
"Variety-wise Daily Market Prices Data of Commodity" API,
and produces a compact JSON file for use on the Heranba website.

Logic:
1. Pull ALL records for today's arrival date (paginated, since the API
   caps results per request).
2. If today's data isn't published yet, fall back to yesterday.
3. Rank markets within each state by how many different commodity
   listings they have that day (a proxy for market size/importance).
4. Keep only the top 3 markets per state, but ALL commodities traded
   at those markets.
5. Write the result to mandi_prices.json.

Requires: pip install requests --break-system-packages
"""

import requests
import json
import os
from datetime import datetime, timedelta

# The API key can be hardcoded for local testing, but in production
# (GitHub Actions) it should come from an environment variable / secret
# instead — never commit a real key into a public repo.
API_KEY = os.environ.get(
    "DATA_GOV_API_KEY",
    "579b464db66ec23bdd000001ee428f4b1aed4e0e6afc0fd68fe44756",
)
RESOURCE_ID = "35985678-0d79-46b4-9ed6-6f13308a1d24"
BASE_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
PAGE_SIZE = 1000
TOP_MARKETS_PER_STATE = 3
# Some networks (corporate proxies/firewalls) throttle or hang requests sent
# with the default "python-requests/x.x" User-Agent. A normal-looking UA
# avoids that.
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; mandi-prices-fetcher/1.0)"}


def fetch_all_records_for_date(date_str, max_pages=100):
    """Fetch every record for a given Arrival_Date (DD/MM/YYYY), paginated."""
    records = []
    offset = 0
    for _ in range(max_pages):
        params = {
            "api-key": API_KEY,
            "format": "json",
            "limit": PAGE_SIZE,
            "offset": offset,
            "filters[Arrival_Date]": date_str,
        }
        resp = requests.get(BASE_URL, params=params, headers=REQUEST_HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("records", [])
        if not batch:
            break
        records.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return records


def get_latest_available_records(max_days_back=5):
    """Try today, then walk backwards until we find a day with data."""
    today = datetime.now()
    for days_back in range(max_days_back):
        d = today - timedelta(days=days_back)
        date_str = d.strftime("%d/%m/%Y")
        records = fetch_all_records_for_date(date_str)
        if records:
            return date_str, records
    return None, []


def build_dataset():
    date_str, records = get_latest_available_records()

    if not records:
        return {
            "last_updated": None,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "states": {},
            "note": "No data found in the last few days — check API status.",
        }

    # Count commodity listings per (state, market) to identify "major" markets
    market_counts = {}
    for r in records:
        state = (r.get("State") or "").strip()
        market = (r.get("Market") or "").strip()
        if not state or not market:
            continue
        key = (state, market)
        market_counts[key] = market_counts.get(key, 0) + 1

    state_markets = {}
    for (state, market), count in market_counts.items():
        state_markets.setdefault(state, []).append((market, count))

    top_markets = {}
    for state, markets in state_markets.items():
        markets.sort(key=lambda x: x[1], reverse=True)
        top_markets[state] = {m for m, _ in markets[:TOP_MARKETS_PER_STATE]}

    # Build final filtered output
    output = {}
    for r in records:
        state = (r.get("State") or "").strip()
        market = (r.get("Market") or "").strip()
        if state in top_markets and market in top_markets[state]:
            output.setdefault(state, {}).setdefault(market, []).append(
                {
                    "commodity": r.get("Commodity"),
                    "variety": r.get("Variety"),
                    "grade": r.get("Grade"),
                    "min_price": r.get("Min_Price"),
                    "max_price": r.get("Max_Price"),
                    "modal_price": r.get("Modal_Price"),
                }
            )

    return {
        "last_updated": date_str,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "states": output,
    }


if __name__ == "__main__":
    result = build_dataset()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mandi_prices.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    n_states = len(result.get("states", {}))
    print(f"Saved mandi_prices.json — {n_states} states, date: {result.get('last_updated')}")

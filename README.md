# Mandi Prices Automation — Setup Steps

## What this does
Every day, a script pulls the day's mandi prices from data.gov.in, keeps only
the top 3 markets per state (by number of commodities traded — a proxy for
market size), and saves it all as `mandi_prices.json`. Your website just
reads this JSON file — no live API calls from the browser, no exposed key.

## One-time setup

1. **Create a GitHub repo** (can be private) — e.g. `heranba-mandi-data`.
2. Add these two files to the repo root:
   - `fetch_mandi_prices.py`
   - `.github/workflows/mandi-prices-update.yml` (the workflow file — put
     it inside a `.github/workflows/` folder, GitHub requires that path)
3. **Add your API key as a secret** (don't paste it directly in code):
   - Repo → Settings → Secrets and variables → Actions → New repository secret
   - Name: `DATA_GOV_API_KEY`
   - Value: your data.gov.in key
4. Commit and push. Go to the **Actions** tab → run the workflow manually
   once (workflow_dispatch) to confirm it works and produces
   `mandi_prices.json` in the repo.
5. From then on, it runs automatically every day at 9 AM IST — free, via
   GitHub Actions' free tier.

## How your website reads the data

If the repo is public, the JSON is directly fetchable at:
```
https://raw.githubusercontent.com/YOUR_USERNAME/heranba-mandi-data/main/mandi_prices.json
```
Your site's frontend JS can just `fetch()` that URL and render it — no
backend needed on your end.

If you'd rather not have even the repo public, host the JSON instead via
GitHub Pages (still free) with the repo set to private + Pages enabled on a
separate public branch — happy to walk through that if needed.

## Output shape (mandi_prices.json)

```json
{
  "last_updated": "01/07/2026",
  "generated_at": "2026-07-01T03:30:12Z",
  "states": {
    "Uttar Pradesh": {
      "Lucknow": [
        {
          "commodity": "Wheat",
          "variety": "PBW-343",
          "grade": "FAQ",
          "min_price": "2100",
          "max_price": "2250",
          "modal_price": "2180"
        }
      ]
    }
  }
}
```

## Note on testing
I wasn't able to test-run this script directly from my end — my sandbox's
network access doesn't include api.data.gov.in. Run it locally once first
(`python fetch_mandi_prices.py` after `pip install requests`) to confirm it
works with your key before wiring up GitHub Actions.

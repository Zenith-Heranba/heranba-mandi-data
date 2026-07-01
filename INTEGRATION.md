# Integration Guide — Mandi Prices for heranba.vercel.app

This repo publishes daily mandi (market) price data as a single JSON file, auto-updated
every day around 9:05 AM IST. This doc is everything the site/agency needs to consume it.

## Data source URL

```
https://raw.githubusercontent.com/Zenith-Heranba/heranba-mandi-data/master/mandi_prices.json
```

- Public, no authentication or API key needed.
- CORS is open (`Access-Control-Allow-Origin: *`), so it can be fetched directly from
  client-side JS in the browser — no backend proxy required.
- CDN-cached for ~5 minutes (`Cache-Control: max-age=300`), which is fine since the
  underlying data itself only changes once a day.

## JSON shape

```json
{
  "last_updated": "01/07/2026",
  "generated_at": "2026-07-01T07:17:10.123456Z",
  "states": {
    "Keralam": {
      "Pampady Market": [
        {
          "commodity": "Ashgourd",
          "variety": "Ashgourd",
          "grade": "FAQ",
          "min_price": "2500",
          "max_price": "4000",
          "modal_price": "3500"
        }
      ]
    }
  }
}
```

- `last_updated`: the mandi arrival date the prices are for, as `DD/MM/YYYY`. Show this
  to users ("Prices as of ...") since it may occasionally lag by a day if the source
  data wasn't published yet, or if the update job didn't run that day (see Reliability
  note below).
- `generated_at`: ISO 8601 UTC timestamp of when this file was actually generated.
- `states`: keyed by state name → market name → array of commodity price rows.
  Only the top 3 markets per state (by number of commodities traded) are included, to
  keep the payload small — not every market in India.
- Prices (`min_price`/`max_price`/`modal_price`) are numbers or numeric strings in ₹
  per quintal, as published by the source.
- If no data was available at all in the last few days, the JSON instead looks like:
  ```json
  { "last_updated": null, "generated_at": "...", "states": {}, "note": "No data found in the last few days — check API status." }
  ```
  Handle `states` being `{}` gracefully (e.g. show a "prices unavailable" message).

## Example fetch (client-side, works in any React/Next.js component)

```javascript
async function getMandiPrices() {
  const res = await fetch(
    "https://raw.githubusercontent.com/Zenith-Heranba/heranba-mandi-data/master/mandi_prices.json"
  );
  if (!res.ok) throw new Error("Failed to load mandi prices");
  return res.json();
}

// Usage in a component:
// const data = await getMandiPrices();
// data.last_updated -> "01/07/2026"
// Object.entries(data.states) -> [["Keralam", { "Pampady Market": [...] }], ...]
```

## Example: Next.js Server Component with revalidation

If the site is Next.js (App Router) and prefers server-side fetching with ISR-style
caching instead of a client fetch:

```javascript
export default async function MandiPricesSection() {
  const res = await fetch(
    "https://raw.githubusercontent.com/Zenith-Heranba/heranba-mandi-data/master/mandi_prices.json",
    { next: { revalidate: 3600 } } // re-check hourly; source only changes daily
  );
  const data = await res.json();

  return (
    <div>
      <p>Prices as of {data.last_updated}</p>
      {Object.entries(data.states).map(([state, markets]) => (
        <div key={state}>
          <h3>{state}</h3>
          {Object.entries(markets).map(([market, rows]) => (
            <div key={market}>
              <h4>{market}</h4>
              <table>
                <thead>
                  <tr><th>Commodity</th><th>Variety</th><th>Min</th><th>Max</th><th>Modal</th></tr>
                </thead>
                <tbody>
                  {rows.map((r, i) => (
                    <tr key={i}>
                      <td>{r.commodity}</td>
                      <td>{r.variety}</td>
                      <td>{r.min_price}</td>
                      <td>{r.max_price}</td>
                      <td>{r.modal_price}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
```

## Reliability note (important for the agency to design around)

The update job currently runs on a self-hosted machine (not GitHub's cloud), because
data.gov.in blocks requests from GitHub-hosted cloud IPs. This means:

- The JSON updates automatically every day around 9:05 AM IST **only while that
  machine is on and a specific runner session is active**. If it's off or logged out
  that day, the file simply keeps yesterday's (or the last available) data.
- The site should always display the `last_updated` date so users can see how fresh
  the data is, rather than assuming it's always today's prices.
- Worst case if updates ever stop entirely: the JSON file just stops changing — the
  site won't error, it'll keep showing the last successful update.

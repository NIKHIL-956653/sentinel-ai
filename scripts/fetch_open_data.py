"""
Fetch openly licensed military statistics from the World Bank API and write
data/military_open_data.json with full provenance.

Indicators (World Bank, source: SIPRI / IISS, licence CC BY 4.0):
  MS.MIL.XPND.CD     Military expenditure (current US$)
  MS.MIL.XPND.GD.ZS  Military expenditure (% of GDP)
  MS.MIL.TOTL.P1     Armed forces personnel, total

Run once (needs internet), commit the JSON, re-run yearly:
  python scripts/fetch_open_data.py
"""
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

API = "https://api.worldbank.org/v2"
INDICATORS = {
    "MS.MIL.XPND.CD": "expenditure_usd",
    "MS.MIL.XPND.GD.ZS": "expenditure_gdp_pct",
    "MS.MIL.TOTL.P1": "personnel_total",
}
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "military_open_data.json")


def get_json(url, params):
    for attempt in range(3):
        r = requests.get(url, params={"format": "json", "per_page": 20000, **params}, timeout=60)
        if r.status_code == 200:
            return r.json()
        time.sleep(2 * (attempt + 1))
    r.raise_for_status()


def real_countries():
    """ISO3 → name for actual countries (World Bank also returns regional aggregates)."""
    data = get_json(f"{API}/country", {})
    out = {}
    for c in data[1]:
        if c.get("region", {}).get("value") != "Aggregates" and c.get("iso2Code") and len(c["id"]) == 3:
            out[c["id"]] = c["name"]
    return out


def main():
    print("Fetching country list…")
    countries = real_countries()
    print(f"  {len(countries)} countries")

    table = {iso3: {"name": name} for iso3, name in countries.items()}
    for code, key in INDICATORS.items():
        print(f"Fetching {code} ({key})…")
        # mrnev=1 → most recent non-empty value per country
        data = get_json(f"{API}/country/all/indicator/{code}", {"mrnev": 1})
        rows = data[1] if len(data) > 1 and data[1] else []
        n = 0
        for row in rows:
            iso3 = row.get("countryiso3code")
            if iso3 in table and row.get("value") is not None:
                table[iso3][key] = {"value": row["value"], "year": int(row["date"])}
                n += 1
        print(f"  {n} values")

    # Rank by most recent expenditure (transparent, reproducible — unlike proprietary power indexes)
    ranked = sorted((iso3 for iso3 in table if "expenditure_usd" in table[iso3]),
                    key=lambda i: table[i]["expenditure_usd"]["value"], reverse=True)
    for pos, iso3 in enumerate(ranked, 1):
        table[iso3]["rank_by_expenditure"] = pos

    payload = {
        "_source": "World Bank Open Data (indicators sourced from SIPRI Military Expenditure Database and IISS Military Balance)",
        "_license": "CC BY 4.0 — https://datacatalog.worldbank.org/public-licenses",
        "_indicators": INDICATORS,
        "_fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "_ranking": "rank_by_expenditure = position by most recent military expenditure (current US$) among countries with data",
        "countries": table,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)
    print(f"✅ wrote {OUT} ({len(ranked)} countries ranked)")


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as e:
        print(f"❌ network error: {e}")
        sys.exit(1)

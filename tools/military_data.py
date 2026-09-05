"""
Open military statistics (World Bank / SIPRI / IISS) loaded from data/military_open_data.json.
Replaces the GlobalFirepower HTML scrape (fragile selectors, ToS risk, opaque "power index").

If the file is missing, every lookup returns None and the caller labels fields honestly —
run `python scripts/fetch_open_data.py` once to create it.
"""
import json
import os
from functools import lru_cache

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "data", "military_open_data.json")

# Frontend / user country names → ISO3. World Bank uses formal names ("Iran, Islamic Rep."),
# so we key everything by ISO3 and never string-match names.
ISO3 = {
    "afghanistan": "AFG", "albania": "ALB", "algeria": "DZA", "andorra": "AND", "angola": "AGO",
    "argentina": "ARG", "armenia": "ARM", "australia": "AUS", "austria": "AUT", "azerbaijan": "AZE",
    "bahrain": "BHR", "bangladesh": "BGD", "belarus": "BLR", "belgium": "BEL", "bolivia": "BOL",
    "bosnia and herzegovina": "BIH", "brazil": "BRA", "bulgaria": "BGR", "cambodia": "KHM",
    "cameroon": "CMR", "canada": "CAN", "chile": "CHL", "china": "CHN", "colombia": "COL",
    "croatia": "HRV", "cuba": "CUB", "czech republic": "CZE", "czechia": "CZE", "denmark": "DNK",
    "ecuador": "ECU", "egypt": "EGY", "ethiopia": "ETH", "finland": "FIN", "france": "FRA",
    "georgia": "GEO", "germany": "DEU", "ghana": "GHA", "greece": "GRC", "hungary": "HUN",
    "india": "IND", "indonesia": "IDN", "iran": "IRN", "iraq": "IRQ", "ireland": "IRL",
    "israel": "ISR", "italy": "ITA", "japan": "JPN", "jordan": "JOR", "kazakhstan": "KAZ",
    "kenya": "KEN", "kuwait": "KWT", "kyrgyzstan": "KGZ", "lebanon": "LBN", "libya": "LBY",
    "lithuania": "LTU", "malaysia": "MYS", "mexico": "MEX", "morocco": "MAR", "myanmar": "MMR",
    "netherlands": "NLD", "new zealand": "NZL", "nigeria": "NGA", "north korea": "PRK",
    "norway": "NOR", "oman": "OMN", "pakistan": "PAK", "peru": "PER", "philippines": "PHL",
    "poland": "POL", "portugal": "PRT", "qatar": "QAT", "romania": "ROU", "russia": "RUS",
    "russian federation": "RUS", "saudi arabia": "SAU", "serbia": "SRB", "singapore": "SGP",
    "south africa": "ZAF", "south korea": "KOR", "spain": "ESP", "sri lanka": "LKA", "sudan": "SDN",
    "sweden": "SWE", "switzerland": "CHE", "syria": "SYR", "taiwan": "TWN", "tajikistan": "TJK",
    "thailand": "THA", "tunisia": "TUN", "turkey": "TUR", "turkiye": "TUR", "turkmenistan": "TKM",
    "uae": "ARE", "united arab emirates": "ARE", "uganda": "UGA", "ukraine": "UKR",
    "united kingdom": "GBR", "uk": "GBR", "united states": "USA", "usa": "USA", "us": "USA",
    "uzbekistan": "UZB", "venezuela": "VEN", "vietnam": "VNM", "yemen": "YEM", "zimbabwe": "ZWE",
    "estonia": "EST", "latvia": "LVA", "slovakia": "SVK", "slovenia": "SVN", "luxembourg": "LUX",
    "iceland": "ISL", "cyprus": "CYP", "malta": "MLT", "moldova": "MDA", "montenegro": "MNE",
    "north macedonia": "MKD", "mongolia": "MNG", "nepal": "NPL", "laos": "LAO", "brunei": "BRN",
    "papua new guinea": "PNG", "fiji": "FJI", "mali": "MLI", "niger": "NER", "chad": "TCD",
    "senegal": "SEN", "ivory coast": "CIV", "cote d'ivoire": "CIV", "tanzania": "TZA",
    "mozambique": "MOZ", "zambia": "ZMB", "botswana": "BWA", "namibia": "NAM", "rwanda": "RWA",
    "somalia": "SOM", "eritrea": "ERI", "djibouti": "DJI", "mauritania": "MRT", "guatemala": "GTM",
    "honduras": "HND", "el salvador": "SLV", "nicaragua": "NIC", "costa rica": "CRI", "panama": "PAN",
    "dominican republic": "DOM", "haiti": "HTI", "jamaica": "JAM", "uruguay": "URY", "paraguay": "PRY",
}


def iso3_for(country: str):
    return ISO3.get((country or "").strip().lower())


@lru_cache(maxsize=1)
def _load():
    if not os.path.exists(DATA_PATH):
        return None
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def available() -> bool:
    return _load() is not None


def provenance() -> dict:
    d = _load()
    if not d:
        return {"source": "not fetched — run scripts/fetch_open_data.py", "fetched_at": None}
    return {"source": d.get("_source"), "license": d.get("_license"), "fetched_at": d.get("_fetched_at"),
            "ranking": d.get("_ranking")}


def fmt_usd(v: float) -> str:
    if v >= 1e12:
        return f"${v/1e12:.2f}T"
    if v >= 1e9:
        return f"${v/1e9:.1f}B"
    if v >= 1e6:
        return f"${v/1e6:.0f}M"
    return f"${v:,.0f}"


def get_stats(country: str):
    """
    Returns a dict of display-ready fields for the dossier, or None when the dataset
    is missing or the country is unknown. Every number carries its year.
    """
    d = _load()
    iso3 = iso3_for(country)
    if not d or not iso3:
        return None
    row = d["countries"].get(iso3)
    if not row:
        return None
    out = {"iso3": iso3, "wb_name": row.get("name")}
    if "expenditure_usd" in row:
        e = row["expenditure_usd"]
        out["defense_budget"] = f"{fmt_usd(e['value'])} ({e['year']})"
        out["defense_budget_usd"] = e["value"]
        out["defense_budget_year"] = e["year"]
    if "expenditure_gdp_pct" in row:
        g = row["expenditure_gdp_pct"]
        out["defense_budget_gdp_pct"] = f"{g['value']:.1f}% of GDP ({g['year']})"
    if "personnel_total" in row:
        p = row["personnel_total"]
        out["active_personnel"] = f"{int(p['value']):,} ({p['year']})"
        out["active_personnel_count"] = int(p["value"])
    if "rank_by_expenditure" in row:
        out["global_rank"] = row["rank_by_expenditure"]
        out["global_rank_basis"] = "military expenditure (World Bank/SIPRI)"
    return out

"""
Geotag stories for the live threat map.

One LLM call per search: the model reads every headline and returns, for each story it can place,
the country the event is about — restricted to names in COUNTRY_COORDS so the result is always
plottable. Fail-soft: any error → no geo on stories, map shows nothing extra.
"""
from tools.llm import chat_json, LLMError, untrusted, UNTRUSTED_NOTE

# Approximate geographic centroids (degrees). Good enough to place a marker on a world map.
COUNTRY_COORDS = {
    "Afghanistan": (33.9, 67.7), "Albania": (41.2, 20.2), "Algeria": (28.0, 1.7), "Angola": (-11.2, 17.9),
    "Argentina": (-38.4, -63.6), "Armenia": (40.1, 45.0), "Australia": (-25.3, 133.8), "Austria": (47.5, 14.6),
    "Azerbaijan": (40.1, 47.6), "Bahrain": (26.0, 50.6), "Bangladesh": (23.7, 90.4), "Belarus": (53.7, 27.9),
    "Belgium": (50.5, 4.5), "Bolivia": (-16.3, -63.6), "Bosnia and Herzegovina": (43.9, 17.7), "Brazil": (-14.2, -51.9),
    "Bulgaria": (42.7, 25.5), "Cambodia": (12.6, 105.0), "Cameroon": (7.4, 12.4), "Canada": (56.1, -106.3),
    "Chad": (15.5, 18.7), "Chile": (-35.7, -71.5), "China": (35.9, 104.2), "Colombia": (4.6, -74.3),
    "Croatia": (45.1, 15.2), "Cuba": (21.5, -77.8), "Cyprus": (35.1, 33.4), "Czech Republic": (49.8, 15.5),
    "Denmark": (56.3, 9.5), "Djibouti": (11.8, 42.6), "Ecuador": (-1.8, -78.2), "Egypt": (26.8, 30.8),
    "Eritrea": (15.2, 39.8), "Estonia": (58.6, 25.0), "Ethiopia": (9.1, 40.5), "Finland": (61.9, 25.7),
    "France": (46.2, 2.2), "Georgia": (42.3, 43.4), "Germany": (51.2, 10.5), "Ghana": (7.9, -1.0),
    "Greece": (39.1, 21.8), "Haiti": (18.97, -72.3), "Hungary": (47.2, 19.5), "India": (20.6, 79.0),
    "Indonesia": (-0.8, 113.9), "Iran": (32.4, 53.7), "Iraq": (33.2, 43.7), "Ireland": (53.1, -8.2),
    "Israel": (31.0, 34.9), "Italy": (41.9, 12.6), "Japan": (36.2, 138.3), "Jordan": (30.6, 36.2),
    "Kazakhstan": (48.0, 66.9), "Kenya": (-0.02, 37.9), "Kuwait": (29.3, 47.5), "Kyrgyzstan": (41.2, 74.8),
    "Latvia": (56.9, 24.6), "Lebanon": (33.9, 35.9), "Libya": (26.3, 17.2), "Lithuania": (55.2, 23.9),
    "Malaysia": (4.2, 101.9), "Mali": (17.6, -4.0), "Mexico": (23.6, -102.5), "Moldova": (47.4, 28.4),
    "Mongolia": (46.9, 103.8), "Morocco": (31.8, -7.1), "Mozambique": (-18.7, 35.5), "Myanmar": (21.9, 95.9),
    "Nepal": (28.4, 84.1), "Netherlands": (52.1, 5.3), "New Zealand": (-40.9, 174.9), "Niger": (17.6, 8.1),
    "Nigeria": (9.1, 8.7), "North Korea": (40.3, 127.5), "Norway": (60.5, 8.5), "Oman": (21.5, 55.9),
    "Pakistan": (30.4, 69.3), "Palestine": (31.9, 35.2), "Panama": (8.5, -80.8), "Peru": (-9.2, -75.0),
    "Philippines": (12.9, 121.8), "Poland": (51.9, 19.1), "Portugal": (39.4, -8.2), "Qatar": (25.4, 51.2),
    "Romania": (45.9, 25.0), "Russia": (61.5, 105.3), "Saudi Arabia": (23.9, 45.1), "Senegal": (14.5, -14.5),
    "Serbia": (44.0, 21.0), "Singapore": (1.35, 103.8), "Slovakia": (48.7, 19.7), "Somalia": (5.2, 46.2),
    "South Africa": (-30.6, 22.9), "South Korea": (35.9, 127.8), "Spain": (40.5, -3.7), "Sri Lanka": (7.9, 80.8),
    "Sudan": (12.9, 30.2), "Sweden": (60.1, 18.6), "Switzerland": (46.8, 8.2), "Syria": (34.8, 39.0),
    "Taiwan": (23.7, 121.0), "Tajikistan": (38.9, 71.3), "Tanzania": (-6.4, 34.9), "Thailand": (15.9, 100.99),
    "Tunisia": (33.9, 9.5), "Turkey": (39.0, 35.2), "Turkmenistan": (38.97, 59.6), "UAE": (23.4, 53.8),
    "Uganda": (1.4, 32.3), "Ukraine": (48.4, 31.2), "United Kingdom": (55.4, -3.4), "United States": (37.1, -95.7),
    "Uzbekistan": (41.4, 64.6), "Venezuela": (6.4, -66.6), "Vietnam": (14.1, 108.3), "Yemen": (15.6, 48.5),
    "Zimbabwe": (-19.0, 29.2),
    # bodies of water / regions that stories are often "about"
    "Red Sea": (20.0, 38.5), "Strait of Hormuz": (26.6, 56.3), "South China Sea": (12.0, 114.0),
    "Black Sea": (43.4, 34.3), "Baltic Sea": (58.0, 20.0), "Taiwan Strait": (24.5, 119.5),
    "Persian Gulf": (26.5, 51.5), "Mediterranean Sea": (35.0, 18.0), "Arctic": (80.0, 0.0),
}

# Cities / hotspots that headlines name directly. Precision "city" beats the country centroid.
CITY_COORDS = {
    "Kyiv": (50.45, 30.52), "Kharkiv": (49.99, 36.23), "Odesa": (46.48, 30.73), "Odessa": (46.48, 30.73),
    "Donetsk": (48.02, 37.80), "Zaporizhzhia": (47.84, 35.14), "Kherson": (46.64, 32.62), "Lviv": (49.84, 24.03),
    "Moscow": (55.76, 37.62), "Sevastopol": (44.62, 33.52), "Belgorod": (50.60, 36.59), "Kursk": (51.73, 36.19),
    "Gaza City": (31.50, 34.47), "Rafah": (31.29, 34.25), "Khan Younis": (31.34, 34.31), "Tel Aviv": (32.08, 34.78),
    "Jerusalem": (31.77, 35.21), "Haifa": (32.79, 34.99), "Beirut": (33.89, 35.50), "Tyre": (33.27, 35.20),
    "Damascus": (33.51, 36.29), "Aleppo": (36.20, 37.16), "Idlib": (35.93, 36.63), "Baghdad": (33.34, 44.40),
    "Mosul": (36.34, 43.13), "Erbil": (36.19, 44.01), "Tehran": (35.69, 51.39), "Isfahan": (32.65, 51.68),
    "Natanz": (33.51, 51.92), "Bandar Abbas": (27.18, 56.27), "Sanaa": (15.37, 44.19), "Aden": (12.79, 45.02),
    "Hodeidah": (14.80, 42.95), "Riyadh": (24.71, 46.68), "Abu Dhabi": (24.45, 54.38), "Dubai": (25.20, 55.27),
    "Doha": (25.29, 51.53), "Kabul": (34.56, 69.21), "Islamabad": (33.69, 73.04), "Karachi": (24.86, 67.01),
    "Lahore": (31.55, 74.34), "New Delhi": (28.61, 77.21), "Srinagar": (34.08, 74.80), "Mumbai": (19.08, 72.88),
    "Beijing": (39.90, 116.40), "Shanghai": (31.23, 121.47), "Taipei": (25.03, 121.57), "Hong Kong": (22.32, 114.17),
    "Pyongyang": (39.02, 125.75), "Seoul": (37.57, 126.98), "Tokyo": (35.68, 139.69), "Okinawa": (26.33, 127.80),
    "Manila": (14.60, 120.98), "Hanoi": (21.03, 105.85), "Khartoum": (15.50, 32.56), "Port Sudan": (19.62, 37.22),
    "Tripoli": (32.90, 13.18), "Benghazi": (32.12, 20.07), "Mogadishu": (2.05, 45.32), "Nairobi": (-1.29, 36.82),
    "Addis Ababa": (9.02, 38.75), "Niamey": (13.51, 2.11), "Bamako": (12.64, -8.00), "Ouagadougou": (12.37, -1.52),
    "Goma": (-1.68, 29.22), "Kinshasa": (-4.32, 15.31), "Caracas": (10.48, -66.90), "Bogotá": (4.71, -74.07),
    "Bogota": (4.71, -74.07), "Mexico City": (19.43, -99.13), "Port-au-Prince": (18.59, -72.31), "Havana": (23.11, -82.37),
    "Washington": (38.91, -77.04), "Washington, D.C.": (38.91, -77.04), "New York": (40.71, -74.01), "London": (51.51, -0.13),
    "Paris": (48.86, 2.35), "Berlin": (52.52, 13.41), "Brussels": (50.85, 4.35), "Warsaw": (52.23, 21.01),
    "Vilnius": (54.69, 25.28), "Kaliningrad": (54.71, 20.51), "Minsk": (53.90, 27.57), "Ankara": (39.93, 32.86),
    "Istanbul": (41.01, 28.98), "Athens": (37.98, 23.73), "Nicosia": (35.19, 33.38), "Belgrade": (44.79, 20.45),
    "Pristina": (42.66, 21.17), "Chisinau": (47.01, 28.86), "Tbilisi": (41.72, 44.79), "Yerevan": (40.18, 44.51),
    "Baku": (40.41, 49.87), "Stepanakert": (39.82, 46.75), "Tashkent": (41.30, 69.24), "Astana": (51.17, 71.43),
    "Naypyidaw": (19.76, 96.08), "Yangon": (16.87, 96.20), "Dhaka": (23.81, 90.41), "Colombo": (6.93, 79.85),
    "Canberra": (-35.28, 149.13), "Darwin": (-12.46, 130.84), "Guam": (13.44, 144.79), "Diego Garcia": (-7.31, 72.41),
    "Djibouti City": (11.59, 43.15), "Suez": (29.97, 32.55), "Cairo": (30.04, 31.24),
}
_CITY_LOWER = {k.lower(): k for k in CITY_COORDS}

ALIASES = {
    "usa": "United States", "us": "United States", "u.s.": "United States", "america": "United States",
    "uk": "United Kingdom", "britain": "United Kingdom", "united arab emirates": "UAE",
    "russian federation": "Russia", "gaza": "Palestine", "west bank": "Palestine", "czechia": "Czech Republic",
    "türkiye": "Turkey", "turkiye": "Turkey", "korea": "South Korea", "dprk": "North Korea",
    "hormuz": "Strait of Hormuz", "gulf": "Persian Gulf",
}

_LOWER = {k.lower(): k for k in COUNTRY_COORDS}


def normalise(name: str):
    if not isinstance(name, str):
        return None
    n = name.strip()
    if not n:
        return None
    key = _LOWER.get(n.lower()) or _LOWER.get(ALIASES.get(n.lower(), "").lower())
    return key


def geo_for(name: str, place: str | None = None):
    """Country centroid, or the named city's coordinates when we know it (precision: city)."""
    key = normalise(name)
    if not key:
        return None
    lat, lng = COUNTRY_COORDS[key]
    geo = {"country": key, "lat": lat, "lng": lng, "precision": "country", "place": None}
    if isinstance(place, str) and place.strip():
        city = _CITY_LOWER.get(place.strip().lower())
        if city:
            geo.update(lat=CITY_COORDS[city][0], lng=CITY_COORDS[city][1], precision="city", place=city)
    return geo


def parse_geotags(raw, n_stories: int) -> dict:
    """{story_index: geo} from the model's [{"i":..,"country":..}] list; ignores junk."""
    out = {}
    if not isinstance(raw, list):
        return out
    for item in raw:
        try:
            i = int(item["i"])
        except (KeyError, TypeError, ValueError):
            continue
        if not (0 <= i < n_stories) or i in out:
            continue
        geo = geo_for(item.get("country"), item.get("place"))
        if geo:
            out[i] = geo
    return out


def geotag_stories(stories: list) -> list:
    """Attach story['geo'] (or None). Never raises."""
    for s in stories:
        s.setdefault("geo", None)
    if not stories:
        return stories
    lines = [f"[{i}] {untrusted(s['titles'][0], 200)}" for i, s in enumerate(stories) if s.get("titles")]
    prompt = f"""For each news headline below, name the ONE country or region the event is primarily
located in. {UNTRUSTED_NOTE} Use ONLY names from this list (exact spelling): {", ".join(COUNTRY_COORDS.keys())}.
If the headline names a specific city or town, add it as "place" (most common English name); otherwise omit "place".
Skip a headline if the location is unclear or global.

Headlines:
{chr(10).join(lines)}

Return ONLY a JSON array: [{{"i": <index>, "country": "<name from list>", "place": "<city or omit>"}}]"""
    try:
        tags = parse_geotags(chat_json(prompt, max_tokens=500), len(stories))
        for i, geo in tags.items():
            stories[i]["geo"] = geo
        cities = sum(1 for g in tags.values() if g.get("precision") == "city")
        print(f"🗺️  geotagged {len(tags)}/{len(stories)} stories ({cities} at city precision)")
    except LLMError as e:
        print(f"⚠️ geotag skipped: {e}")
    return stories

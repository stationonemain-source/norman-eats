"""Addresses -> coordinates with the US Census Bureau batch geocoder (public domain, no key), cached in
data/work/geocode_cache.json so a rebuild costs nothing. Falls back to nothing: a place with no match gets no map."""
import csv, io, json, os, time
import requests

CACHE = os.path.join(os.path.dirname(__file__), "..", "data", "work", "geocode_cache.json")
URL = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"
UA = "norman-eats-directory-build/0.1 (Station; stationonemain@gmail.com)"


def _load():
    try:
        return json.load(open(CACHE, encoding="utf-8"))
    except Exception:
        return {}


def _save(c):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(c, open(CACHE, "w", encoding="utf-8"), indent=0, sort_keys=True)


def geocode_many(addresses):
    """addresses: list of (key, street, city, state, zip). Returns {key: {lat, lon, matched, quality}}."""
    cache = _load()
    todo = [a for a in addresses if a[0] not in cache]
    for i in range(0, len(todo), 500):
        chunk = todo[i:i + 500]
        buf = io.StringIO()
        w = csv.writer(buf)
        for key, street, city, state, zip5 in chunk:
            w.writerow([key, street, city, state, zip5])
        files = {"addressFile": ("addresses.csv", buf.getvalue().encode("utf-8"), "text/csv")}
        for attempt in range(3):
            try:
                r = requests.post(URL, files=files, data={"benchmark": "Public_AR_Current"},
                                  headers={"User-Agent": UA}, timeout=300)
                if r.status_code == 200:
                    break
                print("census geocoder", r.status_code, r.text[:200])
            except Exception as e:
                print("census geocoder", type(e).__name__, str(e)[:120])
            time.sleep(10 * (attempt + 1))
        else:
            return {k: cache.get(k) for k, *_ in addresses}
        for row in csv.reader(io.StringIO(r.text)):
            if not row:
                continue
            key = row[0]
            rec = {"matched": row[2] == "Match", "quality": row[3] if len(row) > 3 else "", "lat": None, "lon": None,
                   "matched_address": row[4] if len(row) > 4 else ""}
            if rec["matched"] and len(row) > 5 and "," in row[5]:
                lon, lat = row[5].split(",")
                rec["lat"], rec["lon"] = round(float(lat), 6), round(float(lon), 6)
            cache[key] = rec
        _save(cache)
    # second chance for the few the Census file does not match: OpenStreetMap's Nominatim, one request a second,
    # accepted only when the hit is inside Norman (usage policy: light use, identified User-Agent, cached)
    for key, street, city, state, zip5 in addresses:
        rec = cache.get(key) or {}
        if rec.get("matched") or rec.get("nominatim_tried"):
            continue
        rec["nominatim_tried"] = True
        q = f"{street}, {city}, {state} {zip5}".strip()
        try:
            time.sleep(1.1)
            r = requests.get("https://nominatim.openstreetmap.org/search",
                             params={"q": q, "format": "jsonv2", "limit": 1, "countrycodes": "us", "addressdetails": 1},
                             headers={"User-Agent": UA}, timeout=60)
            hits = r.json() if r.status_code == 200 else []
            if hits:
                h = hits[0]
                a = h.get("address", {})
                town = (a.get("city") or a.get("town") or a.get("village") or "").lower()
                if "norman" in town or "norman" in h.get("display_name", "").lower():
                    rec.update({"matched": True, "quality": "nominatim:" + h.get("type", ""), "lat": round(float(h["lat"]), 6),
                                "lon": round(float(h["lon"]), 6), "matched_address": h.get("display_name", "")[:160]})
        except Exception as ex:
            print("nominatim", type(ex).__name__, str(ex)[:100])
        cache[key] = rec
        _save(cache)
    return {k: cache.get(k) for k, *_ in addresses}

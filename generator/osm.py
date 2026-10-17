"""OpenStreetMap places in Norman (data/raw/osm_pois.json, Overpass 'out center meta'). ODbL: attribute OpenStreetMap contributors.
Only tags a directory can honestly show: name, cuisine, opening_hours, website, phone, address, position, last-edit timestamp."""
import json, os, re
from textnorm import street_key
RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "osm_pois.json")
KIND = {"restaurant": "restaurant", "fast_food": "fast_food", "cafe": "cafe", "bar": "bar", "pub": "pub", "biergarten": "bar",
        "nightclub": "nightclub", "ice_cream": "ice_cream", "food_court": "restaurant", "bakery": "bakery", "deli": "deli",
        "coffee": "cafe", "alcohol": "liquor_store", "wine": "wine_shop", "beverages": "shop", "tea": "cafe",
        "brewery": "brewery", "distillery": "distillery", "winery": "winery"}
def load():
    d = json.load(open(RAW, encoding="utf-8"))
    out = []
    for e in d["elements"]:
        t = e.get("tags", {})
        if not t.get("name"): continue
        lat, lon = (e.get("lat"), e.get("lon")) if e["type"] == "node" else (e.get("center", {}).get("lat"), e.get("center", {}).get("lon"))
        kind = KIND.get(t.get("amenity") or t.get("shop") or t.get("craft") or ("brewery" if t.get("microbrewery") == "yes" else ""), "")
        if t.get("microbrewery") == "yes" and kind in ("", "bar", "pub", "restaurant"): kind = "brewery"
        street = " ".join(x for x in (t.get("addr:housenumber", ""), t.get("addr:street", "")) if x).strip()
        num, core = street_key(street) if street else ("", "")
        out.append({
            "osm_id": f"{e['type']}/{e['id']}", "osm_url": f"https://www.openstreetmap.org/{e['type']}/{e['id']}",
            "name": t["name"], "kind": kind, "cuisine": t.get("cuisine", ""), "opening_hours": t.get("opening_hours", ""),
            "website": t.get("website") or t.get("contact:website", ""), "phone": t.get("phone") or t.get("contact:phone", ""),
            "street": street, "unit": t.get("addr:unit", ""), "zip": t.get("addr:postcode", ""), "street_key": (num, core),
            "lat": lat, "lon": lon, "brand": t.get("brand", ""), "timestamp": e.get("timestamp", ""),
            "check_date": t.get("check_date") or t.get("survey:date") or "", "takeaway": t.get("takeaway", ""),
            "outdoor_seating": t.get("outdoor_seating", ""), "wheelchair": t.get("wheelchair", ""), "diet_vegetarian": t.get("diet:vegetarian", ""),
            "disused": any(k.startswith("disused:") or k.startswith("was:") for k in t), "tags": t,
        })
    return out, d.get("osm3s", {}).get("timestamp_osm_base", "")
if __name__ == "__main__":
    pois, ts = load(); print(len(pois), "named OSM places; data as of", ts)
    import collections; print(collections.Counter(p["kind"] for p in pois).most_common())
    print(sum(1 for p in pois if p["street_key"][0]), "with a house number")

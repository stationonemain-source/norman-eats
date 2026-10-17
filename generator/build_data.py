"""Pipeline: licences -> places, + health inspections, + OpenStreetMap, + coordinates -> data/work/places.json.
Run with -v to print the join report. Everything it writes is derived from data/raw and is safe to delete."""
import json, os, re, sys, datetime, collections
import able, places as P, osm as OSM, osdh as OSDH, geocode, classify
from match import match_osm, match_osdh
from textnorm import street_key, title_name, name_key, simplify_name

WORK = os.path.join(os.path.dirname(__file__), "..", "data", "work")
TODAY = datetime.date.today()
FRESH_INSPECTION_DAYS = 480   # ~16 months: the longest routine interval the source shows for low-risk kitchens, plus slack



def fmt_street(s):
    s = title_name(s) if s.upper() == s else s
    s = re.sub(r"\b(Nw|Ne|Sw|Se)\b", lambda m: m.group(1).upper(), s)
    s = re.sub(r"\b(\d+)(St|Nd|Rd|Th)\b", lambda m: m.group(1) + m.group(2).lower(), s)
    s = re.sub(r"\bE\b(?=\s)", "E", s)
    words = []
    for w in s.split():
        if w.isupper() and len(w) > 3 and w not in ("NCED",):
            w = w.capitalize()
        words.append(w)
    return " ".join(words)


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower().replace("'", "")).strip("-")
    return s or "place"


def display_name(n):
    """Store numbers and franchise codes are not part of a name: 'McDonald's #10726' -> "McDonald's"; 'Diner, the' -> 'The Diner'."""
    n = n.replace("Caf�", "Café").replace("caf�", "café")
    n = re.sub(r"\s*#\s*\d+[a-z]?\b", "", n)
    n = re.sub(r"\s+\d{4,}\b", "", n)
    n = re.sub(r"\s*\(norman\s*\w*\)$", "", n, flags=re.I)
    n = re.sub(r"\s*-\s*norman$", "", n, flags=re.I)
    m = re.match(r"^(.*),\s*(the|a)$", n.strip(), re.I)
    if m:
        n = m.group(2).capitalize() + " " + m.group(1)
    return re.sub(r"\s+", " ", n).strip(" ,-")


def main(verbose=False):
    os.makedirs(WORK, exist_ok=True)
    rows = able.load()
    plcs = P.fold(rows)
    pois, osm_ts = OSM.load()
    ests, osdh_ts = OSDH.load()
    licensed = [p for p in plcs if p["licensed"]]
    for p in plcs:
        p["sources"] = ["able"]
    # OSDH: match licensed places first, then add every other Norman kitchen that looks like a public eatery
    leftover_ests = match_osdh(licensed, ests)
    added, unsorted = [], []
    for e in leftover_ests:
        if not e["last_inspection"]:
            continue
        if classify.exclusion_reason(e["name"], e["street"]):
            continue
        if not classify.has_food_signal(e["name"]):
            unsorted.append(e)
            continue
        pl = {"name": title_name(e["name"]), "aka": [], "street": e["street"], "unit": e["unit"], "city": "Norman",
              "zip": e["zip"], "licensed": False, "licence_types": [], "licence_records": [], "licence_first_date": None,
              "licence_current_since": None, "licence_latest_status": "", "able_name_key": name_key(e["name"]),
              "osdh": e, "osdh_sim": 1.0, "sources": ["osdh"]}
        added.append(pl)
    # an ABLE place that is no longer licensed but still inspected recently is still a restaurant (it stopped selling alcohol)
    unlicensed = [p for p in plcs if not p["licensed"]]
    rest_ests = match_osdh(unlicensed, leftover_ests)
    for p in unlicensed:
        if p.get("osdh") and p["osdh"]["last_inspection"] and not any(p["osdh"] is a.get("osdh") for a in added):
            p["sources"] = ["able-lapsed", "osdh"]
    # the OSDH-only additions must not duplicate an unlicensed-but-inspected ABLE place, nor each other
    taken = {id(p["osdh"]) for p in unlicensed if p.get("osdh")}
    added = [a for a in added if id(a["osdh"]) not in taken]
    from textnorm import name_sim as _ns
    dedup = []
    anchors = licensed + [p for p in unlicensed if p.get("osdh")]
    for a in sorted(added, key=lambda a: a["osdh"]["last_inspection"], reverse=True):
        ka = street_key(a["street"])
        twin = next((b for b in anchors + dedup if street_key(b["street"]) == ka and _ns(a["name"], b["name"]) >= 0.75), None)
        if twin:
            twin.setdefault("osdh_extra", []).append(a["osdh"])
            continue
        # a residential street type with nothing else on record is probably a home kitchen (cottage bakery, a
        # caterer's house): not listed, a person decides
        if re.search(r"\b(ter|terrace|cir|circle|ct|court|ln|lane|pl|place|way|trl|trail)\.?$", a["street"], re.I) and not a.get("osm"):
            unsorted.append(a["osdh"])
            continue
        dedup.append(a)
    added = dedup
    candidates = licensed + [p for p in unlicensed if p.get("osdh")] + added
    for p in candidates:
        if p.get("osdh"):
            p["sources"] = sorted(set(p["sources"]) | {"osdh"})
    # OSM
    leftover_pois = match_osm(candidates, pois)
    for p in candidates:
        if p.get("osm"):
            p["sources"] = sorted(set(p["sources"]) | {"osm"})
    # coordinates: Census first, OSM position as fallback
    addr = []
    for p in candidates:
        p["geo_key"] = f"{p['street']} {p['unit']} {p['zip']}".strip().lower()
        addr.append((p["geo_key"], p["street"], "Norman", "OK", p["zip"] or ""))
    uniq = {a[0]: a for a in addr}
    geo = geocode.geocode_many(list(uniq.values()))
    for p in candidates:
        g = geo.get(p["geo_key"]) or {}
        osm = p.get("osm") or {}
        if g.get("matched") and g.get("lat"):
            p["lat"], p["lon"], p["geo_source"] = g["lat"], g["lon"], "census"
            if osm.get("lat"):
                # Census and OSM should agree to ~300 m; if not, the OSM match is suspect and is dropped
                dlat, dlon = abs(osm["lat"] - g["lat"]), abs(osm["lon"] - g["lon"])
                if dlat > 0.004 or dlon > 0.005:
                    p["osm_dropped"] = {"name": osm["name"], "why": "position disagrees with the address"}
                    del p["osm"]
                    p["sources"] = [s for s in p["sources"] if s != "osm"]
        elif osm.get("lat"):
            p["lat"], p["lon"], p["geo_source"] = osm["lat"], osm["lon"], "osm"
        else:
            p["lat"], p["lon"], p["geo_source"] = None, None, ""
    # decide: in the directory, or set aside with a reason
    kept, excluded = [], []
    for p in candidates:
        why = classify.exclusion_reason(p["name"], p.get("street", ""))
        osdh = p.get("osdh") or {}
        last = osdh.get("last_inspection")
        fresh = bool(last) and (TODAY - datetime.date.fromisoformat(last)).days <= FRESH_INSPECTION_DAYS
        p["inspection_fresh"] = fresh
        if why:
            excluded.append((p, why))
            continue
        if not p["licensed"] and not fresh:
            excluded.append((p, f"no current liquor licence and no health inspection in the last {FRESH_INSPECTION_DAYS} days"))
            continue
        kept.append(p)
    # presentation fields
    slugs = collections.Counter()
    for p in kept:
        p["category"] = classify.category(p)
        p["category_label"] = classify.CATEGORIES.get(p["category"], "Other")
        p["cuisines"] = classify.cuisine_labels(p)
        p["area"] = classify.area_for(p["lat"], p["lon"], p["street"])
        p["area_label"] = classify.AREA_LABEL.get(p["area"], "Elsewhere in Norman")
        p["street_display"] = fmt_street(p["street"]) + (f", Suite {p['unit']}" if p["unit"] and p["unit"][0].isdigit() else (f" {p['unit']}" if p["unit"] else ""))
        p["name"] = display_name(p["name"])
        base = slugify(p["name"])
        slugs[base] += 1
        p["slug"] = base if slugs[base] == 1 else f"{base}-{slugify(p['street'])}"
        p["evidence"] = []
        if p["licensed"]:
            p["evidence"].append("Oklahoma ABLE licence active on " + TODAY.isoformat())
        if p.get("osdh") and p["osdh"]["last_inspection"]:
            p["evidence"].append("Health inspection on " + p["osdh"]["last_inspection"])
        if p.get("osm"):
            p["evidence"].append("On OpenStreetMap (edited " + (p["osm"].get("timestamp") or "")[:10] + ")")
    kept.sort(key=lambda p: name_key(p["name"]) or p["name"].lower())
    stats = {
        "built": TODAY.isoformat(), "places": len(kept), "licensed": sum(1 for p in kept if p["licensed"]),
        "with_inspection": sum(1 for p in kept if p.get("osdh")), "with_osm": sum(1 for p in kept if p.get("osm")),
        "with_position": sum(1 for p in kept if p["lat"]), "by_source": dict(collections.Counter("+".join(p["sources"]) for p in kept)),
        "by_category": dict(collections.Counter(p["category_label"] for p in kept)),
        "by_area": dict(collections.Counter(p["area_label"] for p in kept)),
        "excluded": len(excluded), "able_rows": len(rows), "able_places_all_time": len(plcs), "osdh_norman_establishments": len(ests),
        "osm_named_places": len(pois), "osm_unmatched": len(leftover_pois), "osm_data_as_of": osm_ts, "osdh_pulled_at": osdh_ts,
    }
    stats["osdh_unsorted"] = len(unsorted)
    json.dump({"stats": stats, "places": kept}, open(os.path.join(WORK, "places.json"), "w", encoding="utf-8"), indent=1, default=str)
    json.dump([{"name": p["name"], "street": p["street"], "why": why, "sources": p["sources"], "licence_types": p["licence_types"],
                "last_inspection": (p.get("osdh") or {}).get("last_inspection")} for p, why in excluded],
              open(os.path.join(WORK, "excluded.json"), "w", encoding="utf-8"), indent=1)
    json.dump([{"name": q["name"], "kind": q["kind"], "street": q["street"], "osm": q["osm_url"], "edited": q["timestamp"][:10]}
               for q in leftover_pois], open(os.path.join(WORK, "osm_unmatched.json"), "w", encoding="utf-8"), indent=1)
    json.dump([{"name": e["name"], "street": e["street"], "last_inspection": e["last_inspection"]} for e in sorted(unsorted, key=lambda e: e["name"])],
              open(os.path.join(WORK, "unsorted.json"), "w", encoding="utf-8"), indent=1)
    stats["osdh_unsorted"] = len(unsorted)
    if verbose:
        print(json.dumps(stats, indent=1))
        print("--- excluded ---")
        for p, why in excluded:
            print(f"  {p['name'][:36]:36s} {p['street'][:24]:24s} :: {why}")
    return kept, stats


if __name__ == "__main__":
    main(verbose="-v" in sys.argv)

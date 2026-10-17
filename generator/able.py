"""Oklahoma ABLE Commission licence records (data/raw/norman_*.json from pull_able.py) -> clean licence rows.
Only the fields the public portal shows are kept: date, record number, licence type, trade name, expiration, status, address."""
import json, glob, re, os, datetime
RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
VENUE_TYPES = {
    "Mixed Beverage License": "mixed_beverage",
    "Mixed Beverage Combination License": "mixed_beverage_combination",
    "Beer and Wine License": "beer_and_wine",
    "Small Brewer License": "small_brewer",
    "Brew Pub License": "brew_pub",
    "Small Farm Winery License": "small_farm_winery",
    "Caterer & Storage License": "caterer",
    "Caterer License": "caterer",
    "Hotel License": "hotel",
}
CURRENT = ("Active", "About to Expire")
def norm_space(s): return re.sub(r"\s+", " ", (s or "").replace(" ", " ")).strip()
def parse_date(s):
    try: return datetime.datetime.strptime(s.strip(), "%m/%d/%Y").date()
    except Exception: return None
def parse_address(raw):
    """'2627 Classen Blvd Suite 104, Norman OK 73071 United States' -> street, unit, city, zip.
    The portal's trailing ', 1300' (a repeated house number) and 'Norman, OK OK 73071' both occur."""
    s = norm_space(raw).replace(" United States", "")
    s = re.sub(r",\s*\d+\s*$", "", s)                      # trailing repeated house number
    s = re.sub(r",\s*OK\s+OK\s+", " OK ", s)                # 'Norman, OK OK 73071'
    m = re.search(r",?\s*([A-Za-z .'-]+?)\s*(?:,\s*)?(?:OK\s+)?(\d{5})(?:-\d{4})?\s*$", s)
    city, zip5 = "", ""
    if m:
        city, zip5 = m.group(1).strip(" ,"), m.group(2); street = s[:m.start()].strip(" ,")
    else:
        street = s
    street = norm_space(street)
    unit = ""
    um = re.search(r"(?:,\s*|\s+)(?:(?:Suite|Ste\.?|Ste|Unit|#|STE|Bldg)\s*#?\s*([\w-]+)|([A-Z]-[A-Z]))\s*$", street, re.I)
    if um:
        unit = (um.group(1) or um.group(2) or "").strip(); street = street[:um.start()].strip(" ,")
    else:
        um2 = re.search(r",\s*([\w-]{1,6})\s*$", street)   # '229 E Main St, 110'
        if um2 and re.match(r"^\d", um2.group(1)): unit = um2.group(1); street = street[:um2.start()].strip(" ,")
    return street, unit, city, zip5
def load():
    rows = []
    for f in sorted(glob.glob(os.path.join(RAW, "norman_*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        for r in d["rows"]:
            typ = norm_space(r.get("type"))
            if typ not in VENUE_TYPES: continue          # drops the junk fee grid the Fraternal search returned
            dt = parse_date(r.get("date", ""))
            if not dt or not r.get("record"): continue
            street, unit, city, zip5 = parse_address(r.get("address", ""))
            rows.append({
                "record": norm_space(r["record"]), "licence_type": typ, "licence_key": VENUE_TYPES[typ],
                "name": norm_space(r.get("name")), "date": dt.isoformat(),
                "expiration": (parse_date(r.get("expiration","")) or datetime.date(1900,1,1)).isoformat() if r.get("expiration") else "",
                "status": norm_space(r.get("status")), "current": norm_space(r.get("status")) in CURRENT,
                "street": street, "unit": unit, "city": city or "Norman", "zip": zip5,
                "address_raw": norm_space(r.get("address")).replace(" United States", ""),
                "source_url": "https://aca-prod.accela.com" + r["href"] if r.get("href") else "",
            })
    return rows
if __name__ == "__main__":
    rows = load()
    cur = [r for r in rows if r["current"]]
    print(len(rows), "licence rows;", len(cur), "current")
    for r in cur[:8]: print(r["name"], "|", r["street"], "|", r["unit"], "|", r["city"], r["zip"], "|", r["date"], r["status"])
    odd = [r for r in rows if not re.match(r"^\d", r["street"]) or not r["zip"]]
    print("odd addresses:", [(r["name"], r["address_raw"]) for r in odd][:10])

"""Oklahoma State Department of Health food-service inspections for Norman (data/raw/osdh_norman.json from pull_osdh.py).
The source's own framing is kept with the data: 'An inspection is a snapshot in time.'"""
import json, os, datetime
from textnorm import street_key

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "osdh_norman.json")
SOURCE_URL = "https://www.phin.state.ok.us/Inspections/"


def load():
    try:
        d = json.load(open(RAW, encoding="utf-8"))
    except FileNotFoundError:
        return [], None
    out = []
    for e in d["norman"]:
        insp = sorted(e.get("inspections", []), key=lambda i: i["date"], reverse=True)
        street = e["address"]
        unit = ""
        for marker in (" STE ", " SUITE ", " UNIT ", " # ", " BLDG "):
            if marker in " " + street + " ":
                pos = (" " + street + " ").find(marker)
                unit = street[pos - 1 + len(marker):].strip()
                street = street[:pos - 1].strip()
                break
        num, core = street_key(street)
        out.append({
            "name": e["name"], "street": street, "unit": unit, "zip": e.get("zip", ""), "street_key": (num, core),
            "inspections": insp, "last_inspection": insp[0]["date"] if insp else None,
            "inspections_12mo": sum(1 for i in insp if i["date"] >= (datetime.date.today() - datetime.timedelta(days=365)).isoformat()),
            "first_inspection": insp[-1]["date"] if insp else None,
        })
    return out, d.get("pulled_at")


if __name__ == "__main__":
    rows, ts = load()
    print(len(rows), "Norman establishments, pulled", ts)
    import collections
    print("last inspection by year:", collections.Counter((r["last_inspection"] or "none")[:4] for r in rows).most_common())

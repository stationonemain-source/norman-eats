"""Fold ABLE licence rows into PLACES: one record per door (house number + street + unit), merging renewals and
sister licences, so a venue with a 2012 Mixed Beverage licence and a 2026 Combination licence is ONE place."""
import re
from textnorm import street_key, name_sim, name_key, title_name
import able


def fold(rows):
    groups = {}
    for r in rows:
        num, core = street_key(r["street"])
        groups.setdefault((num, core, (r["unit"] or "").lower()), []).append(r)
    # a unit-less record joins a unit-ed group at the same door when the names agree (portal entries drop suites at random)
    merged = {}
    for key, rs in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2] == "")):
        num, core, unit = key
        if unit == "":
            placed = False
            for k2, rs2 in merged.items():
                if k2[0] == num and k2[1] == core and k2[2] != "" and \
                        any(name_sim(a["name"], b["name"]) >= 0.5 for a in rs for b in rs2):
                    rs2.extend(rs)
                    placed = True
                    break
            if placed:
                continue
        merged[key] = list(rs)
    # within one door, split by name: unrelated businesses succeed each other at the same address over the years
    places = []
    for key, rs in merged.items():
        clusters = []
        for r in sorted(rs, key=lambda x: x["date"], reverse=True):
            for c in clusters:
                if any(name_sim(r["name"], o["name"]) >= 0.5 for o in c):
                    c.append(r)
                    break
            else:
                clusters.append([r])
        for c in clusters:
            places.append(make_place(c))
    return places


def make_place(rs):
    rs = sorted(rs, key=lambda x: (x["current"], x["date"]), reverse=True)
    head = rs[0]
    current = [r for r in rs if r["current"]]
    names = sorted({title_name(r["name"]) for r in rs},
                   key=lambda n: -sum(1 for r in rs if title_name(r["name"]) == n))
    first = min(r["date"] for r in rs)
    first_current = min((r["date"] for r in current), default=None)
    street = title_name(head["street"])
    return {
        "name": title_name(head["name"]), "aka": [n for n in names if n != title_name(head["name"])],
        "street": street, "unit": head["unit"], "city": "Norman", "zip": head["zip"],
        "licensed": bool(current),
        "licence_types": sorted({r["licence_type"].replace(" License", "") for r in current}),
        "licence_records": [{"record": r["record"], "type": r["licence_type"].replace(" License", ""), "date": r["date"],
                             "expiration": r["expiration"], "status": r["status"], "url": r["source_url"]} for r in rs],
        "licence_first_date": first, "licence_current_since": first_current,
        "licence_latest_status": head["status"], "able_name_key": name_key(head["name"]),
    }


if __name__ == "__main__":
    rows = able.load()
    places = fold(rows)
    lic = [p for p in places if p["licensed"]]
    print(len(places), "places from", len(rows), "rows;", len(lic), "currently licensed")
    for p in sorted(lic, key=lambda p: p["name"].lower()):
        print(f"{p['name'][:34]:34s} | {p['street'][:26]:26s} {p['unit']:5s} | since {p['licence_first_date']} | "
              f"{', '.join(p['licence_types'])[:40]} | aka {p['aka'][:2]}")

"""Join the three sources on the DOOR (house number + street core), then on the name.
ABLE places are the spine for licensed venues; OSDH establishments are the spine for everything else that serves food;
OSM adds cuisine, hours, website, phone and a position. A join needs the same door AND a name similarity >= 0.5,
or the same door when only one candidate sits behind it and the names do not clash outright. A second pass allows
a near door (same street, house number within 30) when the names agree strongly: the sources disagree on numbers."""
from textnorm import name_sim, street_key, simplify_name


def index_by_door(items, key_fn):
    idx = {}
    for it in items:
        k = key_fn(it)
        if k and k[0]:
            idx.setdefault(k, []).append(it)
    return idx


def best(cands, name, used):
    scored = []
    for c in cands:
        if id(c) in used:
            continue
        scored.append((name_sim(name, c["name"]), c))
    if not scored:
        return None, 0.0
    scored.sort(key=lambda s: -s[0])
    sim, c = scored[0]
    if sim >= 0.5:
        return c, sim
    if len(scored) == 1 and sim > 0:
        return c, sim
    return None, sim


def near_door(idx, k, name, used, max_gap=30):
    """Same street core, house number within max_gap, strong name agreement."""
    try:
        n = int(k[0])
    except (TypeError, ValueError):
        return None, 0.0
    bestc, bests = None, 0.0
    for (num, core), cands in idx.items():
        if core != k[1] or not num.isdigit() or abs(int(num) - n) > max_gap:
            continue
        for c in cands:
            if id(c) in used:
                continue
            s = name_sim(name, c["name"])
            if s >= 0.75 and s > bests:
                bestc, bests = c, s
    return bestc, bests


def match_osm(places, pois):
    idx = index_by_door(pois, lambda p: p["street_key"])
    used = set()
    for pl in places:
        k = street_key(pl["street"])
        c, sim = best(idx.get(k, []), pl["name"], used)
        if c is None:
            c, sim = near_door(idx, k, pl["name"], used)
        if c is None:
            for cand in pois:          # OSM often lacks addr:*; accept an exact-ish name anywhere in Norman
                if id(cand) in used or cand["street_key"][0]:
                    continue
                if name_sim(pl["name"], cand["name"]) >= 0.75 and len(simplify_name(cand["name"])) >= 1:
                    c, sim = cand, name_sim(pl["name"], cand["name"])
                    break
        if c is not None:
            used.add(id(c))
            pl["osm"] = c
            pl["osm_sim"] = round(sim, 2)
    return [p for p in pois if id(p) not in used]


def match_osdh(places, ests):
    idx = index_by_door(ests, lambda e: e["street_key"])
    used = set()
    for pl in places:
        k = street_key(pl["street"])
        c, sim = best(idx.get(k, []), pl["name"], used)
        if c is None:
            c, sim = near_door(idx, k, pl["name"], used)
        if c is not None:
            used.add(id(c))
            pl["osdh"] = c
            pl["osdh_sim"] = round(sim, 2)
    # a second OSDH entry at the same door with the same name (a banquet room, a second counter) rides along
    for pl in places:
        if not pl.get("osdh"):
            continue
        k = street_key(pl["street"])
        for e in idx.get(k, []):
            if id(e) in used:
                continue
            if name_sim(pl["name"], e["name"]) >= 0.75:
                used.add(id(e))
                pl.setdefault("osdh_extra", []).append(e)
    return [e for e in ests if id(e) not in used]

"""Hand-drawn-feeling SVG street maps from OpenStreetMap ways (data/raw/osm_roads.json, 'out geom').
No tiles, no third-party request at runtime: the map is inline SVG. Data (c) OpenStreetMap contributors, ODbL."""
import json, math, os

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "osm_roads.json")
BOUNDARY = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "osm_boundary.json")
ROAD_STYLE = {   # stroke width in px at the place-page scale, and a class for colour
    "motorway": (7, "mw"), "motorway_link": (3, "mw"), "trunk": (6, "mw"), "trunk_link": (3, "mw"),
    "primary": (5, "pri"), "primary_link": (2.5, "pri"), "secondary": (4, "sec"), "secondary_link": (2, "sec"),
    "tertiary": (3, "ter"), "tertiary_link": (1.8, "ter"), "residential": (1.6, "res"), "unclassified": (1.6, "res"),
    "living_street": (1.4, "res"), "pedestrian": (1.4, "res"),
}
_cache = {}


def load():
    if "ways" in _cache:
        return _cache["ways"]
    d = json.load(open(RAW, encoding="utf-8"))
    ways = []
    for e in d["elements"]:
        if e["type"] == "way" and e.get("geometry"):
            t = e.get("tags", {})
            kind = "road" if "highway" in t else "rail" if t.get("railway") == "rail" else \
                "water" if (t.get("natural") == "water" or t.get("waterway")) else "green" if (t.get("leisure") == "park" or t.get("landuse") in ("grass", "cemetery") or t.get("amenity") == "university") else ""
            if not kind:
                continue
            pts = [(g["lon"], g["lat"]) for g in e["geometry"]]
            lons = [p[0] for p in pts]; lats = [p[1] for p in pts]
            ways.append({"kind": kind, "hw": t.get("highway", ""), "name": t.get("name", ""), "pts": pts,
                         "bbox": (min(lons), min(lats), max(lons), max(lats)), "area": t.get("natural") == "water" or kind == "green",
                         "ref": t.get("ref", "")})
        elif e["type"] == "relation" and e.get("members"):
            t = e.get("tags", {})
            kind = "water" if t.get("natural") == "water" else "green" if t.get("amenity") == "university" else ""
            if not kind:
                continue
            for m in e["members"]:
                if m.get("type") == "way" and m.get("geometry") and m.get("role") in ("outer", ""):
                    pts = [(g["lon"], g["lat"]) for g in m["geometry"]]
                    lons = [p[0] for p in pts]; lats = [p[1] for p in pts]
                    ways.append({"kind": kind, "hw": "", "name": t.get("name", ""), "pts": pts,
                                 "bbox": (min(lons), min(lats), max(lons), max(lats)), "area": True, "ref": ""})
    _cache["ways"] = ways
    return ways


def boundary_rings():
    """The city limit as rings of (lon, lat), chained from the relation's outer ways."""
    if "rings" in _cache:
        return _cache["rings"]
    d = json.load(open(BOUNDARY, encoding="utf-8"))
    segs = []
    for m in d["elements"][0]["members"]:
        if m.get("type") == "way" and m.get("role") == "outer" and m.get("geometry"):
            segs.append([(g["lon"], g["lat"]) for g in m["geometry"]])
    rings = []
    while segs:
        ring = segs.pop(0)
        changed = True
        while changed and segs:
            changed = False
            for i, s in enumerate(segs):
                if s[0] == ring[-1]:
                    ring += s[1:]; segs.pop(i); changed = True; break
                if s[-1] == ring[-1]:
                    ring += list(reversed(s))[1:]; segs.pop(i); changed = True; break
                if s[-1] == ring[0]:
                    ring = s[:-1] + ring; segs.pop(i); changed = True; break
                if s[0] == ring[0]:
                    ring = list(reversed(s))[:-1] + ring; segs.pop(i); changed = True; break
        rings.append(ring)
    _cache["rings"] = rings
    return rings


def _proj(lat0):
    k = math.cos(math.radians(lat0))
    return lambda lon, lat: (lon * k, lat)


def place_map(lat, lon, size=560, radius_m=520, label=True):
    """A square SVG, centred on the place, radius_m metres to each edge."""
    ways = load()
    half_deg_lat = radius_m / 111_320
    half_deg_lon = half_deg_lat / math.cos(math.radians(lat))
    x0, x1, y0, y1 = lon - half_deg_lon, lon + half_deg_lon, lat - half_deg_lat, lat + half_deg_lat
    sx = size / (x1 - x0); sy = size / (y1 - y0)
    def P(pt):
        return (round((pt[0] - x0) * sx, 1), round((y1 - pt[1]) * sy, 1))
    def inside(b):
        return not (b[2] < x0 or b[0] > x1 or b[3] < y0 or b[1] > y1)
    out = [f'<svg class="minimap" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg" role="img" '
           f'aria-label="Street map around this address, drawn from OpenStreetMap data">',
           f'<rect width="{size}" height="{size}" class="mm-bg"/>']
    for kind in ("green", "water"):
        for w in ways:
            if w["kind"] == kind and inside(w["bbox"]):
                pts = " ".join(f"{x},{y}" for x, y in map(P, w["pts"]))
                out.append(f'<polygon points="{pts}" class="mm-{kind}"/>' if w["area"] else f'<polyline points="{pts}" class="mm-{kind}line"/>')
    labels = []
    for pass_ in ("casing", "fill"):
        for w in ways:
            if w["kind"] not in ("road", "rail") or not inside(w["bbox"]):
                continue
            pts = " ".join(f"{x},{y}" for x, y in map(P, w["pts"]))
            if w["kind"] == "rail":
                if pass_ == "fill":
                    out.append(f'<polyline points="{pts}" class="mm-rail"/>')
                continue
            width, cls = ROAD_STYLE.get(w["hw"], (1.4, "res"))
            if pass_ == "casing":
                out.append(f'<polyline points="{pts}" class="mm-casing" stroke-width="{width + 2.2}"/>')
            else:
                out.append(f'<polyline points="{pts}" class="mm-road mm-{cls}" stroke-width="{width}"/>')
                if label and w["name"] and cls in ("mw", "pri", "sec", "ter") and len(w["pts"]) >= 2:
                    labels.append((w, width))
    # street labels: one per distinct name, set along the longest visible segment
    seen = set()
    for w, width in sorted(labels, key=lambda t: -len(t[0]["pts"])):
        nm = w["name"]
        if nm in seen or len(seen) >= 9:
            continue
        pts = [P(p) for p in w["pts"] if x0 <= p[0] <= x1 and y0 <= p[1] <= y1]
        if len(pts) < 2:
            continue
        # longest segment
        best = max(range(len(pts) - 1), key=lambda i: (pts[i+1][0]-pts[i][0])**2 + (pts[i+1][1]-pts[i][1])**2)
        (ax, ay), (bx, by) = pts[best], pts[best + 1]
        seg = math.hypot(bx - ax, by - ay)
        if seg < 60:
            continue
        ang = math.degrees(math.atan2(by - ay, bx - ax))
        if ang > 90: ang -= 180
        if ang < -90: ang += 180
        mx, my = (ax + bx) / 2, (ay + by) / 2
        seen.add(nm)
        short = nm.replace("Northwest", "NW").replace("Southwest", "SW").replace("Northeast", "NE").replace("Southeast", "SE") \
                  .replace("Avenue", "Ave").replace("Street", "St").replace("Boulevard", "Blvd").replace("Parkway", "Pkwy").replace("Highway", "Hwy")
        if len(short) > 26 and w.get("ref"):
            short = w["ref"].replace("I ", "I-").replace(";", " / ")   # "Interstate 35 ... Memorial Highway" -> "I-35"
        elif len(short) > 30:
            short = short[:28].rstrip() + "..."
        out.append(f'<text class="mm-label" transform="translate({mx:.0f},{my:.0f}) rotate({ang:.0f})" dy="-{width/2+3:.0f}">{_esc(short)}</text>')
    cx, cy = size / 2, size / 2
    out.append(f'<g class="mm-pin"><circle cx="{cx}" cy="{cy}" r="13" class="mm-pin-halo"/><circle cx="{cx}" cy="{cy}" r="6.5" class="mm-pin-dot"/></g>')
    out.append(f'<text x="{size - 8}" y="{size - 8}" class="mm-credit" text-anchor="end">© OpenStreetMap contributors</text>')
    out.append("</svg>")
    return "\n".join(out)


def overview_map(points, width=900, height=640, pad=0.01):
    """Norman's outline with one dot per place. points: list of (lat, lon, slug, name, category)."""
    rings = boundary_rings()
    allpts = [p for r in rings for p in r]
    lons = [p[0] for p in allpts]; lats = [p[1] for p in allpts]
    k = math.cos(math.radians(sum(lats) / len(lats)))
    x0, x1 = (min(lons) - pad) * k, (max(lons) + pad) * k
    y0, y1 = min(lats) - pad, max(lats) + pad
    s = min(width / (x1 - x0), height / (y1 - y0))
    ox = (width - (x1 - x0) * s) / 2; oy = (height - (y1 - y0) * s) / 2
    def P(lon, lat):
        return (round((lon * k - x0) * s + ox, 1), round((y1 - lat) * s + oy, 1))
    out = [f'<svg class="overview" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Map of Norman with one dot for each place in the directory">']
    for r in rings:
        out.append('<polygon class="ov-city" points="' + " ".join(f"{x},{y}" for x, y in (P(*p) for p in r)) + '"/>')
    ways = load()
    for w in ways:
        if w["kind"] == "green" and w["area"] and w["name"] and "University of Oklahoma" in w["name"] and len(w["pts"]) > 20:
            out.append('<polygon class="ov-green" points="' + " ".join(f"{x},{y}" for x, y in (P(*p) for p in w["pts"])) + '"/>')
    for w in ways:
        if w["kind"] == "water" and w["area"] and len(w["pts"]) > 30:
            out.append('<polygon class="ov-water" points="' + " ".join(f"{x},{y}" for x, y in (P(*p) for p in w["pts"])) + '"/>')
    for w in ways:
        if w["kind"] == "road" and w["hw"] in ("motorway", "trunk", "primary", "secondary"):
            out.append(f'<polyline class="ov-road ov-{w["hw"]}" points="' + " ".join(f"{x},{y}" for x, y in (P(*p) for p in w["pts"])) + '"/>')
    for lat, lon, slug, name, cat in points:
        x, y = P(lon, lat)
        out.append(f'<a href="/places/{slug}/"><circle class="ov-dot ov-{cat}" cx="{x}" cy="{y}" r="4.2"><title>{_esc(name)}</title></circle></a>')
    out.append(f'<text x="{width - 10}" y="{height - 10}" class="mm-credit" text-anchor="end">© OpenStreetMap contributors</text>')
    out.append("</svg>")
    return "\n".join(out)


def _esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

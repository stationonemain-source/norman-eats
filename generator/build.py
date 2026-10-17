"""Build the whole static site into docs/ (the GitHub Pages source). Usage: python generator/build.py [--data]
--data re-runs the data pipeline first (licences + inspections + OSM + geocoding); without it the last data/work/places.json is used."""
import json, os, shutil, sys, datetime
sys.path.insert(0, os.path.dirname(__file__))
import render as R
from classify import CATEGORIES, CATEGORY_ORDER, AREA_LABEL, AREAS

ROOT = os.path.join(os.path.dirname(__file__), "..")
DOCS = os.path.join(ROOT, "docs")
WORK = os.path.join(ROOT, "data", "work")
SITE = os.path.join(ROOT, "site")


def write(path, html):
    full = os.path.join(DOCS, path.strip("/"))
    if path.endswith("/") or not os.path.splitext(path)[1]:
        full = os.path.join(full, "index.html")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    import time
    for attempt in range(4):   # Windows: an indexer or a preview server can hold a freshly made folder for a moment
        try:
            with open(full, "w", encoding="utf-8", newline="\n") as f:
                f.write(html)
            return
        except OSError:
            if attempt == 3:
                raise
            time.sleep(0.3)


def main():
    if "--data" in sys.argv or not os.path.exists(os.path.join(WORK, "places.json")):
        import build_data
        build_data.main(verbose=True)
    d = json.load(open(os.path.join(WORK, "places.json"), encoding="utf-8"))
    places, stats = d["places"], d["stats"]
    built = stats["built"]
    try:
        excluded = len(json.load(open(os.path.join(WORK, "excluded.json"), encoding="utf-8")))
    except Exception:
        excluded = 0
    if os.path.isdir(DOCS):
        shutil.rmtree(DOCS)
    shutil.copytree(os.path.join(SITE, "assets"), os.path.join(DOCS, "assets"))
    write("/", R.home(places, stats, built))
    write("/a-z/", R.az(places, built))
    write("/cuisine/", R.cuisine_index(places, built))
    write("/areas/", R.areas_index(places, built))
    write("/claim/", R.claim_page(built))
    write("/about/", R.about(stats, built, excluded))
    write("/404.html", R.not_found(built))
    urls = ["/", "/a-z/", "/cuisine/", "/areas/", "/claim/", "/about/"]
    for k in CATEGORY_ORDER:
        ps = [p for p in places if p["category"] == k]
        if ps:
            write(f"/kind/{k}/", R.group_page(CATEGORIES[k], ps, built, current="cuisine", fact="since"))
            urls.append(f"/kind/{k}/")
    cuis = {}
    for p in places:
        for c in p["cuisines"]:
            cuis.setdefault(c, []).append(p)
    for c, ps in cuis.items():
        write(f"/cuisine/{R.slug(c)}/", R.group_page(c, ps, built, current="cuisine", fact="since"))
        urls.append(f"/cuisine/{R.slug(c)}/")
    areas = {}
    for p in places:
        areas.setdefault(p["area"], []).append(p)
    for k, ps in areas.items():
        write(f"/areas/{k}/", R.group_page(AREA_LABEL.get(k, "Elsewhere in Norman"), sorted(ps, key=lambda p: p["name"].lower()), built,
                                          intro="", current="areas", fact="category"))
        urls.append(f"/areas/{k}/")
    for p in places:
        write(f"/places/{p['slug']}/", R.place_page(p, built))
        urls.append(f"/places/{p['slug']}/")
    # a slim public export (no inspection detail lines), for reuse and for checking
    slim = [{"name": p["name"], "slug": p["slug"], "address": p["street_display"], "zip": p.get("zip"), "category": p["category_label"],
             "cuisines": p["cuisines"], "area": p["area_label"], "lat": p["lat"], "lon": p["lon"], "licensed": p["licensed"],
             "licence_types": p["licence_types"], "licence_on_record_since": p.get("licence_first_date"),
             "last_inspection": (p.get("osdh") or {}).get("last_inspection"), "osm": (p.get("osm") or {}).get("osm_url"),
             "sources": p["sources"]} for p in places]
    os.makedirs(os.path.join(DOCS, "data"), exist_ok=True)
    json.dump({"built": built, "attribution": "Licence data: Oklahoma ABLE Commission. Inspection data: Oklahoma State Department of Health. "
               "Map data (c) OpenStreetMap contributors, ODbL. Positions: US Census Bureau geocoder.", "places": slim},
              open(os.path.join(DOCS, "data", "norman-eats.json"), "w", encoding="utf-8"), indent=1)
    # robots and sitemap follow the PUBLIC switch
    if R.PUBLIC:
        open(os.path.join(DOCS, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: https://stationonemain-source.github.io{R.BASE}/sitemap.xml\n")
        with open(os.path.join(DOCS, "sitemap.xml"), "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            for url in urls:
                f.write(f"  <url><loc>https://stationonemain-source.github.io{R.BASE}{url}</loc><lastmod>{built}</lastmod></url>\n")
            f.write("</urlset>\n")
    else:
        open(os.path.join(DOCS, "robots.txt"), "w").write("User-agent: *\nDisallow: /\n")
    open(os.path.join(DOCS, ".nojekyll"), "w").write("")
    print(f"built {len(urls)} pages into docs/ (base {R.BASE!r}, public={R.PUBLIC})")


if __name__ == "__main__":
    main()

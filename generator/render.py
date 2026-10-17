"""HTML for every page. Plain functions, no template engine: what you read here is what ships.
Copy rules (DESIGN.md §7): no em-dashes, nothing invented, every number traceable to a record on the page."""
import datetime, html, os, re
import minimap, hours as H
from classify import CATEGORIES, CATEGORY_ORDER, AREA_LABEL, AREAS

BASE = os.environ.get("NE_BASE", "/norman-eats")      # GitHub project pages serve under /norman-eats/
PUBLIC = os.environ.get("NE_PUBLIC", "0") == "1"       # unlisted until Circle approves: noindex + robots Disallow
SITE_NAME = "Norman Eats"
TAGLINE = "Every restaurant and bar in Norman, Oklahoma, from the public record."
CONTACT = "main@station.solutions"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
INSPECTION_NOTE = "The Health Department's own caution: an inspection is a snapshot in time."


def e(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def u(path):
    return BASE + path


def month_year(iso):
    if not iso:
        return ""
    d = datetime.date.fromisoformat(iso[:10])
    return f"{MONTHS[d.month - 1]} {d.year}"


def long_date(iso):
    if not iso:
        return ""
    d = datetime.date.fromisoformat(iso[:10])
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower().replace("&", " and ")).strip("-")


def page(title, body, *, desc="", current="", extra_head="", built=""):
    robots = "" if PUBLIC else '<meta name="robots" content="noindex, nofollow">\n  '
    nav = [("/", "Home", "home"), ("/a-z/", "A to Z", "a-z"), ("/cuisine/", "By cuisine", "cuisine"), ("/areas/", "By area", "areas"),
           ("/claim/", "Claim a page", "claim"), ("/about/", "About the data", "about")]
    cur_attr = ' aria-current="page"'
    nav_html = "".join('<a href="' + u(p) + '"' + (cur_attr if key == current else "") + '>' + label + '</a>' for p, label, key in nav)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)}</title>
  {robots}<meta name="description" content="{e(desc or TAGLINE)}">
  <meta property="og:title" content="{e(title)}">
  <meta property="og:description" content="{e(desc or TAGLINE)}">
  <meta property="og:type" content="website">
  <link rel="icon" href="{u('/assets/favicon.svg')}" type="image/svg+xml">
  <link rel="stylesheet" href="{u('/assets/site.css')}">
  {extra_head}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="mast"><div class="wrap">
  <div class="row">
    <a class="name" href="{u('/')}">{SITE_NAME}</a>
    <p class="tag">{TAGLINE}</p>
  </div>
  <nav class="nav" aria-label="Site">{nav_html}</nav>
</div></header>
<main id="main"><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">
  <p class="credit">Designed &amp; hosted by <a href="https://station.solutions/" target="_blank" rel="noopener">Station.Solutions</a>, Norman, Oklahoma.</p>
  <p>Licence records: <a href="https://oklahoma.gov/able-commission/legal/licensee-search.html" rel="noopener">Oklahoma ABLE Commission</a>. Inspection records: <a href="https://www.phin.state.ok.us/Inspections/" rel="noopener">Oklahoma State Department of Health</a>. Map data &copy; <a href="https://www.openstreetmap.org/copyright" rel="noopener">OpenStreetMap contributors</a>, ODbL.</p>
  <p>Built {e(long_date(built))}. Something wrong? <a href="mailto:{CONTACT}?subject=Norman%20Eats%3A%20a%20correction">Email a correction</a>. Not affiliated with any restaurant, the City of Norman or the University of Oklahoma.</p>
</div></footer>
</body>
</html>
"""


def board(places, fact="category", where="street"):
    items = []
    for p in places:
        if fact == "category":
            f = p["category_label"]
        elif fact == "since":
            f = f"since {p['licence_first_date'][:4]}" if p.get("licence_first_date") and p["licensed"] else \
                (f"inspected {month_year(p['osdh']['last_inspection'])}" if p.get("osdh") and p["osdh"].get("last_inspection") else "")
        elif fact == "area":
            f = p["area_label"]
        else:
            f = ""
        w = p["street_display"] if where == "street" else p["area_label"]
        items.append(f'<li><span class="nm"><a href="{u("/places/" + p["slug"] + "/")}">{e(p["name"])}</a></span>'
                     f'<span class="dots" aria-hidden="true"></span><span class="where">{e(w)}</span><span class="fact">{e(f)}</span></li>')
    return '<ul class="board">' + "".join(items) + "</ul>"


def claim_block(place=None, standalone=False):
    biz = e(place["name"]) if place else ""
    addr = e(place["street_display"] + ", Norman, OK " + (place.get("zip") or "")) if place else ""
    industry = e(place["category_label"] + " / Norman Eats page claim") if place else "Norman Eats page claim"
    heading = "Is this your restaurant? Claim this page." if place else "Claim your page"
    intro = (f"If you run {biz}, tell us. A person at Station will reply to confirm it's you, then correct the hours, "
             f"add your website and menu link, and mark the page as owner-verified. It costs nothing.") if place else \
            ("If you run a restaurant or bar in Norman, tell us which one. A person at Station will reply to confirm it's you, "
             "then correct the hours, add your website and menu link, and mark the page as owner-verified. It costs nothing.")
    place_field = "" if place else '''<div class="field full"><label for="c-business">Which place</label>
      <input id="c-business" name="business" required autocomplete="organization" placeholder="Name of the restaurant or bar"></div>
    <div class="field full"><label for="c-address">Its address</label><input id="c-address" name="address" autocomplete="street-address"></div>'''
    hidden = (f'<input type="hidden" name="business" value="{biz}"><input type="hidden" name="address" value="{addr}">' if place else "")
    return f"""<section class="claim" id="claim">
  <h2>{heading}</h2>
  <p>{intro}</p>
  <form data-claim method="post" action="#claim" novalidate>
    {hidden}<input type="hidden" name="industry" value="{industry}">
    {place_field}
    <div class="field"><label for="c-name">Your name</label><input id="c-name" name="name" required autocomplete="name"></div>
    <div class="field"><label for="c-role">Your role</label>
      <select id="c-role" name="role"><option>Owner</option><option>Manager</option><option>Staff</option><option>Family or friend of the owner</option></select></div>
    <div class="field"><label for="c-email">Email</label><input id="c-email" name="email" type="email" required autocomplete="email"></div>
    <div class="field"><label for="c-phone">Phone (optional)</label><input id="c-phone" name="phone" type="tel" autocomplete="tel"></div>
    <div class="field full"><label for="c-website">Your website or menu link (optional)</label><input id="c-website" name="website" type="url" autocomplete="url" placeholder="https://"></div>
    <div class="field full"><label for="c-leak">Anything to correct on the page? (optional)</label><textarea id="c-leak" name="leak"></textarea></div>
    <div class="hp" aria-hidden="true"><label for="c-url">Company URL</label><input id="c-url" name="company_url" tabindex="-1" autocomplete="off"></div>
    <div class="full"><button class="btn" type="submit">Claim this page</button>
      <p class="fine">We use what you type here to reply to you and to correct this listing, nothing else.</p></div>
  </form>
  <div class="done" tabindex="-1" role="status">
    <p><b>Sent.</b> Your claim is on its way to Station. If you don't hear from a person within two business days,
    <a data-mail href="mailto:{CONTACT}?subject=Norman%20Eats%20claim">email us directly</a> and we'll sort it out.</p>
  </div>
</section>"""


def home(places, stats, built):
    pts = [(p["lat"], p["lon"], p["slug"], p["name"], p["category"]) for p in places if p["lat"]]
    ov = minimap.overview_map(pts)
    newest = sorted([p for p in places if p["licensed"] and p.get("licence_first_date") and p["licence_first_date"] >= (datetime.date.today() - datetime.timedelta(days=365)).isoformat()],
                    key=lambda p: p["licence_first_date"], reverse=True)[:12]
    cats = {}
    for p in places:
        cats[p["category"]] = cats.get(p["category"], 0) + 1
    cuis = {}
    for p in places:
        for c in p["cuisines"]:
            cuis[c] = cuis.get(c, 0) + 1
    top_cuis = sorted(cuis.items(), key=lambda kv: -kv[1])[:8]
    areas = {}
    for p in places:
        areas[p["area"]] = areas.get(p["area"], 0) + 1
    area_order = [k for k, _, _ in AREAS] + ["elsewhere"]
    body = f"""
<h1>Where to eat and drink in Norman, by the record.</h1>
<p class="lede">Every place listed here holds a <b>current Oklahoma liquor licence</b> or has had a <b>health inspection</b> within the
last sixteen months. We read the public record, draw the map, and let the people who run each place fix what's wrong.
No ratings, no ads, no pay-to-list.</p>
<div class="counts">
  <div><strong>{stats['places']}</strong>places listed</div>
  <div><strong>{stats['licensed']}</strong>with a current liquor licence</div>
  <div><strong>{stats['with_inspection']}</strong>with an inspection on file</div>
  <div><strong>{len(cuis)}</strong>cuisines</div>
</div>
<div class="home-grid">
  <div>
    {ov}
    <p class="map-note">Each dot is a place in the directory. Tap one to open its page. City limits and roads from OpenStreetMap.</p>
  </div>
  <div class="browse">
    <div><h2>By kind</h2><ul>{''.join(f'<li><a href="{u("/kind/" + k + "/")}">{e(CATEGORIES[k])}</a><span>{cats[k]}</span></li>' for k in CATEGORY_ORDER if cats.get(k))}</ul></div>
    <div><h2>By cuisine</h2><ul>{''.join(f'<li><a href="{u("/cuisine/" + slug(c) + "/")}">{e(c)}</a><span>{n}</span></li>' for c, n in top_cuis)}<li><a href="{u('/cuisine/')}">All cuisines</a><span>{len(cuis)}</span></li></ul></div>
    <div><h2>By area</h2><ul>{''.join(f'<li><a href="{u("/areas/" + k + "/")}">{e(AREA_LABEL.get(k, "Elsewhere in Norman"))}</a><span>{areas[k]}</span></li>' for k in area_order if areas.get(k))}</ul></div>
  </div>
</div>
<h2>New on the record</h2>
<p class="muted">Places whose first liquor licence appeared in the last twelve months. A new licence usually means a new kitchen or a new owner.</p>
{board(newest, fact="since")}
{claim_block(None)}
"""
    return page(f"{SITE_NAME}: restaurants and bars in Norman, Oklahoma", body, current="home", built=built)


def az(places, built):
    groups = {}
    for p in places:
        first = re.sub(r"^(the|el|la|los|las)\s+", "", p["name"].lower()).strip()[:1].upper()
        if not first.isalpha():
            first = "#"
        groups.setdefault(first, []).append(p)
    letters = [chr(c) for c in range(65, 91)]
    alpha = '<p class="alpha">' + "".join((f'<a href="#{l}">{l}</a>' if l in groups else f"<span>{l}</span>") for l in letters) + (f'<a href="#num">#</a>' if "#" in groups else "") + "</p>"
    sections = []
    for l in (["#"] if "#" in groups else []) + [l for l in letters if l in groups]:
        sections.append(f'<section class="letter" id="{"num" if l == "#" else l}"><h2>{l}</h2>{board(groups[l], fact="category")}</section>')
    body = f"<h1>A to Z</h1><p class='muted'>{len(places)} places. The street and the kind of place, nothing else; open a page for the record.</p>{alpha}{''.join(sections)}"
    return page(f"A to Z of Norman restaurants and bars, {SITE_NAME}", body, current="a-z", built=built)


def cuisine_index(places, built):
    cuis, cats = {}, {}
    for p in places:
        cats[p["category"]] = cats.get(p["category"], 0) + 1
        for c in p["cuisines"]:
            cuis[c] = cuis.get(c, 0) + 1
    body = f"""<h1>By kind and by cuisine</h1>
<p class="muted">Cuisine comes from OpenStreetMap where someone has mapped it, or from the name when it says so plainly. Where neither does, the page says so, and the owner can fix it.</p>
<div class="browse">
  <div><h2>Kind of place</h2><ul>{''.join(f'<li><a href="{u("/kind/" + k + "/")}">{e(CATEGORIES[k])}</a><span>{cats[k]}</span></li>' for k in CATEGORY_ORDER if cats.get(k))}</ul></div>
  <div><h2>Cuisine</h2><ul>{''.join(f'<li><a href="{u("/cuisine/" + slug(c) + "/")}">{e(c)}</a><span>{n}</span></li>' for c, n in sorted(cuis.items(), key=lambda kv: (-kv[1], kv[0])))}</ul></div>
</div>"""
    return page(f"Norman restaurants by cuisine, {SITE_NAME}", body, current="cuisine", built=built)


def group_page(title, places, built, intro="", current="cuisine", fact="since"):
    body = f"<h1>{e(title)}</h1><p class='muted'>{e(intro) if intro else ''} {len(places)} place{'s' if len(places) != 1 else ''}.</p>{board(places, fact=fact)}"
    return page(f"{title} in Norman, {SITE_NAME}", body, current=current, built=built)


def areas_index(places, built):
    areas = {}
    for p in places:
        areas.setdefault(p["area"], []).append(p)
    order = [k for k, _, _ in AREAS] + ["elsewhere"]
    pts = [(p["lat"], p["lon"], p["slug"], p["name"], p["category"]) for p in places if p["lat"]]
    body = f"""<h1>By area</h1>
<p class="muted">Nine parts of town, drawn by hand around where people actually go: Campus Corner north of the university, Main Street downtown, the Lindsey Street strip, the I-35 retail miles, and the rest.</p>
{minimap.overview_map(pts)}
<div class="browse">{''.join(f'<div><h2><a href="{u("/areas/" + k + "/")}">{e(AREA_LABEL.get(k, "Elsewhere in Norman"))}</a></h2><ul>' + ''.join(f'<li><a href="{u("/places/" + p["slug"] + "/")}">{e(p["name"])}</a><span>{e(p["category_label"])}</span></li>' for p in sorted(areas[k], key=lambda p: p["name"].lower())[:6]) + (f'<li><a href="{u("/areas/" + k + "/")}">All {len(areas[k])}</a><span></span></li>' if len(areas[k]) > 6 else "") + '</ul></div>' for k in order if areas.get(k))}</div>"""
    return page(f"Norman restaurants and bars by area, {SITE_NAME}", body, current="areas", built=built)


def place_page(p, built):
    osm = p.get("osm") or {}
    osdh = p.get("osdh") or {}
    kind = e(p["category_label"]) + (" <span class='muted'>&middot;</span> " + e(", ".join(p["cuisines"][:3])) if p["cuisines"] else "")
    facts = [f'<dt>Address</dt><dd class="addr">{e(p["street_display"])}<br>Norman, OK {e(p.get("zip") or "")}</dd>']
    if osm.get("opening_hours"):
        rows = H.humanize(osm["opening_hours"])
        if rows:
            hrs = "<ul class='hours'>" + "".join(f"<li><span>{e(d)}</span><span>{e(t)}</span></li>" for d, t in rows) + "</ul>"
        else:
            hrs = f"<p>{e(osm['opening_hours'])}</p>"
        facts.append(f'<dt>Hours</dt><dd>{hrs}<p class="small muted">As mapped on OpenStreetMap, edited {e(month_year(osm.get("timestamp")))}. Call before you go.</p></dd>')
    else:
        facts.append('<dt>Hours</dt><dd class="muted">Not listed yet. Own the place? <a href="#claim">Add them.</a></dd>')
    if osm.get("website"):
        site = osm["website"]
        shown = re.sub(r"^https?://(www\.)?", "", site).rstrip("/")
        facts.append(f'<dt>Website</dt><dd><a href="{e(site)}" rel="nofollow noopener" target="_blank">{e(shown)}</a></dd>')
    if osm.get("phone"):
        facts.append(f'<dt>Phone</dt><dd><a href="tel:{e(re.sub(r"[^+0-9]", "", osm["phone"]))}">{e(osm["phone"])}</a></dd>')
    extras = []
    if osm.get("outdoor_seating") == "yes":
        extras.append("outdoor seating")
    if osm.get("takeaway") == "yes":
        extras.append("takeout")
    if osm.get("wheelchair") == "yes":
        extras.append("wheelchair accessible")
    if osm.get("diet_vegetarian") in ("yes", "only"):
        extras.append("vegetarian options")
    if extras:
        facts.append(f'<dt>Noted</dt><dd>{e(", ".join(extras).capitalize())} <span class="small muted">(OpenStreetMap)</span></dd>')
    # the record
    rec = []
    cur = [r for r in p["licence_records"] if r["status"] in ("Active", "About to Expire")]
    if cur:
        for r in sorted(cur, key=lambda r: r["date"]):
            link = f' <a class="src" href="{e(r["url"])}" rel="noopener">record {e(r["record"])}</a>' if r.get("url") else ""
            rec.append(f'<li><span>{e(r["type"])} licence, {e(r["status"].lower())}, issued {e(long_date(r["date"]))}, expires {e(long_date(r["expiration"]))}</span><span class="src">Oklahoma ABLE Commission{link}</span></li>')
        if p.get("licence_first_date") and p["licence_first_date"] < min(r["date"] for r in cur):
            rec.append(f'<li><span>Liquor licence on record at this address under this name since {e(month_year(p["licence_first_date"]))}</span><span class="src">Oklahoma ABLE Commission, records from 1985 on</span></li>')
    elif p["licence_records"]:
        last = max(p["licence_records"], key=lambda r: r["date"])
        rec.append(f'<li><span>No current liquor licence. The last one ({e(last["type"])}) is marked {e(last["status"].lower())}{", expired " + e(long_date(last["expiration"])) if last.get("expiration") and last["status"] == "Expired" else ""}.</span><span class="src">Oklahoma ABLE Commission</span></li>')
    if osdh.get("last_inspection"):
        n = osdh.get("inspections_12mo", 0)
        rec.append(f'<li><span>Health inspection on {e(long_date(osdh["last_inspection"]))}{f", {n} in the last twelve months" if n else ""}. {INSPECTION_NOTE}</span><span class="src"><a href="https://www.phin.state.ok.us/Inspections/" rel="noopener">OSDH inspections</a> (search Cleveland County for the name)</span></li>')
    if osm:
        rec.append(f'<li><span>Mapped on OpenStreetMap, last edited {e(long_date(osm.get("timestamp", "")[:10]))}</span><span class="src"><a href="{e(osm["osm_url"])}" rel="noopener">OpenStreetMap</a></span></li>')
    map_html = (minimap.place_map(p["lat"], p["lon"]) + f'<p class="map-note">{e(p["street_display"])}, Norman. Streets from OpenStreetMap; the pin sits on the address as the US Census Bureau geocoder placed it{" (OpenStreetMap position)" if p.get("geo_source") == "osm" else ""}. <a href="https://www.openstreetmap.org/?mlat={p["lat"]}&amp;mlon={p["lon"]}#map=17/{p["lat"]}/{p["lon"]}" rel="noopener">Open the full map</a>.</p>') if p.get("lat") else \
        '<p class="map-note">No map yet: the address could not be placed by the geocoder. The address above is as the licence or inspection record gives it.</p>'
    aka = f'<p class="muted small">Also on record as {e(", ".join(p["aka"][:3]))}.</p>' if p.get("aka") else ""
    report = (f"mailto:{CONTACT}?subject=" + html.escape(re.sub(r"\s+", "%20", f"Norman Eats: problem with {p['name']}")) +
              "&amp;body=" + html.escape("What's wrong (closed, moved, wrong hours, wrong name)? ".replace(" ", "%20")))
    body = f"""
<div class="place-head">
  <p class="crumbs"><a href="{u('/')}">Norman Eats</a> / <a href="{u('/areas/' + p['area'] + '/')}">{e(p['area_label'])}</a> / <a href="{u('/kind/' + p['category'] + '/')}">{e(p['category_label'])}</a></p>
  <h1>{e(p['name'])}</h1>
  <p class="kind">{kind}</p>
  {aka}
</div>
<div class="place-grid">
  <div class="facts">
    <dl>{''.join(facts)}</dl>
    <section class="record">
      <h2 style="margin-top:0;font-size:20px">On the record</h2>
      <ul>{''.join(rec)}</ul>
      <p class="verified">Checked against these records on {e(long_date(built))}. {'Still open, as far as the record shows.' if p['licensed'] or p.get('inspection_fresh') else ''}
      <a href="{report}">Report a problem</a> (closed, moved, wrong hours).</p>
    </section>
  </div>
  <div>{map_html}</div>
</div>
{claim_block(p)}
<script src="{u('/assets/claim.js')}" defer></script>
"""
    desc = f"{p['name']}, {p['street_display']}, Norman, OK. {p['category_label']}{(': ' + ', '.join(p['cuisines'])) if p['cuisines'] else ''}. From the public record: liquor licence and health inspections."
    return page(f"{p['name']}, {p['street_display']}, Norman OK", body, desc=desc, current="", built=built)


def claim_page(built):
    body = f"<h1>Claim your page</h1><p class='lede'>Norman Eats lists every licensed or inspected restaurant and bar in town from public records. The people who run them know better than any record does.</p>{claim_block(None)}<script src='{u('/assets/claim.js')}' defer></script>"
    return page(f"Claim your restaurant's page, {SITE_NAME}", body, current="claim", built=built)


def about(stats, built, excluded_count):
    body = f"""<h1>About the data</h1>
<p class="lede">Three public sources, joined by address, rebuilt from scratch every time. Nothing here was typed in by hand except the names of the areas.</p>
<h2>Who gets listed</h2>
<p>A place appears when at least one authority says it is operating now: a <b>current liquor licence</b> from the Oklahoma ABLE Commission
(status Active or About to Expire on the day of the build), or a <b>health inspection</b> by the Oklahoma State Department of Health
within the last sixteen months. Places with neither are left out, however well known. A closed restaurant shown as open is the one
mistake this site is built to avoid, so when the record goes quiet, the page goes too.</p>
<p>Left out on purpose: concession operators for university venues, caterers with no dining room, cinemas, car washes and shops that
happen to hold a beer licence, and institutional kitchens (schools, care homes, fraternities). {excluded_count} licence holders were set aside this way.</p>
<h2>What each line means</h2>
<ul>
<li><b>Liquor licence on record since.</b> The earliest licence at this address under this name in the ABLE portal, whose records begin in 1985.
It is when the record starts, not when the doors opened. Legend's has served since 1971; its record starts in 1988.</li>
<li><b>Health inspection on.</b> The latest inspection date in the OSDH database, and how many inspections it lists in the last twelve months.
We print the department's own caution with it: an inspection is a snapshot in time. We do not grade or score anyone.</li>
<li><b>Hours, website, phone, cuisine.</b> From OpenStreetMap, with the date the entry was last edited. Where nobody has mapped them, the page says so.</li>
<li><b>Maps.</b> Drawn from OpenStreetMap street data, with the pin placed by the US Census Bureau's geocoder. Both are free, public and attributed.</li>
</ul>
<h2>Sources and terms</h2>
<ul>
<li><a href="https://oklahoma.gov/able-commission/legal/licensee-search.html" rel="noopener">Oklahoma ABLE Commission licensee search</a>, a public search the Commission offers so anyone can verify a licensed business. Licence records are public records under the Oklahoma Open Records Act.</li>
<li><a href="https://www.phin.state.ok.us/Inspections/" rel="noopener">Oklahoma Food Service Establishment Inspections</a>, published by OSDH. Inspection reports are public documents under OAC 310:258-13-25.</li>
<li><a href="https://www.openstreetmap.org/copyright" rel="noopener">OpenStreetMap</a>, &copy; OpenStreetMap contributors, Open Database License. Positions from the <a href="https://geocoding.geo.census.gov/" rel="noopener">US Census Bureau geocoder</a> (public domain).</li>
<li>Nothing is taken from Google, Yelp or any listing site, and no listing is paid for.</li>
</ul>
<h2>Counts this build</h2>
<div class="counts">
  <div><strong>{stats['places']}</strong>places</div>
  <div><strong>{stats['licensed']}</strong>licensed</div>
  <div><strong>{stats['with_inspection']}</strong>inspected</div>
  <div><strong>{stats['with_osm']}</strong>on OpenStreetMap</div>
  <div><strong>{stats['with_position']}</strong>on the map</div>
</div>
<h2>Fix something</h2>
<p>Run one of these places? <a href="{u('/claim/')}">Claim its page</a>. Spotted a closed place still listed, or a wrong address?
<a href="mailto:{CONTACT}?subject=Norman%20Eats%3A%20a%20correction">Email a correction</a> and say which page. We check the record and change the page, not the other way round.</p>
"""
    return page(f"About the data, {SITE_NAME}", body, current="about", built=built)


def not_found(built):
    body = f"<h1>No page here</h1><p class='lede'>The address you followed doesn't match a page on Norman Eats. Try the <a href='{u('/a-z/')}'>A to Z</a>, or <a href='{u('/')}'>start at the map</a>.</p>"
    return page(f"Page not found, {SITE_NAME}", body, built=built)

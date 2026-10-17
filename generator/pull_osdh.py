"""Crawl the Oklahoma State Department of Health food-service inspection search for Cleveland County,
keep every establishment in NORMAN, and fetch each one's inspection history (dates + violation lines).
Plain WebForms postbacks over HTTPS, no login, no CAPTCHA, ~1 request/second, identified User-Agent.
Source: https://www.phin.state.ok.us/Inspections/  (OAC 310:258-13-25: inspection reports are public documents)."""
import requests, re, html, time, json, sys, os, datetime
UA = "norman-eats-directory-build/0.1 (Station; stationonemain@gmail.com)"
BASE = "https://www.phin.state.ok.us/Inspections/"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "osdh_norman.json")
LOG = os.path.join(os.path.dirname(__file__), "..", "data", "work", "osdh_pull.log")
COUNTY = "14"  # Cleveland
PAUSE = 1.0
def log(s):
    line = f"{datetime.datetime.now():%H:%M:%S} {s}"; print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f: f.write(line + "\n")
def hidden(h): return dict(re.findall(r'<input type="hidden" name="(__[A-Z]+)" id="__[A-Z]+" value="([^"]*)"', h))
def strip(x): return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", x))).strip()
def rows_of(h):
    out = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", h, re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) != 6: continue
        cells = [strip(c) for c in tds]
        m = re.search(r"__doPostBack\(&#39;(dgRestaurants\$ctl\d+\$lbDetails)&#39;", tr)
        if cells[5] == "Details" and m:
            out.append({"name": cells[0], "address": cells[1], "city": cells[2], "zip": cells[3], "county": cells[4], "target": m.group(1)})
    return out
def pager_targets(h):
    # the pager row: numbers are links except the current page (plain text); '...' links move to the next/previous block
    seg = re.search(r"<tr[^>]*>((?:(?!</tr>).)*dgRestaurants\$ctl\d+\$ctl\d+(?:(?!</tr>).)*)</tr>", h, re.S)
    if not seg: return [], None
    s = seg.group(1)
    items = re.findall(r"(?:<a[^>]*__doPostBack\(&#39;([^&]+)&#39;[^>]*>\s*([^<]+?)\s*</a>|<span[^>]*>\s*(\d+)\s*</span>)", s)
    links = [(t.strip(), lab.strip()) for t, lab, cur in items if t]
    cur = next((c for t, lab, c in items if c), None)
    return links, cur
def parse_detail(h):
    txt = strip(h.replace("<", " <"))
    # Inspection blocks: "Inspection Date: m/d/yyyy" followed by violation lines until the next date
    parts = re.split(r"Inspection Date:\s*", txt)
    insp = []
    for p in parts[1:]:
        m = re.match(r"(\d{1,2}/\d{1,2}/\d{4})(.*)", p)
        if not m: continue
        body = m.group(2)
        body = re.split(r"\*Highlighted items are violations", body)[0]
        lines = [l.strip(" |") for l in re.split(r"\s\|\s", body) if l.strip(" |")]
        lines = [l for l in lines if l and l not in ("Violations", "Notes") and not re.match(r"^[\W_]+$", l)]
        insp.append({"date": datetime.datetime.strptime(m.group(1), "%m/%d/%Y").date().isoformat(), "violations": lines})
    return insp
def main():
    s = requests.Session(); s.headers["User-Agent"] = UA
    h = s.get(BASE, timeout=60).text
    f = hidden(h); f.update({"cmbCounties": COUNTY, "txtSearch": "", "cmdSearch": "Find"})
    time.sleep(PAUSE); h = s.post(BASE, data=f, timeout=120).text
    seen_pages, all_rows, page_no = set(), [], 1
    details = {}
    while True:
        rows = rows_of(h)
        log(f"page {page_no}: {len(rows)} rows")
        page_vs = hidden(h)
        for r in rows:
            r["page"] = page_no
            all_rows.append(r)
            if r["city"].upper() != "NORMAN": continue
            key = f"{r['name']}|{r['address']}"
            if key in details: continue
            fd = dict(page_vs); fd.update({"__EVENTTARGET": r["target"], "__EVENTARGUMENT": "", "cmbCounties": COUNTY, "txtSearch": ""})
            for attempt in (1, 2, 3):
                try:
                    time.sleep(PAUSE); hd = s.post(BASE, data=fd, timeout=120).text
                    if r["name"].split(" ")[0] not in hd.upper() and "Inspection Date" not in hd:
                        raise RuntimeError("detail page did not render")
                    details[key] = {"name": r["name"], "address": r["address"], "city": r["city"], "zip": r["zip"], "inspections": parse_detail(hd)}
                    break
                except Exception as e:
                    log(f"  detail {key}: attempt {attempt} {type(e).__name__} {str(e)[:80]}"); time.sleep(5)
        links, cur = pager_targets(h)
        seen_pages.add(cur or str(page_no))
        nxt = None
        # prefer the next numbered page; else the trailing '...' link
        nums = [(t, int(l)) for t, l in links if l.isdigit()]
        bigger = sorted([(n, t) for t, n in nums if n == page_no + 1])
        if bigger: nxt = bigger[0][1]
        else:
            # the trailing '...' moves to the next block of ten; a leading '...' (the only one on the LAST block)
            # moves BACK, which once sent this crawler round in circles until its page cap
            dots = [(i, t) for i, (t, l) in enumerate(links) if "..." in l]
            if dots and nums and dots[-1][0] > max(i for i, (t, l) in enumerate(links) if l.isdigit()):
                nxt = dots[-1][1]
        if not nxt: break
        fd = dict(page_vs); fd.update({"__EVENTTARGET": nxt, "__EVENTARGUMENT": "", "cmbCounties": COUNTY, "txtSearch": ""})
        time.sleep(PAUSE); h = s.post(BASE, data=fd, timeout=120).text
        page_no += 1
        if page_no > 400: break
    norman = [r for r in all_rows if r["city"].upper() == "NORMAN"]
    log(f"done: {len(all_rows)} Cleveland County rows, {len(norman)} Norman, {len(details)} details")
    json.dump({"pulled_at": datetime.datetime.now().isoformat(timespec="seconds"), "source": BASE, "county": "Cleveland",
               "list": all_rows, "norman": list(details.values())}, open(OUT, "w", encoding="utf-8"), indent=1)
if __name__ == "__main__": main()

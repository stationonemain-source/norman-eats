"""Pull every ABLE licence record with a Norman address, per venue licence type, from the public Accela portal.
Headless pinned Playwright Chromium (never the everyday Chrome). Output: one JSON per type + a log."""
import os, json, sys, time, datetime
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
HOME = os.path.expanduser("~")
PW = os.path.join(HOME, "AppData", "Local", "ms-playwright", "chromium-1228", "chrome-win64", "chrome.exe")
URL = "https://aca-prod.accela.com/ABLE/Cap/CapHome.aspx?module=ABC&TabName=ABC"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
P = "#ctl00_PlaceHolderMain_generalSearchForm_"
TYPES = [
    "ABC/LBD/Mixed Beverage/License",
    "ABC/LBD/Mixed Beverage Combination/License",
    "ABC/LBD/Beer and Wine/License",
    "ABC/LBD/Mixed Beverage Fraternal/License",
    "ABC/LBD/Hotel/License",
    "ABC/Distributors Wholesalers/Brew Pub/License",
    "ABC/Distributors Wholesalers/Small Brewer/License",
    "ABC/Distributors Wholesalers/Small Farm Winery/License",
    "ABC/Distributors Wholesalers/Distiller/License",
    "ABC/LBD/Caterer/License",
]
CITY = sys.argv[1] if len(sys.argv) > 1 else "Norman"
ROW_JS = r"""
() => {
  const hdrRow = document.querySelector('tr[class*="ACA_TabRow_Header"], tr[class*="TabRow_Header"]');
  const headers = hdrRow ? [...hdrRow.querySelectorAll('th,td')].map(c => c.innerText.replace(/\s+/g,' ').trim().toLowerCase()) : [];
  const find = (re) => headers.findIndex(h => re.test(h));
  const iDate = find(/^date/), iRec = find(/record number|record #|^record$|license number/), iType = find(/record type|license type/),
        iName = find(/dba|trade name|business name|^name|applicant/), iStatus = find(/^status/),
        iExp = find(/expir/), iAddr = find(/address/);
  const out = [];
  for (const tr of document.querySelectorAll('tr[class*="ACA_TabRow"]')) {
    if (/Header/i.test(tr.className)) continue;
    const cells = [...tr.querySelectorAll('td')].map(td => td.innerText.replace(/\s+/g,' ').trim());
    if (cells.filter(Boolean).length < 3) continue;
    const pick = (i) => (i >= 0 && i < cells.length ? cells[i] : '') || '';
    let address = pick(iAddr);
    if (!address) { const m = cells.filter(c => /\b[A-Z]{2}\s+\d{5}\b/.test(c) || /\b\d{5}\b/.test(c)); address = m.length ? m[m.length-1] : ''; }
    const a = tr.querySelector('a[href*="CapDetail"]');
    out.push({ date: pick(iDate), record: pick(iRec), type: pick(iType), name: pick(iName), status: pick(iStatus),
               expiration: pick(iExp), address, href: a ? a.getAttribute('href') : null, raw: cells });
  }
  return { headers, rows: out };
}"""
PAGER_JS = r"""
() => {
  const t = document.querySelector('table.aca_pagination');
  if (!t) return { has_next: false, current: null, text: '' };
  const links = [...t.querySelectorAll('a')].filter(a => a.innerText.trim());
  const next = links.find(a => /^Next/.test(a.innerText.trim()));
  const cur = t.querySelector('.SelectedPageButton');
  return { has_next: !!next, current: cur ? cur.innerText.trim() : null, text: t.innerText.replace(/\s+/g,' ').slice(0,200) };
}"""
MSG_JS = r"""
() => {
  const root = document.querySelector('#ctl00_PlaceHolderMain') || document.body;
  const m = root.innerText.match(/Showing [^\n|]*/);
  const e = document.querySelector('.ACA_Label_Error, [id*="lblMsg"], [id*="lblNoRecord"]');
  return (m ? m[0].trim() : '') + (e && e.innerText.trim() ? ' | ' + e.innerText.trim().slice(0,160) : '');
}"""
def log(s):
    line = f"{datetime.datetime.now():%H:%M:%S} {s}"
    print(line, flush=True)
    with open("pull.log", "a", encoding="utf-8") as f: f.write(line + "\n")

def settle(page, ms):
    page.wait_for_timeout(ms)
    try: page.wait_for_load_state("networkidle", timeout=30000)
    except PWTimeout: pass

today = datetime.date.today().strftime("%m/%d/%Y")
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=PW, headless=True)
    pg = b.new_page(user_agent=UA, viewport={"width": 1400, "height": 1000})
    pg.set_default_timeout(60000)
    for tv in TYPES:
        slug = tv.split("/")[-2].replace(" ", "_").lower()
        outpath = f"norman_{slug}.json"
        if os.path.exists(outpath):
            log(f"skip {tv} (exists)"); continue
        rows_all, ok = [], False
        for attempt in (1, 2, 3):
            try:
                pg.goto(URL, wait_until="networkidle", timeout=90000)
                pg.select_option(P + "ddlGSPermitType", value=tv)
                settle(pg, 1200)
                if pg.input_value(P + "ddlGSPermitType") != tv:
                    log(f"{tv}: type did not stick, retry"); continue
                pg.fill(P + "txtGSCity", CITY)
                pg.evaluate("""([s, e]) => { const p='ctl00_PlaceHolderMain_generalSearchForm_';
                    document.getElementById(p+'txtGSStartDate').value = s;
                    document.getElementById(p+'txtGSEndDate').value = e; }""", ["01/01/1980", today])
                pg.click("#ctl00_PlaceHolderMain_btnNewSearch", timeout=20000)
                settle(pg, 6000)
                msg = pg.evaluate(MSG_JS)
                log(f"{tv}: {msg or 'no result banner'}")
                pages = 0
                while True:
                    pages += 1
                    got = pg.evaluate(ROW_JS)
                    if pages == 1: log(f"  headers={got['headers']}")
                    rows_all.extend(got["rows"])
                    pager = pg.evaluate(PAGER_JS)
                    if not pager["has_next"] or pages > 400: break
                    pg.locator("table.aca_pagination a", has_text="Next").first.click()
                    settle(pg, 3500)
                if not rows_all and "correct format" in pg.content():
                    log(f"{tv}: portal error shell, retry"); rows_all = []; continue
                ok = True
                log(f"{tv}: {len(rows_all)} rows over {pages} pages")
                break
            except Exception as e:
                log(f"{tv}: attempt {attempt} {type(e).__name__}: {str(e)[:160]}")
                time.sleep(4)
        json.dump({"type": tv, "city": CITY, "pulled_at": datetime.datetime.now().isoformat(timespec='seconds'),
                   "ok": ok, "rows": rows_all}, open(outpath, "w", encoding="utf-8"), indent=1)
        time.sleep(2)
    b.close()
log("DONE")

# Norman Eats

A static directory of every restaurant and bar in Norman, Oklahoma, built from public records only, with a
"Claim this page" path that becomes a lead for Station. No runtime services, no LLM calls, no paid data.

Read `STATE.md` first. It is the HEAD for this system.

## How it is built

```
python generator/pull_able.py          # Oklahoma ABLE licence records for Norman (headless pinned Chromium)
python generator/pull_osdh.py          # OSDH food-service inspections, Cleveland County -> Norman (plain HTTP, 1 req/s)
# OpenStreetMap POIs, roads and the city boundary come from one-off Overpass queries (see generator/fetch_osm.py)
python generator/build.py --data       # join, geocode (US Census), classify, render docs/
```

`docs/` is what GitHub Pages serves. Everything in `data/work/` is derived and safe to delete.

Environment switches: `NE_BASE` (default `/norman-eats`, the Pages project path; set to `""` for a custom domain),
`NE_PUBLIC=1` to drop the `noindex` tag and publish `robots.txt` + `sitemap.xml`.

## Sources and licences

| Source | What we take | Terms |
|---|---|---|
| Oklahoma ABLE Commission, public licensee search (Accela) | licence type, status, dates, trade name, address | public search offered by the Commission; public records (Oklahoma Open Records Act) |
| Oklahoma State Department of Health, food-service inspections | establishment, inspection dates, violation lines (dates only are shown) | public documents (OAC 310:258-13-25) |
| OpenStreetMap (Overpass) | names, cuisine, hours, website, phone, positions, roads, boundary | ODbL, attributed on every page and inside every map |
| US Census Bureau geocoder | coordinates for addresses | public domain |

Never used: Google Places (its content may not be stored), Yelp, any listing site, anything behind a login.

Fonts: Fraunces and Archivo, SIL Open Font License, in `site/assets/fonts/`.

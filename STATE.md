# Norman Eats, HEAD

**Read this first. Update it last.** What this is, where it runs, what is true today, and what Circle has not decided yet.

## What it is

An unlisted consumer directory of every restaurant and bar in Norman, Oklahoma, built from public records only, with
"Is this your restaurant? Claim this page." on every place page. A claim is a lead into Station (the n8n Range relay,
`/webhook/range-lead`, which Circle's command center pulls). No runtime services, no LLM, no paid data, $0 to run.

- Live (unlisted): https://stationonemain-source.github.io/norman-eats/ (GitHub Pages, `main` branch, `/docs`)
- Repo: https://github.com/stationonemain-source/norman-eats (public; the data is public record)
- Built 2026-10-17 by a Station session from the PC. Nothing is scheduled; a rebuild is a person running the generator.

## Status 2026-10-17 (first build)

| | |
|---|---|
| Places listed | **416** |
| With a current ABLE liquor licence | 142 |
| With a health inspection on file (16-month window) | 404 |
| Matched to OpenStreetMap (hours, website, phone, cuisine) | 179 |
| On the map (US Census geocoder, Nominatim fallback) | 413 |
| Set aside with a reason (`data/work/excluded.json`) | 23 licence holders |
| Health-department kitchens with no food signal, not listed (`data/work/unsorted.json`) | 54 |
| Pages generated | 490 |

Sources this build: ABLE portal searched by City = Norman for 10 venue licence types (519 rows, 164 current, folded to
439 all-time places); OSDH Cleveland County search, 895 Norman establishments with inspection history; OSM Overpass
(280 POIs, roads, city boundary) as of 2026-10-17 18:52 UTC.

**Unlisted means:** `<meta name="robots" content="noindex, nofollow">` on every page, `robots.txt` Disallow all, no
sitemap, linked from nowhere. Flip with `NE_PUBLIC=1` at build time.

## Who gets listed (the rule that avoids "closed shown as open")

A place appears only if an authority says it operates now: ABLE licence status Active or About to Expire on build day,
or an OSDH inspection within 480 days. Both come from the record, never from a listing site. OSM alone never lists a
place (96 OSM-only names were left out). Health-department kitchens are listed only when the name carries a food
signal and the address is a storefront (no room numbers, no stadium/campus/hospital addresses, no Greek houses,
no stores, no dispensaries, no "nutrition" supplement shops).

## The 20-place hand check (2026-10-17, web search against each place's own site or current listings)

Deterministic sample: every 22nd place in slug order from the first full build.

| # | Place | Finding |
|---|---|---|
| 1 | 1942 Tacos & Tequila | confirmed at 2164 24th Ave NW (active on delivery apps) |
| 2 | Bedrock Cafe, 1406 Asp Ave Rm 207a | nothing online; a counter inside an OU building. **Removed** (room-number rule) |
| 3 | Buffalo Wild Wings | confirmed |
| 4 | Chipotle, 765 Asp Ave | confirmed |
| 5 | Del Taco, 110 12th Ave NE | confirmed (opened 2017, still listed for delivery) |
| 6 | El Huevo Mexi Diner | confirmed |
| 7 | Gallion Sports Nutrition | open at the address, but a supplement store with a shake bar. **Removed** (nutrition rule) |
| 8 | Hebrews 11:6, 1321 E Lindsey | nothing online. **Removed** (no food signal in the name) |
| 9 | Jersey Mike's, 1204 N Interstate | confirmed |
| 10 | Lazy Circles Brewing | confirmed (sponsored Brewtoberfest, 3 Oct 2026) |
| 11 | Marco's Pizza, 1004 24th Ave NW | confirmed |
| 12 | Mr. Gatti's Pizza, 333 N Interstate Dr | operating, but it is the counter inside Walmart at that address |
| 13 | P.F. Chang's | confirmed (opened April 2026) |
| 14 | Porch, 311 W Boyd | confirmed as a Campus Corner bar; address is the licence's |
| 15 | Rosa Mezcal | confirmed |
| 16 | Sky European Gourmet, 211 34th Ave SW | no web presence found; inspected 27 Mar 2026. Listed, flagged |
| 17 | Starbucks, 1200 W Lindsey | confirmed (standalone drive-thru) |
| 18 | Taco Bell, 1101 12th Ave NE | confirmed |
| 19 | Torchy's Tacos | confirmed |
| 20 | Wendy's, 3351 W Tecumseh | web search did not confirm; OSDH and OSM both carry it. Listed, flagged |

Result: **16 of 20 confirmed open at the address; none found closed.** 3 were removed from the directory by rules
added after the check (they were not restaurants), 1 is a counter inside a store. Of the 17 that remain listed, 15
are confirmed by an outside source and 2 rest on the public record alone.

## How to rebuild

```
python generator/pull_able.py      # ABLE, headless pinned Playwright Chromium (never the everyday Chrome), ~6 min
python generator/pull_osdh.py      # OSDH Cleveland County -> Norman, plain HTTP 1 req/s, ~25 min
python generator/build.py --data   # join + Census geocode (cached) + render docs/
git add -A && git commit -- . && git push
```
OSM data is a one-off Overpass pull kept in `data/raw/` (the public API was at capacity twice; mirrors in
`generator/fetch_osm.py` are not committed, see the scratch script in the session). Refresh it rarely and politely.

## Claim form, verified by dry run (nothing sent)

`site/assets/claim.js` posts one JSON lead to the Range relay the way station.solutions does (sendBeacon, text/plain,
fetch no-cors fallback). Payload: name, email, phone, website, business, address, industry ("<kind> / Norman Eats page
claim (<role>)"), leak (the note), variant `norman-eats-claim`, ref `norman-eats`, path, sid, and `source=norman-eats`.
The relay (n8n `ESAggDPVu6JIfgIb`, Store Lead) keeps every field except `source`; `ref` and `variant` carry the tag.
In Circle it lands as a website lead: bell "Free audit requested - <business>" (that title is Circle's wording for all
website leads; a claim-aware title is a one-line change in station-world), Contacts > Leads, pipeline card. No email
goes to anyone; the claimant sees "a person at Station will reply" and a mailto fallback.

## Not done / Circle decides before it goes public

1. **Name and domain.** "Norman Eats" is the repo name, not a checked brand; the public name, domain and whether this
   is a Station brand or its own are open. `NE_BASE=""` once a domain is attached.
2. **Indexing.** Flip `NE_PUBLIC=1`, rebuild, and the sitemap + robots change. Nothing links to it today.
3. **Inspection data.** Pages show the latest inspection date and the count in the last twelve months, with OSDH's own
   caution, and link to the OSDH search. Violation lines are in `data/raw` and are not shown. Show more, less, or none.
4. **The claim promise.** Every place page says a person will reply. Someone must work the `norman-eats-claim` leads.
5. **Fonts.** Fraunces + Archivo (OFL, self-hosted) were chosen for this build, not by Circle.
6. **Hotel bars, lounges, entertainment venues** are listed as their own kinds; keep or cut.
7. **The 54 unsorted kitchens and 96 unmatched OSM names** may hide real restaurants; a person could pass over them.
8. **Overrides.** Claims will need `data/overrides.json` (hours, website, menu, verified flag) wired into the build.
   Not written yet; the pages already promise those corrections, so this is the next piece of code.

# Norman Eats, design contract

A local directory should feel like it was made in the town it lists: a small newspaper's food page, a menu board with
dotted leaders, a map drawn by hand. Not a SaaS template.

## 1. Brand facts
- Working name **Norman Eats** (the repo name; the public name and domain are Circle's call).
- Voice: plain, local, factual. We say where a fact came from. We never invent hours, menus or history.
- One promise in the copy: "built from the public record, corrected by the people who run the places".

## 2. Palette (warm paper, ink, one crimson)
```css
:root {
  --paper: #F6F1E7;     /* page */
  --paper-2: #EDE4D2;   /* bands, table stripes */
  --paper-3: #E2D7C1;   /* map ground, deep band */
  --ink: #1E1B16;       /* text */
  --ink-2: #514A3F;     /* secondary text, 7.4:1 on paper */
  --rule: #CFC3AB;      /* hairlines */
  --accent: #8C1D2B;    /* Norman crimson-brick: links on paper, the pin, the claim button. <= 2 uses a screen */
  --accent-ink: #6B1420;
  --water: #BCD2DA; --green: #D8DFC6; --road: #3B3630; --road-minor: #857B6C;
}
```
Neutrals carry ~90% of the pixels. The crimson appears at most twice per screen: the pin and the claim button,
or a link and a button. No gradients, no shadows beyond a 1px rule, no rounded "tile" cards.

## 3. Type (two faces, self-hosted, OFL)
- **Fraunces** (variable: opsz, wght, SOFT, WONK) for the masthead and headings. Masthead at `WONK 1, SOFT 60`
  so the swashy alternates show; headings at `SOFT 30`. Tracking -0.02em above 32px.
- **Archivo** (variable: wdth, wght) for everything else. Body 17px/1.55 at width 100; small labels in caps at
  width 88, letter-spacing 0.08em, 12.5px.
- Scale: 12.5 / 14 / 17 / 20 / 26 / 34 / 52 (masthead). Weights 400 / 500 / 600 only.

## 4. Layout
- Max text measure 68ch. Page width 1080px, 16px gutters on phones, 32px from 720px up.
- Lists are **menu boards**: name, dotted leader, street, and a right-aligned fact (since year, or category).
  On phones the leader row stacks and the dots go away.
- Place pages: two columns from 820px (facts left, map right), one column below.
- Hairlines (`1px solid var(--rule)`) separate sections; no boxes-in-boxes.

## 5. The map
Inline SVG drawn by the generator from OpenStreetMap ways: paper ground, ink roads with a paper casing, labelled
arterials, a crimson pin. The city overview on the home page is the Norman outline with one dot per place.
Attribution "© OpenStreetMap contributors" is printed inside every map.

## 6. Motion
None beyond `:hover` underline and the claim button's 1px press. No scroll effects.

## 7. Copy rules
No em-dashes on the page. No "Discover"/"Elevate"/"Explore the best of". No star ratings, no "top 10".
Every number on a page comes from a record we link to. Unknown is written as unknown ("Hours not listed yet").

## 8. Accessibility
Body contrast ≥ 7:1, labels ≥ 4.5:1. Every map has a text alternative (the address). Focus rings visible
(2px ink outline). Forms label every field; the honeypot is `aria-hidden` and off-screen.

## 9. What marks it as ours
The masthead's wonky Fraunces, the dotted leaders, the hand-feel maps, and the footer line
"Designed & hosted by Station.Solutions" on every page.

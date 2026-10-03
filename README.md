# Course Clock

Free triathlon calculators (finish time, fueling, sweat rate) plus course-specific race planner pages.

## How the site is built

The pages are generated, not hand-written. Edit the sources, never the built HTML.

| File | What it controls |
|---|---|
| `races.py` | Every race: dates, distances, climbing, course notes, cutoffs |
| `build.py` | Page templates, race list, date logic, default inputs, the `DOMAIN` setting |
| `src/style.css` | All styling for every page |
| `src/app.js` | All calculator math |
| `src/favicon.svg` | Browser tab icon |

Netlify runs `python3 build.py` on every push and publishes `dist/site/` (see `netlify.toml`).

To build locally: `python3 build.py`, then open `dist/site/index.html`.

## Adding or updating a race

Each race is one `race(...)` call in `races.py`:

```python
race("ironman-70-3-example", "IRONMAN 70.3 Example", "City", "ST", "half",
     "2026-06-07",      # 2026 date, or None
     "2027-06-06",      # 2027 date, or None until announced
     "Swim notes", "Bike notes", "Run notes",
     bikeGainFt=1800,   # only if a source gives it, otherwise leave it out
     swimFactor=0.9,    # only for current-assisted swims
     weather="Optional race notes")
```

- Distances default to 1.2/56/13.1 (`half`) or 2.4/112/26.2 (`full`). Override with `swimMi=` when a course differs.
- Cutoffs default to the standard IRONMAN limits with a note saying so. Override with `cutoffs=` and `cutoffNote=` when a guide differs.
- Unknown climbing: leave `bikeGainFt` and `runGainFt` out. Add `bikeTerrain="Flat"` etc. only when a source describes it.
- The page decides what date to show at build time: an upcoming 2026 race first, then the 2027 date, then "2027 date not yet announced".

Only publish facts that can be traced to a source. If a cutoff comes from an older athlete guide, say so in `cutoffNote`.

## When IRONMAN releases the 2027 calendar

1. Fill in `d2027` for every race that has a date.
2. Remove races that were dropped; add new ones.
3. Re-check courses that changed.
4. Push. Netlify rebuilds every page.

## Course adjustment model

When adjustments are on: swim time x `swimFactor`; bike time x (1 + 0.002 x feet of climbing per mile); run time x (1 + 0.001 x feet of climbing per mile). Rough rules of thumb, worth calibrating against real splits.

## Domain

Set `DOMAIN` in `build.py` (e.g. `"https://courseclock.com"`). That turns on canonical tags, the sitemap, and the sitemap line in robots.txt.

## Open items

- Confirm IRONMAN Chattanooga 2026 cutoffs against the athlete guide (currently from older guides, labeled on the page).

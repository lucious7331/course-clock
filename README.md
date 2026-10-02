# Course Clock

Free triathlon calculators (finish time, fueling, sweat rate) plus course-specific race planner pages.

## How the site is built

The pages are generated, not hand-written. Edit the sources, never the built HTML.

| File | What it controls |
|---|---|
| `build.py` | Page templates, race data (`RACES` list), default inputs, the `DOMAIN` setting |
| `src/style.css` | All styling for every page |
| `src/app.js` | All calculator math |
| `src/favicon.svg` | Browser tab icon |

Netlify runs `python3 build.py` on every push and publishes `dist/site/` (see `netlify.toml`).

To build locally: `python3 build.py`, then open `dist/site/index.html`.

## Adding a race

Add one entry to the `RACES` list in `build.py`. Fields:

- `slug`: URL name, e.g. `ironman-lake-placid`
- `dist`: `half` or `full` (sets default paces)
- `swimMi`, `bikeMi`, `runMi`: course distances in miles
- `bikeGainFt`, `runGainFt`: climbing in feet, or `None` if flat or unknown
- `swimFactor`: `0.9` for a current-assisted swim, otherwise `1`
- `cutoffs`: seconds from the athlete's own start for `swim`, `bike` (swim + T1 + bike) and `total`; `None` if unknown
- `cutoffNote`: plain statement of where the cutoffs came from
- `legs`: short Swim, Bike, Run descriptions
- `title`, `desc`: search result title and description

Only publish facts that can be traced to a source. If a cutoff comes from an older athlete guide, say so in `cutoffNote`.

## Course adjustment model

When adjustments are on: swim time x `swimFactor`; bike time x (1 + 0.002 x feet of climbing per mile); run time x (1 + 0.001 x feet of climbing per mile). Rough rules of thumb, worth calibrating against real splits.

## Domain

Set `DOMAIN` in `build.py` (e.g. `"https://courseclock.com"`). That turns on canonical tags, the sitemap, and the sitemap line in robots.txt.

## Open items

- Confirm IRONMAN Chattanooga 2026 cutoffs against the athlete guide (currently from older guides, labeled on the page).

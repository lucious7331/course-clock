"""Build the Course Clock static site.

Outputs:
  dist/site/      full static site for Netlify or Vercel (drag the folder in)
  dist/preview/   same site, index body without the document wrapper, for the Claude artifact preview
"""
import json, os, shutil, html, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
OUT = os.path.join(ROOT, "dist")
SITE_NAME = "Course Clock"
# Set this once you buy a domain, e.g. "https://courseclock.com". Leave empty until then.
DOMAIN = ""
FONTS = ("https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700"
         "&family=IBM+Plex+Mono:wght@400;500;600&family=Source+Sans+3:wght@400;600;700&display=swap")

from races import RACES

TODAY = datetime.date.today()
MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"]


DEFAULTS = {
    "full": {"swim": "2:00", "mph": "18", "run": "10:30", "t1": "8", "t2": "5", "start": "07:00", "carbBike": 80, "carbRun": 60},
    "half": {"swim": "1:55", "mph": "19", "run": "9:30", "t1": "5", "t2": "3", "start": "07:00", "carbBike": 75, "carbRun": 60},
}


def head(title, desc, css, prefix="", path=""):
    canon = f'<link rel="canonical" href="{DOMAIN}/{path}">\n<meta property="og:url" content="{DOMAIN}/{path}">\n' if DOMAIN else ""
    return f"""<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta name="twitter:card" content="summary">
<meta name="theme-color" content="#0a6c8f">
<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
{canon}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{prefix}assets/style.css">
"""


def topbar(prefix):
    return f"""<header class="topbar"><div class="wrap">
<a class="brand" href="{prefix}index.html">Course<span>/</span>Clock</a>
<nav aria-label="Main">
<a href="{prefix}index.html#predictor">Finish time</a>
<a href="{prefix}index.html#fueling">Fueling</a>
<a href="{prefix}index.html#sweat">Sweat rate</a>
<a href="{prefix}races/index.html">Races</a>
</nav></div></header>"""


def footer():
    return f"""<footer><div class="wrap">
<p>{SITE_NAME} gives estimates for training and planning. Race organizers publish the official course, cutoffs and rules in each year's athlete guide, and those always win.</p>
<p>IRONMAN and 70.3 are trademarks of World Triathlon Corporation. {SITE_NAME} is an independent site and is not affiliated with or endorsed by IRONMAN.</p>
</div></footer>"""


def predictor(d, race):
    dist_field = ""
    if race is None:
        dist_field = """<div class="field"><label for="dist">Race distance</label>
<select id="dist"><option value="sprint">Sprint</option><option value="olympic">Olympic</option>
<option value="half" selected>70.3 (half)</option><option value="full">140.6 (full)</option></select></div>"""
    adj = ""
    if race is not None:
        adj = """<label class="toggle" for="adjust"><input type="checkbox" id="adjust" checked>
<span>Apply course adjustments for current and climbing. Turn off to see flat course times.</span></label>"""
    return f"""<div class="panel" data-calc="predict" id="predictor">
<div class="panel-head"><h2>Finish time predictor</h2>
<p>Enter the paces you can hold on race day, not your best training day. Splits update as you type.</p></div>
<div class="fields">
{dist_field}
<div class="field"><label for="swimPace">Swim pace per 100 (m:ss)</label><input id="swimPace" value="{d['swim']}" inputmode="numeric" placeholder="1:55"></div>
<div class="field"><label for="swimUnit">Pool unit</label><select id="swimUnit"><option value="yd">Yards</option><option value="m">Meters</option></select></div>
<div class="field"><label for="bikeMph">Bike speed (mph)</label><input id="bikeMph" type="number" step="0.1" min="5" value="{d['mph']}"></div>
<div class="field"><label for="runPace">Run pace per mile (m:ss)</label><input id="runPace" value="{d['run']}" inputmode="numeric" placeholder="9:30"></div>
<div class="field"><label for="t1">T1 (min)</label><input id="t1" type="number" min="0" step="0.5" value="{d['t1']}"></div>
<div class="field"><label for="t2">T2 (min)</label><input id="t2" type="number" min="0" step="0.5" value="{d['t2']}"></div>
<div class="field"><label for="start">Your start time</label><input id="start" type="time" value="{d['start']}"></div>
</div>
{adj}
<div class="result">
<div class="big" id="total">--</div>
<div class="pills" id="cutoffPills"></div>
<div class="table-wrap"><table class="splits"><thead><tr><th>Leg</th><th>Distance</th><th>Split</th><th>Elapsed</th><th>Clock</th></tr></thead><tbody id="splits"></tbody></table></div>
<p class="note" id="adjNote"></p>
</div></div>"""


def fueling(d):
    return f"""<div class="panel" data-calc="fuel" id="fueling">
<div class="panel-head"><h2>Fueling planner</h2>
<p>Uses your predicted bike and run times. Many long course athletes target 60 to 90 g of carbs per hour, built up in training.</p></div>
<div class="fields">
<div class="field"><label for="carbBike">Bike carbs (g/hr)</label><input id="carbBike" type="number" min="0" value="{d['carbBike']}"></div>
<div class="field"><label for="carbRun">Run carbs (g/hr)</label><input id="carbRun" type="number" min="0" value="{d['carbRun']}"></div>
<div class="field"><label for="bottlesPerHr">Bottles per hour</label><input id="bottlesPerHr" type="number" min="0" step="0.25" value="1"></div>
<div class="field"><label for="carbPerBottle">Carbs per bottle (g)</label><input id="carbPerBottle" type="number" min="0" value="60"></div>
<div class="field"><label for="gelCarb">Carbs per gel (g)</label><input id="gelCarb" type="number" min="1" value="25"></div>
<div class="field"><label for="sodium">Sodium (mg/hr)</label><input id="sodium" type="number" min="0" step="50" value="600"></div>
</div>
<div class="result" id="fuelOut"></div>
</div>"""


def sweat():
    return """<div class="panel" data-calc="sweat" id="sweat">
<div class="panel-head"><h2>Sweat rate calculator</h2>
<p>Weigh yourself nude before and after a training session of at least an hour, then fill this in. Example numbers are loaded.</p></div>
<div class="fields">
<div class="field"><label for="sweatUnit">Units</label><select id="sweatUnit"><option value="imperial">lb and oz</option><option value="metric">kg and ml</option></select></div>
<div class="field"><label for="preWt" data-unit-w="Weight before ({u})">Weight before (lb)</label><input id="preWt" type="number" step="0.1" value="170"></div>
<div class="field"><label for="postWt" data-unit-w="Weight after ({u})">Weight after (lb)</label><input id="postWt" type="number" step="0.1" value="167.6"></div>
<div class="field"><label for="drank" data-unit-v="Fluid drunk ({u})">Fluid drunk (oz)</label><input id="drank" type="number" min="0" value="24"></div>
<div class="field"><label for="urine" data-unit-v="Urine, if any ({u})">Urine, if any (oz)</label><input id="urine" type="number" min="0" value="0"></div>
<div class="field"><label for="sweatMin">Session length (min)</label><input id="sweatMin" type="number" min="1" value="90"></div>
</div>
<div class="result" id="sweatOut"></div>
</div>"""


def _d(iso):
    return datetime.date.fromisoformat(iso) if iso else None


def fmt_date(d, short=False):
    m = MONTHS[d.month - 1]
    return f"{m[:3] if short else m} {d.day}, {d.year}"


def sort_key(r):
    """Order races through the season by their next or most recent date."""
    d = _d(r["d2027"]) or _d(r["d2026"])
    return (d.month, d.day, r["name"]) if d else (13, 0, r["name"])


def when_parts(r):
    """(headline, detail) describing when the race happens, from today's point of view."""
    d26, d27 = _d(r["d2026"]), _d(r["d2027"])
    if d26 and d26 >= TODAY:
        detail = f"2027: {fmt_date(d27)}" if d27 else "2027 date not yet announced"
        return f"Next race {fmt_date(d26)}", detail
    if d27:
        label = r.get("d2027_label") or fmt_date(d27)
        return label, "2027 date confirmed"
    return "2027 date not yet announced", f"2026 race was {fmt_date(d26)}"


def list_date(r):
    d26, d27 = _d(r["d2026"]), _d(r["d2027"])
    if d26 and d26 >= TODAY:
        return fmt_date(d26, True), ""
    if d27:
        return (r.get("d2027_label") or fmt_date(d27, True)), ""
    return f"Usually {MONTHS[d26.month - 1][:3]}", "tba"


def climb(gain, terrain):
    if gain:
        return f"{gain:,} ft climbing"
    return terrain or "Climbing not listed"


def race_bib(r):
    total = r["cutoffs"]["total"]
    head_, detail = when_parts(r)
    return f"""<div class="bib" aria-label="Course summary">
<div><span class="k">Swim</span><span class="v">{r['swimMi']} mi</span></div>
<div><span class="k">Bike</span><span class="v">{r['bikeMi']} mi</span><span class="s">{climb(r['bikeGainFt'], r['bikeTerrain'])}</span></div>
<div><span class="k">Run</span><span class="v">{r['runMi']} mi</span><span class="s">{climb(r['runGainFt'], r['runTerrain'])}</span></div>
<div><span class="k">Course limit</span><span class="v">{int(total // 3600)}:{int(total % 3600 // 60):02d}</span><span class="s">from your start</span></div>
<div class="when"><span class="k">When</span><span class="w">{head_}</span><span class="s">{detail}</span></div>
</div>"""


def race_rows(races, prefix):
    rows = ""
    for r in sorted(races, key=sort_key):
        date, cls = list_date(r)
        search = f"{r['name']} {r['place']} {r['state']}".lower()
        rows += (f'<a class="race-row" href="{prefix}races/{r["slug"]}.html" data-search="{html.escape(search)}">'
                 f'<span class="rn">{r["name"]}</span><span class="rp">{r["place"]}</span>'
                 f'<span class="rd {cls}">{date}</span></a>')
    return rows


def race_list(prefix, intro=True):
    fulls = [r for r in RACES if r["dist"] == "full"]
    halves = [r for r in RACES if r["dist"] == "half"]
    intro_html = (f'<h2>Race planners</h2><p class="lede">{len(RACES)} US IRONMAN and IRONMAN 70.3 races with the distances, '
                  'climbing and cutoffs already loaded. Dates show the next race, or the 2027 date once IRONMAN announces it.</p>') if intro else ""
    return f"""<section id="races" class="race-index">
<div class="race-index-head">{intro_html}
<div class="field race-filter"><label for="raceFilter">Find a race</label><input id="raceFilter" type="search" placeholder="Race, city or state" autocomplete="off"></div></div>
<div class="race-group"><h3>Full IRONMAN <span class="count">{len(fulls)}</span></h3><div class="race-rows">{race_rows(fulls, prefix)}</div></div>
<div class="race-group"><h3>IRONMAN 70.3 <span class="count">{len(halves)}</span></h3><div class="race-rows">{race_rows(halves, prefix)}</div></div>
<p class="note" id="raceFilterEmpty" hidden>No races match that search.</p>
</section>"""


def related(r, prefix):
    same = [x for x in RACES if x["slug"] != r["slug"] and x["dist"] == r["dist"] and x["region"] == r["region"]]
    if len(same) < 4:
        same += [x for x in RACES if x["slug"] != r["slug"] and x["dist"] == r["dist"] and x not in same][: 4 - len(same)]
    kind = "full IRONMAN" if r["dist"] == "full" else "70.3"
    return f"""<section class="race-index"><h2>More {kind} planners</h2>
<div class="race-rows">{race_rows(same[:8], prefix)}</div>
<p><a href="{prefix}races/index.html">See all {len(RACES)} race planners</a></p></section>"""


def page_doc(head_html, body_html, script_src, data=None, wrapper=True):
    data_tag = f'<script type="application/json" id="race-data">{json.dumps(data)}</script>\n' if data else ""
    inner = f"{head_html}{body_html}\n{data_tag}<script src=\"{script_src}\"></script>\n"
    if not wrapper:
        return inner
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{head_html}</head><body>
{body_html}
{data_tag}<script src="{script_src}"></script>
</body></html>
"""


def build_index(wrapper):
    d = DEFAULTS["half"]
    body = f"""{topbar('')}
<main class="wrap">
<div class="hero"><span class="eyebrow">Triathlon race day math</span>
<h1>Know your finish time before the gun goes off</h1>
<p class="lede">Predict your splits, check them against the cutoffs, and turn the result into a carb, fluid and sodium plan. Free, no sign up.</p></div>
<section>{predictor(d, None)}</section>
<section class="two-up">{fueling(d)}{sweat()}</section>
{race_list('')}
</main>
{footer()}"""
    h = head(f"{SITE_NAME}: Triathlon Finish Time, Fueling and Sweat Rate Calculators",
             "Free triathlon calculators: predict your sprint, Olympic, 70.3 or IRONMAN finish time, plan race fueling, and measure your sweat rate.", "", "", "")
    return page_doc(h, body, "assets/app.js", None, wrapper)


def build_race(r):
    d = DEFAULTS[r["dist"]]
    legs = "".join(f'<div class="leg"><h3>{k}</h3><p>{v}</p></div>' for k, v in r["legs"].items())
    note_html = f'<p class="callout">{r["note"]}</p>' if r.get("note") else ""
    official_label = ("Official race page on ironman.com: course maps, athlete guide and registration"
                      if r["officialExact"] else "Find the official race page in IRONMAN's race finder on ironman.com")
    official_html = (f'<p class="official"><a href="{r["official"]}" target="_blank" rel="noopener">'
                     f'{official_label}<span aria-hidden="true"> ↗</span></a></p>')
    weather_html = f'<p class="note"><strong>Race notes:</strong> {r["weather"]}</p>' if r.get("weather") else ""
    kind = "IRONMAN 70.3" if r["dist"] == "half" else "full IRONMAN"
    title = f"{r['name']} Race Planner: Finish Time, Cutoffs and Fueling"
    desc = (f"Plan {r['name']} in {r['place']}: predict your finish time with course details for this {kind}, "
            f"check the cutoffs, and build a carb and sodium plan. Free, no sign up.")
    body = f"""{topbar('../')}
<main class="wrap">
<div class="hero"><span class="eyebrow">{r['place']} · {kind} race planner</span>
<h1>{r['name']}</h1>
<p class="lede">Finish time, cutoff check and fueling plan built for this course.</p></div>
{race_bib(r)}
{official_html}
{note_html}
<section>{predictor(d, r)}
<p class="callout">{r['cutoffNote']}</p></section>
<section><h2>The course</h2><div class="legs">{legs}</div>
<p class="note">Course details describe the most recent race we could verify and can change from year to year.</p>
{weather_html}</section>
<section class="two-up">{fueling(d)}{sweat()}</section>
{related(r, '../')}
</main>
{footer()}"""
    data = {k: r[k] for k in ("swimMi", "bikeMi", "runMi", "bikeGainFt", "runGainFt", "swimFactor", "cutoffs")}
    return page_doc(head(title, desc, "", "../", f"races/{r['slug']}.html"), body, "../assets/app.js", data, True)


def build_race_index():
    body = f"""{topbar('../')}
<main class="wrap">
<div class="hero"><span class="eyebrow">2026 and 2027 seasons</span>
<h1>Every US IRONMAN and 70.3 race planner</h1>
<p class="lede">Pick your race to get a finish time prediction, cutoff check and fueling plan with that course already loaded. {len(RACES)} races, with 2027 dates shown as IRONMAN announces them.</p></div>
{race_list('../', intro=False)}
</main>
{footer()}"""
    h = head(f"US IRONMAN and 70.3 Race Planners for 2027 | {SITE_NAME}",
             f"Free race planners for {len(RACES)} US IRONMAN and IRONMAN 70.3 triathlons: finish time, cutoffs and fueling for each course, with 2027 dates as they are announced.",
             "", "../", "races/")
    return page_doc(h, body, "../assets/app.js", None, True)


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    for target in ("site", "preview"):
        base = os.path.join(OUT, target)
        os.makedirs(os.path.join(base, "assets"))
        os.makedirs(os.path.join(base, "races"))
        shutil.copy(os.path.join(SRC, "style.css"), os.path.join(base, "assets", "style.css"))
        shutil.copy(os.path.join(SRC, "app.js"), os.path.join(base, "assets", "app.js"))
        shutil.copy(os.path.join(SRC, "favicon.svg"), os.path.join(base, "assets", "favicon.svg"))
        with open(os.path.join(base, "index.html"), "w") as f:
            f.write(build_index(wrapper=(target == "site")))
        for r in RACES:
            with open(os.path.join(base, "races", r["slug"] + ".html"), "w") as f:
                f.write(build_race(r))
        with open(os.path.join(base, "races", "index.html"), "w") as f:
            f.write(build_race_index())
    site = os.path.join(OUT, "site")
    with open(os.path.join(site, "404.html"), "w") as f:
        body = f"""{topbar('/')}<main class="wrap"><div class="hero"><span class="eyebrow">404</span>
<h1>That page took a wrong turn</h1><p class="lede">The page you wanted is not here. Try the <a href="/index.html">calculators</a> or pick a race below.</p></div>
{race_list('/')}</main>{footer()}"""
        f.write(page_doc(head(f"Page not found | {SITE_NAME}", "Page not found.", "", "/"), body, "/assets/app.js", None, True))
    urls = ["index.html", "races/"] + [f"races/{r['slug']}.html" for r in sorted(RACES, key=sort_key)]
    with open(os.path.join(site, "robots.txt"), "w") as f:
        f.write("User-agent: *\nAllow: /\n" + (f"Sitemap: {DOMAIN}/sitemap.xml\n" if DOMAIN else ""))
    if DOMAIN:  # a sitemap needs full URLs, so it is only written once the domain is set
        with open(os.path.join(site, "sitemap.xml"), "w") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            for u in urls:
                f.write(f"  <url><loc>{DOMAIN}/{'' if u == 'index.html' else u}</loc></url>\n")
            f.write("</urlset>\n")
    print(f"built {len(urls)} pages ({len(RACES)} races)")


if __name__ == "__main__":
    main()

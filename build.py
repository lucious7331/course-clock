"""Build the Course Clock static site.

Outputs:
  dist/site/      full static site for Netlify or Vercel (drag the folder in)
  dist/preview/   same site, index body without the document wrapper, for the Claude artifact preview
"""
import json, os, shutil, html

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
OUT = os.path.join(ROOT, "dist")
SITE_NAME = "Course Clock"
# Set this once you buy a domain, e.g. "https://courseclock.com". Leave empty until then.
DOMAIN = ""
FONTS = ("https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700"
         "&family=IBM+Plex+Mono:wght@400;500;600&family=Source+Sans+3:wght@400;600;700&display=swap")

H = 3600
RACES = [
    {
        "slug": "ironman-chattanooga",
        "name": "IRONMAN Chattanooga",
        "short": "Chattanooga 140.6",
        "place": "Chattanooga, Tennessee",
        "when": "Late September (2026 race was Sept 27)",
        "dist": "full", "swimMi": 2.4, "bikeMi": 112, "runMi": 26.2,
        "bikeGainFt": 4300, "runGainFt": 1150, "swimFactor": 0.9,
        "cutoffs": {"swim": None, "bike": 10 * H, "total": 16.5 * H},
        "cutoffNote": "Cutoffs shown are the last ones we could confirm (10 hours for swim, T1 and bike; 16:30 total from your own start). Check this year's athlete guide.",
        "weather": "Often hot and humid. Plan for heat on the run.",
        "legs": {
            "Swim": "Point to point, downstream in the Tennessee River, finishing at Ross's Landing. The current usually makes this one of the faster IRONMAN swims, so the predictor takes 10% off your pool pace when course adjustments are on.",
            "Bike": "A course introduced in 2024 with three loops on US-27 and a dedicated lane, about 4,300 ft of climbing over 112 miles. Steady effort matters more than chasing speed on the climbs.",
            "Run": "Two loops through downtown, the Riverwalk, Veterans Bridge and the North Shore, about 1,150 ft of climbing. The North Shore hills come twice, so save something for the second loop.",
        },
        "title": "IRONMAN Chattanooga Race Planner: Finish Time and Fueling",
        "desc": "Predict your IRONMAN Chattanooga finish time with course adjustments for the downstream swim and hilly bike and run, then build a carb and sodium plan.",
    },
    {
        "slug": "ironman-70-3-chattanooga",
        "name": "IRONMAN 70.3 Chattanooga",
        "short": "Chattanooga 70.3",
        "place": "Chattanooga, Tennessee",
        "when": "Mid May (2026 race was May 17)",
        "dist": "half", "swimMi": 1.4, "bikeMi": 56, "runMi": 13.1,
        "bikeGainFt": 2500, "runGainFt": 550, "swimFactor": 0.9,
        "cutoffs": {"swim": None, "bike": 5.5 * H, "total": 8.5 * H},
        "cutoffNote": "Cutoffs shown are 5:30 for swim, T1 and bike and 8:30 total from your own start, plus intermediate cutoffs on the bike and run in past guides. Check this year's athlete guide.",
        "weather": "Late spring heat is common. Water has typically been in the low 70s F, so a wetsuit is likely.",
        "legs": {
            "Swim": "Point to point, downriver in the Tennessee River to Ross's Landing. The 2026 race listed it at 1.4 miles; it was 1.2 miles in earlier years. The current helps.",
            "Bike": "About 11 miles south of town, then a 34-mile loop in north Georgia past Chickamauga and along Lookout Mountain. Rolling, with roughly 2,500 ft of climbing.",
            "Run": "Two loops through downtown, the Riverwalk and the North Shore, finishing at Ross's Landing. About 550 ft of climbing. In 2026 a temporary detour skipped the Walnut Street Bridge.",
        },
        "title": "IRONMAN 70.3 Chattanooga Race Planner: Finish Time and Fueling",
        "desc": "Predict your IRONMAN 70.3 Chattanooga finish time with adjustments for the downriver swim and rolling north Georgia bike, then plan carbs and sodium.",
    },
    {
        "slug": "ironman-70-3-north-carolina",
        "name": "IRONMAN 70.3 North Carolina",
        "short": "North Carolina 70.3",
        "place": "Wilmington, North Carolina",
        "when": "Mid to late October (2026 race is Oct 17)",
        "dist": "half", "swimMi": 1.2, "bikeMi": 56, "runMi": 13.1,
        "bikeGainFt": None, "runGainFt": None, "swimFactor": 1,
        "cutoffs": {"swim": 70 * 60, "bike": 5.5 * H, "total": 8.5 * H},
        "cutoffNote": "Cutoffs shown are the standard IRONMAN 70.3 limits (1:10 swim, 5:30 swim through bike, 8:30 total). Check this year's athlete guide.",
        "weather": "Usually mild fall racing on the coast. Wind on the bike matters more than heat.",
        "legs": {
            "Swim": "In Banks Channel at Wrightsville Beach, connected to the Intracoastal Waterway. Tides and current vary by year, so the predictor uses your normal pace.",
            "Bike": "Point to point from the beach out into the countryside across two counties and back into Wilmington over the Isabel Holmes Bridge. Mostly flat, so aero position and steady power pay off.",
            "Run": "From downtown south along Front Street to Greenfield Lake, around the lake, then back to finish on Water Street across from Battleship North Carolina.",
        },
        "title": "IRONMAN 70.3 North Carolina (Wilmington) Race Planner",
        "desc": "Predict your IRONMAN 70.3 North Carolina finish time in Wilmington, check cutoffs, and build a race day carb and sodium plan.",
    },
    {
        "slug": "ironman-florida",
        "name": "IRONMAN Florida",
        "short": "Florida 140.6",
        "place": "Panama City Beach, Florida",
        "when": "Early November (2026 race is Nov 7)",
        "dist": "full", "swimMi": 2.4, "bikeMi": 112, "runMi": 26.2,
        "bikeGainFt": 1600, "runGainFt": 100, "swimFactor": 1,
        "cutoffs": {"swim": 140 * 60, "bike": 10.5 * H, "total": 17 * H},
        "cutoffNote": "Cutoffs shown are the standard IRONMAN limits (2:20 swim, 10:30 swim through bike, 17:00 total). Check this year's athlete guide.",
        "weather": "Usually mild, but Gulf wind and chop can slow the swim and the open stretches of the bike.",
        "legs": {
            "Swim": "Two loops in the Gulf of Mexico off the beach. Conditions change year to year, from glassy to choppy, so the predictor uses your normal pace.",
            "Bike": "Along the intracoastal waterways into Pine Log State Forest and back to the beach. About 1,600 ft of climbing, which is close to flat for a full.",
            "Run": "Two loops past the beachfront hotels on Front Beach Road, one of the best courses for spectators. Nearly flat.",
        },
        "title": "IRONMAN Florida (Panama City Beach) Race Planner",
        "desc": "Predict your IRONMAN Florida finish time, check the swim, bike and finish cutoffs, and build a full-distance carb and sodium plan.",
    },
]

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
<a href="{prefix}index.html#races">Races</a>
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


def race_bib(r):
    gain = f"{r['bikeGainFt']:,} ft" if r["bikeGainFt"] else "Mostly flat"
    total = r["cutoffs"]["total"]
    return f"""<div class="bib" aria-label="Course summary">
<div><span class="k">Swim</span><span class="v">{r['swimMi']} mi</span></div>
<div><span class="k">Bike</span><span class="v">{r['bikeMi']} mi</span><span class="s">{gain}</span></div>
<div><span class="k">Run</span><span class="v">{r['runMi']} mi</span><span class="s">{(str(r['runGainFt']) + ' ft') if r['runGainFt'] else 'Mostly flat'}</span></div>
<div><span class="k">Course limit</span><span class="v">{int(total // 3600)}:{int(total % 3600 // 60):02d}</span><span class="s">from your start</span></div>
<div><span class="k">When</span><span class="s" style="color:var(--ink);font-size:1rem">{r['when']}</span></div>
</div>"""


def race_cards(prefix):
    cards = ""
    for r in RACES:
        cards += f"""<a class="race-card" href="{prefix}races/{r['slug']}.html">
<span class="meta">{r['place'].upper()}</span><strong>{r['name']}</strong>
<span class="meta">{r['when']}</span></a>"""
    return f'<section id="races"><h2>Race planners</h2><p class="lede">Course specific pages with the distances, climbing and cutoffs already loaded.</p><div class="races">{cards}</div></section>'


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
{race_cards('')}
</main>
{footer()}"""
    h = head(f"{SITE_NAME}: Triathlon Finish Time, Fueling and Sweat Rate Calculators",
             "Free triathlon calculators: predict your sprint, Olympic, 70.3 or IRONMAN finish time, plan race fueling, and measure your sweat rate.", "", "", "")
    return page_doc(h, body, "assets/app.js", None, wrapper)


def build_race(r):
    d = DEFAULTS[r["dist"]]
    legs = "".join(f'<div class="leg"><h3>{k}</h3><p>{v}</p></div>' for k, v in r["legs"].items())
    body = f"""{topbar('../')}
<main class="wrap">
<div class="hero"><span class="eyebrow">{r['place']} · Race planner</span>
<h1>{r['name']}</h1>
<p class="lede">Finish time, cutoff check and fueling plan built for this course.</p></div>
{race_bib(r)}
<section>{predictor(d, r)}
<p class="callout">{r['cutoffNote']}</p></section>
<section><h2>The course</h2><div class="legs">{legs}</div>
<p class="note"><strong>Weather:</strong> {r['weather']}</p></section>
<section class="two-up">{fueling(d)}{sweat()}</section>
{race_cards('../')}
</main>
{footer()}"""
    data = {k: r[k] for k in ("swimMi", "bikeMi", "runMi", "bikeGainFt", "runGainFt", "swimFactor", "cutoffs")}
    return page_doc(head(r["title"], r["desc"], "", "../", f"races/{r['slug']}.html"), body, "../assets/app.js", data, True)


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
    site = os.path.join(OUT, "site")
    with open(os.path.join(site, "404.html"), "w") as f:
        body = f"""{topbar('/')}<main class="wrap"><div class="hero"><span class="eyebrow">404</span>
<h1>That page took a wrong turn</h1><p class="lede">The page you wanted is not here. Try the <a href="/index.html">calculators</a> or pick a race below.</p></div>
{race_cards('/')}</main>{footer()}"""
        f.write(page_doc(head(f"Page not found | {SITE_NAME}", "Page not found.", "", "/"), body, "/assets/app.js", None, True))
    urls = ["index.html"] + [f"races/{r['slug']}.html" for r in RACES]
    with open(os.path.join(site, "robots.txt"), "w") as f:
        f.write("User-agent: *\nAllow: /\n" + (f"Sitemap: {DOMAIN}/sitemap.xml\n" if DOMAIN else ""))
    if DOMAIN:  # a sitemap needs full URLs, so it is only written once the domain is set
        with open(os.path.join(site, "sitemap.xml"), "w") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            for u in urls:
                f.write(f"  <url><loc>{DOMAIN}/{'' if u == 'index.html' else u}</loc></url>\n")
            f.write("</urlset>\n")
    print("built", urls)


if __name__ == "__main__":
    main()

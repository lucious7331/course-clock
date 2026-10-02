(function () {
  "use strict";

  var DIST = {
    sprint:  { label: "Sprint",          swimMi: 750 / 1609.34,  bikeMi: 12.4, runMi: 3.1 },
    olympic: { label: "Olympic",         swimMi: 1500 / 1609.34, bikeMi: 24.8, runMi: 6.2 },
    half:    { label: "70.3 (half)",     swimMi: 1.2,            bikeMi: 56,   runMi: 13.1 },
    full:    { label: "140.6 (full)",    swimMi: 2.4,            bikeMi: 112,  runMi: 26.2 }
  };
  var STD_CUTOFFS = {
    half: { swim: 70 * 60, bike: 5.5 * 3600, total: 8.5 * 3600 },
    full: { swim: 140 * 60, bike: 10.5 * 3600, total: 17 * 3600 }
  };

  var raceEl = document.getElementById("race-data");
  var RACE = raceEl ? JSON.parse(raceEl.textContent) : null;

  function $(id) { return document.getElementById(id); }
  function num(id, fallback) {
    var el = $(id); if (!el) return fallback;
    var v = parseFloat(el.value); return isFinite(v) ? v : fallback;
  }
  function parseClock(str) {
    if (!str) return NaN;
    var parts = String(str).trim().split(":").map(Number);
    if (parts.some(function (p) { return !isFinite(p); })) return NaN;
    var s = 0; for (var i = 0; i < parts.length; i++) s = s * 60 + parts[i];
    return s;
  }
  function fmt(sec, withHours) {
    if (!isFinite(sec) || sec < 0) return "--";
    sec = Math.round(sec);
    var h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = sec % 60;
    var mm = String(m).padStart(2, "0"), ss = String(s).padStart(2, "0");
    return (h > 0 || withHours) ? h + ":" + mm + ":" + ss : m + ":" + ss;
  }
  function clockOfDay(startStr, offsetSec) {
    var parts = (startStr || "07:00").split(":").map(Number);
    var t = (parts[0] * 3600 + (parts[1] || 0) * 60 + offsetSec) % 86400;
    var h = Math.floor(t / 3600), m = Math.floor((t % 3600) / 60);
    var ap = h >= 12 ? "pm" : "am", h12 = h % 12 === 0 ? 12 : h % 12;
    return h12 + ":" + String(m).padStart(2, "0") + " " + ap;
  }

  /* ---------- Course model ---------- */
  function course() {
    if (RACE) return RACE;
    var key = $("dist") ? $("dist").value : "half";
    var d = DIST[key];
    return { swimMi: d.swimMi, bikeMi: d.bikeMi, runMi: d.runMi, distKey: key, cutoffs: STD_CUTOFFS[key] || null };
  }
  function adjustments(c) {
    var on = $("adjust") ? $("adjust").checked : false;
    var a = { swim: 1, bike: 1, run: 1, lines: [] };
    if (!RACE || !on) return a;
    if (c.swimFactor && c.swimFactor !== 1) {
      a.swim = c.swimFactor;
      a.lines.push("Swim " + Math.round((1 - c.swimFactor) * 100) + "% faster for river current");
    }
    if (c.bikeGainFt) {
      var fpm = c.bikeGainFt / c.bikeMi;
      a.bike = 1 + 0.002 * fpm;
      a.lines.push("Bike " + ((a.bike - 1) * 100).toFixed(1) + "% slower for " + Math.round(fpm) + " ft of climbing per mile");
    }
    if (c.runGainFt) {
      var rpm = c.runGainFt / c.runMi;
      a.run = 1 + 0.001 * rpm;
      a.lines.push("Run " + ((a.run - 1) * 100).toFixed(1) + "% slower for " + Math.round(rpm) + " ft of climbing per mile");
    }
    return a;
  }

  var last = null; // latest predicted splits, shared with the fueling planner

  function predict() {
    if (!$("splits")) return;
    var c = course(), adj = adjustments(c);
    var swimUnit = $("swimUnit") ? $("swimUnit").value : "yd";
    var per100 = parseClock($("swimPace").value);
    var swimDist = swimUnit === "yd" ? c.swimMi * 1760 : c.swimMi * 1609.34;
    var swim = per100 / 100 * swimDist * adj.swim;
    var mph = num("bikeMph", 18);
    var bike = mph > 0 ? c.bikeMi / mph * 3600 * adj.bike : NaN;
    var run = parseClock($("runPace").value) * c.runMi * adj.run;
    var t1 = num("t1", 5) * 60, t2 = num("t2", 3) * 60;
    var start = ($("start") && $("start").value) || "07:00";

    var problems = [];
    if (!(swim > 0)) problems.push("swim pace (use m:ss, like 1:55)");
    if (!(bike > 0)) problems.push("bike speed (a number above 0)");
    if (!(run > 0)) problems.push("run pace (use m:ss, like 9:30)");
    if (problems.length) {
      $("splits").innerHTML = "";
      $("total").innerHTML = "<small style=\"margin:0\">Check your " + problems.join(" and ") + ".</small>";
      $("cutoffPills").innerHTML = "";
      if ($("adjNote")) $("adjNote").textContent = "";
      last = null; if ($("fuelOut")) $("fuelOut").innerHTML = "<p class=\"note\">Fix the predictor inputs above to see your fueling plan.</p>";
      return;
    }

    var rows = [
      ["Swim", c.swimMi.toFixed(2) + " mi", swim],
      ["T1", "", t1],
      ["Bike", c.bikeMi + " mi", bike],
      ["T2", "", t2],
      ["Run", c.runMi + " mi", run]
    ];
    var elapsed = 0, html = "";
    rows.forEach(function (r) {
      elapsed += r[2];
      html += "<tr><td>" + r[0] + "</td><td class=\"num\">" + r[1] + "</td><td class=\"num\">" + fmt(r[2]) +
        "</td><td class=\"num\">" + fmt(elapsed, true) + "</td><td class=\"num\">" + clockOfDay(start, elapsed) + "</td></tr>";
    });
    html += "<tr class=\"total\"><td>Finish</td><td></td><td></td><td class=\"num\">" + fmt(elapsed, true) +
      "</td><td class=\"num\">" + clockOfDay(start, elapsed) + "</td></tr>";
    $("splits").innerHTML = html;
    $("total").innerHTML = fmt(elapsed, true) + "<small>finish at " + clockOfDay(start, elapsed) + "</small>";

    // cutoff checks, measured from your own swim start
    var pills = "";
    var co = c.cutoffs;
    if (co) {
      var checks = [
        ["Swim", swim, co.swim],
        ["Swim + T1 + bike", swim + t1 + bike, co.bike],
        ["Finish", elapsed, co.total]
      ];
      checks.forEach(function (k) {
        if (!k[2]) return;
        var margin = k[2] - k[1], cls = margin < 0 ? "bad" : (margin < k[2] * 0.1 ? "warn" : "good");
        var word = margin < 0 ? "over by " + fmt(-margin, true) : fmt(margin, true) + " to spare";
        pills += "<span class=\"pill " + cls + "\">" + k[0] + " cutoff " + fmt(k[2], true) + ": " + word + "</span>";
      });
    }
    $("cutoffPills").innerHTML = pills;
    if ($("adjNote")) {
      $("adjNote").textContent = adj.lines.length ? "Course adjustments applied: " + adj.lines.join("; ") + "." :
        (RACE ? "Flat course times, no course adjustments." : "");
    }
    last = { bike: bike, run: run };
    fuel();
  }

  /* ---------- Fueling ---------- */
  function fuel() {
    var out = $("fuelOut"); if (!out || !last) return;
    var bikeH = last.bike / 3600, runH = last.run / 3600;
    if (!isFinite(bikeH) || !isFinite(runH)) { out.innerHTML = ""; return; }
    var cb = num("carbBike", 80), cr = num("carbRun", 60);
    var bph = num("bottlesPerHr", 1), cpb = num("carbPerBottle", 60);
    var gel = Math.max(1, num("gelCarb", 25)), na = num("sodium", 600);

    var bikeCarbs = cb * bikeH;
    var bottles = Math.ceil(bph * bikeH);
    var fromBottles = Math.min(bikeCarbs, bottles * cpb);
    var bikeGels = Math.max(0, Math.ceil((bikeCarbs - fromBottles) / gel));
    var runCarbs = cr * runH;
    var runGels = Math.ceil(runCarbs / gel);
    var every = runGels > 0 ? (last.run / 60) / runGels : 0;
    var bikeEvery = bikeGels > 0 ? (last.bike / 60) / bikeGels : 0;

    out.innerHTML =
      "<div class=\"stat-row\">" +
      stat("Bike carbs", Math.round(bikeCarbs) + " g") +
      stat("Bottles of mix", bottles, Math.round(fromBottles) + " g of carbs") +
      stat("Bike gels", bikeGels, bikeGels ? "1 every " + Math.round(bikeEvery) + " min" : "bottles cover it") +
      stat("Run carbs", Math.round(runCarbs) + " g") +
      stat("Run gels", runGels, runGels ? "1 every " + Math.round(every) + " min" : "") +
      stat("Sodium total", Math.round(na * (bikeH + runH)).toLocaleString() + " mg") +
      "</div>" +
      "<p class=\"note\">Based on your predicted " + fmt(last.bike, true) + " bike and " + fmt(last.run, true) +
      " run. Practice this exact plan in long training sessions before race day.</p>";
  }
  function stat(k, v, sub) {
    return "<div class=\"stat\"><span class=\"k\">" + k + "</span><span class=\"v\">" + v + "</span>" +
      (sub ? "<span class=\"sub\">" + sub + "</span>" : "") + "</div>";
  }

  /* ---------- Sweat rate ---------- */
  function sweat() {
    var out = $("sweatOut"); if (!out) return;
    var imperial = $("sweatUnit").value === "imperial";
    var pre = num("preWt", NaN), post = num("postWt", NaN), drank = num("drank", 0), urine = num("urine", 0), mins = num("sweatMin", NaN);
    if (!(pre > 0 && post > 0 && mins > 0)) { out.innerHTML = "<p class=\"note\">Enter weights and duration to see your sweat rate.</p>"; return; }
    // convert everything to liters
    var lossL = imperial ? (pre - post) * 0.453592 : (pre - post);
    var inL = imperial ? drank * 0.0295735 : drank / 1000;
    var outL = imperial ? urine * 0.0295735 : urine / 1000;
    var sweatL = lossL + inL - outL;
    var perHrL = sweatL / (mins / 60);
    var pct = (pre - post) / pre * 100;
    var cls = pct > 2 ? "bad" : (pct > 1 ? "warn" : "good");
    var bottleMin = perHrL > 0 ? 0.71 / perHrL * 60 : 0; // 24 oz bottle

    out.innerHTML =
      "<div class=\"big\">" + (imperial ? Math.round(perHrL * 33.814) + "<small>oz per hour</small>" : perHrL.toFixed(2) + "<small>liters per hour</small>") + "</div>" +
      "<div class=\"stat-row\">" +
      stat("Total sweat lost", imperial ? Math.round(sweatL * 33.814) + " oz" : sweatL.toFixed(2) + " L") +
      stat("Per hour (other unit)", imperial ? perHrL.toFixed(2) + " L" : Math.round(perHrL * 33.814) + " oz") +
      stat("One 24 oz bottle every", bottleMin ? Math.round(bottleMin) + " min" : "--", "matches your loss") +
      "</div>" +
      "<div class=\"pills\"><span class=\"pill " + cls + "\">Body weight change: " + (pct >= 0 ? "-" : "+") + Math.abs(pct).toFixed(1) + "%</span></div>" +
      "<p class=\"note\">Most athletes aim to keep losses under about 2% of body weight. Drinking more than you sweat carries its own risk, so do not plan to replace more than this rate. Test in conditions close to race day weather.</p>";
  }

  /* ---------- Wire up ---------- */
  document.querySelectorAll("[data-calc='predict'] input, [data-calc='predict'] select").forEach(function (el) {
    el.addEventListener("input", predict); el.addEventListener("change", predict);
  });
  document.querySelectorAll("[data-calc='fuel'] input").forEach(function (el) { el.addEventListener("input", fuel); });
  document.querySelectorAll("[data-calc='sweat'] input, [data-calc='sweat'] select").forEach(function (el) {
    el.addEventListener("input", sweat); el.addEventListener("change", sweat);
  });
  if ($("sweatUnit")) {
    $("sweatUnit").addEventListener("change", function () {
      var imp = this.value === "imperial";
      document.querySelectorAll("[data-unit-w]").forEach(function (l) { l.textContent = l.getAttribute("data-unit-w").replace("{u}", imp ? "lb" : "kg"); });
      document.querySelectorAll("[data-unit-v]").forEach(function (l) { l.textContent = l.getAttribute("data-unit-v").replace("{u}", imp ? "oz" : "ml"); });
    });
  }

  // expose pure functions for testing in Node
  if (typeof module !== "undefined") module.exports = { parseClock: parseClock, fmt: fmt };

  predict(); sweat();
})();

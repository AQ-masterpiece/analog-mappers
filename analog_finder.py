"""
Analog Finder - The Analog Mappers (NASA Space Apps 2026)

Scores Earth sites by how similar they are to a Moon base site
(lunar south pole) and a Mars landing site (Jezero Crater), using
NASA POWER climate data. Uses ONLY built-in Python - nothing to install.

How to run:   python analog_finder.py
Output:       results.csv  and  analog_map.html  (open it in a browser)
"""

import csv
import json
import os
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SITES_FILE = os.path.join(HERE, "sites.csv")
CACHE_FILE = os.path.join(HERE, "nasa_power_cache.json")
RESULTS_FILE = os.path.join(HERE, "results.csv")
MAP_FILE = os.path.join(HERE, "analog_map.html")

# NASA POWER parameters (long-term climate averages)
#   T2M         mean air temperature (C)
#   T2M_RANGE   daily temperature swing, max - min (C)
#   PRECTOTCORR rainfall (mm/day)
#   RH2M        relative humidity (%)
#   ALLSKY_SFC_SW_DWN  sunlight reaching the ground (kWh/m2/day)
PARAMS = ["T2M", "T2M_RANGE", "PRECTOTCORR", "RH2M", "ALLSKY_SFC_SW_DWN"]
POWER_URL = (
    "https://power.larc.nasa.gov/api/temporal/climatology/point"
    "?parameters={params}&community=RE&longitude={lon}&latitude={lat}&format=JSON"
)

# ---------------------------------------------------------------------------
# 1. TARGETS: what makes a site Moon-like or Mars-like
#    weights = how important each feature is (they add up to 1.0)
#    terrain = how well each terrain type matches (0 to 1)
# ---------------------------------------------------------------------------
TARGETS = {
    "mars": {
        "label": "Mars - Jezero Crater",
        "weights": {"dryness": 0.25, "low_humidity": 0.15, "temp_swing": 0.10,
                    "cold": 0.20, "altitude": 0.10, "terrain": 0.20},
        "terrain": {"cave": 0.9, "desert": 1.0, "acidic": 1.0, "polar": 1.0, "crater": 0.9,
                    "volcanic": 0.8, "dunes": 0.8},
    },
    "moon": {
        "label": "Moon - South Pole",
        "weights": {"dryness": 0.15, "low_humidity": 0.10, "temp_swing": 0.15,
                    "cold": 0.20, "altitude": 0.10, "terrain": 0.30},
        "terrain": {"cave": 1.0, "volcanic": 1.0, "crater": 1.0, "polar": 0.9, "desert": 0.5,
                    "dunes": 0.4, "acidic": 0.4},
    },
}

# Real NASA measurements of the targets (shown on the map for comparison)
#   Mars: Perseverance rover MEDA weather station, Jezero Crater
#   Moon: LRO Diviner Lunar Radiometer, south polar region
TARGET_FACTS = {
    "mars": {
        "where": "Jezero Crater, 18.44 N 77.45 E",
        "mean_temp_C": -55,
        "temp_swing_C": "50 to 60",
        "rain_mm_day": 0,
        "pressure_kPa": 0.72,
        "notes": "Ancient lake bed. Air pressure under 1% of Earth's.",
        "source": "NASA Perseverance rover, MEDA instrument",
    },
    "moon": {
        "where": "Lunar south pole (Artemis region)",
        "mean_temp_C": "-53 on sunlit crater rims, down to -248 in shadowed craters",
        "temp_swing_C": "about 300 at the equator (127 to -173)",
        "rain_mm_day": 0,
        "pressure_kPa": 0,
        "notes": "Water ice in permanently shadowed craters. No atmosphere.",
        "source": "NASA Lunar Reconnaissance Orbiter, Diviner instrument",
    },
}

FEATURE_NAMES = {
    "dryness": "Very little rain",
    "low_humidity": "Dry air",
    "temp_swing": "Big day-night temperature swing",
    "cold": "Cold",
    "altitude": "High altitude (thin air)",
    "terrain": "Terrain type",
}


def clamp(x):
    return max(0.0, min(1.0, x))


# ---------------------------------------------------------------------------
# 2. DATA: download NASA POWER climate data for one site (with a cache,
#    so running the script again is instant and works offline)
# ---------------------------------------------------------------------------
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=1)


def fetch_power(lat, lon, cache):
    key = f"{lat},{lon}"
    if key in cache:
        return cache[key]
    url = POWER_URL.format(params=",".join(PARAMS), lat=lat, lon=lon)
    with urllib.request.urlopen(url, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    values = {}
    for p in PARAMS:
        v = data["properties"]["parameter"][p]["ANN"]  # yearly average
        values[p] = None if v is None or v <= -999 else v
    coords = data.get("geometry", {}).get("coordinates", [])
    values["ELEVATION"] = coords[2] if len(coords) > 2 else None
    cache[key] = values
    save_cache(cache)
    time.sleep(0.5)  # be polite to the NASA server
    return values


# ---------------------------------------------------------------------------
# 3. SCORING: turn raw numbers into 0-1 feature scores, then 0-100 totals
# ---------------------------------------------------------------------------
def feature_scores(climate, terrain, target):
    rain = climate.get("PRECTOTCORR") or 0
    rh = climate.get("RH2M") or 50
    swing = climate.get("T2M_RANGE") or 0
    temp = climate.get("T2M") if climate.get("T2M") is not None else 20
    elev = climate.get("ELEVATION") or 0
    return {
        "dryness": clamp(1 - rain / 2.0),        # 0 mm/day -> 1, 2+ mm/day -> 0
        "low_humidity": clamp(1 - rh / 80.0),    # 0% -> 1, 80%+ -> 0
        "temp_swing": clamp(swing / 18.0),       # 18 C+ daily swing -> 1
        "cold": clamp((25 - temp) / 45.0),       # -20 C -> 1, 25 C -> 0
        "altitude": clamp(elev / 4000.0),        # 4000 m+ -> 1
        "terrain": TARGETS[target]["terrain"].get(terrain, 0.3),
    }


def total_score(fs, target):
    w = TARGETS[target]["weights"]
    return round(100 * sum(fs[k] * w[k] for k in w), 1)


# ---------------------------------------------------------------------------
# 4. MAIN
# ---------------------------------------------------------------------------
def main():
    with open(SITES_FILE, encoding="utf-8-sig") as f:
        sites = list(csv.DictReader(f))
    print(f"Loaded {len(sites)} sites. Downloading NASA POWER data...\n")

    cache = load_cache()
    results = []
    for i, s in enumerate(sites, 1):
        lat, lon = float(s["lat"]), float(s["lon"])
        try:
            climate = fetch_power(lat, lon, cache)
        except Exception as e:
            print(f"  [{i}/{len(sites)}] {s['name']}: FAILED ({e}) - skipped")
            continue
        row = {
            "name": s["name"], "lat": lat, "lon": lon,
            "terrain": s["terrain"].strip().lower(),
            "known_analog": s["known_analog"].strip().lower() == "yes",
            "climate": climate,
        }
        for t in TARGETS:
            fs = feature_scores(climate, row["terrain"], t)
            row[f"{t}_features"] = {k: round(v, 4) for k, v in fs.items()}
            row[f"{t}_score"] = total_score(fs, t)
        results.append(row)
        print(f"  [{i}/{len(sites)}] {s['name']:<24} Mars {row['mars_score']:>5}   "
              f"Moon {row['moon_score']:>5}")

    if not results:
        print("No data downloaded - check your internet connection.")
        return

    # Save results table
    with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name", "lat", "lon", "terrain", "known_analog", "mars_score",
                    "moon_score", "temp_C", "temp_swing_C", "rain_mm_day",
                    "humidity_pct", "sunlight_kWh", "elevation_m"])
        for r in sorted(results, key=lambda r: -r["mars_score"]):
            c = r["climate"]
            w.writerow([r["name"], r["lat"], r["lon"], r["terrain"],
                        "yes" if r["known_analog"] else "no", r["mars_score"],
                        r["moon_score"], c.get("T2M"), c.get("T2M_RANGE"),
                        c.get("PRECTOTCORR"), c.get("RH2M"),
                        c.get("ALLSKY_SFC_SW_DWN"), c.get("ELEVATION")])

    # Validation: do known analogs score higher than average?
    print("\n=== VALIDATION ===")
    for t in TARGETS:
        known = [r[f"{t}_score"] for r in results if r["known_analog"]]
        new = [r[f"{t}_score"] for r in results if not r["known_analog"]]
        if known and new:
            print(f"{TARGETS[t]['label']}: known analogs avg {sum(known)/len(known):.1f}"
                  f"  |  new candidates avg {sum(new)/len(new):.1f}")
        top_new = sorted([r for r in results if not r["known_analog"]],
                         key=lambda r: -r[f"{t}_score"])[:5]
        print("  Top new candidates: " + ", ".join(
            f"{r['name']} ({r[f'{t}_score']})" for r in top_new))

    build_map(results)
    print(f"\nDone! Saved {os.path.basename(RESULTS_FILE)} and "
          f"{os.path.basename(MAP_FILE)} - open the map in your browser.")


# ---------------------------------------------------------------------------
# 5. MAP: one HTML file with a Leaflet map (works in any browser)
# ---------------------------------------------------------------------------
def build_map(results):
    payload = json.dumps({
        "sites": results,
        "targets": {t: TARGETS[t]["label"] for t in TARGETS},
        "featureNames": FEATURE_NAMES,
        "facts": TARGET_FACTS,
        "weights": {t: TARGETS[t]["weights"] for t in TARGETS},
    })
    html = MAP_TEMPLATE.replace("__DATA__", payload)
    with open(MAP_FILE, "w", encoding="utf-8") as f:
        f.write(html)


MAP_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Analog Finder - The Analog Mappers</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; font-family: system-ui, -apple-system, Segoe UI, sans-serif;
         background: #0b0f1a; color: #e8eaf0; display: flex; height: 100vh; }
  #side { width: 360px; padding: 20px; overflow-y: auto; border-right: 1px solid #222a3d; }
  #map { flex: 1; }
  h1 { font-size: 20px; margin: 0 0 4px; }
  .sub { color: #9aa3b8; font-size: 13px; margin-bottom: 16px; line-height: 1.5; }
  .switch { display: flex; gap: 6px; margin-bottom: 16px; }
  .switch button { flex: 1; padding: 10px; border-radius: 8px; border: 1px solid #2c3550;
         background: #141a2a; color: #e8eaf0; cursor: pointer; font-size: 14px; }
  .switch button.on { background: #c1440e; border-color: #c1440e; }
  .switch button.on.moon { background: #5b6a8f; border-color: #5b6a8f; }
  .row { display: flex; align-items: center; gap: 10px; padding: 8px 6px;
         border-radius: 6px; cursor: pointer; font-size: 14px; }
  .row:hover { background: #161d30; }
  .rank { width: 22px; color: #6b7590; }
  .nm { flex: 1; }
  .tag { font-size: 11px; padding: 2px 6px; border-radius: 4px; background: #23304d; color: #a9b8db; }
  .tag.new { background: #3d2a12; color: #ffb066; }
  .sc { width: 42px; text-align: right; font-weight: 600; }
  .legend { font-size: 12px; color: #9aa3b8; margin: 8px 0 14px; }
  .bar { height: 8px; border-radius: 4px; background: linear-gradient(90deg,#2b83ba,#ffffbf,#d7191c); margin: 4px 0; }
  .card h3 { margin: 0 0 4px; font-size: 16px; }
  .card .big { font-size: 26px; font-weight: 700; margin: 6px 0; }
  .f { font-size: 12px; margin: 5px 0; }
  .fb { height: 6px; background: #ddd; border-radius: 3px; overflow: hidden; }
  .fb div { height: 100%; background: #c1440e; }
  .leaflet-popup-content { min-width: 230px; }
  #weights { background: #141a2a; border: 1px solid #2c3550; border-radius: 8px; padding: 10px 12px; margin-bottom: 14px; }
  #weights .wt { font-size: 13px; font-weight: 600; margin-bottom: 6px; }
  #weights .wr { display: grid; grid-template-columns: 1fr 90px 34px; gap: 8px; align-items: center; font-size: 12px; color: #c4cbe0; margin: 4px 0; }
  #weights input { width: 100%; accent-color: #c1440e; }
  #weights button { margin-top: 8px; width: 100%; padding: 6px; border-radius: 6px; border: 1px solid #2c3550;
         background: #0b0f1a; color: #e8eaf0; cursor: pointer; font-size: 12px; }
</style>
</head>
<body>
<div id="side">
  <h1>Analog Finder</h1>
  <div class="sub">The Analog Mappers - NASA Space Apps 2026.<br>
    Which places on Earth are most like the Moon or Mars? Scores use NASA POWER climate data
    + terrain type. Click a site to see why it matches.</div>
  <div class="switch">
    <button id="bMars" class="on" onclick="setTarget('mars')">Mars</button>
    <button id="bMoon" class="moon" onclick="setTarget('moon')">Moon</button>
  </div>
  <div class="legend">Similarity score
    <div class="bar"></div>
    <div style="display:flex;justify-content:space-between"><span>0 low</span><span>100 high</span></div>
    Ring = known analog &nbsp; | &nbsp; <span class="tag new">NEW</span> = our candidate
  </div>
  <div id="weights"></div>
  <div id="facts" style="font-size:12px;line-height:1.6;background:#141a2a;border:1px solid #2c3550;border-radius:8px;padding:10px 12px;margin-bottom:14px"></div>
  <div id="list"></div>
</div>
<div id="map"></div>
<script>
const DATA = __DATA__;
let target = "mars";
let W = { ...DATA.weights[target] };

function score(s) {
  const fs = s[target + "_features"];
  let sum = 0, tot = 0;
  for (const k in W) { sum += fs[k] * W[k]; tot += W[k]; }
  return tot > 0 ? Math.round(1000 * sum / tot) / 10 : 0;
}

function buildSliders() {
  let h = `<div class="wt">What matters for your mission?</div>`;
  for (const k in W) {
    h += `<div class="wr"><span>${DATA.featureNames[k]}</span>
      <input type="range" min="0" max="50" step="1" value="${Math.round(W[k] * 100)}" oninput="setWeight('${k}', this.value)">
      <span id="w_${k}">${Math.round(W[k] * 100)}</span></div>`;
  }
  h += `<button onclick="resetWeights()">Reset to our default weights</button>`;
  document.getElementById("weights").innerHTML = h;
}

function setWeight(k, v) {
  W[k] = v / 100;
  document.getElementById("w_" + k).textContent = v;
  render();
}

function resetWeights() {
  W = { ...DATA.weights[target] };
  buildSliders(); render();
}
const map = L.map("map", { worldCopyJump: true }).setView([20, 20], 2);
L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
  { attribution: "Imagery: Esri", maxZoom: 18 }).addTo(map);
let layer = L.layerGroup().addTo(map);
const markers = {};

function color(s) {
  const t = Math.max(0, Math.min(1, s / 100));
  const stops = [[43,131,186],[255,255,191],[215,25,28]];
  const seg = t < 0.5 ? 0 : 1, u = t < 0.5 ? t * 2 : (t - 0.5) * 2;
  const a = stops[seg], b = stops[seg + 1];
  return `rgb(${a.map((v, i) => Math.round(v + (b[i] - v) * u)).join(",")})`;
}

function card(s) {
  const fs = s[target + "_features"], c = s.climate;
  const fmt = (v, d = 1) => v == null ? "n/a" : Number(v).toFixed(d);
  let h = `<div class="card"><h3>${s.name}</h3>
    <span class="tag ${s.known_analog ? "" : "new"}">${s.known_analog ? "Known analog" : "NEW candidate"}</span>
    <span class="tag">${s.terrain}</span>
    <div class="big" style="color:${color(score(s))}">${score(s)} / 100</div>
    <div class="f">${DATA.targets[target]}</div>`;
  for (const k in fs) {
    h += `<div class="f">${DATA.featureNames[k]} - ${Math.round(fs[k] * 100)}%
      <div class="fb"><div style="width:${fs[k] * 100}%"></div></div></div>`;
  }
  const tf = DATA.facts[target];
  const pressure = c.ELEVATION == null ? null : 101.3 * Math.exp(-c.ELEVATION / 8400);
  const td = "padding:2px 6px;border-bottom:1px solid #eee";
  h += `<table style="width:100%;font-size:11px;border-collapse:collapse;margin-top:8px">
    <tr><th style="${td};text-align:left"></th><th style="${td}">This site</th><th style="${td}">${target === "mars" ? "Mars" : "Moon"}</th></tr>
    <tr><td style="${td}">Mean temp (C)</td><td style="${td}">${fmt(c.T2M)}</td><td style="${td}">${tf.mean_temp_C}</td></tr>
    <tr><td style="${td}">Day-night swing (C)</td><td style="${td}">${fmt(c.T2M_RANGE)}</td><td style="${td}">${tf.temp_swing_C}</td></tr>
    <tr><td style="${td}">Rain (mm/day)</td><td style="${td}">${fmt(c.PRECTOTCORR, 2)}</td><td style="${td}">${tf.rain_mm_day}</td></tr>
    <tr><td style="${td}">Air pressure (kPa)</td><td style="${td}">${fmt(pressure)}</td><td style="${td}">${tf.pressure_kPa}</td></tr>
  </table>
  <div class="f" style="color:#666">Humidity ${fmt(c.RH2M, 0)}%, elevation ${fmt(c.ELEVATION, 0)} m.
    Earth data: NASA POWER. ${target === "mars" ? "Mars" : "Moon"} data: ${tf.source}.</div></div>`;
  return h;
}

function showFacts() {
  const tf = DATA.facts[target];
  document.getElementById("facts").innerHTML = `<b>Target: ${DATA.targets[target]}</b><br>
    ${tf.where}<br>Mean temp: ${tf.mean_temp_C} C<br>Day-night swing: ${tf.temp_swing_C} C<br>
    Air pressure: ${tf.pressure_kPa} kPa (Earth: 101.3)<br>${tf.notes}<br>
    <span style="color:#9aa3b8">Source: ${tf.source}</span>`;
}

function render() {
  showFacts();
  layer.clearLayers();
  const sorted = [...DATA.sites].sort((a, b) => score(b) - score(a));
  sorted.forEach(s => {
    const sc = score(s);
    const m = L.circleMarker([s.lat, s.lon], {
      radius: 7 + sc / 10, fillColor: color(sc), fillOpacity: 0.9,
      color: s.known_analog ? "#ffffff" : "#000000", weight: s.known_analog ? 3 : 1
    }).bindPopup(card(s));
    m.addTo(layer); markers[s.name] = m;
  });
  document.getElementById("list").innerHTML = sorted.map((s, i) => `
    <div class="row" onclick="focusSite('${s.name.replace(/'/g, "\\'")}')">
      <span class="rank">${i + 1}</span><span class="nm">${s.name}</span>
      ${s.known_analog ? "" : '<span class="tag new">NEW</span>'}
      <span class="sc" style="color:${color(score(s))}">${score(s)}</span>
    </div>`).join("");
}

function focusSite(name) {
  const s = DATA.sites.find(x => x.name === name);
  map.flyTo([s.lat, s.lon], 6); markers[name].openPopup();
}

function setTarget(t) {
  target = t;
  document.getElementById("bMars").classList.toggle("on", t === "mars");
  document.getElementById("bMoon").classList.toggle("on", t === "moon");
  W = { ...DATA.weights[target] };
  buildSliders();
  render();
}
buildSliders();
render();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
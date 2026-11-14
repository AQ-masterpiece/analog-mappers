// DATA comes from map_data.js, which analog_finder.py creates

// ---------- Night mode / morning mode (remembered in the browser) ----------
function applyTheme(t) {
  document.body.classList.toggle("light", t === "light");
  document.getElementById("themeBtn").textContent = t === "light" ? "🌙 Night mode" : "☀️ Morning mode";
  try { localStorage.setItem("analogTheme", t); } catch (e) {}
}
function toggleTheme() {
  applyTheme(document.body.classList.contains("light") ? "dark" : "light");
}
let savedTheme = "dark";
try { savedTheme = localStorage.getItem("analogTheme") || "dark"; } catch (e) {}
applyTheme(savedTheme);

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
    Earth data: NASA POWER. ${target === "mars" ? "Mars" : "Moon"} data: ${tf.source}.</div>
  <div class="best">Best for testing: ${s.tests.join(" · ")}</div></div>`;
  return h;
}

function showFacts() {
  const tf = DATA.facts[target];
  document.getElementById("facts").innerHTML = `<b>Target: ${DATA.targets[target]}</b><br>
    ${tf.where}<br>Mean temp: ${tf.mean_temp_C} C<br>Day-night swing: ${tf.temp_swing_C} C<br>
    Air pressure: ${tf.pressure_kPa} kPa (Earth: 101.3)<br>${tf.notes}<br>
    <span class="muted">Source: ${tf.source}</span>`;
}

function render() {
  showFacts();
  layer.clearLayers();
  const sorted = [...DATA.sites].sort((a, b) => score(b) - score(a));
  sorted.forEach(s => {
    const sc = score(s);
    const m = L.circleMarker([s.lat, s.lon], {
      radius: 7 + sc / 10, fillColor: color(sc), fillOpacity: 0.9,
      color: s.known_analog ? "#ffffff" : "#000000", weight: s.known_analog ? 3 : 1,
      bubblingMouseEvents: false
    }).bindPopup(card(s));
    m.addTo(layer); markers[s.name] = m;
  });
  document.getElementById("list").innerHTML = sorted.map((s, i) => `
    <div class="row" onclick="focusSite('${s.name.replace(/'/g, "\\'")}')">
      <span class="rank">${i + 1}</span><span class="nm">${s.name}</span>
      ${s.known_analog ? "" : '<span class="tag new">NEW</span>'}
      <span class="dot" style="background:${color(score(s))}"></span>
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
// ---------- Scan any place on Earth (live NASA POWER request) ----------
const POWER = "https://power.larc.nasa.gov/api/temporal/climatology/point?parameters=T2M,T2M_RANGE,PRECTOTCORR,RH2M,ALLSKY_SFC_SW_DWN&community=RE&format=JSON";
const clamp = x => Math.max(0, Math.min(1, x));
let scan = null, scanMarker = null;

function featuresFor(c, terrain, t) {
  const rain = c.PRECTOTCORR || 0, rh = c.RH2M == null ? 50 : c.RH2M, swing = c.T2M_RANGE || 0;
  const temp = c.T2M == null ? 20 : c.T2M, elev = c.ELEVATION || 0;
  return {
    dryness: clamp(1 - rain / 2), low_humidity: clamp(1 - rh / 80), temp_swing: clamp(swing / 18),
    cold: clamp((25 - temp) / 45), altitude: clamp(elev / 4000),
    terrain: DATA.terrainValues[t][terrain] ?? 0.3,
  };
}

function bestFor(terrain, fs) {
  const tests = [];
  if (DATA.terrainTests[terrain]) tests.push(DATA.terrainTests[terrain]);
  for (const [f, min, idea] of DATA.featureTests) if (fs[f] >= min && !tests.includes(idea)) tests.push(idea);
  if (!tests.length) tests.push("general astronaut field training");
  return tests.slice(0, 3);
}

function scanCard() {
  const c = scan.climate, other = target === "mars" ? "moon" : "mars";
  const site = { name: "Scanned place", climate: c, known_analog: false, terrain: scan.terrain,
                 tests: bestFor(scan.terrain, featuresFor(c, scan.terrain, "mars")) };
  site[target + "_features"] = featuresFor(c, scan.terrain, target);
  let html = card(site).replace("NEW candidate", "Live scan").replace("<h3>Scanned place</h3>",
    `<h3>Scanned place</h3><div class="f">${scan.lat.toFixed(2)}, ${scan.lon.toFixed(2)} · live NASA POWER data</div>`);
  const ow = DATA.weights[other], ofs = featuresFor(c, scan.terrain, other);
  let osc = 0; for (const k in ow) osc += ofs[k] * ow[k];
  const opts = Object.keys(DATA.terrainValues.mars).map(k => `<option ${k === scan.terrain ? "selected" : ""}>${k}</option>`).join("");
  html = html.replace(`<div class="f">${DATA.targets[target]}</div>`,
    `<div class="f">${DATA.targets[target]} · ${other === "mars" ? "Mars" : "Moon"} score: ${Math.round(osc * 1000) / 10}</div>
     <div class="f">Ground type: <select onchange="setScanTerrain(this.value)">${opts}</select></div>`);
  return html;
}

function setScanTerrain(t) { scan.terrain = t; scanMarker.setPopupContent(scanCard()); }

async function scanPlace(lat, lon) {
  lon = ((lon + 180) % 360 + 360) % 360 - 180;
  if (scanMarker) map.removeLayer(scanMarker);
  scanMarker = L.circleMarker([lat, lon], { radius: 10, color: "#ffb066", weight: 3, dashArray: "4 4",
    fillOpacity: 0.2, bubblingMouseEvents: false }).addTo(map)
    .bindPopup(`<div class="card"><h3>Scanning…</h3><div class="f">Asking NASA POWER about ${lat.toFixed(2)}, ${lon.toFixed(2)}</div></div>`).openPopup();
  try {
    const r = await fetch(`${POWER}&latitude=${lat.toFixed(4)}&longitude=${lon.toFixed(4)}`);
    if (!r.ok) throw new Error("NASA POWER answered " + r.status);
    const d = await r.json(), c = {};
    for (const k of ["T2M", "T2M_RANGE", "PRECTOTCORR", "RH2M", "ALLSKY_SFC_SW_DWN"]) {
      const v = d.properties.parameter[k].ANN; c[k] = (v == null || v <= -999) ? null : v;
    }
    const g = (d.geometry || {}).coordinates || [];
    c.ELEVATION = g.length > 2 ? g[2] : null;
    scan = { lat, lon, climate: c, terrain: "desert" };
    scanMarker.setPopupContent(scanCard());
  } catch (e) {
    scan = null;
    scanMarker.setPopupContent(`<div class="card"><h3>Couldn't scan this place</h3>
      <div class="scanerr">NASA POWER could not be reached from this browser (${e.message}). Check your internet and try again.</div></div>`);
  }
}

map.on("click", e => scanPlace(e.latlng.lat, e.latlng.lng));
const _render = render;
render = function () { _render(); if (scan && scanMarker && scanMarker.isPopupOpen()) scanMarker.setPopupContent(scanCard()); };

buildSliders();
render();

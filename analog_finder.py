"""
Analog Finder - The Analog Mappers (NASA Space Apps 2026)

The main program. Scores Earth places by how similar they are to the Moon's
south pole and Mars's Jezero Crater, using NASA POWER climate data.
Uses ONLY built-in Python - nothing to install.

How to run:   python analog_finder.py
Creates:      results.csv   (table of all scores)
              map_data.js   (the data the website analog_map.html shows)

The other files:
  config.py      settings: targets, weights, Mars/Moon facts, test ideas
  nasa_power.py  downloads NASA data (and keeps a cache)
  scoring.py     the score math and "Best for testing"
  analog_map.html, map.css, map.js   the website
"""

import csv
import json
import os

from config import (TARGETS, TARGET_FACTS, FEATURE_NAMES, TERRAIN_TESTS, FEATURE_TESTS)
from nasa_power import load_cache, fetch_power
from scoring import feature_scores, total_score, best_for_testing

HERE = os.path.dirname(os.path.abspath(__file__))
SITES_FILE = os.path.join(HERE, "sites.csv")
RESULTS_FILE = os.path.join(HERE, "results.csv")
MAP_DATA_FILE = os.path.join(HERE, "map_data.js")


def score_all_sites():
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
        row["tests"] = best_for_testing(row["terrain"], row["mars_features"])
        results.append(row)
        print(f"  [{i}/{len(sites)}] {s['name']:<24} Mars {row['mars_score']:>5}   "
              f"Moon {row['moon_score']:>5}")
    return results


def save_results_csv(results):
    with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name", "lat", "lon", "terrain", "known_analog", "mars_score",
                    "moon_score", "temp_C", "temp_swing_C", "rain_mm_day",
                    "humidity_pct", "sunlight_kWh", "elevation_m", "best_for_testing"])
        for r in sorted(results, key=lambda r: -r["mars_score"]):
            c = r["climate"]
            w.writerow([r["name"], r["lat"], r["lon"], r["terrain"],
                        "yes" if r["known_analog"] else "no", r["mars_score"],
                        r["moon_score"], c.get("T2M"), c.get("T2M_RANGE"),
                        c.get("PRECTOTCORR"), c.get("RH2M"),
                        c.get("ALLSKY_SFC_SW_DWN"), c.get("ELEVATION"),
                        "; ".join(r["tests"])])


def print_validation(results):
    """Do known analogs score high? Which new places score best?"""
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


def save_map_data(results):
    """Write map_data.js, which the website (analog_map.html) reads."""
    data = {
        "sites": results,
        "targets": {t: TARGETS[t]["label"] for t in TARGETS},
        "featureNames": FEATURE_NAMES,
        "facts": TARGET_FACTS,
        "weights": {t: TARGETS[t]["weights"] for t in TARGETS},
        "terrainValues": {t: TARGETS[t]["terrain"] for t in TARGETS},
        "terrainTests": TERRAIN_TESTS,
        "featureTests": FEATURE_TESTS,
    }
    with open(MAP_DATA_FILE, "w", encoding="utf-8") as f:
        f.write("// Created automatically by analog_finder.py - do not edit by hand\n")
        f.write("const DATA = " + json.dumps(data) + ";\n")


def main():
    results = score_all_sites()
    if not results:
        print("No data downloaded - check your internet connection.")
        return
    save_results_csv(results)
    print_validation(results)
    save_map_data(results)
    print("\nDone! Saved results.csv and map_data.js - open analog_map.html in your browser.")


if __name__ == "__main__":
    main()

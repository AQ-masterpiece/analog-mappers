"""
nasa_power.py - Downloads climate data from NASA POWER (https://power.larc.nasa.gov)

Each answer is saved in nasa_power_cache.json, so running the program again
is instant and works offline. Uses only built-in Python.
"""

import json
import os
import time
import urllib.request

from config import PARAMS, POWER_URL

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(HERE, "nasa_power_cache.json")


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=1)


def fetch_power(lat, lon, cache):
    """Return the yearly-average climate for one place (from the cache, or from NASA)."""
    key = f"{lat},{lon}"
    if key in cache:
        return cache[key]
    url = POWER_URL.format(params=",".join(PARAMS), lat=lat, lon=lon)
    with urllib.request.urlopen(url, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    values = {}
    for p in PARAMS:
        v = data["properties"]["parameter"][p]["ANN"]  # ANN = yearly average
        values[p] = None if v is None or v <= -999 else v  # -999 means "no data"
    coords = data.get("geometry", {}).get("coordinates", [])
    values["ELEVATION"] = coords[2] if len(coords) > 2 else None
    cache[key] = values
    save_cache(cache)
    time.sleep(0.5)  # be polite to the NASA server
    return values

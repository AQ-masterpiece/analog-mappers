"""
config.py - The settings of Analog Finder (The Analog Mappers, NASA Space Apps 2026)

Everything here is a choice our team made, or a real NASA measurement we typed in.
Change a weight or a rule here, run analog_finder.py, and the map updates.
"""

# ---------------------------------------------------------------------------
# NASA POWER: which climate numbers we download for each place
#   T2M         mean air temperature (C)
#   T2M_RANGE   daily temperature swing, max - min (C)
#   PRECTOTCORR rainfall (mm/day)
#   RH2M        relative humidity (%)
#   ALLSKY_SFC_SW_DWN  sunlight reaching the ground (kWh/m2/day)
# ---------------------------------------------------------------------------
PARAMS = ["T2M", "T2M_RANGE", "PRECTOTCORR", "RH2M", "ALLSKY_SFC_SW_DWN"]
POWER_URL = (
    "https://power.larc.nasa.gov/api/temporal/climatology/point"
    "?parameters={params}&community=RE&longitude={lon}&latitude={lat}&format=JSON"
)

# ---------------------------------------------------------------------------
# TARGETS: what makes a place Moon-like or Mars-like
#   weights = how important each feature is (they add up to 1.0)
#   terrain = how well each type of land matches (0 to 1)
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

# ---------------------------------------------------------------------------
# Real NASA measurements of the targets (shown on the map for comparison)
#   Mars: Perseverance rover, MEDA weather station, Jezero Crater
#   Moon: Lunar Reconnaissance Orbiter, Diviner instrument, south polar region
# ---------------------------------------------------------------------------
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

# Names of the 6 features, as shown on the website
FEATURE_NAMES = {
    "dryness": "Very little rain",
    "low_humidity": "Dry air",
    "temp_swing": "Big day-night temperature swing",
    "cold": "Cold",
    "altitude": "High altitude (thin air)",
    "terrain": "Terrain type",
}

# ---------------------------------------------------------------------------
# "Best for testing": what NASA could test at each kind of place
# ---------------------------------------------------------------------------
TERRAIN_TESTS = {
    "cave": "building a base inside a lava tube and cave-exploring robots",
    "polar": "ice drilling and cold-proof equipment",
    "volcanic": "driving rovers on rough basalt rock",
    "crater": "landing and navigating inside craters",
    "acidic": "searching for signs of life in harsh chemistry",
    "desert": "long rover drives on dry, rocky ground",
    "dunes": "rover wheels and mobility on loose sand",
}
FEATURE_TESTS = [
    # (feature, minimum 0-1 score, test idea)
    ("cold", 0.7, "ice drilling and cold-proof equipment"),
    ("dryness", 0.9, "dust-proof rovers and solar panels"),
    ("temp_swing", 0.8, "materials that survive hot days and cold nights"),
    ("altitude", 0.6, "equipment in thin air and strong UV"),
]

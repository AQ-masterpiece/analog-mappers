"""
scoring.py - Turns NASA numbers into a 0-100 similarity score

Step 1: each NASA number becomes a feature score from 0 to 1 (1 = very Moon/Mars-like)
Step 2: each feature score is multiplied by its weight (from config.py)
Step 3: the results are added up and multiplied by 100
"""

from config import TARGETS, TERRAIN_TESTS, FEATURE_TESTS


def clamp(x):
    """Keep a number between 0 and 1."""
    return max(0.0, min(1.0, x))


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


def best_for_testing(terrain, fs):
    """Pick up to 3 test ideas from the terrain and the strongest features."""
    tests = []
    if terrain in TERRAIN_TESTS:
        tests.append(TERRAIN_TESTS[terrain])
    for feature, minimum, idea in FEATURE_TESTS:
        if fs[feature] >= minimum and idea not in tests:
            tests.append(idea)
    if not tests:
        tests.append("general astronaut field training")
    return tests[:3]

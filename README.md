# Analog Finder 🌍➡️🌕🔴
**The Analog Mappers, NASA Space Apps Challenge 2026 (Bahrain)**

🔗 **Live map:** https://aq-masterpiece.github.io/analog-mappers/analog_map.html

## What it does
Analog Finder scores **30 places on Earth** by how similar they are to two future exploration sites:
- 🔴 **Mars: Jezero Crater** (Perseverance landing site)
- 🌕 **Moon: South Pole** (Artemis base region)

Sites cover every environment in the challenge: **deserts, polar regions, volcanic fields, craters, dunes, acidic terrain and lava tube caves**.

## Features
- **Similarity score (0–100)** for Mars and the Moon, from NASA climate data plus terrain type
- **Interactive map** with a ranked list and a card for each site explaining *why* it matches
- **Mars vs Moon comparison table** on every card (this site vs real NASA mission measurements)
- **🎚️ Mission sliders:** users set how much each feature matters (cold, dryness, terrain…) and the ranking updates live, so scientists can tune it to their own mission
- **🧪 "Best for testing":** each site suggests what NASA could test there (e.g. ice drilling, dust-proof rovers, building a base inside a lava tube)

## Validation
With our default weights, **3 of the top 4 Mars sites are well-known NASA analogs** (Qaidam Basin, McMurdo Dry Valleys, Atacama Desert). This gives us confidence in the less-established sites that score close to them.

## Highlighted candidates
- **Mars-like:** Tso Kar (Ladakh, India), Wadi Rum (Jordan), Tibesti (Chad)
- **Moon-like:** Tibesti, Harrat Khaybar (Saudi Arabia), Al Wahbah Crater (Saudi Arabia)
- **🕳️ Umm Jirsan lava tube (Saudi Arabia):** top 3 for both Mars and the Moon among our candidates, a potential site to practice building bases inside lava tubes

## Data sources
- **Earth:** NASA POWER Climatology API (temperature, day-night swing, rain, humidity, elevation)
- **Mars:** NASA Perseverance rover, MEDA instrument (Rodríguez-Manfredi et al., 2023, *Nature Geoscience*)
- **Moon:** NASA Lunar Reconnaissance Orbiter, Diviner Lunar Radiometer
- **Base map:** Esri World Imagery

## How to run
Needs only Python 3, nothing to install.
```
python analog_finder.py
```
This downloads NASA data, prints the scores, and builds `analog_map.html` and `results.csv`.

## Limitations (v1)
- Climate data is a ~50 km grid average, not the exact spot
- Terrain types, thresholds and default weights are our team's choices (the sliders let users change the weights)
- Cave scores use surface climate, not conditions inside the cave
- Some highlighted candidates have been studied before; we call them *less-established*, not new to science

## Team
The Analog Mappers, NASA Space Apps Challenge 2026, Bahrain
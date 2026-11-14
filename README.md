# Analog Finder 🌍➡️🌕🔴
**The Analog Mappers, NASA Space Apps Challenge 2026 (Bahrain)**

🔗 **Live map:** https://aq-masterpiece.github.io/analog-mappers/analog_map.html

## What it does
Analog Finder scores 30 places on Earth by how similar they are to two future exploration sites:
- 🔴 **Mars: Jezero Crater** (Perseverance landing site)
- 🌕 **Moon: South Pole** (Artemis base region)

Each site gets a 0–100 similarity score from NASA climate data plus terrain type, shown on an interactive map with a card explaining *why* it matches.

## Validation
Our method ranked three famous NASA Mars analogs (Qaidam Basin, McMurdo Dry Valleys, Atacama) in the **top 4 of 30**, so we trust the new sites that score close to them.

## New analog candidates
- **Mars-like:** Tso Kar (Ladakh), Wadi Rum (Jordan), Tibesti (Chad)
- **Moon-like:** Tibesti, Harrat Khaybar and Al Wahbah Crater (Saudi Arabia)
- **Caves:** Umm Jirsan lava tube (Saudi Arabia) is the most Mars-like cave in our study

## Data sources
- **Earth:** NASA POWER Climatology API (temperature, day-night swing, rain, humidity, elevation)
- **Mars:** NASA Perseverance rover, MEDA instrument (Rodríguez-Manfredi et al., 2023, *Nature Geoscience*)
- **Moon:** NASA Lunar Reconnaissance Orbiter, Diviner Lunar Radiometer
- Base map: Esri World Imagery

## How to run
Needs only Python 3, nothing to install.
python analog_finder.py

## Limitations (v1)
- Climate is a ~50 km grid average, not the exact spot
- Terrain types and scoring weights are our team's choices
- Cave scores use surface climate, not cave interiors
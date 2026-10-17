# Stratospheric balloon coverage over Europe → Black Sea

Google's [Balloon Learning Environment](https://github.com/google/balloon-learning-environment)
(BLE) driven by **real 2025 winds** instead of its synthetic tropical wind
model, to test year-round stratospheric balloon coverage from Portugal to the
Black Sea.

## Findings so far

| Study | Script | Result |
|---|---|---|
| Station-keeping at 22 European / Black Sea sites, 2 flights/month | `run_coverage.py`, `analyze.py` | ~4% time within 50 km (vs 38% for the same controller in stock tropical BLE). Winter westerlies leave nothing to steer with. |
| Slow-traversal fleet (steer for the lowest wind), 5 launch sites × 24 dates × 3 controllers | `run_drift.py`, `analyze_drift.py` | Mean 5.4 days over region per balloon (3.2 passive) → ~310 launches/day for full 50 km-cell coverage. Winter ~1.5 days. |
| Radio return by glider | `glide.py`, `glider_sizing.py` | 78% recovered at 16 kg/m² wing loading, 94% at 29 kg/m² (L/D 12): heavier gliders penetrate headwinds better. |
| Envelope landing after cut-down | `analyze_envelopes.py` | 66% land on land; median 26 km parachute drift. |
| Burning the envelope at altitude | `burn_sim.py` | Median 90% consumed but film shreds scatter over ~200 km; ~215 kg CO₂ per balloon if fully burnt. Not safer than parachute cut-down. |

Charts and per-flight CSVs are in `results/`.

## Setup

```bash
uv venv -p 3.10 .venv
uv pip install -p .venv -r requirements.txt
```

Run with `PYTHONWARNINGS=ignore .venv/bin/python -I <script>.py`.
The full drift sweep takes ~7 min on 8 cores; the station-keeping sweep ~3.3 h.

## Data

`data/gfs_europe_2025.npz`: hourly GFS winds for 2025 at 150/100/70/50/30 hPa
on a 2.5° × 5° grid (32.5–65°N, 15°W–50°E), from the
[Open-Meteo](https://open-meteo.com/) historical forecast API (CC BY 4.0).
Regenerate with `fetch.py` (throttled for the free tier, ~40 min).

## Modelling caveats

- BLE's solar model rejects |lat| ≥ 60°, so the region stops at 59.5°N.
- BLE's physics assumes helium; the hydrogen case changes only gas mass/lift.
- No wind data below 150 hPa: glider and parachute descent use the 150 hPa
  wind tapered to 30% at the surface.
- Controllers are simple heuristics (BLE's StationSeeker, slow-wind and
  steer-to-centre), not a trained agent.

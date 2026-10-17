# Stratospheric balloon coverage over Europe → Black Sea

Google's [Balloon Learning Environment](https://github.com/google/balloon-learning-environment)
(BLE) driven by **real 2025 winds** instead of its synthetic tropical wind
model, to test year-round stratospheric balloon coverage from Portugal to the
Black Sea.

## Findings so far

| Study | Script | Result |
|---|---|---|
| Station-keeping at 22 European / Black Sea sites, 2 flights/month | `run_coverage.py`, `analyze.py` | ~4% time within 50 km (vs 38% for the same controller in stock tropical BLE). Winter westerlies leave nothing to steer with. |
| Slow-traversal fleet (steer for the lowest wind), 5 launch sites × 24 dates × 3 controllers | `run_drift.py`, `analyze_drift.py` | Mean 5.4 days over region per balloon (3.2 passive); winter ~1.5 days. ~310 launches/day only if balloons tiled the region perfectly; with random spacing, ~95% coverage needs ~1,100/day (see cost model). |
| Radio return by glider | `glide.py`, `glider_sizing.py` | 78% recovered at 16 kg/m² wing loading, 94% at 29 kg/m² (L/D 12): heavier gliders penetrate headwinds better. |
| Envelope landing after cut-down | `analyze_envelopes.py` | 66% land on land; median 26 km parachute drift. |
| Burning the envelope at altitude | `burn_sim.py` | Median 90% consumed but film shreds scatter over ~200 km; ~215 kg CO₂ per balloon if fully burnt. Not safer than parachute cut-down. |
| Cost vs satellite systems | `cost_model.py` → `results/cost_comparison.md` | ~€15.5 B/yr (€10.6–22.1 B) for ~95% year-round coverage, ~53× Starlink's attributable cost per km². Envelope and payload costs dominate; hydrogen is ~0.3%. |
| Cost reduction levers | `cost_reduction.py` → `results/cost_reduction.md` | Engineering levers (envelope cost at volume, 94% payload recovery, 60–80 km footprint) cut the 95% year-round fleet to ~€4.2 B/yr, ~15× Starlink. Only a thinner hybrid service (50% coverage with satellite backstop, winter 50%, populated land) reaches ~4.6×. |
| Forecast-lookahead controller | `planner.py`, `run_drift.py --controllers plan` | Paired with the slow controller: fewer very short flights but no change in mean dwell (Little's law: launches ∝ 1/mean dwell), so no cost saving; winter unchanged. |
| Glider return tuning (Fable) | `glide_tuning.py` → `results/glider_tuning.md` | Speed-to-fly guidance + release at last hour a site is reachable with 100 km margin; L/D 14 @ 20 kg/m² recovers 98.0% under wind-error Monte Carlo (vs 64% today). Ceiling 98.3%: add a west-Ireland/Brittany site. |
| Multi-pass hemispheric flights | `run_multipass.py`, `analyze_multipass.py` (NOAA band winds) | Median 85-day flights, 2.5 laps, 4 Europe passes → launches ×0.42–0.62. But ~22% of time over Russia/C.Asia/China; China avoidance via a northern corridor fails (all flights still cross, more power failures) → launches ×0.60–0.77. |
| Ship vs land launch | `run_ship.py` | With a run-for-Europe approach rule, Atlantic ship launches match the best land sites (~3.1 d rotating, 13% never arrive) but don't beat them; choosing the best site per date (mobile launch) gives ×1.6–1.75 dwell with hindsight. |
| Combined per-flight cost | `combined_cost.py` | Lighter hardware + learning curve + 98% glider recovery + gig pickup + launch-site choice: ~€12k/flight (€7–27k), fleet ~€3.8 B/yr ≈ 13× Starlink; with 60–80 km footprint ~6× (2.7–20×). |

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

`data/ncep_band_2025.npz` (not committed, 72 MB): NCEP/NCAR Reanalysis-1 2025 winds, 25–70°N, all longitudes, 6-hourly, from NOAA PSL. Download `uwnd.2025.nc` and `vwnd.2025.nc` from https://downloads.psl.noaa.gov/Datasets/ncep.reanalysis/pressure/ and run `python subset_ncep.py <dir>`.

## Modelling caveats

- BLE's solar model rejects |lat| ≥ 60°, so the region stops at 59.5°N.
- BLE's physics assumes helium; the hydrogen case changes only gas mass/lift.
- No wind data below 150 hPa: glider and parachute descent use the 150 hPa
  wind tapered to 30% at the surface.
- Controllers are simple heuristics (BLE's StationSeeker, slow-wind and
  steer-to-centre), not a trained agent.

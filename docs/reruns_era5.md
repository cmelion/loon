# Runbook: the ERA5 reruns

*2026-10-17. For whoever runs the simulations on the machine that has the engine. The nine reruns are listed in `results/mitigation_research.md` in the order they pay; this file says, for each one, what exists in the repository today, the exact command, what it writes, and what number it changes. Three of the nine can be run now. The rest need code that is specified here and not yet written.*

## 0. Before anything

```bash
cd loon && git pull
uv venv -p 3.10 .venv && uv pip install -p .venv -r requirements.txt
uv pip install -p .venv cdsapi
```

ERA5 needs a Copernicus Climate Data Store account and the API key in `~/.cdsapirc`; the registration and the licence acceptance are a person's clicks, not a script's: https://cds.climate.copernicus.eu/how-to-api. Requests are queued; a year of one product takes minutes to hours.

What changed in the code for these reruns (all backward compatible; every existing command runs as before):

- `europe_ble.WindGrid` now reads the file's `t0` key as its epoch, so a file for 2019 places a 2019 launch date correctly. `WIND_GRID=<path>` overrides the default grid for every script that calls `WindGrid()` without a path, and the module epoch `T0` follows it.
- `run_drift.py` and `run_multipass.py` take `YEAR=<yyyy>` (default: the grid's year) and write `results/drift_<year>.csv`; multipass keeps its `multipass_2025` name, so copy or tag its output per year by hand.
- `outage_scenario.py` takes `BALLOON_GBPS=a,b,c` and writes `results/outage_scenario_<a>_<b>_<c>.csv`.
- New: `fetch_era5.py` (rerun 1) and `shear_hist.py` (rerun 2).

## 1. ERA5 ingest (everything else depends on it)

Two products, one file per year. Resolution is a budget decision: 0.25° hourly full column over the band is about 35 billion values per component per year and does not fit anything; 1° six-hourly fits a laptop and is finer than the 2.5° × 5° grid every published number came from.

```bash
# hemispheric band to the pole, 150-30 hPa, for multipass, ship and border runs
.venv/bin/python fetch_era5.py --product band   --years 2010-2025 --grid 1.0
# Europe full column 1000-30 hPa (and an upper-only copy), for descent, glider, drift
.venv/bin/python fetch_era5.py --product europe --years 2010-2025 --grid 1.0
# one winter at 0.25 deg over western Europe for the W10 terminal-phase study
.venv/bin/python fetch_era5.py --product europe --years 2024 --grid 0.25 --area 60,-15,40,20 --tag w10
```

Volume: band 1° about 1.4 GB a year, europe 1° about 0.7 GB a year, both components, float32 compressed. Start with 2025 (direct comparison with the GFS and NCEP files) and one older winter, then the rest. Check each file the way `subset_ncep_full.py` does: the printed NaN fraction should be 0, and the January mean eastward wind at 50°N 10°E should rise from a few m/s at 1000 hPa to 20–40 at 250 hPa and fall again above 100 hPa.

Writes `data/era5_band_<year>.npz`, `data/era5_europe_<year>.npz`, `data/era5_europe_upper_<year>.npz`, none committed (add `data/era5_*` to `.gitignore` if it is not there).

## 2. Winter shear and the perfect-controller ceiling (W1) — runs now

```bash
.venv/bin/python shear_hist.py data/gfs_europe_2025.npz --tag gfs_2025_djf          # baseline, already run
.venv/bin/python shear_hist.py data/era5_europe_upper_2025.npz --tag era5_2025_djf
for y in 2010 2012 2015 2018 2019 2021 2024; do
  .venv/bin/python shear_hist.py data/era5_europe_upper_$y.npz --tag era5_${y}_djf
  .venv/bin/python shear_hist.py data/era5_europe_upper_$y.npz --months 6,7,8 --tag era5_${y}_jja
done
```

What it gives: for every grid point at 45–55°N and every six hours of the season, the largest angle between wind directions across 150–30 hPa (if small, there is no level to choose), the speed at the slowest level, and the crossing time of a 3,000 km region for a controller that always sits at that level. On the 2025 GFS file, already in `results/shear_gfs_2025_*.csv`: in December–February the median spread is 31° and the slowest level still runs 13 m/s eastward 93 % of the time, so the ceiling is 2.4 days; in June–August the spread is 152° and the slowest level is 2.7 m/s, ceiling 12 days. The question the ERA5 years answer is whether 2025 was a typical winter. Paste the printed summaries into a table in `results/shear_summary.md`; if several winters give a ceiling above four days, W1's "nothing to steer with" is too strong and the winter product changes.

## 3. Descent winds and release rules on ERA5 (W7, W10) — runs now for 2025

`jet_test.py` names its grids in a dict at the top. Add ERA5 rows and run:

```python
GRIDS = {'gfs_taper': 'data/gfs_europe_2025.npz',
         'ncep_taper': 'data/ncep_europe_upper_2025.npz',
         'ncep_full': 'data/ncep_europe_full_2025.npz',
         'era5_taper': 'data/era5_europe_upper_2025.npz',
         'era5_full': 'data/era5_europe_2025.npz'}
```

```bash
PYTHONWARNINGS=ignore .venv/bin/python -I jet_test.py          # results/jet_test.csv, .md
PYTHONWARNINGS=ignore .venv/bin/python -I forecast_release.py  # results/forecast_release.csv, .md
```

Both scripts replay the 120 stored slow-controller tracks from 2025 (`results/slow_tracks.csv`), so they are valid for 2025 only; other years need rerun 4 first. The number that changes: the 98.3 % recovery ceiling and the 1.98-day forecast-release dwell. Expect the headline near the site-network ceiling; expect the terminal phase (last 3 km) to be where ERA5's finer winds bite. The W10 0.25° file is for a separate descent-only study: no script exists for it yet; the specification is one Monte Carlo of parachute and parafoil descents from 150 hPa over the W10 box with the full column, reporting landing-ellipse radius against release altitude, and it belongs with the recovery decision in `results/mitigation_research.md`.

## 4. Re-fly the drift set per year, and winter power (W3, W5) — drift runs now, power needs code

```bash
for y in 2019 2021 2024 2025; do
  WIND_GRID=data/era5_europe_upper_$y.npz PYTHONWARNINGS=ignore .venv/bin/python -I run_drift.py   # ~7 min on 8 cores
done
# then the per-year dwell table:
.venv/bin/python analyze_drift.py   # reads results/drift_2025.csv; point it at each year's file or loop by hand
```

`WIND_GRID` moves the whole run to that year: the grid, the epoch and the launch dates. The number that changes: mean dwell 5.4 days (and the winter 1.3–1.9 days) becomes a distribution across years, which is what the cost model should use instead of one year.

The light vehicle (W3) is not in the code. BLE's balloon mass, envelope volume and solar array live in `balloon_learning_environment.env.balloon.balloon` and `stable_init`; the light-vehicle rerun needs a subclass with the 40 kg payload, the 16–18 kg envelope from `results/envelope_cost.md` and the array area from the power budget, and `run_drift.py` to accept it as a flag. The power rerun (W5) needs `analyze_power.py` to take a latitude and a date for irradiance instead of BLE's solar model. Both are half a day of work each for someone with the engine running and are the right first coding task after the ingest.

## 5. The outage scenario at Loon-class capacity (W11, W23) — runs now

```bash
BALLOON_GBPS=0.04,0.2,0.5 .venv/bin/python -I outage_scenario.py   # results/outage_scenario_0.04_0.2_0.5.csv
```

The number that changes: 254 balloons and 443 launches a day for the 300 km winter voice-and-text zone were computed at 2 Gbps a balloon; at 0.2 Gbps the balloon count is set by capacity rather than by cell geometry, and the launch rate scales with it. Then do the W23 arithmetic by hand from the new launches-per-day column: at 6–12 launches a site a day, sites needed = launches ÷ 6 and ÷ 12. That is the honest surge geometry until `surge_dispatch.py` exists (specification below).

## 6. Availability on population cells and time to N balloons (W24, W25) — needs code

Not written. Specification for `availability.py`: inputs are the per-year track files from rerun 4 (positions each hour), a population raster (GHSL GHS-POP 2025 at 1 km or Eurostat GEOSTAT 1 km grid, downloaded by the operator), a launch schedule (launches per site per day, from `outage_scenario` or a standing-layer count) and a service radius (40, 80, 194 km). For every hour, place every balloon aloft under the schedule on its track, mark the population cells within the radius, split each balloon's capacity across its cells, and record per cell whether it is served. Outputs: population-weighted availability by month, the distribution of outage durations per cell, and winter separated, per year. The time-to-N replay (W24) is the same loop started from a cold start or from 50 or 100 balloons already aloft at random track positions, reporting hours to 10, 50 and 90 % of the required balloon count over each candidate zone. These two replace the random-placement branch in `cost_model.py` and are the biggest single change to a published number ("95 % coverage"); they are a one-to-two-day coding task once rerun 4's tracks exist.

## 7. Mesh connectivity on the tracks (W15) — needs code

Specification: for every hour of the availability replay, build the graph of balloons aloft with edges at 500 km and at 700 km, add gateway sites as nodes with a 200 km ground radius, and report the share of balloons connected to at least one gateway, the largest connected component, and the number of balloons whose only path is longer than four hops. Weather-correlated gateway loss: remove every gateway inside a storm box for a day and repeat. Output a table by month and by standing-layer size (25, 50, 100). Half a day on top of rerun 6.

## 8. Border and FIR tagging, and envelope mass flow (W20, W21) — needs data and code

For the border tagging: download the Eurocontrol or OpenAIP FIR boundaries, tag every hourly track position with its FIR and whether the state has authorised overflight (a table the operator fills in), and report hours per flight in unauthorised airspace and the share of flights that cross a border before their forecast termination point. For the mass flow: `cost_comparison.md`'s envelope mass per year at three recovery rates (full land recovery, a third at sea, zero) is arithmetic from the launch counts of reruns 5 and 6 and the envelope mass in `results/envelope_cost.md`; it needs no simulation, only the new launch counts.

## 9. The scenario ledger (W27) — needs code

One table per scenario (planning case, readiness, pilot) that ties launches per day, inventory and circulation time of payloads, envelope mass, delivered capacity and cost per year together, each row traceable to the result file it came from. The €0.2–0.5 B readiness figure is withdrawn until this exists. It is a spreadsheet-sized Python script over the CSVs of reruns 4–7 and should be the last thing written, not the first.

## Reporting back

Commit the small outputs (`results/shear_*.csv`, `results/outage_scenario_*.csv`, `results/jet_test.*`, `results/forecast_release.*`, `results/drift_<year>.csv`) and not the data files. For each rerun, one paragraph in `results/mitigation_research.md` under the rerun's number: the command, the number before, the number after, and whether the architecture decision it supports still holds.

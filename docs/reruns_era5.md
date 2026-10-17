# Runbook: the ERA5 reruns

*2026-10-17. For whoever runs the simulations on the machine that has the engine. The nine reruns are listed in `results/mitigation_research.md` in the order they pay; this file says, for each one, what exists in the repository today, the exact command, what it writes, and what number it changes. Reruns 1, 2, 3 and 5 run now. Reruns 4 (light vehicle and winter power), 6, 7 and 9 have their scripts written and tested on synthetic inputs; none has yet run on the engine or on real tracks, and the light vehicle has not flown. Rerun 8 still needs data and code.*

## 0. Before anything

Tests for the scripts of reruns 4, 6, 7 and 9 run without the engine on synthetic inputs: `uv pip install -p .venv pytest && .venv/bin/python -m pytest tests` (or `python tests/test_<name>.py` one by one). They check the arithmetic, not the physics; the physics still needs the flights listed under rerun 4.

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

Volume: band 1° about 1.4 GB a year, europe 1° about 0.7 GB a year, both components, float32 compressed. Start with 2025 (direct comparison with the GFS and NCEP files) and one older winter, then the rest. Check each file as it lands: the printed NaN fraction should be 0, and `python profile_check.py data/era5_europe_<year>.npz` should show the January box-mean eastward wind over 30–60°N, 0–20°E rising from a few m/s near the surface to a peak of 15–30 m/s near 200–300 hPa and falling again above 100 hPa. A single point such as 50°N 10°E is not a valid check: in January 2025 the jet core over that longitude band sat at about 32°N, so the point shows no 250 hPa peak at all while the box does. The 2025 GFS file gives the box mean at the overlapping levels as 19.1, 18.7, 18.5, 19.7 and 24.9 m/s at 150, 100, 70, 50 and 30 hPa, with the maximum at 32.5°N at 150 hPa and at 60°N above it (the polar-night jet); an ERA5 January file that matches those within 1–2 m/s and shows a 200–300 hPa peak south of 45°N is good. A file with no peak at any latitude in the band has a level-axis, component or sign problem and nothing downstream should run on it.

Writes `data/era5_band_<year>.npz`, `data/era5_europe_<year>.npz`, `data/era5_europe_upper_<year>.npz`, none committed (add `data/era5_*` to `.gitignore` if it is not there).

## 1b. Putting the wind data in the repository

The data belong with the code, and GitHub refuses any file over 100 MB in a commit, so the ERA5 files go up as release assets rather than tracked files (`data/era5_*` stays in `.gitignore`). One release holds them all, one asset per product and year; GitHub allows 2 GB per asset. From the machine that fetched them:

```bash
gh release create data-era5 --repo cmelion/loon --title "ERA5 wind files" --notes "WindGrid npz files from fetch_era5.py; see docs/reruns_era5.md" || true
gh release upload data-era5 data/era5_*.npz --repo cmelion/loon --clobber
```

and on any other machine:

```bash
gh release download data-era5 --repo cmelion/loon --dir data --pattern 'era5_*_2025.npz'
```

The `--pattern` picks the years wanted. The NCEP files (`ncep_band_2025.npz`, `ncep_europe_full_2025.npz`, `ncep_europe_upper_2025.npz`) can go up the same way under a `data-ncep` release so the 2025 comparison is reproducible without NOAA downloads. Record the release tag and the file's `t0` and shape in the rerun's paragraph when a result is reported.

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

## 4. Re-fly the drift set per year, and winter power (W3, W5) — drift runs now; light vehicle and power written, untested on the engine

```bash
for y in 2019 2021 2024 2025; do
  WIND_GRID=data/era5_europe_upper_$y.npz PYTHONWARNINGS=ignore .venv/bin/python -I run_drift.py   # ~7 min on 8 cores
done
# then the per-year dwell table:
.venv/bin/python analyze_drift.py   # reads results/drift_2025.csv; point it at each year's file or loop by hand
```

`WIND_GRID` moves the whole run to that year: the grid, the epoch and the launch dates. `LAUNCH_SET=nordic` flies Copenhagen, Gothenburg, Riga and Tallinn instead of the five western and central sites (`LAUNCH_SET=all` flies both sets), writing `results/drift_<year>_nordic.csv`; these were never run, winter should carry them out of the region within a day and summer should make them the best sites, and the per-month dwell by site is the number to report. The number that changes: mean dwell 5.4 days (and the winter 1.3–1.9 days) becomes a distribution across years, which is what the cost model should use instead of one year.

**The heavy vehicle (class M) needs no new dwell run.** In mass it is the simulator's own balloon: `vehicle.py`'s `heavy` preset (100 kg payload, 60 kg envelope, hydrogen, Loon's 2,380 Pa film) sizes to 1,864 m³ against BLE's 1,804, so every track in `results/` already describes its drift and dwell. What it changes is power: 1,000 W by day, 300 W at night for a reduced service, a 3,000 Wp array and a fuel cell on the lift gas for the rest of the night, all labelled assumptions in the preset. Run:

```bash
VEHICLE=heavy PYTHONWARNINGS=ignore .venv/bin/python -I run_drift.py                      # end modes and dwell under the class M loads; writes results/drift_<year>_heavy.csv
VEHICLE=heavy WINTER=1 MAX_DAYS=60 FUEL_CELL=vent PYTHONWARNINGS=ignore .venv/bin/python -I run_multipass.py   # winter nights on the lift gas; rename the multipass_2025*.jsonl it writes with a _heavy tag
.venv/bin/python winter_power.py --vehicle heavy --array tilt --area-m2 14 --lat 50 --dates 2025-01-15,2025-06-15   # the day budget by hand; 14 m² is about 3 kWp at 22 %
```

The numbers to report: how many January nights the class M loads survive before the fuel cell has burned 7–16 % of the lift gas, and whether a 3 kWp array closes the day at 50°N in January. Those are the phase 3 gate in `results/deployable_now.md`.

The light vehicle (W3) is in `vehicle.py` and has not flown. `vehicle.size()` derives what BLE needs from the envelope note's inputs (40 kg payload, 18 kg envelope, 60 hPa ceiling, 5 % spare lift, 1,000 Pa design superpressure, hydrogen): 2,268 mol of H₂ (4.6 kg) and a 676 m³ envelope, against the note's 678 m³; `vehicle.apply()` writes those into the BLE balloon state after the arena is built, re-runs `stable_init`, sets the lift-gas molar mass to hydrogen, scales the pump and the array, and `run_drift.py --vehicle light` (also `track_slow.py --vehicle light`) calls it and writes `results/drift_<year>_light.csv`. The sizing is tested (`tests/test_vehicle.py`); the flight is not, and the module docstring lists what the first engine run must check, in order: whether the vehicle survives its first sunset and sunrise at 1,000 Pa in BLE's thermal model (raise `dp_max_pa` if it bursts and record the rating), the launch pressure, the pump and array scaling assumptions, then the re-fly. The hydrogen correction is a monkeypatch of `constants.HE_MOLAR_MASS` in the worker process; confirm no other module caches it.

```bash
python -I vehicle.py                                              # sizing table, no engine
WIND_GRID=data/era5_europe_upper_2025.npz PYTHONWARNINGS=ignore .venv/bin/python -I run_drift.py --vehicle light
WIND_GRID=data/era5_europe_upper_2025.npz PYTHONWARNINGS=ignore .venv/bin/python -I track_slow.py --vehicle light --procs 8
```

The power rerun (W5) is `winter_power.py`, a sibling of `analyze_power.py` (which still reads the multipass runs). It takes latitude, date, float pressure, array model and area, hotel loads and the battery, and computes the day from the sun's geometry with BLE's own attenuation and, for `--array loon`, BLE's exact six-panel array, so it ties back to the multipass runs; it writes `results/winter_power_budget_<tag>.csv` with day and night length, harvest, surplus, the night's need, whether the day closes the night, the largest night load the array carries, and the battery and array mass against the 40 kg payload. What it already says, with no engine: at 50 °N on 15 January at 60 hPa the night is 14.7 h; BLE's own array (1,042 W peak, 8.0 kWh harvested) leaves a 6.9 kWh surplus against a 2.7 kWh night at BLE's 184 W, but BLE's 3 kWh battery at 80 % depth cannot hold that night, which is why the 3 kWh flights in `results/winter_power_summary.csv` died at 1.8 days; and a 300 W night on the light vehicle needs 4.4 kWh, a 37 kg pack at 150 Wh/kg, which is the whole payload (W5). Cloud, frost and gondola attitude are not modelled; every mass and efficiency is a labelled ASSUMPTION.

```bash
python winter_power.py --vehicle light --array tilt --sweep-area 2,4,8 --night-w 300 --lat 50 --monthly 2025
python winter_power.py --vehicle loon --array loon --lat 50 --monthly 2025          # BLE's array, for the tie-back
python -m pytest tests/test_vehicle.py tests/test_winter_power.py
```

The runbook's track files: `track_slow.py` now follows `WIND_GRID`/`YEAR` and writes `results/slow_tracks_<year>.csv` (plus `_summary`), which reruns 6 and 7 replay; the 2025 GFS run keeps its original name `results/slow_tracks.csv`. Run it for each year after `run_drift.py`, since the per-flight drift file has no hourly positions.

## 5. The outage scenario at Loon-class capacity (W11, W23) — runs now

```bash
BALLOON_GBPS=0.04,0.2,0.5 .venv/bin/python -I outage_scenario.py   # results/outage_scenario_0.04_0.2_0.5.csv
```

The number that changes: 254 balloons and 443 launches a day for the 300 km winter voice-and-text zone were computed at 2 Gbps a balloon; at 0.2 Gbps the balloon count is set by capacity rather than by cell geometry, and the launch rate scales with it. Then do the W23 arithmetic by hand from the new launches-per-day column: at 6–12 launches a site a day, sites needed = launches ÷ 6 and ÷ 12. That is the honest surge geometry until `surge_dispatch.py` exists (specification below).

## 6. Availability on population cells and time to N balloons (W24, W25) — written, needs the tracks and a raster

`availability.py` does this, on top of `replay.py` (shared with rerun 7), and is tested on synthetic tracks and a synthetic population (`tests/test_replay.py`, `tests/test_availability.py`). Inputs: the track file(s) from `track_slow.py`, a population file the operator downloads (GHSL GHS-POP GeoTIFF with `rasterio`, a GEOSTAT CSV with `pyproj`, or any `lat,lon,pop` CSV; aggregated to `--cell-km`, default 10 km), a schedule (`--launches-per-day` from the `launches_day` column of rerun 5, or `--standing N` for a layer held at N by Little's law each month), the radii, `--balloon-gbps` (default 0.2) and `--mbps-per-person` (0.015 voice and text, 0.05 degraded data, as in `outage_scenario.py`). Service ends at exit, or at the release hour with `--drift results/drift_<year>.csv`. Each launch flies a stored track of the same site launched within three weeks of it, so the replay keeps site and season but not the day's weather; balloons launched in the same fortnight share a few tracks, which clusters them more than reality and is the conservative direction. Each hour, each balloon's capacity is split over the cells in its disc by population; a cell is covered if any disc reaches it and served if the capacity it receives meets its demand.

```bash
.venv/bin/python track_slow.py --procs 8                                      # 2025 tracks if not present
# population: e.g. GHS_POP_E2025_GLOBE_R2023A_54009_1000_V1_0.tif from the GHSL download page, or the GEOSTAT 1 km CSV
.venv/bin/python availability.py --tracks results/slow_tracks.csv --pop data/ghs_pop_2025_1km.tif \
    --standing 100 --radius-km 40,80,194 --drift results/drift_2025.csv --time-to-n
.venv/bin/python availability.py --tracks results/slow_tracks.csv --pop data/ghs_pop_2025_1km.tif \
    --launches-per-day 443 --radius-km 80 --balloon-gbps 0.2
for y in 2019 2021 2024; do .venv/bin/python availability.py --tracks results/slow_tracks_$y.csv --pop data/ghs_pop_2025_1km.tif --standing 100 --drift results/drift_$y.csv; done
```

Writes `results/availability_<tag>.csv` (by radius and month, plus DJF, JJA and the year: population-weighted covered and served shares, mean aloft, launches a day), `_outages.csv` (population-weighted outage-duration tails by season of onset, for coverage and for capacity, with p50 and p90), `_cells.csv` (per cell, for a map) and, with `--time-to-n`, `results/time_to_n_<tag>.csv`: for the 21 recovery stations as candidate zone centres (or `--zones` CSV) and a start every day of the year, hours from a cold start and from 50 or 100 balloons already aloft at random track positions to 10, 50 and 90 % of the zone's requirement (its population from the raster at the given demand and capacity, floored at one balloon per `--footprint-km` disc), launching at `--surge-per-site-day` (default 12, W23) from every site, with the share of starts that never got there within a week. On synthetic data the capacity rows already show the shape to expect: at 0.2 Gbps a balloon a standing layer of 100 covers people but serves almost none of them, and no 300 km zone reaches its requirement in 72 hours; use `--n-required` to ask the time-to-N question for a fixed balloon count instead. The number that changes: "95 % coverage" becomes a served share by month with a winter row, per year, and the cost model's random-placement branch is replaced by `served_pop_share` (the ledger in section 9 reads it).

## 7. Mesh connectivity on the tracks (W15) — written, needs the tracks

`mesh_connectivity.py` does this on the same replay (`tests/test_mesh.py` checks the graph metrics on a hand-placed chain and the replay on synthetic tracks). Every `--every-h` hours (default 6) it builds the graph of balloons aloft under a standing layer of 25, 50 and 100, with balloon-balloon edges at 500 and 700 km and balloon-gateway edges within 200 km of a gateway (default: the 21 recovery stations; `--gateways` CSV or `--gateway-grid-km 350` for the sixty-site grid of `target_population.md`), and reports by month, DJF, JJA and year: share of balloons with a path to a gateway, largest balloon-only component as a share of aloft, share more than four hops from any gateway (or unconnected), isolated share and mean degree. `--storm-box 44,56,-12,8` (default) removes every gateway in the box and evaluates the same hours again, so each row comes as `gateways=all` and `gateways=storm`. On synthetic eastward tracks the random-geometric estimates of `target_population.md` section F reproduce: 25 balloons fragment at 500 km and hold together at 700 km, 100 are connected at either range.

```bash
.venv/bin/python mesh_connectivity.py --tracks results/slow_tracks.csv --standing 25,50,100 --every-h 6
for y in 2019 2021 2024; do .venv/bin/python mesh_connectivity.py --tracks results/slow_tracks_$y.csv --standing 25,50,100; done
```

Writes `results/mesh_<tag>.csv`. Routing capacity, acquisition time and the number of terminals a balloon carries (its mesh degree) are not modelled; the number that changes is the mesh floor, 50 balloons at 500 km in the note, measured on real winter chains and summer scatter rather than random placement.

## 8. Border and FIR tagging, and envelope mass flow (W20, W21) — needs data and code

For the border tagging: download the Eurocontrol or OpenAIP FIR boundaries, tag every hourly track position with its FIR and whether the state has authorised overflight (a table the operator fills in), and report hours per flight in unauthorised airspace and the share of flights that cross a border before their forecast termination point. For the mass flow: `cost_comparison.md`'s envelope mass per year at three recovery rates (full land recovery, a third at sea, zero) is arithmetic from the launch counts of reruns 5 and 6 and the envelope mass in `results/envelope_cost.md`; it needs no simulation, only the new launch counts.

## 9. The scenario ledger (W27) — written, reads whatever reruns 4–7 have produced

`scenario_ledger.py` writes `results/scenario_ledger.csv` (scenario, metric, value, unit, source) and `results/scenario_ledger.md`, one table per scenario (pilot from `deployable_now.md` Configuration B; readiness as a standing layer of `--standing` plus one `--surge-days` surge a year to the `outage_scenario` row for a `--zone-km` winter voice-and-text zone at `--gbps`; planning as the 95 % random-placement layer at `--footprint-km`). It reads `results/drift_<year>.csv` for service dwell (release where recovered) by month and the recovery share, the rerun 5 CSV for the surge balloons and launches a day, and, when present, `results/availability_*.csv` (served share, matched by `standing<N>` in the tag), `results/mesh_*.csv` and `results/time_to_n_*.csv`; everything else is a constant in `CONSTANTS` with its source. Per scenario: launches a day standing and surge, flights a year, sites at 12 launches a site a day, payload circulation (service dwell plus `--turnaround-days`) and inventory by Little's law on the peak rate, payloads consumed, envelope stock for the surge, envelope mass launched and unrecovered at three recovery rates (all recovered, a third at sea, none), gross and delivered capacity, and cost a year in four lines with a low and high per-flight case. `tests/test_ledger.py` runs it on a synthetic `results/` folder.

```bash
.venv/bin/python scenario_ledger.py --year 2025 --gbps 0.2 --standing 100 --zone-km 300 --surge-days 30
.venv/bin/python scenario_ledger.py --year 2019 --standing 50 --turnaround-days 7
```

The number that changes: the withdrawn €0.2–0.5 B readiness figure gets an arithmetic with named inputs; expect the payload inventory (surge launches a day times circulation days) and the sites to be the lines that move it, as the W27 reviewers said.

## Reporting back

Commit the small outputs (`results/shear_*.csv`, `results/outage_scenario_*.csv`, `results/jet_test.*`, `results/forecast_release.*`, `results/drift_<year>.csv`) and not the data files. For each rerun, one paragraph in `results/mitigation_research.md` under the rerun's number: the command, the number before, the number after, and whether the architecture decision it supports still holds.

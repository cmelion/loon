# scenarios/ — scenario bible for the Kessler-world graphic novel

- `world_primer.md` — one page: what is real (cited), what is extrapolated, twelve in-world rules each derived from a simulation result.
- `scenario_catalog.md` — eleven episodes: logline, roles, 6–10 panel beats, problem → solution, and the flight each is built on.
- `epNN_<name>/flight.json` — the real simulated flight the episode uses (track, timeline, altitudes, power state, release/glide/envelope outcome), produced by the tools below. `facts.md` lists every number used and the script or result file it comes from. Some episodes also have `glide_cases.json` (glider variants) or `outage_case.json`.
- `tools/` — small helpers that **replay** existing runs without modifying the simulation scripts:
  - `fly_track.py` replicates `run_drift.fly` (and `run_ship.py`'s approach mode) for one flight and logs the hourly state;
  - `fly_multipass_track.py` replicates `run_multipass.fly` for one hemispheric flight (options via `BATTERY_WH`, `THRUST_MS`, `MAX_DAYS` as in the original runs);
  - `glide_cases.py` evaluates today's and the tuned glider from a flight's track with `glide.py` physics;
  - `outage_case.py` applies `outage_scenario.py`'s formulas to a named zone/population/month;
  - `envelope_stats.py` reproduces `analyze_envelopes.py`'s landing statistics without redrawing its figure.

Every replay was checked against the recorded result (end point, release point and site, glide outcome; for hemispheric flights also days, Europe-days, China-days and max latitude) and matched exactly. One bookkeeping difference: `flight.json` `summary.dwell_h` counts only the 3-minute steps spent inside the region (as the current `run_drift.fly` does), while the older `results/drift_2025.csv` sweep counted all steps, so one-way flights read 0.05 h shorter here (e.g. 13.95 h vs 14.0 h); `summary.flight_h` equals the recorded value.

Regenerate, from the repo root:

```bash
PYTHONWARNINGS=ignore .venv/bin/python -I scenarios/tools/fly_track.py --site Bucharest --date 2025-03-15 --seed 31832 --out scenarios/ep01_westerlies/flight.json
```

```bash
BATTERY_WH=10000 THRUST_MS=3 MAX_DAYS=150 PYTHONWARNINGS=ignore .venv/bin/python -I scenarios/tools/fly_multipass_track.py --site Bucharest --date 2025-05-01 --seed 418984 --out scenarios/ep06_overflight/flight.json
```

The exact site/date/seed/options for each episode are the first lines of its `facts.md`. One-way flights take 1–3 minutes each; 150-day hemispheric flights take a few minutes (the China flight took about four).

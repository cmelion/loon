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
| Combined per-flight cost | `combined_cost.py` | With the redesigned envelope (~€1.1k), 98% glider recovery, lighter hardware, gig pickup and launch-site choice: ~€11k/flight (€6–25k), fleet ~€3.4 B/yr ≈ 12× Starlink per km² (~6× with 60–80 km footprint). |
| Envelope cost (Fable) | `envelope_cost.py` → `results/envelope_cost.md` | Low-Δp (1,000 Pa) 25–30 µm mLLDPE pumpkin, 16–18 kg for a 40 kg payload, built at 400k/yr: ~€1,070 per envelope (€390–2,900), ~9× cheaper than today. Residual cost is parts/operations, not film. |
| Fuel cell + propulsion, China routing | `run_multipass.py` (BATTERY_WH, THRUST_MS) | 10 kWh store: launches ×0.53/0.41/0.32 at 30/60/100-day life. + 3 m/s latitude hold: China reach 100% → 88%, time over China 6% → 2%, launches ×0.49/0.37/0.30, but polar excursions persist and propulsion uses ~52 kWh (~3 kg H₂) per 30 days. |
| Western Canada launches | `run_multipass.py` (LAUNCH_SET=canada) | 60-day flights from BC/Alberta: 4.8 d over Canada, 4.5 d Atlantic, 12.6 d Europe; useful time 46% vs 26% Europe-only; all reach Europe (day ~10). |
| Regional ground-network loss | `outage_scenario.py` → `results/outage_scenario.csv` | 300 km zone (34 M people) without towers: voice/text needs ~250 balloons, 141 launches/day summer (€1.8 M/day) to 443 winter (€5.5 M/day); degraded data 1.7 Tbps vs Starlink's ~0.55 Tbps pro-rata in the zone. |
| Winter power: battery vs fuel cell on the lift gas | `run_multipass.py` (FUEL_CELL=vent/retain, WINTER=1), `analyze_power.py` | 20 Nov–Feb launches per setup, 60-day cap, propeller power charged: median survival 1.8 d (3 kWh), 8.9 d (10 kWh), 13.2 d (fuel cell, water vented), 9.9 d (water kept). Fuel-cell flights all end when 7–16% of the lift gas (0.9–2.3 kg H2) is burned and the envelope loses pressure; kept water only adds mass against the same margin. |

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

## Reviews

- `medium/review.md`: internal fact-check of the Medium draft against `results/` (2026-10-17).
- `medium/panel_review.md`: external five-model review of the same draft, with the reruns it asks for (2026-10-17). Headline: the physics holds; €3.4 B/yr, 98 % recovery and 5.4-day dwell do not survive as findings until the forecast-only glider release, the redesigned vehicle and full-column descent winds are in the runs.
- `results/cost_funding_vs_starlink.md`: cost per person, four ways of pricing equivalent Starlink bandwidth, terminal and refresh costs, funding models (permanent layer vs readiness), and the utility/shortfall lists against Starlink (2026-10-17).
- `results/target_population.md`: who the layer is for, in numbers: residents outside coverage (4–8 M), people passing through uncovered land, government and emergency users (6–9 M), and the surge population whose towers fail (1–50 M at a time); why the fleet should be sized to the surge, a thin standing layer of 50–100 balloons as the exercised form of readiness, the attack-radius comparison with satellites, and the time-to-coverage limit (2026-10-17).
- `results/weakness_register.md` and `results/mitigation_research.md`: every weakness found to date (W1–W50) and the adjudicated mitigation for each from a four-cluster external review; four architecture decisions (winter is a transit product, the radio is Loon-class until proven, recovery by parachute to drop zones rather than glider, exercised readiness with a priced counterfactual to beat) and the nine reruns in the order they pay (2026-10-17).
- `results/radio_and_backhaul.md`: is 2 Gbps per platform feasible and can the backhaul carry it. Plausible as gross outdoor downlink on a 90–100 kg-class payload with 40–70 beams reusing 20 MHz; out of reach on the costed 40 kg payload; no loaded multi-beam stratospheric aggregate published anywhere. Backhaul link classes, the egress funnel, ring gateways as heads not sites, laser energy, and the fuel cell for short winter flights (2026-10-17).
- `results/deployable_now.md`: what can be deployed in the next year (a Thunderhead-flown pilot with a Loon-class radio, summer 2027 and winter 2027–28, €10–20 M), the staged upgrade path with a measurable gate per phase, what is useful on day one, how production and participation scaling carry the cost case, what a comparable constellation costs (IRIS², OneWeb, Kuiper, Starlink, direct-to-cell), the competition for low orbit, and Kessler syndrome as the structural argument for a layer that cannot cascade. Reviewed by four seats the same day (2026-10-17).

## Modelling caveats

- BLE's solar model rejects |lat| ≥ 60°, so the region stops at 59.5°N.
- BLE's physics assumes helium; the hydrogen case changes only gas mass/lift.
- No wind data below 150 hPa: glider and parachute descent use the 150 hPa
  wind tapered to 30% at the surface.
- Controllers are simple heuristics (BLE's StationSeeker, slow-wind and
  steer-to-centre), not a trained agent.

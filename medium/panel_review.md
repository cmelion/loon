# Research note: external panel review of the Medium draft (2026-10-17)

**Status:** findings, not yet acted on. Each item names what it affects and the rerun, recomputation or wording change that closes it. Complements `medium/review.md` (the internal fact-check against `results/`), which already covers the Starlink-outage length, the Iberian figures, the 1995 Belarus wording, the ICAO link, the winter-dwell month range and the outage-table cost basis; those are not repeated here except where the panel adds something.

**What was reviewed:** the Medium draft as of 2026-10-17 (text as in `medium/medium_body.md`, charts omitted). Five non-Claude reviewers (gpt-5.6-sol, gemini-3.1-pro-preview, grok-4.6, gpt-6.1-sol, gpt-6-sol) answered a seven-question brief independently, with the arithmetic and incident checks from the internal review stated as the first opinion. Counts below are how many of the five raised the point. Raw answers, brief and context are archived outside the repo.

## Summary

The physics, the arithmetic and the cited incidents hold. The headline figures do not survive as findings: €3.4 bn/yr, 98 % glider recovery, 5.4-day dwell, 7.7 Tbps and 95 % coverage are scenario outputs resting on (a) hindsight in the glider release that is not carried into the cost, (b) a vehicle that was costed but never flown, (c) a descent wind profile with no troposphere, and (d) a wind grid coarser than the quantities it measures. The panel's path: three reruns (A1, A3, A4 below) before publishing a cost, or publish now as a research note with a question for a title.

## A. Findings that change numbers

| # | Finding | Raised by | Affects | Closes it |
|---|---|---|---|---|
| A1 | Forecast-only glider release costs 77–98 h of coverage per flight against ~35 h with the hindsight rule (`results/glider_tuning.md`, Recommendation). On ~5.4-day flights that is a factor-of-two-class hit to useful dwell. `combined_cost.py` applies the ×1.35 haircut to launch-site hindsight only. | 5/5 | Finding 2, 5; the €3.4 bn | Recompute launch-rate-weighted dwell trajectory by trajectory under the on-board release rule (H = 24 h) and feed it into `combined_cost.py`. Publish hindsight and forecast-only figures side by side. |
| A2 | Trajectories were flown with BLE's 68.5 kg envelope + 92.5 kg payload; the cost case is a 16–18 kg envelope + 40 kg payload (`results/envelope_cost.md`). Volume, pump authority, power draw, diurnal superpressure and time constants differ. | 4/5 | Every dwell and recovery figure as applied to the costed fleet | Re-fly a representative subset of `run_drift.py` with the redesigned mass, volume and pump model, or state in the article that dwell figures are for the Loon-class vehicle. |
| A3 | "No wind data below 13.6 km" is a fetch choice (`fetch.py` LEVELS = 150…30 hPa), not a data limit: Open-Meteo serves pressure levels to 1000 hPa, and ERA5 exists. Tapering the 150 hPa wind to 30 % at the surface cannot reproduce the 8–12 km winter jet, which is often faster than the air above it. | 5/5 | Finding 3 (98.0 %) | Extend `fetch.py` to the full column (1000–30 hPa) for the 120 slow-controller tracks and rerun `glide_tuning.py`. Until then, call 98 % an idealised upper bound. |
| A4 | The 2.5° × 5° grid is ~280 × 360 km at 50°N, wider than the 50 km station-keeping criterion and about a day's drift. Five levels are also vertically sparse for finding reverse layers. | 5/5 | Finding 1 values (4 %, 33–37 %); dwell values | Rerun `run_coverage.py` and `run_drift.py` at native resolution (0.25° GFS or ERA5) for a sensitivity subset. The qualitative winter result ("every reachable altitude is westerly") survives because it is vortex-scale. |
| A5 | Hydrogen (14 kg, €127) and the burn (215 kg CO₂ = 68.5 kg PE × 3.14) belong to the heavy vehicle. The redesigned envelope needs ~5–7 kg H₂ and burns to ~53 kg CO₂. | 5/5 | Finding 4, 5, the risks list, `burn_sim.py` paragraph | Put every mass, gas and burn figure on one vehicle. |
| A6 | Hemispheric runs report median peak latitude 82.6°N against a 70°N wind domain (`subset_ncep.py`) and BLE's 60°N solar cut-off. | 2/5 | Finding 6, 7 | Document how trajectories above both limits were computed (clamping, extrapolation, solar bypass in `run_multipass.py`) or drop the loop results from the article. |
| A7 | 98 % recovery × 15-flight life leaves ~75 % of radios after 14 recoveries; attrition is absent from the payload line. | 1/5 | Finding 5 | Add per-flight attrition to `combined_cost.py`. |
| A8 | Allied satellite capacity sums worldwide figures (IRIS² 3.3 Tbps, Lightspeed ~10 Tbps, KONNECT VHTS 500 Gbps across EMEA) as if European. | 3/5 | Capacity section | Allocate a defensible European share or drop the "9–11 Tbps over the region" sum. |
| A9 | 2 Gbps per balloon from 100–200 MHz × 2–5 bit/s/Hz is 0.2–1 Gbps per spatial channel; the rest is unstated reuse. One reviewer doubts a 1.26 kW array powers a 2 Gbps 5G payload through a 16 h winter night. Note: 2 Gbps drives capacity, outage counts and the Starlink match, not the €3.4 bn, which is a coverage fleet. | 2/5 | Capacity, outage, comparison | Write the beam-count, spectrum and power budget, or present 2 Gbps as a target with Loon's 10–40 Mbps as the demonstrated floor. |
| A10 | A 5° beam needs a 1–2 m aperture at 2.6 GHz and several metres at 700–900 MHz; the 1.7 km spot is not the 40–80 km footprint used elsewhere. | 3/5 | "Surgical" section | State the array size and how beams tile the footprint, or drop the 1.7 km claim. |
| A11 | 1,000 km balloon-to-balloon laser link is the grazing horizon through the dense lower atmosphere; ~500–700 km with 10–15 km of path clearance. | 3/5 | Backhaul | Correct the figure. |
| A12 | One year (2025) is a case study: one QBO phase, one winter, at most one SSW. | 4/5 | All seasonal figures and the €1.5–9.2 bn range | Repeat the drift runs over several years before quoting an annual cost range. |
| A13 | Glider tuning and evaluation used the same 120 trajectories with synthetic perturbations; 97.5–98.3 % is not an out-of-sample interval. | 1/5 | Finding 3 | Hold out trajectories or a year for evaluation. |
| A14 | 95 % coverage is undefined (area-time, population, instantaneous availability?) and fleet-size-over-footprint is not a coverage probability; drifting nodes cluster. | 2/5 | Finding 5 | Define the metric; compute coverage from the drift tracks rather than from the footprint count. |

## B. Statements to correct

- "2025 reanalysis winds" describes only the hemispheric runs; the European runs are archived GFS forecasts/analyses from Open-Meteo. Name each dataset where its results appear. (3/5)
- "Star trackers (the sky at 20 km is dark enough)": the daytime sky at 20 km is dark blue, and a star tracker gives attitude, not a position fix. (5/5)
- "We flew 1,600 simulated balloons": say "simulated 1,600 trajectories". (1/5)
- Article 8 of the Chicago Convention: the governing instrument for unmanned free balloons is ICAO Annex 2 (plus national rules); Article 8 alone does not settle it. (3/5)
- "Keep sites under 5 t" of hydrogen is threshold avoidance, not a safety case; ATEX, pressure-equipment, maritime and workplace rules still apply. (3/5)
- "Both ways of counting are fair" on Starlink: global dish broadband against regional phone-direct is not like for like, and the pro-rata figure is an allocation convention, not a price. (4/5)
- "Losing a node: Even" is wrong in contested airspace; 20 km is fighter and SAM altitude, and the draft cites two shoot-downs. (2/5)
- Jamming: uplink and downlink geometries are mixed; at the 80 km footprint edge the balloon is ~14° up, inside a 25–30° panel beam; the phone-relevant satellite comparator is direct-to-cell (AST, Starlink D2C), not a Starlink dish. (3/5)
- The 20 dB and 29 dB figures are distance-only free-space terms, not anti-jam margins or link budgets. (5/5)

## C. Framing and transmission

- The title fails its own test; "no foreign commercial off-switch" survives, "no one" does not. (5/5)
- Lead with "a simulation suggests" and name the three unproven dependencies in the first paragraph: useful dwell under forecasts, recoverable radio, licensed 2 Gbps radio. (5/5)
- Cut the capability material (cameras, jammer geolocation, GNSS-denied navigation stack, ship tracking, "anti-jam arrays"); it is unnecessary to the policy case and invites an ITAR/privacy/China reply. (4/5)
- Reduce Findings 6–7 to a sidebar ("loops clip China; Canada is upwind"); they are not in the conservative cost case. (4/5)
- Remove the staccato verdict list and the one-word headings; replace slogans with plain sentences. (5/5)
- ~800 autonomous 40 kg glider descents a day through IFR airspace, landing at 15–20 m/s (~8 kJ), is a UAS-integration programme and needs a safety case; say so. (5/5)
- 5,000 t/yr polyethylene, a third of it at sea, is a permitting and politics issue, not a pickup-cost line. (3/5)
- "Available on request" is not reproducibility; publish the repo or say "internally reproducible". (4/5)

## D. What the panel says survives

Winter westerlies make altitude-only station-keeping hard at these latitudes; the conveyor architecture; the winter launch-rate spike; launch-site sensitivity and upwind launch; the recoverable radio as the economic lever (as a concept, not at 98 %); hemispheric loops cross China; Canada is upwind of Europe.

## E. Dissent

- Two reviewers rejected the suggestion that 4 % vs 38 % is a flight-length artefact: both runs were two-day flights. The live objections are the 16-flight tropical baseline, the tropical-tuned StationSeeker, and two days against Loon's weeks.
- One reviewer called the piece military advocacy; the others treat it as a civil-protection proposal that drifted into a capability sketch. Section C's third item resolves it.
- One reviewer tied the grid objection to gravity waves; the synoptic-scale argument is sufficient on its own.

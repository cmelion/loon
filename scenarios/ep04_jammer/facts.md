# Episode 4 — "No Fix" (GNSS jamming near Kaliningrad vs glider recovery)

**Flight:** Brest, launched 2025-12-01 06:00 UTC, seed 8602, `slow` controller, GFS 2025 winds. Flight id `Brest_2025-12-01_8602` in `results/drift_2025.csv` (118.15 h, EXIT_E, released to Warsaw at h71). Replayed with `scenarios/tools/fly_track.py`; replay matches.

| Fact | Value | Source |
|---|---|---|
| Track | 1 Dec 18:00 south of Paris (48.5 N 1.6 E) → 2 Dec 06:00 Saarland (49.5 N 7.2 E) → 2 Dec 18:00 Thuringia (50.4 N 11.5 E) → 3 Dec 06:00 Saxony/Bohemia (50.9 N 14.8 E) → 3 Dec 18:00 Poznań (52.0 N 17.6 E) → 4 Dec 05:00 Masuria (53.4 N 21.4 E) | flight.json `track` |
| Mean speed | 29.8 km/h; 3,519 km path in 118 h | flight.json `summary` |
| December nights | battery 13.9 % at dawn 2 Dec, 13.7 % 3 Dec, 10.5 % 4 Dec, 11.5 % 5 Dec; nights ~16 h at 184 W vs 3.06 kWh battery | track; BLE `balloon.py` defaults |
| Sim release (today's rule) | h71, 04 Dec 05:00 UTC, 53.395 N 21.384 E, 79.2 hPa / 17.66 km, 135 km from Warsaw; glide 2.07 h, 174 km ground, lands 0.1 km from Warsaw | flight.json `release`, `glide` |
| Distance from release point to Kaliningrad city (54.71 N 20.51 E) | 157 km; 106 km south of the oblast's southern border (54.35 N) | computed, `run_drift.gc_km` |
| Wind at release | 8.8 m/s from WSW (u 7.7, v 4.3) | `europe_ble.WindGrid.lookup` |
| Tuned glider (L/D 14, 20 kg/m², crab + speed-to-fly), same release | margin 85 km, 51/51 Monte Carlo (wind bias to 5 m/s, surface taper 0.1–1.0), worst miss 3.0 km | `glide_cases.json` `B_…` |
| Tuned release rule | h68 (02:00 UTC) at 52.99 N 19.82 E, 104 hPa, 119 km from Warsaw, margin 103 km, 51/51; costs 48 h of coverage the balloon would otherwise give over Belarus/Russia | glide_cases.json `C_…` |
| Pure dead-reckoning error if GNSS is lost | unknown wind 5 m/s × 2.05 h glide = 37 km; recovery radius in the model is 25 km | arithmetic; `glide.REACH_KM` |
| Where the balloon goes afterwards | 4 Dec 18:00 54.4 N 27.4 E (Belarus, near Minsk) → 5 Dec 06:00 53.8 N 32.5 E (Smolensk) → exits at 50.3 N 42.0 E on 6 Dec 04:09 UTC | track |
| Envelope if cut at release | lands 53.48 N 21.52 E (Masuria, land) after 0.62 h, 13 km drift | flight.json |
| Fleet-wide glider numbers | today: 78 % recovered (16 kg/m², L/D 12, fixed-150 rule); 64 % under wind-error Monte Carlo. Tuned: 98.0 % (P10–P90 97.5–98.3 %); ceiling 98.3 % | `results/glider_tuning.md` |
| Real-world anchor | Kaliningrad/Baltic named by EASA in 2022 as a GNSS-interference area; Lithuania's regulator (Mar 2026) says Kaliningrad jammers affect aircraft beyond 400 km and >30 jamming sources operated in 2025 | EASA SIB 2022-02 via gpsworld.com; lrt.lt 2026-03-09; spire.com |

**Physics behind the beat:** the glider's guidance in `glide_batch.py` assumes it measures its ground track (i.e. has a position fix) and crabs into the wind. Without GNSS it flies heading-and-airspeed only and inherits the full wind error: 37 km over the glide, more than the 25 km recovery circle. The arrival margin (103 km of still-air range, ≈7 km of altitude to spare at L/D 14) is enough to circle and home on a local non-GNSS beacon at the recovery site; that is the episode's engineering fix. Nothing in the repo simulates a beacon; the margin is the quantitative part.

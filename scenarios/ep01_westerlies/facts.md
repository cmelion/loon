# Episode 1 — "Fourteen Hours" (winter westerlies collapse flight times)

**Flight:** Bucharest, launched 2025-03-15 06:00 UTC, seed 31832, `slow` controller, GFS 2025 winds.
Same job as `results/drift_2025.csv` / `results/slow_tracks.csv` (flight id `Bucharest_2025-03-15_31832`); replayed with `scenarios/tools/fly_track.py` → `flight.json`. Replay reproduces the recorded dwell (14.0 h) and end point (43.81 N 42.04 E) exactly.

| Fact used in the episode | Value | Source |
|---|---|---|
| Launch point | 44.39 N 26.17 E (Bucharest), 06:00 UTC | flight.json `launch` |
| Time over the region before exiting east at 42 E | 13.95 h (fastest of the 120 slow flights) | flight.json `summary.dwell_h`; `results/slow_tracks_summary.csv` |
| Mean ground speed | 91.4 km/h; path 1,276 km | flight.json `summary` |
| Black Sea crossing | 28.9 E at 08:00 UTC → 38.3 E at 16:00 UTC (8 h) | flight.json `track` h2–h10 |
| Chosen "slowest" level during the day | 95.7 hPa, 16.46 km; wind there at h5 = 25.5 m/s (92 km/h) due east | track h5–h9; `europe_ble.WindGrid.lookup` |
| Night climb | 16:00–18:00 UTC up to 74.0 hPa / 18.09 km; wind 21.4 m/s (77 km/h) | track h10–h12 |
| Battery | 100 % all day; 75 % at exit (20:00 UTC) after 4 h of night at 184 W | track `batt_pct`; BLE `nighttime_power_load` 183.7 W |
| Closest approach to the Russian coast (Tuapse 44.1 N 39.08 E) | 16 km at h11 (17:00 UTC) | computed from track with `run_drift.gc_km` |
| Sim radio release (today's rule: last hour within 150 km of a site) | h13, 43.94 N 41.14 E, 122 km from Sochi; glide 2.10 h, 119 km, lands 14.7 km from Sochi → "recovered" | flight.json `release`, `glide` |
| Envelope if cut at release | 0.63 h parachute descent, drifts 35 km, lands 43.81 N 41.54 E (Russian Caucasus) | flight.json `envelope_cut_at_release` (`glide.simulate_descent`) |
| Envelope if flown to exit | lands 43.67 N 42.42 E (Georgia/Russia border) | flight.json `envelope_cut_at_end` |
| Alternatives before Russian airspace (tuned glider L/D 14, 20 kg/m², crab + speed-to-fly) | Constanta reachable h1–h2 (margin 194 / 137 km); nothing reachable h3–h6 (Odesa −20…−155 km); Sochi from h7 | `glide_cases.json` `reachability_by_hour` |
| Tuned glider to Sochi (not allowed in-world) | release h12, margin 170 km, 51/51 Monte Carlo recoveries | glide_cases.json `C_tuned_rule_tuned_glider` |
| March mean dwell over the region | 1.5 d (10 flights); winter Dec–Mar mean 2.28 d; summer Jun–Aug 9.92 d | `results/drift_2025.csv` slow controller, grouped by month (`cost_comparison.md` table) |
| Share of winter flights under 2 days | 52 % (Dec–Mar), 33 % all year | drift_2025.csv, computed |
| Exit directions, 120 slow flights | E 56, S 31, N 16, W 14, 30-day cap 3 | drift_2025.csv |
| Launch rate implied for 95 % winter coverage | 1,871 (1,449–2,408) launches/day; summer 453 | `results/cost_comparison.md` scenarios table (`cost_model.py`) |

**Physics behind the beat:** in winter the stratospheric westerlies over the Black Sea blow 20–25 m/s at every reachable level (74–96 hPa), so the slow controller has nothing to steer with; the balloon is a 92 km/h object with no brake. The only in-world choice is where it comes down: cut it over the Black Sea before 39 E (envelope into the sea, 13 % of all envelopes already land in the Black Sea per `scenarios/tools/envelope_stats.py`), or let it enter Russian airspace.

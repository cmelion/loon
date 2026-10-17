# Episode 5 — "The Flank" (a Black Sea surge in January)

**Flight:** Dublin, launched 2025-01-01 06:00 UTC, seed 15839, `slow` controller, GFS 2025 winds. Flight id `Dublin_2025-01-01_15839` in `results/drift_2025.csv` (39.6 h, EXIT_E, released to Trabzon). Replayed with `scenarios/tools/fly_track.py`; replay matches.

| Fact | Value | Source |
|---|---|---|
| Dublin → Georgian border | 39.6 h; mean 96.3 km/h; 3,808 km | flight.json `summary` |
| Waypoints | 09:00 Lincolnshire (53.0 N −0.2 E) → 12:00 Netherlands (52.5 N 5.5 E) → 15:00 Harz (51.8 N 10.8 E) → 18:00 Bohemia/Silesia (50.7 N 15.65 E) → 21:00 Tatras (49.7 N 19.5 E) → 2 Jan 00:00 Zakarpattia, Ukraine (48.7 N 23.0 E) → 03:00 Suceava (47.6 N 26.3 E) → 06:00 Odesa oblast (46.4 N 29.3 E) → 09:00 Black Sea (45.0 N 32.1 E) → 12:00 43.9 N 34.7 E → 15:00 42.8 N 37.2 E → 18:00 Turkish coast (41.7 N 39.4 E) | track |
| Time over western Ukraine/Moldova (22–30 E, >45.5 N) | h18–h24 (2 Jan 00:00–06:00 UTC) | track |
| Closest approach to Crimea (Sevastopol 44.6 N 33.5 E) | 44 km at h28 | computed with `run_drift.gc_km` |
| Altitude | 15.3–18.3 km; night of 1–2 Jan at 110 hPa (15.5 km) pumping DOWN | track |
| Battery | 15.4 % at 06:00 UTC on 2 Jan after a 15-h night; 100 % by 12:00 | track |
| Sim release (today's rule) | h38 (2 Jan 20:00 UTC) 41.115 N 40.893 E (Rize province), 101 km from Trabzon; glide 1.92 h, 122 km, lands on the site | flight.json |
| Tuned rule | release h37 at 41.43 N 40.18 E, 62 km out, margin 134 km, 51/51 Monte Carlo | `glide_cases.json` |
| Earlier recovery options (tuned glider) | Berlin h7–h10 (margin to 118 km), Odesa h22–h26 (to 160 km), Sochi h32–h34 (to 58 km), Trabzon h35–h38 | glide_cases.json `reachability_by_hour` |
| Still-air glide range from 114 hPa | 15.34 km × L/D 12 = 184 km | `glide.isa_altitude` |
| Envelope if cut at release | 41.13 N 41.12 E (Artvin province, land), 19 km drift | flight.json |
| January fleet statistics | mean dwell 2.4 d; 8/10 January radios recovered with today's glider; winter 95 % coverage needs 1,871 launches/day; 50 % coverage 547/day | `results/cost_comparison.md` |
| Coverage time of this balloon over the Black Sea littoral (lon > 27 E) | ≈ h24–h39.6 ≈ 15 h | track |
| Fastest flights in the sweep | Bucharest 15 Mar 14.0 h; Bucharest 1 Jan 17.05 h; Bucharest 1 Mar 18.45 h | `results/slow_tracks_summary.csv` |

**Problem the sim exposes:** in January every launch west of the Black Sea reaches the eastern shore in 1.5–2 days and must be terminated before 42 E. A surge of coverage over Romania/Bulgaria/Turkey therefore means a conveyor: each balloon gives ~15 h on the flank per launch, and the launchers upstream (Dublin, Brest, Vienna, Bucharest) must fire continuously. The in-world rule "cut before 42 E; recover at Trabzon or Constanta" comes straight from the recovery network of `run_drift.RECOVERY`.

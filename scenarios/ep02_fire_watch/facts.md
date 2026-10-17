# Episode 2 — "Fire Watch" (a 30-day summer flight, Ionian Sea to Castile)

**Flight:** Bucharest, launched 2025-07-01 06:00 UTC, seed 32049, `slow` controller, GFS 2025 winds.
Flight id `Bucharest_2025-07-01_32049` in `results/drift_2025.csv` (720 h, MAX_DAYS). Replayed with `scenarios/tools/fly_track.py` → `flight.json`; replay matches the recorded end point 41.85 N −4.69 E.

| Fact | Value | Source |
|---|---|---|
| Duration | 720 h = 30 days (simulation cap), still inside the region on 31 Jul 06:00 UTC | flight.json `summary` |
| Mean ground speed / path | 11.6 km/h; 8,363 km | flight.json `summary` |
| Ionian / southern-Italy phase | 2 Jul 41.7 N 21.9 E (N. Macedonia) → 3 Jul 39.7 N 19.0 E (Corfu/Albania) → 4 Jul 38.8 N 18.0 E (Ionian, off Calabria) → 5 Jul 39.75 N 18.75 E (Salento) → 6 Jul 40.8 N 17.8 E (Bari) | track, 24-h samples |
| Altitudes in that phase | 15.3–18.6 km (114→65 hPa) | track `alt_km`, `hpa` |
| Northern loop | 8 Jul over Vienna (48.15 N 16.86 E), 10 Jul 51.8 N 14.6 E, 12 Jul Luxembourg, 14 Jul The Hague, 17 Jul Paris, 20 Jul English Midlands, 22 Jul Cumbria/Irish Sea | track |
| Battery | never below 58 % (min at 30 Jul 06:00); solar 800–1,140 W by day | flight.json `summary.min_batt_pct`, track |
| Sim radio release (today's rule) | h542 (23 Jul 20:00 UTC) 52.08 N −5.84 E, 139 km from Dublin; glide 2.12 h, 130 km, lands 9.6 km from Dublin | flight.json `release`, `glide` |
| Tuned rule (L/D 14, 20 kg/m², margin ≥ 100 km) | release h540, margin 114 km, 51/51 Monte Carlo; 169 flight-hours over the month had some site reachable with ≥100 km margin (Bucharest, Budapest, Vienna, Berlin, Paris, London, Dublin) | `glide_cases.json` |
| End of flight | 31 Jul 06:00 UTC at 41.85 N −4.69 E (Valladolid, Castile); envelope cut there lands 41.87 N −4.46 E after 0.63 h, 19 km drift (land) | flight.json `summary`, `envelope_cut_at_end` |
| Net drift direction | east→west (Bucharest to Castile): summer stratospheric easterlies | track; same pattern in `results/drift_2025.csv` summer flights |
| Monthly mean dwell | Jun 14.0 d, Jul 9.0 d, Aug 6.8 d (vs Mar 1.5 d) | `results/cost_comparison.md` (drift_2025.csv) |
| Summer fleet, 95 % coverage | 453 (329–639) launches/day, €6.4 B/yr annualised; 50 % coverage 132/day, €1.9 B/yr | `results/cost_comparison.md` |
| Per-balloon radio capacity (model) | ~10–40 Mbps shared, LTE to unmodified phones; 40–50 km footprint | `results/cost_comparison.md` comparator table; `cost_model.py` |
| Real-world anchor | 2025 was the EU's worst EFFIS wildfire year on record (≈1.03–1.08 Mha burnt; Spain ≈401,000 ha, Portugal ≈284,000 ha); Spain's worst fires were mid-August 2025 in León, Zamora and Ourense, with evacuations in the thousands | JRC/EFFIS via tovima.com, aa.com.tr; euronews.com 2025-08-19 (see world_primer.md) |

**Note for the writer:** the flight ends over Valladolid on 31 July only because the simulation caps flights at 30 days. The real August 2025 fires in León/Zamora started about ten days later; the episode's final panel can use that gap honestly ("it was still up there when…" is *not* supported; "it had just come down when…" is).

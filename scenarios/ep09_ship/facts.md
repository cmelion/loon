# Episode 9 — "Launch Deck" (a ship-based launch and recovery crew)

**Flight:** "Ship 52N 13W" (52.0 N −13.0 E, ≈250 km WSW of Dingle, Ireland), launched 2025-02-01 06:00 UTC, seed 71334, `slow` controller with `APPROACH_HOME=1` (steer for Europe until inside the region), NCEP band winds. Row `Ship 52N 13W, 2025-02-01` of `results/ship_approach_2025.csv` (70.85 h, EXIT_S, released to Vienna); replayed with `scenarios/tools/fly_track.py --grid data/ncep_band_2025.npz --approach-home`; replay matches.

| Fact | Value | Source |
|---|---|---|
| Flight vs region time | 73.3 h flown, 70.85 h inside the region (entered at ≈h2.5) | flight.json `summary` |
| Track | 09:00 Kerry (52.7 N −9.2 E) → 12:00 Irish Sea/Wales → 15:00 Cheshire → 18:00 Lincolnshire coast → 2 Feb 00:00 North Sea off Norfolk → 06:00 Dutch/German border (51.2 N 5.75 E) → 12:00 Frankfurt → 18:00 Nuremberg → 3 Feb 00:00 Styria (47.7 N 15.25 E) → 06:00 Osijek (45.8 N 18.95 E) → 12:00 Vidin/Bulgaria (43.9 N 22.4 E) → 18:00 Rhodope → 4 Feb 00:00 Aegean/Manisa (39 N 28.3 E) → exits 36 N 31.43 E (off Antalya) 07:18 UTC | track |
| Mean speed | 55.9 km/h; 3,963 km | summary |
| Altitude | 15.45 km (112 hPa) for most of the first two days, then 19.5 km (59 hPa) over the Balkans | track |
| February nights | battery 23 % at dawn 2 Feb, 21 % at dawn 3 Feb, 34 % at 03:00 on 4 Feb | track |
| Sim release (today's rule) | h44 (3 Feb 02:00 UTC) 47.13 N 16.50 E (Burgenland), 120 km from Vienna; glide 1.93 h, 142 km, lands on the site | flight.json |
| Tuned glider alternatives | Dublin h2–h7 (margin to 192 km), London h9–h18 (to 116 km), Vienna h38–h43 (to 128 km), Budapest h44–h47, Bucharest h53–h58, Istanbul h59–h66 (to 145 km); tuned rule picks Istanbul at h64 (margin 132 km, 51/51) | `glide_cases.json` |
| Envelope if cut at release | 47.06 N 16.74 E (Burgenland, land), 20 km drift | flight.json |
| Envelope if flown to exit | 35.94 N 32.27 E, Mediterranean off Cyprus/Antalya, 76 km drift | flight.json |
| Ship 52N 13W statistics (24 launches, 2025) | 2 of 24 never reached Europe within 5 days; arrivals averaged 4.51 d over the region; 67 % radios recovered (best of the five ship stations) | `results/ship_approach_2025.csv` |
| All five ship stations | 13 % never arrive; arrivals average 5.35 d; land sites on the same NCEP winds average 4.56 d | ship_approach_2025.csv; `results/ship_vs_land_2025.csv`; README |
| README verdict | Atlantic ship launches "match the best land sites (~3.1 d rotating…) but don't beat them"; choosing the best site per date gives ×1.6–1.75 dwell with hindsight | README |
| Why ships at all | the structural case is launch-market independence and relocatable launch; cost model: fleet needs no launch vehicle; ~30–80 land sites otherwise | `results/cost_comparison.md` "Launch-market concentration" |
| Hydrogen per flight | BLE fill 6,830 mol ≈ 13.8 kg H₂; €127/flight at ~€8/kg; 0.3 % of cost | cost_comparison.md |
| Launch tempo context | 1,100 launches/day fleet-wide (base case); 48 launches/site/day nominal in peak month | cost_comparison.md |

**Note:** ship stations lie outside the region box (lon < −10), so the flight counts only time after it crosses −10 E; the ~2.5 h approach is the "run for Europe" the `home` controller steers during.

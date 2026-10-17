# Episode 11 — "Seventy Kilometres Short" (a radio glider races the wind to Madrid)

**Flight:** Lisbon, launched 2025-11-01 06:00 UTC, seed 621, `slow` controller, GFS 2025 winds. Flight id `Lisbon_2025-11-01_621` in `results/drift_2025.csv` (71.85 h, EXIT_S, released to Madrid at h9, **not recovered**: glide ends 70.7 km short). Replayed with `scenarios/tools/fly_track.py`; replay matches. Glider variants computed with `scenarios/tools/glide_cases.py` (physics of `glide.py`, designs and release rule of `glide_tuning.py`).

| Fact | Value | Source |
|---|---|---|
| Climb-out | reaches 60.5 hPa / 19.37 km within 3 h and crosses Spain at that level | track h3–h9 |
| Track | 09:00 Badajoz/Cáceres (39.25 N −6.48 E) → 12:00 Toledo (39.5 N −4.4 E) → 15:00 Cuenca (39.75 N −2.28 E) → 18:00 Valencia coast (39.9 N −0.25 E) → 2 Nov 00:00 Balearics → 2 Nov 09:00 Sardinia (39.2 N 9.2 E) → 2 Nov 21:00 off Sicily (37.75 N 14.3 E) → 3 Nov 18:00 Peloponnese (36.7 N 21.6 E) → exits south of Crete 36 N 26.6 E, 4 Nov 05:51 UTC | track |
| Mean speed | 43.7 km/h; 3,140 km | summary |
| Wind at the h9 release point | 17.0 m/s (61 km/h) from the west (u 16.9, v 2.3); Madrid bears WNW, i.e. a headwind | `europe_ble.WindGrid.lookup` |
| Still-air glide range from 19.37 km | L/D 12 → 232 km; L/D 14 → 271 km | `glide.isa_altitude` × L/D |
| **Case A** today's rule (last hour within 150 km) + today's glider (L/D 12, 16 kg/m², sink 1.5 m/s, point-at-target) | release h9 at 140.5 km from Madrid; 2.17 h glide; lands 40.49 N −2.87 E, **70.7 km short** (Guadalajara province) | flight.json `glide`; glide_cases.json `A` |
| **Case B** same release, tuned glider (L/D 14, 20 kg/m², crab + speed-to-fly) | lands 11.3 km from Madrid (within the 25 km recovery circle) in 1.74 h, but arrives with no margin (−11 km); Monte Carlo (wind bias 0–5 m/s × 8 directions × surface taper 0.1/0.3/1.0): 31/51 = 61 %, worst miss 73 km | glide_cases.json `B` |
| **Case C** tuned release rule (last hour with ≥100 km margin) + tuned glider | release h7 (13:00 UTC) at 39.57 N −3.71 E, 92.5 km from Madrid, 60.5 hPa; margin 177 km; arrives 2.7 km off and spirals down; Monte Carlo 49/51 = 96 %, worst miss 46.5 km (5 m/s bias from the east, full surface wind) | glide_cases.json `C` |
| Wind at the h7 release | 18.0 m/s (65 km/h) westerly | WindGrid.lookup |
| Reachability window for Madrid | margin ≥ 100 km only h3–h7 (11:00–13:00 UTC); by h9 it is −11 km, by h12 −182 km | glide_cases.json `reachability_by_hour` |
| Later chances on the same flight | Rome never (best −53 km at h28); Athens h58–h67 (best margin 87 km at h63) | reachability_by_hour |
| Tuned-glider design point | L/D 14 at 20 kg/m²: sea-level sink 1.43 m/s, best-glide TAS 20 m/s at sea level, 75 m/s at 20 km; lands at 20 m/s (15 m/s with flaps), no chute | `results/glider_tuning.md` |
| Fleet effect | fixed-150 rule + today's glider: 78 % nominal, 64 % under Monte Carlo; tuned rule + tuned glider: 98.0 % (97.5–98.3 %); speed-to-fly alone is worth +8.4 points; crab angle alone −0.6 (noise) | glider_tuning.md |
| What limits the last 2 % | 2 of 120 flights never come within glide range of any site (Brest 1 Apr, Brest 1 Aug); ceiling 98.3 %; "add a west-Ireland/Brittany site" | glider_tuning.md |
| Coverage cost of releasing earlier | tuned rule loses 35 h of coverage per flight on average (27 % of dwell) vs 35 h for the fixed-150 rule; releasing at h7 instead of h9 here costs 2 h | glider_tuning.md; glide_cases.json |
| Payload value at stake | cost_model payload line €16,785/flight amortised (44.5 % of cost) at 78 % recovery; 94–98 % recovery is lever L3 (−19 %) | `results/cost_comparison.md`, `results/cost_reduction.md` |

**Physics behind the beat:** a glider's ground speed into a 17 m/s headwind is airspeed minus 17 m/s; the light 16 kg/m² glider flies ~20 m/s at sea level and barely moves at the bottom of the descent, so it falls 70 km short even though its still-air range (232 km) was ample. The heavier, faster 20 kg/m² wing with speed-to-fly (up to 1.8× best-glide speed into headwinds) penetrates, and releasing two hours earlier, when Madrid is 92 km away instead of 140, buys the margin that survives a 5 m/s forecast error.

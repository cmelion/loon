# Episode 3 — "Grid Down" (an Iberian blackout backfill)

**Flight:** Lisbon, launched 2025-04-28 06:00 UTC, seed 428, `slow` controller, GFS 2025 winds. **New run** (the drift sweep only has 1st/15th launches); produced with `scenarios/tools/fly_track.py` → `flight.json`. 28 April 2025 is the date of the real Iberian blackout.

| Fact | Value | Source |
|---|---|---|
| Time over the region | 87.7 h (28 Apr 06:00 → 1 May 21:45 UTC), exits south at 36 N 9.35 E (Tunisia) | flight.json `summary` |
| Position at blackout onset (≈10:33 UTC, 12:33 CEST) | between h4 (38.74 N −8.39 E, Évora) and h5; 18.99 km, 64.2 hPa | track h3–h6 |
| Over Spain | from ≈h8 (39.0 N −7.2 E, Badajoz) to ≈h37 (38.1 N −0.4 E, Alicante coast) ≈ 29 h | track |
| Mean ground speed | 19.2 km/h (this flight); April median of the slow fleet 11.8 km/h, May 16.5 km/h | flight.json; `results/drift_2025.csv` |
| Night battery | 55 % at 03:00 UTC on each of the three nights, full again by 09:00 (solar 490–990 W) | track |
| Sim radio release (today's rule) | h7 (13:00 UTC) 38.94 N −7.47 E, 144 km from Lisbon; glide 2.15 h, lands 10.5 km from Lisbon | flight.json `release`, `glide` |
| Tuned rule | Madrid reachable with ≥100 km margin from h18 to h24 (29 Apr 00:00–06:00 UTC); release h24 at 38.75 N −3.72 E, 184 km out, margin 102 km, 51/51 Monte Carlo | `glide_cases.json` |
| Envelope if cut at release | lands 39.03 N −7.19 E (Alentejo, land), 26 km drift | flight.json |
| **Backfill sizing, Iberia (58 M people, 430 km radius, April–May drift 14.2 km/h)** | crossing time 60.8 h; first coverage 14–35 h after launching 200–500 km upwind | `scenarios/tools/outage_case.py` → `outage_case.json` (formulas of `outage_scenario.py`) |
| Voice/text only (15 % active × 0.1 Mbps = 0.87 Tbps) | 2 Gbps/balloon: 435 balloons aloft, 172 launches/day, €2.1 M/day (€1.2–4.7 M) | outage_case.json |
| Degraded data (5 % active × 1 Mbps = 2.9 Tbps) | 2 Gbps/balloon: 1,450 balloons, 573 launches/day, €7.1 M/day (€3.8–15.6 M); 1 Gbps: 2,900 balloons, 1,145 launches/day, €14.2 M/day | outage_case.json |
| Minimum for geometric coverage alone | 116 balloons (one per 40 km cell) | outage_case.json |
| Laser trunks needed at the zone edge | 44 (voice/text) / 145 (degraded data) at 20 Gbps each | outage_case.json |
| Satellite comparison in the zone | Starlink pro-rata ≈1.12 Tbps; allied satellites ≈0.11 Tbps | outage_case.json (constants from `outage_scenario.py`) |
| Reference case in the repo (Italy-like 300 km zone, 34 M people) | voice/text 141 launches/day summer (€1.8 M/day) to 443 winter (€5.5 M/day) | `results/outage_scenario.csv`, README |
| Per-flight cost used | €6,700 / €12,400 / €27,200 (best/mid/worst) | `combined_cost.py` via `outage_scenario.PER_FLIGHT_EUR` |
| Real-world anchor | 28 Apr 2025 blackout: Red Eléctrica estimated 6–10 h to restore; 99.16 % of Spain restored by 29 Apr; mobile calls failed on some networks, Vodafone Spain ran at ~70 % capacity on backup power | AP via washingtontimes.com; Riskline advisory; bebeez.eu 2025-05-03 |

**Honest limits:** the balloon model gives capacity, not coverage-in-place: the fleet streams through the zone at 14 km/h, so 435 balloons aloft means 172 launches a day from Lisbon/Atlantic-side launchers for as long as the outage lasts. Demand inputs (active share, per-user rate) are the repo's ASSUMPTIONS in `outage_scenario.py`.

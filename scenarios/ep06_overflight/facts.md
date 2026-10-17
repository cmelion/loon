# Episode 6 — "Overflight" (a long-life balloon drifts into Chinese airspace)

**Flight:** Bucharest, launched 2025-05-01 06:00 UTC, seed 418984, multi-pass controller with China-avoidance corridor, 10 kWh fuel-cell store (`BATTERY_WH=10000`), 3 m/s latitude-hold thrust (`THRUST_MS=3`), 150-day cap, NCEP/NCAR 2025 band winds. Same job as row `Bucharest 2025-05-01` of `results/multipass_2025_nochina_bat10000_thrust3.jsonl`; replayed with `scenarios/tools/fly_multipass_track.py` → `flight.json`. Replay reproduces the recorded china_days 7.3, first entry day 6.07, max latitude 64.4, 19.33 Europe-days.

| Fact | Value | Source |
|---|---|---|
| Flight length | 150 d (cap), 2.26 laps, 3 Europe passes, 19.33 Europe-days (13 % of the flight) | flight.json `summary` |
| Leaves Europe | day 1.89 (3 May 03:27 UTC) at 50.86 N 42.01 E (Volgograd/Saratov) | `events` |
| Over Russia/Central Asia to the Chinese border | 3 May–7 May: 44 E → 111 E in 4.2 days, 15.4–19.5 km | track days 2–6 |
| First China entry | day 6.07, 7 May 07:36 UTC at 43.02 N 111.04 E (Inner Mongolia), thrust +3 m/s already running | `events`, `track` |
| First China crossing | 7 May 07:36 → 9 May 04:06 (1.85 d) along 43–47 N, exits at 47.3 N 135.0 E (Heilongjiang/Primorye) | `events` |
| Second China crossing | day 80.9–86.3 (21–26 Jul): enters from the Yellow Sea at 35.3 N 124.5 E, loops to 34.5 N 109 E (Xi'an) and north through Inner Mongolia, exits 48.7 N 129.9 E | `events`, `track` "china rows" |
| Total over China | 7.30 days; Russia/C.Asia/China sector 44.5 days (30 % of the flight) | summary |
| Why the corridor failed | corridor floor is China's northern border + 2.5° (`china.corridor_floor`); the balloon reached 111 E at 43 N, 5° south of the floor, with the 3 m/s thrust unable to make up the latitude against 15–25 m/s winds | `china.py`, `run_multipass.choose`, track days 4–6 |
| Thrust energy | 1,723 h of thrust, 244 kWh ≈ 14 kg H₂ at the README's 52 kWh ≈ 3 kg | summary `thrust_kwh`; README (fuel cell line) |
| Power | battery never below 76 % (10 kWh store) | summary |
| Recovery chances | 34 two-hourly opportunities within 150 km of a recovery site; day 0.08–0.5 (Bucharest/Constanta), then over Europe days 26.5–36.7 and 139.4–146.7; last at day 144.17 (over northern Poland, 22 Sep) | `recover_days`, `events` |
| Europe passes | 27 May–6 Jun (54–57 N: Ireland→Denmark→Baltic→exits at 57.3 N 42 E); 17–24 Sep (Galicia→Brittany→Rhine→Poland→exits 51.9 N 42 E) | `events`, track |
| Fleet statistics, this configuration | China reach 88 % of flights (100 % without thrust); time over China 2 % (6 % without); launches ×0.49/0.37/0.30 at 30/60/100-day life; recovered radios 78/67/52 % | README; `results/multipass_2025_nochina_bat10000_thrust3_summary.csv` |
| Free-routing hemispheric flights | median 85 days, 2.5 laps, 4 Europe passes; ~22 % of time over Russia/C.Asia/China | README; `analyze_multipass.py` on `multipass_2025.jsonl` |
| Envelope cost case for 30/60/100-day life | €1,347 / €1,484 / €1,674 per envelope at volume, vs €1,167 for a 4-day one | `results/envelope_cost.md` §3(e) |

**Problem the sim exposes:** a fuel-cell balloon that lives 100+ days is a hemispheric object. Even with the corridor logic and 3 m/s of thrust, this flight spends 30 % of its life over Russia, Central Asia and China and crosses China twice. The repo's own conclusion (README): "China avoidance via a northern corridor fails (all flights still cross)". In a world where overflight of Russia and China is forbidden, long-life flights are only possible if the balloon is terminated at its last allied recovery opportunity before 42 E, which is what Episode 8 dramatises; this episode shows what happens when it isn't.

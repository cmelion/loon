# Episode 8 — "Westbound Launch" (a Vancouver balloon crosses to Europe)

**Flight:** Vancouver (49.3 N −123.1 E), launched 2025-08-01 06:00 UTC, seed 119, multi-pass controller with China corridor, 10 kWh store, 3 m/s thrust, 60-day cap (`LAUNCH_SET=canada` run), NCEP band winds. Row `Vancouver 2025-08-01` of `results/multipass_2025_nochina_bat10000_thrust3_canada.jsonl`; replayed with `scenarios/tools/fly_multipass_track.py` → `flight.json`. Replay reproduces 60.0 d, 22.48 Europe-days, 11.33 Canada-days, 5.54 Atlantic-days.

| Fact | Value | Source |
|---|---|---|
| Over Canada | 11.33 d total: BC interior 1–7 Aug (loitering 54–56 N, 121–131 W, i.e. Prince George / Fort St John country, at 18.9 km), out via Idaho on 8 Aug 10:18 UTC (49 N 117.7 W), back in over the Great Lakes 10 Aug, out over Labrador (52.5 N 52 W) 12 Aug 04:27 UTC | `events`, track |
| Atlantic | 5.54 d; crosses 52 W → −10 E between 12 Aug and 21 Aug, with a 4-day loiter at 36–42 N, 40–45 W (NW of the Azores) at 124 hPa / 14.8 km | track days 11–20 |
| Arrival in Europe | 21 Aug 06:33 UTC at 42.9 N −9.98 E (Cape Finisterre), day 20.02 | `events` |
| Europe pass 1 | 22 Aug Zamora/León (41.7 N −5.7 E) → 23 Aug Rioja → 24 Aug Catalonia → 25–26 Aug Sardinia/Sicily → 27 Aug Calabria → 28 Aug Otranto → 29 Aug Belgrade → 30 Aug Satu Mare → 31 Aug Lublin → 1 Sep Suwałki region (53.9 N 23.3 E) → 2–7 Sep Lithuania/Belarus/Latvia border (54.4–55.1 N, 22–29 E) → 8 Sep Pomerania → 10–11 Sep Zealand/Øresund → 12 Sep Kalmar; leaves at 59.5 N 18.9 E (Stockholm latitude) 12 Sep 15:27 UTC | track days 21–42, `events` |
| Europe-days | 22.48 d; useful time (Canada + Europe) 33.8 of 60 d = 56 % for this flight; fleet mean 46 % (Europe-only launches 26 %) | summary; README western-Canada line |
| Recovery opportunities | 13, all over Europe: days 29.8–30.3 (near Warsaw, 31 Aug) and 41.9–42.3 (Stockholm, 12 Sep) | `recover_days`, `run_drift.RECOVERY` |
| After Europe | Finland (13–14 Sep, 61.7–64.2 N), Karelia (15 Sep), Russia from 16 Sep (58.6 N 42.1 E) to Kamchatka (25 Sep), Pacific, BC again 27 Sep, Newfoundland 29 Sep, ends mid-Atlantic 55.4 N −20.8 E on 30 Sep (cap) | `events`, track |
| Thrust use | 498.5 h, 70.7 kWh; −3 m/s (southward) while north of 55 N over the Baltic states | summary, track `thrust_ms` |
| Power | battery never below 70 % | summary |
| Fleet statistics, Canada launches (36 flights, 60-day) | 4.8 d over Canada, 4.5 d Atlantic, 12.6 d Europe per flight; all reach Europe, typically by day ~10 | README |
| Transatlantic time for this flight | Labrador coast (day 10.94) to Finisterre (day 20.02): 9.1 d | `events` |
| Real-world anchor | Canada's 2025 fire season burned ≈8.9 Mha (second worst on record; Saskatchewan and Manitoba more than half); Spain's August 2025 fires in León/Zamora/Ourense: ≈340,000 ha by 19 Aug, four deaths, thousands evacuated | cwfis.cfs.nrcan.gc.ca; theweathernetwork.com; euronews.com 2025-08-19 |

**Problem → solution the sim supports:** launched for Canada's fire season, this balloon serves BC for a week, crosses in nine days, and then gives three weeks over Europe including the Baltic frontier. The sim also shows the price of not stopping: it leaves Europe over Finland and spends 8.3 days over Russia. The in-world rule "terminate at the last allied recovery opportunity before 42 E" means cutting it down near Stockholm on 12 Sep (day 42.3), which is exactly the last entry in `recover_days`.

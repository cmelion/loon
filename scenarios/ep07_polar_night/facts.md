# Episode 7 — "Polar Night" (a November balloon dies at 85 N)

**Flight:** Bucharest, launched 2025-11-01 06:00 UTC, seed 419086, multi-pass controller with China corridor, 10 kWh store, 3 m/s thrust, 150-day cap, NCEP band winds. Row `Bucharest 2025-11-01` of `results/multipass_2025_nochina_bat10000_thrust3.jsonl`; replayed with `scenarios/tools/fly_multipass_track.py` → `flight.json`. Replay reproduces the recorded 25.43 d, OUT_OF_POWER, max latitude 85.0.

| Fact | Value | Source |
|---|---|---|
| Flight length and end | 25.43 d; OUT_OF_POWER on 26 Nov 16:20 UTC at 85.04 N 129.06 E (Arctic Ocean north of the Laptev Sea), 115.7 hPa / 15.3 km | `summary`, last track row |
| Europe time | 3.06 d of 25.4 (two passes) | summary |
| Leaves Europe | day 1.06 (2 Nov 07:24 UTC) at 42.17 N 42.01 E (Georgia) | `events` |
| Clips China | 4 Nov 03:00–04:54 UTC near 47.8–48.5 N, 85.7–88.6 E (Altai) and 5 Nov 04:42–04:54 at 53.4 N 124 E: 2.2 h total | `events`, summary `china_days` 0.09 |
| First Arctic excursion | 6 Nov 61 N 163 E (Kamchatka/Magadan) → 7 Nov 18:00 72.5 N 160 W (north of Alaska) → 8 Nov 73 N 140 W (Beaufort Sea) → 9 Nov 71.4 N 122 W (Canadian Arctic Archipelago) | track days 5.5–8.5 |
| Canada | enters at 60 N 101 W on 10 Nov 19:48 UTC, leaves over Lake Michigan (45 N 87 W) 12 Nov 01:30; again Nova Scotia→Newfoundland 12–13 Nov; 1.58 d total | `events`, summary |
| Mid-Atlantic loiter | 13–17 Nov at 51–58 N, 47–34 W (south of Greenland) | track days 12.5–16 |
| Second Europe pass | enters 18 Nov 12:12 UTC at 48.8 N −10 E → Bay of Biscay → Massif Central (19 Nov 06:00, 44.8 N 3.1 E) → Slovenia (19 Nov 18:00) → Kyiv region (20 Nov 06:00, 51.2 N 31.2 E) → leaves at 52.8 N 42.1 E on 20 Nov 12:24 UTC | `events`, track |
| Last recovery opportunities | within 150 km of a recovery site on days 18.58–19.0 (Kyiv); 6 opportunities in the whole flight | `recover_days`; `run_drift.RECOVERY` |
| Final run north | 23 Nov 61 N 140 E (Yakutia) → 24 Nov 73 N 135 E (Laptev Sea) → 25 Nov 81 N → 26 Nov 85 N | track days 23–25.4 |
| Solar input in the last days | 105 W at 06:00 UTC on 24 Nov, then 0 W continuously (polar night) | track `solar_w` |
| Battery | 100 % on 24 Nov 06:00 → 63 % (25 Nov 06:00) → 41 % → 19 % → 0 % at 26 Nov 16:20; store 10 kWh | track `batt_pct`; `BATTERY_WH` |
| Why it could not descend out of the northward wind | power floor: below 45 % charge (80 % at night) the controller stops pumping (`STAY(power-floor)`), so from 24 Nov the balloon is stuck at 115.7 hPa | `run_multipass.POWER_FLOOR`, `NIGHT_FLOOR`; track `cmd` |
| Thrust | 420.6 h, 59.6 kWh (≈3.4 kg H₂ at 52 kWh per 3 kg); southward (−3 m/s) for the whole final run, against winds of order 10–20 m/s | summary; README fuel-cell line |
| Fleet statistics | November launches in this configuration: all five sites die of power within 25–50 days; max latitudes 73–87 N; README: "polar excursions persist" | `results/multipass_2025_nochina_bat10000_thrust3.jsonl` |
| BLE caveat | BLE's solar model is only valid to 60 N; `run_multipass` re-centres the frame every 2 h so flights continue past it, and the solar model's output there is an extrapolation | README "Modelling caveats"; `run_multipass.REBASE_EVERY` |

**Problem the sim exposes:** at high latitude in November the sun does not rise, a 10 kWh store lasts about 2.5 days of 184 W night load plus thrust, and the power-floor logic that protects the store also removes the only steering the balloon has. The flight also crosses Georgia, Russia, China and Belarus/Russia again (day 19–20) on the way: in-world, it should have been terminated at Kyiv on 20 Nov (its last recovery opportunity) or over the Atlantic before Europe.

# Episode 10 — "Pickup" (envelope recovery by gig crews)

**Flight:** Brest, launched 2025-02-01 06:00 UTC, seed 7982, `slow` controller, GFS 2025 winds. Flight id `Brest_2025-02-01_7982` in `results/drift_2025.csv` (81.65 h, EXIT_S, released to Paris at h12). Replayed with `scenarios/tools/fly_track.py`; replay matches.

| Fact | Value | Source |
|---|---|---|
| Radio release (today's rule) | h12 (1 Feb 18:00 UTC) 47.674 N 1.565 E (Loir-et-Cher, between Blois and Romorantin), 108.9 hPa / 15.6 km, 147 km from Paris; glide 1.94 h, 154 km, lands on the site (0.0 km) | flight.json `release`, `glide` |
| Envelope A: cut down at the release | parachute 0.58 h, lands 47.548 N 1.600 E (Sologne, land), 14 km drift | flight.json `envelope_cut_at_release` |
| Envelope B: flown on to the region exit | balloon continues over the Jura (2 Feb 09:00, 46.7 N 6.1 E), the Alps, Verona (3 Feb 03:00), the Adriatic, N. Macedonia, the Aegean; exits 36.0 N 30.35 E on 4 Feb 15:39 UTC; envelope lands 35.95 N 31.11 E in the Mediterranean, 68 km drift | track; `envelope_cut_at_end` |
| Paris reachability (tuned glider) | margin ≥ 0 only h8–h15; best 54 km at h10; never reaches the 100 km margin the tuned rule wants (this flight is the "below-margin, best effort" case in glider_tuning.md) | `glide_cases.json`; `results/glider_tuning.md` diagnosis table |
| Where the fleet's envelopes land (120 slow flights, cut at release) | land 65.8 %, Atlantic/other 13.3 %, Black Sea 13.3 %, Mediterranean 5.0 %, Baltic 1.7 %, North Sea 0.8 % | `scenarios/tools/envelope_stats.py` (method of `analyze_envelopes.py`) |
| If flown to exit instead | land 63.3 %, Mediterranean 15.8 %, Atlantic 14.2 %, North Sea 5.0 % | envelope_stats.py |
| Parachute drift during descent | median 26 km, P10 13 km, P90 44 km | envelope_stats.py |
| Envelope mass | 68.5 kg (BLE/Loon-class today); redesigned 4-day pumpkin 16.3 kg for a 40 kg payload (film 428 m² at 25 µm, 46 gores, 1,640 m of seams) | BLE `balloon.py`; `results/envelope_cost.md` §1 |
| Envelope cost | today ≈€10k mode (€4–25k); at 400k/yr volume, redesigned: €1,068 (€391–2,879) | `results/envelope_cost.md`, `cost_model.py` |
| What a returned envelope is worth | 16 kg of resin ≈ €4; recovery credit €99 (€7–738) per envelope ≈ 8 % of its cost; refly probability 0–30 % after a €40–150 inspection | envelope_cost.md §3(f) |
| What the pickup costs | €100–1,500 per envelope in the cost model (3 % of fleet cost); "pay the gig pickup for debris reasons; do not count on it for money" | `cost_model.py` ENVELOPE_RECOVERY_EUR; envelope_cost.md |
| Debris at fleet scale | base case 27,510 (21,646–34,486) t/yr of polyethylene coming down over Europe, the Mediterranean and the Black Sea | `results/cost_comparison.md` |
| Burning instead of parachuting | median 90 % of film consumed but shreds scatter over ~200 km; ~215 kg CO₂ per balloon; "not safer than parachute cut-down" | README (`burn_sim.py`, `results/burn_debris.csv`) |
| Collection assumption | 50–90 % of land landings collected | envelope_cost.md assumption register |

**Problem → solution:** the money is not in the film. The pickup network exists so that two-thirds of a fleet's envelopes do not become litter; the one-third that lands at sea (Black Sea 13 %, Mediterranean 5–16 %) is the unsolved part, and cutting down at the radio release (scenario A) rather than at the region edge (B) is what keeps the Mediterranean share at 5 % instead of 16 %.

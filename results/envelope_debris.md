# Envelope debris: how much, where it lands, and what each mitigation does to it

*Research note, 2026-10-17. Answers one question from the author: the envelope litter is significant and, unlike a satellite burning up or a launch plume, it is a visible artefact; how big is it, how does it compare, and what do the mitigations do to the number? Builds on `results/cost_comparison.md`, `results/envelope_cost.md`, `results/mitigation_research.md` (W21, W47) and `results/deployable_now.md`. Every figure is an estimate unless a source is named; the arithmetic is in the text so it can be redone.*

## What comes down, per balloon

A superpressure envelope is polyethylene film. The three vehicles in this repository shed these amounts per flight:

| Vehicle | Envelope mass | Film gauge | Film area if laid flat |
|---|---|---|---|
| Light, 40 kg payload (`results/envelope_cost.md` §4) | 17 kg | 25–30 µm | about 665 m², a 26 m square |
| Loon-class, the simulator's balloon | 68.5 kg | about 59 µm | about 1,250 m² |
| Class M, 90–100 kg payload (`vehicle.py` HEAVY, assumption) | 60 kg | about 59 µm | about 1,100 m² |

The area is the number a bystander meets: a field with a 26 m square of film in it, or a hillside with the sheet draped over the trees, plus tendons, fittings and the flight computer if nothing recovered it. The mass is the number permits are written against. Both are small per flight and large per fleet, which is why the architecture decides this question and the material does not.

## What comes down, per year, by scenario

| Scenario | Flights a year | Envelope | Film coming down | Left on the ground or at sea today (66 % land, 70 % of land pickups succeed) | With drop zones (90 % land, 90 % pickup) | With ships recovering half of sea landings as well |
|---|---|---|---|---|---|---|
| Planning case, light vehicle, 95 % coverage (the article's `About 300,000 flights a year`) | 300,000 | 17 kg | 5,100 t | 2,700 t | 970 t | 710 t |
| Planning case on today's envelope | 300,000 | 68.5 kg | 20,500 t | 11,100 t | 3,900 t | 2,900 t |
| Readiness layer: 50–100 standing on 100-day flights plus one 250-balloon surge a year (`results/deployable_now.md` phase 4) | about 430 | 60 kg | 26 t | 14 t | 5 t | 4 t |
| Standing-layer pilot, 60–120 flights (phase 2) | about 90 | 60 kg | 5 t | 3 t | 1 t | under 1 t |
| Pilot, 3–6 flights (phase 1) | 5 | 60 kg | 0.3 t | 0.2 t | 0.1 t | under 0.1 t |

The land fraction of 66 % and the pickup rate are from `analyze_envelopes.py` and `results/envelope_cost.md` (f); the drop-zone and ship columns are assumptions to be replaced by the parafoil and recovery work in the mitigation plan. The 300,000-flight figure is the article's; `results/cost_comparison.md` carries 27,500 t a year for the baseline fleet on today's envelope with a larger launch count, and the difference is the fleet size each note assumed, not the per-flight mass.

Two things follow. First, the debris problem is a property of the planning case, not of balloons: short winter flights on a light vehicle at hundreds of launches a day put thousands of tonnes on the ground, and no recovery scheme gets that below several hundred. Second, the readiness architecture the mitigation review chose, a thin standing layer on long flights with surge from a few sites, is two orders of magnitude smaller before any mitigation, and a few tonnes a year after it, which is a quantity a country already deals with in weather balloons: Europe's meteorological services release roughly a hundred radiosondes a day whose latex and payloads are not recovered.

## How it compares

The comparison the author asked for is with things the public does and does not see.

| Source | Where it ends up | Material | Amount a year | Visible? | Recoverable? | Basis |
|---|---|---|---|---|---|---|
| Balloon envelopes, planning case | ground and sea over Europe | polyethylene film, tendons, fittings | 5,100 t down, 700–2,700 t unrecovered | yes, a sheet in a field | partly, by pickup | this note |
| Balloon envelopes, readiness layer | ground, mostly in drop zones | same | 26 t down, 4–14 t unrecovered | yes | mostly | this note |
| Fibre-optic drone cable, Ukraine | fields, forests, towns along the front | glass fibre with acrylate coating | about 100,000 drones a month with spools over 10 km, so 1–2 million km a month; the Conflict and Environment Observatory put Russia's need at 6 million km in 2025; at about 70 g a kilometre that is roughly 400 t a year for one side, 500–1,000 t for both (my mass estimate from fibre geometry; nobody has weighed it) | yes, and it tangles machinery, animals and deminers | no, in practice | Ukrainska Pravda, May 2026; CEOBS via NPR, August 2025; Meduza, July 2026 |
| Starlink satellites re-entering | upper atmosphere, 60–80 km, as metal oxide particles | aluminium and alumina, with lithium, copper and others | 1–4 satellites a day in 2025–26 at 300–800 kg each is 100–1,200 t of satellite mass a year; alumina alone was 17 t in 2022 across all re-entries and is projected at 360 t a year at full megaconstellation build (Ferreira et al., GRL 2024) | no | no | USC study via earth.com; McDowell's counts via secondary reports |
| Launches to keep a constellation up | stratosphere and above | CO₂, water, black carbon, alumina | a Falcon 9 launch emits roughly 200–390 t of CO₂ and tonnes of soot into the stratosphere; at about a hundred launches a year that is 20,000–40,000 t of CO₂ and hundreds of tonnes of black carbon, where it persists two to three years and nothing else deposits it | no | no | Interesting Engineering on Ross's work; The Space Review; one vendor figure for soot, unverified |

The reading. Per tonne, the envelope is the least harmful of the four: inert polyethylene on the ground, which can be picked up, against glass that cannot, alumina that chemistry models now link to stratospheric circulation, and soot at an altitude where it is the only soot. Per photograph, the envelope is the most harmful of the four, because it is the only one a person can stand next to. The planning case would put more visible plastic on European ground each year than the drone war puts fibre on Ukrainian ground, and that comparison, not the per-tonne one, is the one the public would make. The readiness layer puts down less than one per cent of that. Both halves are true and the note that argues for the layer should say both.

## What each mitigation does to the number

In the order the mitigation review ranked them, with the effect on the readiness layer's 26 t a year and the planning case's 5,100 t:

1. **Fly fewer, longer flights.** Already the decision: readiness instead of the planning case, class M on 100-day flights instead of the light vehicle on two-day winter crossings. This is the ÷200 in the table, and no other line comes close. The light vehicle's film is thinner, but it flies fifty times as often per balloon-day.
2. **Bring the envelope down whole, into a drop zone, with the payload.** Decision 3 of the mitigation review recovers the payload by parachute or parafoil to pre-cleared zones; the same descent can bring the vented envelope down inside the zone instead of cutting it loose to drift the median 26 km of `analyze_envelopes.py`. Modelled here as 90 % landing on land and 90 % picked up: 26 t becomes 5 t; 5,100 t becomes 970 t. The parafoil's mass and the zone's size are the costs, and the ERA5 descent-wind study (rerun 3, the 0.25° winter pull) is what sizes the zone.
3. **Pay for pickup.** `cost_model.py` already charges €100–1,500 an envelope for pickup; `results/envelope_cost.md` finds the resin worth about €4 and the scheme worth having for litter, not money. A beacon on the envelope and a bounty raise the land pickup rate; 70 % to 90 % is the assumption used above.
4. **Ships for sea landings.** W47: a third of landings at sea for the planning case, uncosted. For the readiness layer with drop zones it is a tenth or less; a ship recovering half of those takes 5 t to 4 t. It is a planning-case mitigation that the readiness layer barely needs.
5. **Material.** No biodegradable film holds 1,000 Pa for weeks at −70 °C; bio-based polyethylene is still polyethylene on the ground; recycling credit is negligible (W21, `results/envelope_cost.md`). Material changes the chemistry of what is left, not the quantity, and belongs after the first four.
6. **Burning at altitude.** Rejected: `burn_sim.py` found a median 90 % consumed, shreds over a 200 km strip, 215 kg of CO₂ a balloon, and a permitting problem worse than litter.
7. **Permit against the residual.** Under MARPOL Annex V for the sea and the single-use plastics regime on land, a quantified loss rate with a recovery plan is a permit application; an unquantified one is a campaign against the project. The readiness layer's residual of 4–14 t a year across a continent is a quantity to put in the application; the planning case's 700–2,700 t is not.

## What this changes in the other notes

`results/deployable_now.md`'s approvals table has an environmental row that cites W21 and W47; it should carry the readiness layer's residual (4–14 t a year, estimate) so the permitting conversation starts from a number. The article's unsolved-risks bullet gives the planning case's 5,000 t and is correct for the fleet it describes; the next installment should say that the architecture the study now proposes puts down about 1 % of that, and show the comparison table. The weakness register's W21 keeps its severity for the planning case and gains the readiness figure.

## Sources

- Ukrainska Pravda, "Glass cobwebs in the fields", 10 May 2026: https://www.pravda.com.ua/eng/articles/2026/05/10/8034095/
- NPR (via member stations), fibre-optic drone litter and the Conflict and Environment Observatory's 6 million km estimate, 7 August 2025: https://www.kaxe.org/2025-08-07/fiber-optic-drones-are-leaving-miles-of-plastic-trash-along-ukraines-front-lines
- Meduza, fibre-optic cables blanketing the front, 29 July 2026: https://meduza.io/en/feature/2026/07/29/fiber-optic-cables-used-to-guide-drones-are-blanketing-ukraine-s-front-line-researchers-are-only-beginning-to-understand-their-environmental-impact
- Earth.com on Ferreira et al. (GRL 2024), 17 t of alumina in 2022 and 360 t a year at full deployment: https://www.earth.com/news/thousands-of-satellites-are-dying-above-our-heads/
- Interesting Engineering on Ross's modelling of rocket exhaust: https://interestingengineering.com/science/physicists-spacex-falcon-9-atmosphere
- The Space Review on black carbon potency and the 0.37 Gg megaconstellation estimate: https://thespacereview.com/article/5090/1

# Technical issues register

What the simulations say the stratospheric network cannot yet do, what would
fix each issue in the real world, and what a fictional setting would have to
assume to get past it. Built from the external panel review
(`medium/panel_review.md`) and the reruns that followed. "Measured" means a
simulation in this repo; "estimate" means a physics or engineering calculation
not simulated here.

Status as of 2026-10-17. Policy-grade numbers stay in `results/`; the "fiction
lever" column is explicitly speculative.

## 1. The radio's return costs coverage (panel A1) — measured, changes the cost

The cost model used the full time a balloon spends over the region (3.65 days,
launch-rate weighted). But coverage ends when the radio is released for its glide
home, and on board only forecasts are available (`forecast_release.py`, 120
slow-controller flights, glide ratio 14 at 20 kg/m², 100 km margin):

| Release rule | Useful dwell (launch-rate weighted) | Recovered | Fleet cost, mid case (scaled from €3.4 B) |
| --- | --- | --- | --- |
| As costed (no release loss) | 3.65 d | n/a | €3.4 B |
| Hindsight (best possible) | 2.48 d | 97.9% | ~€5.0 B |
| 7-day forecast lookahead | 2.27 d | 98.0% | ~€5.5 B |
| 5-day forecast lookahead | 1.98 d | 98.0% | ~€6.3 B |
| 3-day forecast lookahead | 1.73 d | 98.1% | ~€7.2 B |
| 1-day forecast lookahead | 0.91 d | 98.2% | ~€13.6 B |

Recovery is not the problem; the coverage spent getting into glide range is.
Stratospheric trajectory forecasts are usable for roughly 5–7 days, so the
5-day row is the defensible planning case: **about €6.3 B a year, not €3.4 B**.

- **Real-world fix:** recovery points that move with the fleet (ships, or
  sites along the main exit corridors) so a site is almost always in reach and
  the radio can be released late; longer-range gliders (glide ratio 18+, which
  also held up best out of sample, item 3).
- **Fiction lever:** a standing fleet of recovery ships that shadows the
  balloon conveyor, or catcher drones that meet gliders mid-descent, so release
  timing never costs coverage.

## 2. Descent winds below 13.6 km are missing (A3) — not yet measured

The glider and parachute runs taper the 150 hPa wind to 30% at the surface. The
real 8–12 km winter jet is often faster than the air above it. The 98% recovery
is an upper bound until full-column winds (1000–30 hPa) are flown.

- **Real-world fix:** fetch full-column winds along the 120 tracks and rerun
  `glide_tuning.py` (planned).
- **Fiction lever:** gliders that ride the jet instead of fighting it (descend
  early downwind, recover far east), or recovery sites placed under the jet's
  usual exit.

## 3. The glider design was tuned on its own test flights (A13) — measured

Choosing the design on flights launched on the 1st and testing on the 15th (and
the reverse) gives 96.5–100% recovery out of sample, but the winning design is
heavier and faster than the one in the article: **glide ratio 18 at 45–60 kg/m²**,
which lands at about 25–35 m/s and needs a final parachute or flaps.

- **Real-world fix:** adopt the heavier design; budget a small landing chute.
- **Fiction lever:** none needed; this is a design choice.

## 4. The costed vehicle has never been flown (A2) — not yet measured

All dwell and recovery figures use BLE's 68.5 kg envelope and 92.5 kg payload.
The cost case uses a 16–18 kg envelope and 40 kg payload, with different volume,
pump authority, power and day–night pressure swings.

- **Real-world fix:** re-fly a subset with the redesigned mass and volume.
- **Fiction lever:** state that the light vehicle behaves like the Loon-class
  one, or give the story world a mature light-envelope programme.

## 5. Lift-gas power runs out of pressure margin, not energy — measured

A fuel cell burning the lift gas ends every winter flight after 7–16% of the gas
(0.9–2.3 kg of hydrogen) is used, when the envelope can no longer hold pressure
(median 13 days, 20 flights). Keeping the water as ballast is worse (10 days).
Venting vapour is the right default. The redesigned vehicle carries only about
5–7 kg of hydrogen in total (estimate), so its margin is smaller still.

- **Real-world fix:** a separate hydrogen store for power, or an envelope rated
  for more superpressure (which costs the cheap thin-film design); avoid long
  darkness.
- **Fiction lever:** a high-strength film that holds several times today's
  superpressure at today's weight, allowing an overfilled envelope as a fuel tank.

## 6. Balloons drift into the Arctic and polar night (A6) — measured, with a caveat

Hemispheric flights reach a median 79–83°N. North–south winds near the polar
vortex (10–20 m/s) overpower a 3 m/s propeller. Caveat: the hemispheric wind grid
stops at 70°N and clamps above it, and BLE's 60°N solar check is bypassed, so
trajectories above 70°N are indicative only.

- **Real-world fix:** end flights before they leave the band; forecast-based
  latitude planning days ahead; stronger propulsion only near the vortex edge.
- **Fiction lever:** an Arctic exclusion line that operators treat as a hard
  wall, with balloons sacrificed rather than lost into the dark; or a polar
  variant with heavy power systems.

## 7. Winter flights are short — measured

January–March flights last 1.3–1.9 days; winter needs three to four times the
summer launch rate. This drives most of the annual cost.

- **Real-world fix:** ship and mobile launch upwind; the Canada loop.
- **Fiction lever:** a seasonal fleet: thin in winter, surged in summer.

## 8. Capacity per balloon is an assumption (A9, A10) — estimate

2 Gbps per balloon needs several reused beams (one beam at 100–200 MHz and
2–5 bit/s/Hz carries 0.2–1 Gbps). A 5° beam needs an array of about 1.6 m at
2.6 GHz and about 5 m at 800 MHz. A radio of this class plausibly draws
300–600 W, which a winter night (16 h) cannot supply from a 3 kWh battery.

- **Real-world fix:** a written beam, spectrum and power budget; test hardware.
- **Fiction lever:** large lightweight conformal arrays on the envelope itself,
  and a power source that is not the lift gas.

## 9. Overflight and airspace — legal, not technical

Loops clip Chinese airspace on 88–100% of flights. Unauthorised overflight
violates Article 8 of the Chicago Convention and ICAO Annex 2 rules for
unmanned free balloons; balloons have been shot down (2023, 1995).

- **Real-world fix:** end flights over Europe; no loops.
- **Fiction lever:** an overflight treaty, or a world where the balloons are
  tolerated, contested or shot at, as plot requires.

## 10. Smaller corrections that do not change the architecture

- Laser links between balloons: ~500–700 km, not 1,000 km (A11).
- Allied satellite capacity over Europe: about 1.5–2 Tbps by ~2030 once
  worldwide figures are allocated, not summed (A8).
- 20 dB and 29 dB are distance-only path-loss terms, not anti-jam margins.
- Star trackers give attitude, not position.
- Burn and hydrogen figures belong to the heavy vehicle; the redesign burns to
  about 53 kg CO₂ and needs about 5–7 kg H₂ (A5).
- 95% coverage is a footprint count, not computed from drifting tracks, which
  cluster (A14, planned).
- One year of winds (2025) is a case study (A12).

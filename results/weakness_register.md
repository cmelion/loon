# Weakness register

*2026-10-17. Every weakness found so far in one list: from the simulations (`TECHNICAL_ISSUES.md`), the external review of the Medium draft (`medium/panel_review.md`), the external review of the cost note, and the three research notes in `results/`. Severity: **F** could sink the case on its own; **M** changes the numbers or the product; **m** is a correction. Status is as of this date; the verdict on each, from the four-cluster mitigation review, is in `results/mitigation_research.md`. W34–W50 were added by that review.*

## Winds, vehicle and power

| # | Weakness | Evidence | Sev |
|---|---|---|---|
| W1 | Winter westerlies leave no directional diversity to steer with from January to March; flights last 1.3–1.9 days and winter needs three to four times the summer launch rate, which drives most of the annual cost. Confirmed 17 October 2026 on GFS, NCEP and ERA5 for 2025: a perfect altitude controller crosses the region in 1.8–1.9 days in January and 2.4 days over December–February on all three. Still one year. | `results/drift_2025.csv`; TI §7; `results/reruns_2026-10-17.md` §2, §8 | F |
| W2 | All results rest on one year of winds (2025), a 2.5° × 5° grid with five pressure levels, and hemispheric runs on a 2.5° reanalysis that clamps above 70°N. The qualitative winter result survives; the dwell, recovery and China-overflight values do not yet. | panel A4, A6, A12 | M |
| W3 | The costed vehicle (16–18 kg envelope, 40 kg payload) has never been flown in the model; every trajectory used BLE's 68.5 + 92.5 kg Loon-class balloon. Pump authority, power, volume and day–night pressure swing differ. | TI §4; panel A2 | F |
| W4 | The thin-film envelope (25–30 µm at 1,000 Pa) is unproven at volume; Loon's higher superpressure was largely diurnal thermal margin, so the main cost lever is also the main reliability risk. | TI §5; `results/envelope_cost.md` | F |
| W5 | Winter power: 16-hour nights at 50°N against a 3 kWh battery; a fuel cell on the lift gas ends flights when 7–16 % of the gas is burned; a 300–600 W radio cannot be carried through the night on the stock array. | TI §5, §8; `results/winter_power_summary.csv` | M |
| W6 | Hemispheric loops drift to 79–83°N into polar night and clip Chinese airspace on 88–100 % of flights; the cost case already excludes loops, but Canada and the "transatlantic loop" keep reappearing in the prose. | TI §6, §9; panel | m |

## Recovery and the glider

| # | Weakness | Evidence | Sev |
|---|---|---|---|
| W7 | Releasing the radio on forecasts rather than hindsight costs 40–60 % of useful dwell; the planning case is €6.3 B a year, not €3.4 B. | TI §1; `results/forecast_release.md` | F |
| W8 | The glider design was tuned on its own test flights; the out-of-sample winner is heavier and lands at 25–35 m/s; the airframe, actuators and avionics are uncosted; attrition is unknown; 98 % is a peacetime number that assumes roads, ports and safe landing areas. | TI §3; panel A13; cost note §3 | M |
| W9 | Return without GNSS is asserted, not designed: star trackers give attitude not position and do not work in a daytime sky at 20 km; unaided inertial drift over a two-hour descent is kilometres. | panel §5 | M |
| W10 | Descent winds below 13.6 km were a taper until this week; the full-column rerun holds 98.3 % but on a 2.5° reanalysis that smooths jet cores. A 0.25° check has not been run. | TI §2; `results/jet_test.md` | m |

## Radio, network and security

| # | Weakness | Evidence | Sev |
|---|---|---|---|
| W11 | 2 Gbps per balloon is an assumption. One beam at 100–200 MHz and 2–5 bit/s/Hz carries 0.2–1 Gbps; the rest is unstated spatial reuse. Loon demonstrated 10–40 Mbps. Every capacity, outage and Starlink-match figure hangs on this. | TI §8; panel | F |
| W12 | Antenna aperture: a 5° beam needs about 1.6 m at 2.6 GHz and about 5 m at 800 MHz; the article's 1.7 km spot and 40–80 km footprint are not reconciled, and the HIBS bands are low-band. | TI §8 | M |
| W13 | Ordinary handsets at this geometry are undemonstrated: uplink closure at the footprint edge (14° elevation), timing advance, Doppler, cell selection and handover with the node moving at 10–70 km/h. | panel §7 | M |
| W14 | Spectrum: WRC-23 HIBS identification is not a licence; national bands, PFD limits and terrestrial-IMT protection can cap capacity; a balloon drifting across a border cannot lawfully keep transmitting on the first country's band without an emergency-roaming framework that does not exist; operators who supply spectrum in kind hold the product. | panel; cost note §4; target note E | F |
| W15 | Backhaul is not dimensioned: inter-balloon optical links reach 500–700 km with clearance, not 1,000 km; gateways, edge trunks (85 for the degraded-data case) and routing capacity are an allowance of €156 a flight. | panel A11; cost note | M |
| W16 | Island mode is an architecture, not a feature: local core, subscriber authentication without the home network, 112 routing and location, timing without GNSS, lawful-intercept decisions. Uncosted. | panel; target note E | M |
| W17 | Jamming: the 20 dB and 29 dB figures are distance terms; the uplink into a balloon has the opposite geometry; a jammer next to the user or above it defeats both systems; ordinary phones cannot use a directional panel. The smaller visibility radius (about 25× less area than a satellite) is the real advantage and is a reach argument, not a margin. | panel §5; target note E | M |
| W18 | Denial of service: demand overload needs priority and pre-emption classes designed into the core; gateways and the core are internet-facing; island-mode ingress control is a choice to pay for; the fleet's command-and-control plane is a single target whose compromise is a safety event. | target note E; panel §7 | M |

## Operations, airspace, safety and environment

| # | Weakness | Evidence | Sev |
|---|---|---|---|
| W19 | Around 800 autonomous 40 kg glider descents a day through controlled airspace, landing at 15–35 m/s (8 kJ and up), is a UAS-integration programme: detectability, lost-link rules, landing-zone liability, military deconfliction, certification. Permission to fly a balloon does not cover it. | panel A, §7 | F |
| W20 | Overflight: unmanned free balloons need each state's authorisation (ICAO Annex 2); states have shot balloons down (2023, 1995); at 20 km the platform is a slow target wherever the airspace is contested, which is the case the series started from. | TI §9; panel | F (war case) / m (peacetime) |
| W21 | Envelope debris: 5,000 t a year of polyethylene with the redesign, 27,500 t with today's envelope, a third landing at sea; burning at altitude scatters shreds over 200 km. Expected to dominate public reaction and permitting. | `results/cost_comparison.md`; `burn_sim.py`; panel | F |
| W22 | Hydrogen: 6,400 t a year in the baseline; staying under the Seveso lower tier is threshold avoidance, not a safety case; ATEX, transport and maritime rules apply. | cost note; panel | m |
| W23 | Surge geometry: 443–1,476 launches a day for one 300 km zone needs 10–31 sites upwind of a zone that is not known in advance; launches stop in the weather that caused the outage. | `results/outage_scenario.csv`; target note F | M |
| W24 | Time to coverage: 5–36 hours after launch. The Iberian blackout was over for most people before a balloon would have arrived; the surge case is the multi-day event only. | target note D | M |
| W25 | "95 % coverage" is a footprint count, not an availability: drifting nodes cluster; population-weighted availability, outage duration and winter tails have not been computed. | panel A14 | M |

## Economics, programme and evidence

| # | Weakness | Evidence | Sev |
|---|---|---|---|
| W26 | Per square kilometre the layer is 12–53× Starlink depending on the case, and no stack of engineering levers keeps 95 % year-round service within 5×. Per gigabyte it is 60× at the assumed radio and 10,000× at Loon's. | `results/cost_comparison.md`, `cost_reduction.md` | M (as a sovereignty purchase) / F (as a telecom) |
| W27 | The readiness cost (€0.2–0.5 B a year) is a desk estimate outside the model; the stock first described could not field the surge it quoted; a standing layer of 50–100 balloons is the plausible exercised form but is unmodelled. | cost note §4; target note F | M |
| W28 | Funding: no legal basis, budget line or instrument fits as first claimed (rescEU needs an eligibility decision; the EDF funds R&D; NATO resilience is national); no development bill or date for a first operational year. | cost note §4; panel 2 | M |
| W29 | The counterfactual is unpriced: the cheapest allied bundle of IRIS²/OneWeb capacity, pre-positioned terminals and a direct-to-cell contract for the same emergency service. Without it the "autonomy premium" is the gross cost. | cost note §1 | F (for the argument) |
| W30 | The permanently uncovered population is small (about 1 %, 4–8 M) and best served by direct-to-cell; IRIS² and DTC will be in service before a pilot closes the three technology gaps; Loon itself shut down in 2021 as uneconomic. "Why now, and why this" has no written answer. | target note A; panel | M |
| W31 | Evidence quality: private repository described as reproducible; hindsight in launch-site choice and release timing; BLE's tropical controller and solar model at 50°N; one wind year; small samples (16 tropical baseline flights, 36 Canada flights). Partly resolved 17 October 2026: the repository carries an MIT licence and is being made public with the article, and ERA5 reproduces the 2025 GFS and NCEP figures within rounding (`results/reruns_2026-10-17.md`). Hindsight, the tropical controller, the single year and the samples remain. | panel | M |
| W32 | Capability creep: cameras, jammer geolocation, ship tracking and "anti-jam arrays" in a connectivity proposal invite the surveillance reading and an ITAR/privacy/China reply; the external review split on whether to drop or disclose them. | panel | m |
| W33 | Prose and framing: title overclaims; headline numbers precede caveats; machine cadence; "autonomy is worth more than any price tag" is not a budget argument. | panel 1 and 2 | m |

## Added by the mitigation review (2026-10-17)

| # | Weakness | Raised in | Sev |
|---|---|---|---|
| W34 | Launch-weather availability: the storm that causes the outage closes the upwind launch sites, and site closures are spatially correlated. No dispatch-availability model exists. | b1, b3 | M |
| W35 | Pump, valve and compressor cycle life and altitude authority on the light craft; if authority collapses there is no slow transit left. | b1 | M |
| W36 | Thermal control: battery heaters and cold capacity through winter nights; condensation on a two-hour descent from −70 °C into maritime air; icing on a glider through winter cloud. | b1 | M |
| W37 | No configuration-controlled mass and volume budget: the thin envelope, long-range glider, winter power system and optical terminals cannot all be assumed to fit in 40 kg. | b1 | M |
| W38 | Fleet common-mode behaviour: identical controllers on one forecast cluster, exhaust the same altitude band, or terminate together; a bad update or shared trigger could release hundreds at once. | b1, b3 | M |
| W39 | Interference from hundreds of airborne cells into surviving terrestrial networks, and the moving-cell radio-network problem: physical-cell identities, neighbour lists, handover storms at 10–70 km/h. Real outages are patchy, so co-channel operation over a half-live network is the common case. | b2, b3 | F |
| W40 | Indoor uplink in a winter blackout: 15–25 dB building loss at 14° elevation; every demonstration so far was outdoor. | b2 | M |
| W41 | TDD synchronisation and fleet-wide timing under GNSS loss; FDD fallback. | b2 | m |
| W42 | 112 location and caller identity from an 80 km cell; advanced mobile location may not reach the right PSAP in island mode. | b2 | M |
| W43 | Handsets exhaust their batteries searching for a network during the 5–36 hours before balloons arrive. | b2 | m |
| W44 | En-route air traffic and 1090 MHz occupancy: hundreds of transponding balloons climbing through airline levels and loitering at FL650 is a Eurocontrol and address-space problem radiosondes never posed. | b3 | M |
| W45 | Third-party liability and insurance: Regulation 785/2004 cover for hundreds of daily descents over dense land is unlikely without a state indemnity statute. | b3 | F |
| W46 | Hangar consenting: 40–80 hydrogen inflation hangars need planning, ATEX land use and often environmental assessment, a five-to-ten-year programme that sets the first operational year. | b3 | M |
| W47 | Maritime recovery logistics for a third of landings: vessels, weather windows, saltwater survivability, beacons; uncosted. | b3 | M |
| W48 | Emergency airspace competition with rescue, firefighting and military aircraft in the very zone the layer serves. | b3 | m |
| W49 | Environmental permitting beyond litter mass: habitats and birds directives at recovery areas, batteries and electronics, hydrogen leakage, termination zones. | b3 | m |
| W50 | Programme structure: procurement, state aid and concession terms; supplier and control-chain sovereignty component by component; stranded assets and stop gates; simultaneous emergencies; subscriber trust and key custody in island mode. | b4 | M |

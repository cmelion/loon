# Is 2 Gbps per platform feasible, and can the backhaul carry it?

*Research note, 2026-10-17, revised the same day after a three-model external check (gpt-5.6-sol, grok-4.6, gpt-6.1-sol; their corrections are listed at the end). Written to answer one objection to `results/mitigation_research.md`: the panels rebased the radio to tens of megabits without saying what evidence would support more. Outside figures are marked (claim) when they come from the vendor, (reported) when a regulator or third party published them, (estimate) when they are mine. "2 Gbps" throughout means gross outdoor downlink aggregate from one platform, not goodput, not busy-hour carried traffic, not uplink.*

## The answer first

2 Gbps of gross outdoor downlink from one stratospheric platform is physically plausible. It comes from reusing a 20 MHz carrier across 40–70 spatially separated beams at 1.4–2.5 bit/s/Hz, which a 1.6–2 m array at 1.8–2.6 GHz can form and which 0.3–1.2 kW of DC power can drive. That is a 90–100 kg-class payload, the mass class the simulation flew, though not the Loon payload it flew: it is a new radio, a new array and a new power system in that mass. It is not the 40 kg, 300–600 W payload the cost case prices; that one carries a voice, text and thin-data node. Nobody has published a simultaneously loaded multi-beam aggregate from a stratospheric cellular platform above the tens of megabits Loon delivered; the largest built system, Stratospheric Platforms' 3 m array, is a claim of 500 beams at up to 150 Mbps each that has flown only as a single-phone demonstration.

| Payload class | Mass, power, aperture | Beams at 1.8–2.6 GHz over a 40 km-radius footprint | Gross outdoor downlink | Where the confidence sits |
|---|---|---|---|---|
| L: the costed vehicle | 40 kg, 300–600 W, 1.0–1.6 m | 10–25, power-limited, fewer through a winter night on 3 kWh | 0.2–0.6 Gbps | high confidence that 2 Gbps is out of reach |
| M: the simulated mass class | 90–100 kg, 0.8–1.5 kW, 1.6–2 m | 40–70 | 1–2.5 Gbps | physics plausible; mass, power, thermal, interference and backhaul not closed; a new payload, not the Loon one |
| H: aircraft and airship payloads | 150 kg and up, 2–3 kW, 3 m | 100–500 | 5–25 Gbps (Stratospheric Platforms' 500 × 150 Mbps multiplies to 75 Gbps, a product of claims) | physics plausible, flight evidence thin; not a balloon payload this repository flies |

What users would get is a different number from any of these. Uplink from a 0.2 W phone is the binding constraint, building loss in a winter blackout is 15–35 dB, and the product's real indicator is indoor uplink service in an outage, which no demonstration has measured. The reviewers' summary is the right headline: 2 Gbps gross outdoor downlink is physically plausible on a medium or heavy payload with aggressive multi-beam reuse; the balloon payload, the winter energy system and the end-to-end backhaul are not yet engineering-closed.

## 1. What has been flown or built

| System | Platform | Array | Beams | Rate | Mass and power | Where, when | Status |
|---|---|---|---|---|---|---|---|
| Loon LTE | balloon, 20 km | ~0.5 m patch arrays, steerable | a few | 18.9 Mbps down, 4.7 up in Kenya user tests (reported); roughly 5 W per port on 5 MHz (secondary, unsourced) | payload 92.5 kg total; electronics drew on the order of 100 W, the platform more | Kenya 2020–21, Peru, Puerto Rico 2017; tropical | retired 2021 |
| HAPSMobile Sunglider | solar aircraft | not published | MIMO, Band 28 | not published | payload up to 68 kg (design) | New Mexico, Sept 2020, 33°N | demonstration |
| SoftBank six-cell payload | light aircraft at 3 km, not the stratosphere | six cells | 6 | 33 Mbps average at one point 15 km out (reported); 6 × 33 is my product, not a measurement | not published | Tokyo | demonstration |
| CST stratospheric 5G NR cell | Grob aircraft, stratosphere | one cell | 1 | 86 Mbps peak, 50.8 average (regulator-reported) | not published | Red Sea, 2022; very likely the same campaign as Stratospheric Platforms' March 2022 Saudi flight | demonstration |
| Sceye with Nokia | stratospheric airship | not published | | calls, video and emergency calls through SoftBank's core in 2026 (reported); rates not published | hundreds of kg payload class | New Mexico 2023–24, Japan 2026, 33–34°N | pre-commercial |
| AALTO Zephyr D2D payload | solar aircraft | not published | | throughput measured, not published | payload 5–25 kg class | Kenya 2024–25 | demonstration |
| Stratospheric Platforms StratoMast | hydrogen aircraft, 20 km | 3 m × 3 m phased array | up to 500 (claim) | up to 150 Mbps per beam, 140 km diameter, 15,000 km² (claim; the two coverage figures are one claim) | not published; liquid-hydrogen power | subscale array ground trials with BT and Cambridge Consultants 2023; one stratospheric flight connected a phone, 2022 | pre-commercial |
| AST SpaceMobile BlueBird | LEO, 500+ km | 64 m² (Block 1), ~223 m² (BlueBird 6) | many | 98.9 Mbps peak, Block 1, company-reported November 2025; 120–200 Mbps targets for later blocks | satellite class | 2024–26 | commercial ramp; orbital, so a weak comparator |
| Nokia HAPS system study | 7-cell HAPS at ~2 GHz | | 7 | downlink 1.40 bit/s/Hz per cell mean, 0.32 at cell edge; uplink 0.61 and 0.08; simulation output, paper to be cited | | | reference for spectral efficiency, not a measurement |

What the table supports: single stratospheric cells to ordinary phones at 50–86 Mbps are reported; 150 Mbps per beam is a claim; six simultaneous cells have flown at low altitude; hundreds of beams from one platform are built as subscale arrays and funded at full scale but not flown; and no simultaneously loaded multi-beam direct-to-handset aggregate from the stratosphere has been published in anything found for this review.

## 2. The capacity arithmetic

Aggregate downlink = beams × bandwidth per beam × spectral efficiency, with spatially separated beams reusing one carrier. Beam count is capped by aperture, by power, and by interference and the WRC-23 power-flux rules.

**Aperture.** Broadside beamwidth ≈ 70 λ/D degrees; spot at nadir = 2 × 20 km × tan(half-beam). Counting non-overlapping spots inside a 40 km radius with the mean spot taken as 2.5 times the nadir spot (the edge of a 40 km footprint is already 63° off nadir; an 80 km footprint, 76° off nadir, was in the first draft and is removed because scan loss and ground projection make the count meaningless there):

| Frequency | Aperture | Beam | Nadir spot | Separable spots, 40 km radius |
|---|---|---|---|---|
| 800 MHz | 1.6 m | 16° | 5.8 km | ~30 |
| 800 MHz | 3.0 m | 9° | 3.1 km | ~110 |
| 1.8 GHz | 1.6 m | 7° | 2.5 km | ~160 |
| 2.6 GHz | 1.0 m | 8° | 2.8 km | ~130 |
| 2.6 GHz | 1.6 m | 5° | 1.8 km | ~330 |

This is a packing count, not a reuse plan. Adjacent co-channel beams interfere through main-lobe overlap and sidelobes; a reuse-1 plan with a 1.6 m array at 7° beamwidth will run at the Nokia mean of 1.4 bit/s/Hz, not at 2.5, and a three-colour plan halves the aggregate. The conclusion that survives: at 1.8–2.6 GHz the aperture is not the limit on beam count, power and interference are; at 800 MHz the aperture is the limit, which is why the low band is coverage and the mid band is capacity.

**Power.** Broadside gain of a 1.6 m aperture at 60 % efficiency is about 27 dBi at 1.8 GHz and 31 dBi at 2.6 GHz, falling with scan; 25 dBi net is a fair planning figure. Taking 2–5 W of RF per 20 MHz beam as an assumption rather than a derived requirement (a proper link budget at nadir and edge, downlink and uplink, with scan loss, body loss, noise figure, interference and the power-flux cap, is the first missing artefact):

| Beams | RF | DC at 30 % RF efficiency | DC with fixed loads (estimate) |
|---|---|---|---|
| 6 | 12–30 W | 40–100 W | 100–200 W |
| 20 | 40–100 W | 130–330 W | 250–500 W |
| 40–72 | 80–360 W | 270–1,200 W | 0.5–1.5 kW |
| 500 | 1–2.5 kW | 3.3–8.3 kW | 4–10 kW |

The fixed loads matter: digital beamforming over hundreds of elements, converters, baseband, calibration and rejecting a kilowatt of heat into air at 7 % of sea-level density are not covered by a power-amplifier efficiency, and the 1.6 m active aperture itself is 20–40 kg before amplifiers and electronics (estimate). This is where the 40 kg payload stops in daylight and the 90–100 kg payload has to be designed, not assumed.

**Putting it together.** 2 Gbps = 40 beams × 20 MHz × 2.5 bit/s/Hz = 72 beams × 20 MHz × 1.4 bit/s/Hz. With 20 MHz available from one operator at 1.8–2.6 GHz, reuse-1 across the footprint, and the realistic mean efficiency, it is about 70 beams, 150–350 W of RF, 0.5–1.5 kW of DC, on a 1.6–2 m array with 70 RF chains, plus the array's own mass. Timing advance at 40–80 km slant ranges exceeds what LTE supports and points to NR with extended timing, which is one reason not to copy Loon's radio.

**Two corrections to earlier notes.** The 2 Gbps in `outage_scenario.csv` is a class M number and should be read as such. And the panel review's "0.2–1 Gbps per independent channel" arithmetic counted bandwidth in one beam; spatial reuse of a narrow carrier is the larger source of capacity, which the review did not weigh. The earlier verdict that the 40 kg layer is voice and text stands; the suggestion that 2 Gbps is unsupported in principle does not.

## 3. Uplink and indoor

The Nokia study's uplink-to-downlink efficiency ratio is 0.44; after scan loss and many phones sharing uplink resources, 0.3–0.4 is a fair planning ratio, and it is a study result, not a physical bound. Building-entry loss at 1–3 GHz is 15–25 dB for ordinary construction and 25–35 dB for modern thermally efficient European housing (ITU-R P.2109 gives the distributions), and the winter blackout is an indoor scenario. The product should therefore be reported as three numbers, outdoor downlink aggregate, outdoor uplink aggregate and indoor service probability by building class, and the last of these is the one that decides whether a phone in a kitchen reaches the balloon. On the figures here, application-layer busy-hour traffic in an outage is plausibly 0.1–0.4 of the gross outdoor downlink, with a large voice-and-text-only tail. Window and roof repeaters would change that and need power.

## 4. Backhaul

Traffic either stays inside the zone (which needs a local core, authentication and applications that actually run locally, not just two users in the same region) or leaves it over the balloon mesh and down through a gateway to fibre.

| Link | Demonstrated | Rate | Range | Terminal mass and power | Weather and limits |
|---|---|---|---|---|---|
| Balloon to balloon, optical | Loon flew inter-balloon optical links over about 100 km (2016–18; rate unpublished). Loon's 2019 seven-link, roughly 1,000 km relay chain is widely reported but its medium, optical or radio, is not confirmed here. Loon's optical team became Taara, whose ground terminals do 20 Gbps over 20 km (claim). | space terminals are 10–100 Gbps class; the balloon-to-balloon rate is unmeasured | 500–700 km between balloons at 20 km, above the weather | space-qualified terminals: Tesat SCOT80, 10–100 Gbps depending on configuration, 8,000 km, 60–80 W, 12–15 kg (datasheet); smaller 100 Mbps-class terminals under 2 kg and 35 W (Tesat SCOT20 as listed, to be verified); Mynaric CONDOR Mk3, 100 Mbps to 100 Gbps, mass to be obtained | pointing and acquisition on a rotating, swinging gondola is the engineering, not range; a tracked terminal serves one peer at a time, so mesh degree equals terminal count |
| Balloon to ground, E-band radio | 10 Gbps balloon-to-ground links in Loon's patents; a 40 Gbps bidirectional air-to-ground E-band link demonstrated in 2019 (programme and conditions to be cited) | 2–10 Gbps | tens of km slant | a few kg, tens of W | rain and wet snow through the lowest kilometres fade E-band badly; it is the winter fallback for optical ground links and needs its own lower-band fallback and licence |
| Balloon to ground, optical | CAPANINA flew 1.25 Gbps from 22 km to a transportable optical ground station in 2005 | 1–10 Gbps | to the 5° elevation ring, about 194 km (the geometric horizon is 505 km) | as above | cloud blocks it; one North Atlantic low can cover a whole 300–500 km ring, so diversity has to be shown with joint cloud statistics, not asserted |

**The funnel for a zone of 300 km radius.** These are scenarios: they assume every platform delivers its nominal rate at once and that 30 % of traffic stays local, neither of which is established.

| Radio class | Balloons aloft | Aggregate | Egress | Gateway links at 2 Gbps | at 10 Gbps |
|---|---|---|---|---|---|
| Loon-class, 30 Mbps | 254 | 7.6 Gbps | 5 Gbps | 3 | 1 |
| L, 0.2 Gbps | 254 | 51 Gbps | 36 Gbps | 18 | 4 |
| L, 0.2 Gbps | 848 | 170 Gbps | 119 Gbps | 60 | 12 |
| M, 0.5 Gbps carried | 254 | 127 Gbps | 89 Gbps | 45 | 9 |
| M, 2 Gbps gross | 254 | 508 Gbps | 356 Gbps | 178 | 36 |
| M, 2 Gbps gross | 848 | 1.7 Tbps | 1.2 Tbps | 594 | 119 |

**Gateways are many, and sites are not links.** The gateways serving a dark zone sit in the ring 300–500 km from its centre, where grid and fibre are still up and the balloons at the zone's edge can see them inside the 194 km elevation ring; a balloon at the centre cannot see the ring and needs one or two mesh hops, if the links are up and a relay balloon is placed to carry them. The ring is about 503,000 km²; fibre-fed tower sites at 100 km spacing give 50 candidate sites, at 50 km spacing 200. Each simultaneous optical or E-band link needs its own steerable head, tracker, clear field of regard, backhaul port, power, shelter and maintenance, so the number of simultaneous links is set by heads installed, not by sites counted. At 2–10 Gbps a head, 50–200 heads carry the class M carried-traffic case and, with 10 Gbps heads or 50 km spacing, the gross 2 Gbps case; the Loon-class and L cases need a handful. The cost of heads is not in any model: a modest E-band head on an existing tower might be €50–150 k, a tracking optical ground station with power, shelter and fibre extension several times that, and a national programme of a few thousand heads is a capital line of order €0.1–1 B (estimate, to be replaced by quotations). Routing over a wind-blown topology with changing neighbours is Loon's Tempest problem and degrades TCP; it needs its own design.

**Blocking it.** Optical beams are microradians wide and E-band beams are pencils: off-axis jamming and passive interception are impractical, and with many reachable gateways over a mesh there is no single link to attack. Three things remain exposed and are not minor: the ground gateways share weather, so the ring needs lower-band radio fallback and sites far enough apart that one weather system does not cover them; the fibre points of presence and their power are ordinary infrastructure that can be cut; and the mesh's command plane, the access radio and the optical receivers themselves (dazzling, acquisition-channel attacks) are the attack surface the register already names in W18.

## 5. Energy: lasers and the fuel cell

A relaying balloon carries two or three optical terminals plus a gateway link. At space-terminal class that is 120–240 W continuous and 25–45 kg plus gimbals, isolation and beacons, which the 40 kg payload cannot carry and the 90–100 kg class can only with everything else trimmed. Lighter airborne terminals in the 5–10 kg, 30–60 W class are plausible but no datasheet found here supports a number; it is a procurement question.

The night is the sizing case, but the load is not 500 W: the class M radio alone is 0.5–1.5 kW in daylight, and a reduced night mode has to be defined before the store is sized. For 500 W over a 16-hour winter night, 8 kWh:

| Store | System specific energy | Mass for 8 kWh | Notes |
|---|---|---|---|
| Lithium-ion pack | 200–250 Wh/kg warm; less at −60 °C with heaters and reserve | 32–40 kg, a lower bound | the stock BLE battery is 3 kWh |
| Lithium-sulfur | ~400 Wh/kg at cell level (unverified; pack level lower) | ~25 kg and up | flown on solar aircraft, not on balloons |
| Hydrogen fuel cell, separate tank | hydrogen 33 kWh/kg at 50 % stack efficiency gives about 16 kWh per kg consumed, so 0.5 kg a night; a 700 bar composite tank holds 5–6 % hydrogen by mass, so tank plus gas is 8–10 kg per night's fuel; stack, balance of plant, regulator and thermal system add 5–10 kg | 15–30 kg for one to two nights | the first draft's 8–16 kg omitted the stack and balance of plant |
| Regenerative fuel cell | 400–800 Wh/kg at system level in studies (NASA cites ~790 Wh/kg at 53 % round trip; unverified) | 10–20 kg on paper | not flown on a balloon; needs daytime solar to recharge, which 50°N in January does not give |

Two things the first draft missed. Oxygen: ambient pressure at 20 km is about 55 hPa, so an air-breathing stack needs a cathode compressor with its own power and mass, or carried oxygen at about 8 kg per kilogram of hydrogen, 4 kg a night, with its own tank. And daytime: winter sun at 50°N is low and short, so the array has to carry the day load and recharge whatever store is used, and that balance has not been run.

The seasonal picture still favours the fuel cell for winter, with one refinement that is yours. Winter flights last 1.3–2 days. On the 90–100 kg class vehicle with about 14 kg of lift gas, a 500 W night burns 0.5 kg, 3–4 % of the fill; `TECHNICAL_ISSUES.md` §5 found that fuel-cell flights end when 7–16 % has been burned, so one or two winter nights on lift gas stay under the collapse threshold and the separate tank, its mass and its safety case can be dropped for the transit product. On the 40 kg class with 5–7 kg of gas the same night is 7–10 % and the envelope loses pressure after one night. For summer's week-long flights with 8-hour nights, solar plus a 4 kWh store is the candidate, with margin for recharge losses and cloud albedo still to be shown. A separate high-pressure hydrogen cylinder under a hydrogen envelope, where it is used, is a pressure-vessel, leak, ignition, cut-down and dangerous-goods case for the aviation authority, not a line in a table; the oxygen problem applies either way. The fuel cell is a credible candidate for the winter conveyor on the heavier vehicle; the note does not establish that it closes mass and power, and the reviewers were right to say so.

## 6. What this does to the architecture

The simulation flew a 92.5 kg payload and the cost case priced a 40 kg one. The arithmetic says the heavier class is the one that can carry a 1–2 Gbps radio, optical terminals and a night power system, as a new payload designed for that mass; the lighter class carries a voice-and-text node and a single low-rate link to a neighbour. Three ways to resolve it:

1. **One heavy class.** Fly a class M payload on the simulated envelope, accept roughly €37 k a flight from `cost_comparison.md`, and rebuild the payload mass and power budget from zero. The dwell and recovery figures already apply to this mass class; the cost figures do not.
2. **Two classes, hub and spoke.** Loon's super-node patent describes optical links between a few hubs and radio links from hubs to many sub-nodes. It is prior art, not an operating record. A hub must carry its spokes' aggregate traffic, enough terminals for two backbone directions plus a gateway plus the spoke-facing link, and spare energy; losing a hub takes several spokes off the network; spokes must stay within range of hubs while both drift, which is a formation-keeping problem the controller has not been asked to solve; and 2 Gbps becomes a per-hub figure while coverage density follows the spokes. The hub ratio is a design output, not a guess of one in four.
3. **One light class** and a voice-and-text product, which is the panel's verdict and the only option that matches the current cost case.

The cost model should be run for all three; it has only been run for a vehicle nobody designed.

## 7. What would settle it

1. A closed mass, power and link-budget spreadsheet for a class M payload before any flight: array electronics and structure, RF chains, pointing, optical terminals, energy store with oxygen supply, thermal rejection and reserves, with downlink and uplink budgets at nadir and at the 40 km edge under the WRC-23 power-flux limits. If it does not close on paper, nothing else matters.
2. A simultaneous array measurement: 50–70 concurrently loaded beams from a 1–1.6 m array at 1.8–2.6 GHz on a tower or tethered aerostat, with phones loading every beam, reporting aggregate throughput, error vector magnitude, amplifier back-off and co-channel SINR. Cambridge Consultants and BT ran the ground version for Stratospheric Platforms in 2023; ask for the data or repeat it. €0.3–1 M, six to nine months.
3. One class M payload flight at 50°N in winter through at least three nights, with the night mode defined in advance. €2–8 M, one winter.
4. The inter-balloon optical rate: ask X or Taara for Loon's measured link rates, or fly two terminals on two balloons 300–500 km apart and measure acquisition time as well as rate. €1–5 M.
5. The backhaul simulation in `mitigation_research.md`: mesh connectivity and gateway reach on the real tracks, with heads rather than sites, 2 and 10 Gbps links, routing over the drifting topology, and winter cloud and rain statistics for the ring, reporting delivered egress.
6. A fuel-cell night test at 55 hPa and −60 °C with a real cathode air supply, covering start-up, water management and purge losses, for the lift-gas case on the heavy vehicle.

## Review record

Three reviewers checked the first draft on 2026-10-17. Adopted: the evidence table overstated what is measured (150 Mbps is a claim; SoftBank's 33 Mbps was at 3 km altitude; six cells are not "tens of beams"; the Saudi CST test and the Stratospheric Platforms Saudi flight are probably one campaign; Loon's 100 W was the electronics, not the platform; Nokia's efficiencies are simulation outputs) and now says so; the "nobody above 100 Mbps" sentence is restricted to loaded multi-beam cellular access and to what this review found; the 80 km beam columns are removed as meaningless at 76° off nadir; gain stated as 27–31 dBi broadside falling with scan; the power table carries fixed loads and the 40–72-beam RF range (80–360 W) separately; reuse-1 is not assumed free; the uplink ratio is corrected to 0.44 from the cited figures with 0.3–0.4 as a planning value; building loss widened to 25–35 dB for modern housing and the product restated as three numbers; the Loon seven-hop chain's medium marked unconfirmed; terminal figures marked space-class with balloon pointing as the open item; funnel rows labelled scenarios; sites distinguished from heads; the gateway cost widened and marked for quotation; the blocking paragraph softened and the attack surface named; the fuel-cell mass corrected to include tank fraction, stack and balance of plant; oxygen supply at 55 hPa and the winter daytime balance added; the separate-tank safety case stated; the hub-and-spoke section rewritten with terminal degree, hub failure and formation-keeping; numerical confidence odds removed. Not adopted: one reviewer's view that the correction to the panel's single-wide-channel reasoning is unfair; both mechanisms are real and the note now says reuse is the larger one. One reviewer suggested the 40 kg class might still reach more with narrower coverage or more spectrum; the class L row keeps the power-limited range because the night energy, not the footprint, sets it.

**A Connectivity Layer No One Can Switch Off**

*We flew 1,600 simulated balloons through a year of real stratospheric winds. The result: Europe and Canada could run their own phone-direct connectivity layer for about €3.4 billion a year, with no rockets, no dishes and no foreign off-switch. Here is what works, what it costs, and what is still unproven.*

(Alternative title: **Balloons Over Europe: The Numbers Behind a Sovereign Connectivity Layer**. Alternative subtitle: *A year of real winds, 1,600 simulated flights, and an honest cost sheet for a network that phones connect to directly.*)

Europe relies on one foreign company for most of its satellite broadband. Its ground networks can fail across whole countries. On its eastern flank, radio links are jammed as a matter of routine. This article tests one answer: a fleet of steerable balloons at about 20 km that phones connect to directly, launched from ships and depots, whose radios glide home after every flight.

Every number below comes from a simulation we ran, a physics calculation, or a cited figure. Where a number is an engineering estimate or assumption, it says so. The simulation code and results live in a private repository; the scripts named below are available on request.

## Three single points of failure

Europe's connectivity can fail in three ways at once, and the current fallbacks share the weaknesses.

- **One foreign operator.** Satellite broadband over Europe is dominated by Starlink. Its limits on use in Ukraine were widely reported, and on 24 July 2025 an internal software failure took the whole network down for about two and a half hours. A government can't base its resilience on a service someone else can switch off.
- **Ground networks fail together.** In the Iberian blackout of 28 April 2025, more than half of mobile users across large areas of Spain and Portugal lost service within hours as cell-site batteries ran down. One operator's customers were offline for over a day. War, sabotage, cyberattack or a severe storm can do the same to a region the size of a country.
- **Contested spectrum.** Satellite-navigation jamming around Kaliningrad and over the Black Sea is now routine. Signals that come down from orbit arrive weak, which makes them easy to swamp.

A new layer has to answer all three. It must be under allied control, independent of the ground grid, and hard to jam.

## How we tested it

We flew more than 1,600 simulated balloons through a real year of winds, using the physics engine behind Project Loon.

- **Simulator:** Google's open-source [Balloon Learning Environment](https://github.com/google/balloon-learning-environment) (BLE), version 1.0.1. It models a Loon-class superpressure balloon: 68.5 kg envelope, 92.5 kg payload, 3.06 kWh battery and six 210 W solar panels. An air pump changes altitude.
- **Winds, Europe:** hourly GFS winds for all of 2025 at 150, 100, 70, 50 and 30 hPa, from the [Open-Meteo](https://open-meteo.com/) archive. The grid is 2.5° × 5°, from 32.5–65°N and 15°W–50°E. These replace BLE's synthetic tropical winds.
- **Winds, hemisphere:** NOAA's [NCEP/NCAR Reanalysis-1](https://psl.noaa.gov/data/gridded/data.ncep.reanalysis.html) for 2025, 25–70°N, every longitude, every six hours. Used for flights that loop the hemisphere.
- **Experiments:**
  - 528 station-keeping flights at 22 sites
  - 360 one-way crossings with three controllers
  - 120 runs of a forecast-lookahead planner
  - 360 ship versus land launches
  - 276 hemispheric flights with fuel-cell and propulsion options
  - 27,480 candidate glider releases, each tested 40 times against wind errors

Two limits of the setup matter. There is no wind data below 13.6 km, so glider and parachute descents taper the 150 hPa wind to 30 % at the surface. BLE's solar model rejects latitudes at or above 60°, so the study region stops at 59.5°N.

## Finding 1: balloons can't hover over Europe

Over Europe, a balloon stayed within 50 km of its target only 4 % of the time. The same controller managed 38 % in BLE's tropical setup, where Loon operated.

We flew 528 two-day flights at 22 sites from Lisbon to Trabzon, two per month through 2025, with BLE's StationSeeker controller (`run_coverage.py`). The baseline was 16 two-day flights in stock BLE (`baseline.py`).

The cause is physical. In winter the westerlies at 50–140 hPa blow the same way at every altitude a balloon can reach. At 50°N in January, the mean eastward wind ran from about 18 m/s at 150 hPa to 32 m/s at 30 hPa. Changing altitude gives nothing to steer with. Only in summer, when winds high up reverse (−2.8 m/s at 50 hPa in July), does station-keeping briefly work. The best month-site pairs (Paris in August, Rome in April, Bucharest in July) reached 33–37 %.

So the network doesn't ask balloons to hover. They work like a conveyor: launched upwind, crossing slowly, replaced continuously.

## Finding 2: slow down, and launch from the right place

Steering for the slowest wind kept a balloon over the region for 5.4 days on average, against 3.2 days for one that simply drifts.

Every 15 minutes the controller picks the reachable altitude with the lowest forecast wind speed (`run_drift.py`). We flew it, a passive drifter and a steer-to-centre controller from five launch sites on the 1st and 15th of every month.

[CHART: dwell-by-month]

*Days over the region per flight, by launch month and controller. 360 one-way flights from Lisbon, Brest, Dublin, Vienna and Bucharest, 2025 GFS winds.*

Winter is the hard season. From January to March every controller managed only 1.3–1.9 days, because there is no slow altitude to find; December was 2–3 days.

Launch position matters almost as much as steering. The best site changes with the season: Brest or Dublin most months, Vienna in April, Bucharest in June and July, Lisbon in September. Picking the best of the five sites for each launch date raised the launch-rate-weighted dwell (the figure that sets how many launches a day you need) from 3.65 to 6.4 days, a factor of about 1.75. That uses hindsight, so a forecast-based choice will capture part of it. It is the case for mobile and ship launchers.

Ships, with a rule that runs for Europe at full speed before slowing down, roughly matched the land sites (3.1 versus 3.3 days in that comparison) but did not beat them. And 13 % of ship launches never reached the region (`run_ship.py`). Their value is logistics: they can make hydrogen from seawater, avoid moving it by road, and recover radios and envelopes at sea.

## Finding 3: the radio glides home

A tuned glider brings 98.0 % of radios back to a recovery site under realistic wind errors (10th–90th percentile: 97.5–98.3 %). Our first design managed 64 %.

The radio is the expensive part, so this is the technology the economics rest on. At the end of a flight the payload drops away on a small autonomous glider that flies to one of 21 recovery sites. We re-flew all 120 slow-controller flights hour by hour and tested 27,480 candidate releases (`glide_tuning.py`). Each release was run 40 times with a random wind bias of up to 5 m/s, gusts, and an unknown low-altitude wind taper of 0.1–1.0.

- **First design** (glide ratio 12, 16 kg/m², aim straight at the site, release at a fixed 150 km): 64 % recovered under wind errors, 78 % in perfect winds; about 2.1 h descent.
- **Heavier wing** (glide ratio 12, 29 kg/m²): 94 % in perfect winds; 1.6 h descent.
- **Recommended** (glide ratio 14, 20 kg/m², speed-to-fly guidance, reachability release): **98.0 %** under wind errors; 2.1 h descent.

Three changes made the difference:

- **A faster wing.** At 20 kg/m² the glider flies about 75 m/s through the thin air at 20 km, enough to push into headwinds.
- **Speed-to-fly guidance.** Flying up to 1.8 times faster than best-glide speed into headwinds was worth more than 8 points. Steering into the wind to hold the course added almost nothing.
- **A reachability release rule.** Every hour the balloon simulates the glide to every site within 500 km. It releases at the last hour any site is reachable with a 100 km margin. Larger margins bought nothing.

It lands at 15–20 m/s with flaps, so it needs no parachute. The ceiling is 98.3 %: two Brest launches exit west over the Atlantic and never come within reach of a site. A recovery site in west Ireland, Cornwall or Brittany, or a ship, fixes them.

One caveat: that release timing used knowledge of the balloon's future path. A version using only forecasts recovers 98.1–98.2 % but gives up 77–98 hours of coverage per flight instead of about 35.

## Finding 4: the envelope becomes a cheap consumable

A redesigned envelope built at fleet volume costs about €1,070 (range €390–2,900), nine times less than today's roughly €10,000.

If the radio is the asset, the envelope is just a fuel tank for lift. We modelled its mass from film and tendon stresses, calibrated to BLE's 68.5 kg envelope for a 92.5 kg payload, then costed it bottom-up (`envelope_cost.py`). The unit costs are engineering assumptions.

Each lever on its own, applied to today's roughly €10,000 envelope:

- Automated line at about 400,000 a year, same design: −70 % (€10k → about €3k).
- Lower internal pressure (1,000 Pa instead of 2,380) with 25–30 µm film: −37 %.
- Lighter payload, 92.5 → 40 kg: −26 %.
- Recovery and recycling credit: about −8 %.
- **All stacked: about €1,070 per envelope** (range €390–2,900).

The key lever is pressure, not plastic. Tendon and film loads scale with internal pressure, so cutting it from 2,380 to 1,000 Pa allows much thinner film. For a 40 kg payload the envelope shrinks to 16–18 kg, against 68.5 kg today. A 30-day envelope costs only about 15 % more than a 4-day one.

At that price the film itself is only 4 % of cost. What remains is part count: fittings 23 %, labour and seams 28 %, supplier margin 17 %. Fewer gores and moulded fittings are the next targets. The open question is reliability: proving that 25–30 µm film holds 1,000 Pa for days to weeks, at that volume.

## Finding 5: about €11,000 a flight, €3.4 billion a year

Once the radio comes home and the envelope is cheap, a flight costs about €11,100 instead of €37,100.

[CHART: per-flight-bridge]

*Cost per flight, baseline €37,100 to redesigned €11,100, by line item (`combined_cost.py` mid case; unit costs are engineering assumptions).*

The payload line falls because 98 % of radios now return. Each lasts about 15 flights, refurbished at 10 % of its cost each time. It is also lighter and built from commodity 5G parts, assumed at 70 % of today's €35,000 unit. Recovery pickups halve when run like a gig network, the way scooter companies collect their scooters. Launch, hydrogen (€127 a flight), ground network and regulatory costs stay at €1,870.

At fleet level, keeping about 95 % of the region covered all year costs about **€3.4 billion a year (range €1.5–9.2 billion)**, down from €15.4 billion in the baseline model. That includes choosing the launch site from the forecast, assumed to lengthen flights by ×1.35 (×1.15–1.6). That is well under the ×1.75 measured with hindsight.

## Finding 6: looping the hemisphere halves launches, but most flights cross China

With a fuel cell and a small propeller, balloons that ride the westerlies around the hemisphere need only 30–49 % as many launches as one-way crossings. But 88 % of them still clipped Chinese airspace.

We flew 60 flights per configuration for up to 150 days on NOAA's hemispheric winds, launched from the five European sites on the 1st of each month (`run_multipass.py`). Flights steer slow over Europe and fast eastward elsewhere. They try to stay between 35°N and 56°N, using a northern corridor around China.

Launches needed, as a fraction of the one-way fleet, for 30 / 60 / 100-day envelopes:

- **Altitude steering only** (3 kWh battery): 0.77 / 0.68 / 0.62. Every flight entered Chinese airspace; 7.4 % of flight time was over China.
- **Plus a fuel-cell power store** (10 kWh): 0.53 / 0.41 / 0.32. Every flight still entered China (6.0 % of time); median peak latitude 82.6°N.
- **Plus a 3 m/s latitude-holding propeller**: 0.49 / 0.37 / 0.30. 88 % of flights entered China, for 2.1 % of time; median peak latitude 78.8°N.

The best configuration's median flight lasted 133 days, made about three laps and passed over Europe five times. Propulsion cost about 52 kWh per 30 days, roughly 3 kg of hydrogen, so long flights need a gas budget.

Two problems remain. North–south winds near the polar vortex reach 10–20 m/s and overpower a 3 m/s push, so most flights still wandered toward the Arctic, where polar night drains power. And under Article 8 of the [Chicago Convention](https://en.wikisource.org/wiki/Convention_on_International_Civil_Aviation), pilotless aircraft need each state's authorisation to overfly it. States do shoot balloons down. The United States downed a Chinese surveillance balloon off South Carolina in February 2023. In September 1995 a Belarusian helicopter shot down a crewed race balloon, killing both pilots, in a dispute over whether it had clearance.

So the cost figures in this article use the conservative design: flights end over Europe. Hemispheric loops are an upside if propulsion, routing and permissions are solved.

## Finding 7: Canada nearly doubles each balloon's useful time

Balloons launched from western Canada spent 46 % of their flight time over places the network serves, against about 24 % for Europe-only service over the same 60 days. Every one reached Europe.

We launched 36 sixty-day flights from Vancouver, Prince George and Calgary, one per site per month, with the fuel cell and the 3 m/s propeller (`run_multipass.py`, `LAUNCH_SET=canada`). In winter the westerlies run from British Columbia across Canada and the North Atlantic to Europe.

Median days per 60-day flight:

- Over Canada: 4.8
- Over the North Atlantic shipping lanes: 4.5
- Over Europe (first arrival around day 10): 12.6
- **Useful total (median of per-flight totals): 22.4**

June–August launches averaged about 35 useful days; December–February launches about 16. China was still clipped on 72 % of flights within the 60 days, for a median 0.7 days. That is another reason to end flights over Europe.

Canada brings more than airspace. It has cheap low-carbon hydro power in Quebec and British Columbia for hydrogen, Atlantic ports at Halifax and St. John's for ships, MDA's aerospace industry, and Telesat's Lightspeed constellation as a backstop. Arctic coverage would be a separate design problem, needing the fuel cell and stronger propulsion. On balance Canada helps scalability.

## Being surgical where a constellation is a blanket

Balloons can put about three times Starlink's capacity over a 300 km zone within a day or two, because they can be stacked over one place and satellites can't. The price is a surge of several hundred launches a day.

A constellation spreads the same capacity over every square kilometre, controlled by whoever runs it. The balloon layer can be precise in six ways:

- **Where.** A 5° phased-array beam from 20 km lights a spot about 1.7 km across (2 × 20 km × tan 2.5°): one valley, port or convoy.
- **When.** Coverage for an afternoon, a week or a season, leaving nothing behind.
- **How much.** Stack balloons over one zone by launching upwind or steering existing ones.
- **Who.** Priority for responders and hospitals, and an island mode that keeps a cut-off region's phones talking to each other.
- **What.** Radios come home every flight, so payloads change per mission: thermal cameras, ship-tracking receivers, anti-jam arrays.
- **Spectrum.** Each country's own bands, through its own mobile operators.

The clearest test is a regional blackout. We modelled a zone 300 km in radius losing towers, fibre and grid power (`outage_scenario.py`): about 34 million people at 120 per km², roughly France's average density. Demand assumes 15 % of people active at 100 kbps for voice and text, or 5 % at 1 Mbps for degraded data. Capacity assumes 2 Gbps per balloon. Drift speeds come from the 2025 runs.

For a 300 km zone (demand 0.5 Tbps for voice and text, 1.7 Tbps for degraded data):

- **Summer, voice and text:** 254 balloons aloft, 141 launches a day, about €1.8 M a day; first coverage in 14–36 h.
- **Summer, degraded data:** 848 balloons, 472 launches a day, about €5.9 M a day; 14–36 h.
- **Winter, voice and text:** 254 balloons, 443 launches a day, about €5.5 M a day; 5–11 h.
- **Winter, degraded data:** 848 balloons, 1,476 launches a day, about €18 M a day; 5–11 h.

Costs use €12,400 a flight, an earlier mid-case figure; at the €11,100 above they are about 10 % lower.

Starlink's pro-rata capacity over the same zone is about 0.55 Tbps, and every user needs a dish and power. Traffic leaves the zone over laser links between balloons, which can see each other up to about 1,000 km apart at 20 km. It reaches working networks outside the zone, or allied satellites.

The same mechanism serves other missions. Summer fire watch over a 300 km zone needs only about 1.3–2 launches a day to keep three balloons overhead, since the summer crossing takes about 43 hours. That is about €15–25k a day. Fire season is when stratospheric winds are slowest. Phones lost in mountains or at sea can be located by timing and angle across several balloons. Cameras on board would map at 0.25–0.7 m from 20 km (20 km × 3.45 µm pixels / 100–300 mm lenses), shuttered outside allied airspace.

## Jamming: where balloons beat Starlink, and where they don't

Against a distant ground jammer, a balloon has about a 20 dB geometric advantage that a satellite in low orbit lacks. Against a jammer next to the user, Starlink's dish beats a phone. A small directional terminal gives balloon users the same protection, more cheaply.

The numbers are free-space path-loss ratios, 20·log10 of the distance ratio:

- **Distant jammer.** A user 20 km below a balloon and a jammer 200 km away: 20·log10(200/20) = **20 dB** in the user's favour, a factor of 100. From 550 km up, the user and a jammer a few hundred km off are at similar distances, so a satellite gets almost no natural advantage.
- **Signal at the phone.** A base station 20 km up is about 27 times closer than one at 550 km: 20·log10(550/20) ≈ **29 dB**, about 800 times more signal. That is why ordinary phones work, and why satellite direct-to-phone services get only a few Mbps per beam.

Threat by threat:

- **Distant ground jammer:** Starlink has little geometric edge; the balloon has about 20 dB. Balloons better.
- **Signal strength at a phone:** weak from orbit; about 29 dB stronger from 20 km. Balloons better.
- **Jammer next to the user:** Starlink's dish beam rejects it well. Phones have no dish, but an optional panel rejects low-angle jammers by about 20–30 dB. Phones worse; with a directional terminal, even or better.
- **Backhaul:** laser cross-links on both sides. Even.
- **Losing a node:** many satellites, versus an €11k flight with hundreds launched a day. Even.
- **Hardware refresh:** about five years for a satellite, versus every flight cycle, in weeks. Balloons better.
- **Who can switch it off:** one foreign company, versus an allied operator or authority. Balloons better.

A directional terminal works for balloons the same way Starlink's dish does, and it is easier to build. A jammer next to the user sits near the horizon. The balloon is roughly 15–90° up within a 40–80 km footprint, so an antenna pointing up puts the jammer in its side lobes, typically 20–30 dB down. Three things make it cheaper than Starlink's terminal:

- **The target barely moves.** A low-orbit satellite crosses the sky in minutes, so Starlink's dish needs fast beam-steering and frequent handovers. A balloon typically drifts at 10–70 km/h (the 2025 runs; median 24 km/h). A slow-steering panel, or a fixed one re-aimed occasionally, is enough.
- **The signal is already strong.** With about 29 dB less path loss, a smaller antenna gives the same margin. A 30 cm panel at 2.6 GHz has roughly 16 dBi of gain and a beam about 25–30° wide, enough to separate the balloon from a horizon jammer. Starlink's dish is about 50 cm at 12 GHz.
- **Several balloons are in view.** With 2–3 balloons overhead, the terminal can choose the one farthest in angle from the jammer.

It could come as a roof or mast panel for homes, clinics and command posts, a flat panel for vehicles and ships, or a small phased-array patch on a responder's radio. The sizes are engineering estimates, not simulation results. Two limits remain. Ordinary phones keep only the geometry and signal-strength advantages. And a jammer on a drone or aircraft above the user defeats a directional terminal, as it does Starlink's.

Two more capabilities follow from the mesh. Many balloons hear the same jammer from different places, so timing and angle differences can locate it. And the glider's return must not depend on satellite navigation, which is jammed routinely near Kaliningrad. Star trackers (the sky at 20 km is dark enough), inertial navigation, ranging between balloons and magnetic-anomaly maps give position fixes without GNSS. Onboard software fuses them and flags spoofed signals.

## Capacity: allied satellites plus balloons match what Starlink carries

Europe's and Canada's own satellites plus the balloon fleet carry about 9–11 Tbps over the region. That is more than the roughly 5 Tbps Starlink actually carries there.

Over the Europe region:

- **Starlink, its share of network capacity:** about 21 Tbps (`cost_model.py`: ~600 Tbps network × regional share).
- **Starlink, traffic actually carried:** about 5 Tbps (25 % load factor, assumed).
- **Allied satellites by about 2030:** 1.5–3 Tbps. [KONNECT VHTS](https://www.csimagazine.com/csi/Eutelsat-Konnect-VHTS-enters-service.php), 500 Gbps over Europe, North Africa and the Middle East; [IRIS²](https://www.spaceintelreport.com/eu-commission-on-iris2-multi-orbit-constellation-are-we-ready-to-compromise-no-but-well-accept-tradeoffs-if-needed), a reported 3.3 Tbps goal worldwide from 2030; [Telesat Lightspeed](https://spaceq.ca/?p=31873), at least about 10 Tbps worldwide from early 2028.
- **Balloon coverage fleet, about 3,850 balloons:** about 7.7 Tbps (2 Gbps per balloon, assumed).

Capacity per balloon is the weakest assumption. Loon-era LTE gave roughly 10–40 Mbps per balloon. The 2 Gbps figure assumes modern 5G phased arrays with several reused beams, 100–200 MHz of spectrum and 2–5 bit/s/Hz.

Cities stay on towers and fibre, so balloons don't need urban density. Matching Starlink's full raw capacity rather than its traffic would take about 10,500 balloons and roughly €9 billion a year at 2 Gbps each (2.7 × the €3.4 billion fleet). At 5 Gbps it would take about 4,200 balloons and €3.7 billion. That makes radio capacity the most valuable research target after the glider.

## Cost against Starlink, counted both ways

As a standalone network, the balloon layer costs about €3.4 billion a year against €6–10 billion to run Starlink's whole constellation. Charged only for its slice over Europe, Starlink is about 12 times cheaper per km².

- **Starlink, whole constellation:** €6–10 billion a year (USD 7–12 billion: SpaceX's 2025 connectivity-segment costs plus estimated capex, in `cost_model.py`). Users need a dish, USD 300–600.
- **Balloon layer, about 95 % of the region, mid case:** €3.4 billion a year (€1.5–9.2 billion). Users need nothing: phones connect directly.

Both ways of counting are fair, but they answer different questions. Charging Starlink only for the 3–4 % of its constellation over this region gives about €27 per km² a year. On that basis the balloon layer is about 12 times dearer, or about 6 times with 60–80 km footprints. A thinner hybrid service came to about 4.6 times: balloons target 50 % coverage over populated land only, with satellites filling the gaps (`cost_reduction.py`).

But nobody can buy a Europe-only constellation: orbits cover the whole world whether you want them to or not. For a sovereign European and Canadian layer, the relevant number is what the layer itself costs. That is single-digit billions a year, with no rockets, no terminals and no foreign point of control.

## What is not solved yet

Seven risks could break the case. Each has evidence from the simulations and a mitigation to test.

- **Winter winds.** January–March flights last 1.3–1.9 days; winter needs three to four times the summer launch rate. Mitigation: ship and mobile launch, the Canada loop.
- **Capacity per balloon.** 2 Gbps is an assumption, not a test. Mitigation: phased-array 5G research first.
- **Thin-film reliability.** 25–30 µm film at 1,000 Pa is unproven at volume. Mitigation: flight tests and an automated quality line.
- **Navigation without GNSS.** The glider's return assumes a position fix. Mitigation: star tracker, inertial navigation, mesh ranging.
- **Hydrogen safety.** About 14 kg a flight; the EU Seveso III directive's lower tier starts at 5 t of hydrogen on one site. Mitigation: make hydrogen on ships, keep sites under 5 t.
- **Envelope litter.** About 300,000 flights a year × about 17 kg ≈ 5,000 t of polyethylene; 34 % of today's simulated landings are at sea. Mitigation: steered cut-downs, paid pickup, recovery ships.
- **Spectrum and borders.** National bands; signals spill across borders. Mitigation: operator partnerships under the WRC-23 rules for high-altitude IMT base stations (HIBS), which identified the 700/800/900 MHz, 1.8 GHz and 2.6 GHz mobile bands for platforms like these.

Burning envelopes at altitude is not a fix. Our screening model (`burn_sim.py`) found the hydrogen holds enough energy only if 19 % of its heat reaches the film. The median burn consumed 90 %, but leftover shreds scattered over a strip about 200 km long. A complete burn releases about 215 kg of CO₂ per balloon.

## A phased NATO–EU programme

Start with a summer pilot over the Mediterranean, where the winds are kindest and the value clearest. Stop cheaply if its numbers don't hold.

1. **Pilot: Mediterranean fire watch and outage response.** Three 300 km zones for one summer: 3 zones × 90 days × about 2 launches a day ≈ 540 flights. That is about €6 million of operations at €11k a flight, plus a development budget still to be scoped. It proves the three technologies the case rests on: glider return, thin-film envelope and radio capacity.
2. **Flanks: Baltic and western Black Sea.** Year-round service including winter, anti-jam arrays and jammer location. Ships handle launch, recovery and hydrogen.
3. **Continental: Europe-wide layer with the Canada loop.** About 95 % of the region outside cities, at about €3.4 billion a year in the mid case, integrated with IRIS², OneWeb and Telesat Lightspeed.

The ask has four parts:

- **Mandate and fund the pilot** through civil-protection and defence instruments. rescEU and the European Defence Fund fit the Mediterranean phase; NATO's DIANA accelerator and the resilience spending allies agreed in 2025 fit the flanks. Funding routes still need confirming with each programme.
- **Harmonise spectrum.** CEPT and its Electronic Communications Committee could harmonise the WRC-23 HIBS bands, with national emergency use agreed in advance.
- **Open the airspace.** A standing framework for fleets of unmanned free balloons: pre-approved launch pads, sea zones and cut-down areas.
- **Build an allied consortium.** European film makers; Nokia and Ericsson for radios; Airbus, Thales and Leonardo for integration; MDA and Telesat in Canada; shipyards; and the mobile operators whose spectrum the network uses. Canada should be a founding partner, because the transatlantic loop is what makes the fleet efficient.

## Methods, assumptions and sources

Simulation results are reproducible from the repository. Engineering assumptions and outside figures are listed so readers can challenge them.

**Simulation scripts** (private repository, available on request):

- Station-keeping, 528 flights: `run_coverage.py`, `analyze.py`
- One-way crossings, 360 flights: `run_drift.py`, `analyze_drift.py`
- Forecast-lookahead planner: `planner.py`
- Ship versus land launch: `run_ship.py`
- Glider design and release policy: `glide.py`, `glide_tuning.py`, `glider_sizing.py`
- Envelope landings and burning: `analyze_envelopes.py`, `burn_sim.py`
- Hemispheric, fuel-cell, propulsion and Canada flights: `run_multipass.py`, `analyze_multipass.py`, `china.py`, `canada.py`
- Envelope mass and cost: `envelope_cost.py`
- Fleet cost and levers: `cost_model.py`, `cost_reduction.py`, `combined_cost.py`
- Regional outage: `outage_scenario.py`

**Key engineering assumptions** (not simulated): 2 Gbps per balloon; payload unit cost 70 % of €35,000 and about 15 flights of life; envelope unit costs from the bottom-up model; forecast-based launch-site choice worth ×1.35 on dwell; Starlink traffic at 25 % of capacity; winds below 13.6 km taken as the 150 hPa wind tapered to 30 % at the surface.

Starlink's costs and capacity come from the secondary analyses of SpaceX's 2025 filing cited in the repository's `results/cost_comparison.md`.

## Sources

- Google Balloon Learning Environment: https://github.com/google/balloon-learning-environment
- Open-Meteo historical forecast API (GFS winds, CC BY 4.0): https://open-meteo.com/
- NOAA PSL, NCEP/NCAR Reanalysis-1: https://psl.noaa.gov/data/gridded/data.ncep.reanalysis.html
- Starlink global outage, 24 July 2025 (Reuters via Daily Maverick): https://www.dailymaverick.co.za/article/2025-07-25-elon-musks-starlink-network-suffers-rare-global-outage/
- Starlink restrictions in Ukraine (CNN/Isaacson report via Mezha): https://mezha.ua/en/2023/09/07/elon-musk-thwarts-ukraine-s-attack-on-russian-fleet-in-crimea-cnn
- Iberian blackout and mobile networks, 28 April 2025 (Broadband Breakfast, Ookla data): https://broadbandbreakfast.com/iberian-blackout-highlights-gaps-in-telecom-network-resiliency/
- GNSS interference around Kaliningrad and the Baltic (Spire, 2024/2025): https://spire.com/blog/space-reconnaissance/gnss-interference-report-russia/
- Eutelsat KONNECT VHTS enters service, 500 Gbps (CSI Magazine): https://www.csimagazine.com/csi/Eutelsat-Konnect-VHTS-enters-service.php
- IRIS²: about 290 satellites, reported 3.3 Tbps goal, 2030 (Space Intel Report): https://www.spaceintelreport.com/eu-commission-on-iris2-multi-orbit-constellation-are-we-ready-to-compromise-no-but-well-accept-tradeoffs-if-needed
- SpaceRISE IRIS² concession (Eutelsat release): https://www.mynewsdesk.com/eutelsat/pressreleases/spacerise-consortium-inks-agreement-as-concessionaire-for-the-european-unions-landmark-iris2-constellation-3360767
- Telesat Lightspeed, about 10 Tbps (SpaceQ): https://spaceq.ca/?p=31873 ; expansion to 225 satellites and Q1 2028 service (Runway Girl Network): https://runwaygirlnetwork.com/2026/09/telesat-restores-commercial-lightspeed-capacity-with-more-satellites/
- Convention on International Civil Aviation (Chicago, 1944), Article 8, ICAO Doc 7300: https://en.wikisource.org/wiki/Convention_on_International_Civil_Aviation
- Chinese surveillance balloon shot down, 4 February 2023 (Air & Space Forces Magazine): https://www.airandspaceforces.com/chinese-surveillance-balloon-shot-down-f-22/
- Belarus shoots down a Gordon Bennett race balloon, 12 September 1995 (RFE/RL): https://www.rferl.org/a/belarus-american-balloonists-tragedy-25-years-shot-down/30975038.html
- Directive 2012/18/EU (Seveso III), Annex I, hydrogen thresholds: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32012L0018
- WRC-23 outcome for HIBS bands (CTU summary): https://ctu.int/wp-content/uploads/2023/12/Main-WRC-23-Result-20.02.24.pdf

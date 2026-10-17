# Who the layer is for: populations outside tower coverage, responders, and surge events

*Research note, 2026-10-17. Hand-written from public coverage statistics (sources at the end); nothing here is simulated. Figures marked (estimate) are mine. The region is the `analyze.py` box, 36–62°N, roughly 550–650 M people; EU-27 figures use 450 M.*

## The short version

There are four different populations, and they are different by three orders of magnitude.

| Population | Size in the region | How often | What serves them today | Where the layer fits |
|---|---|---|---|---|
| A. Residents with no mobile broadband at home | about 1 %, so 4–8 M people (estimate from a 1 % regional coverage gap) | always | 2G where it exists, satellite dishes, nothing | poorly: scattered, thin, best served by direct-to-cell or a dish |
| B. People who pass through uncovered land | tens of millions of person-days a year on 5–15 % of the land area (estimate; no count exists) | seasonal, daily | nothing while there | poorly for the same reason; partly for fire watch and search |
| C. Government and emergency users | roughly 6–9 M uniformed and field staff, of whom perhaps 1–2 M are on duty at once (estimate) | always, concentrated in events | TETRA/P25 voice, commercial LTE, some satellite | well: known users, priority, directional terminals, local control |
| D. People whose towers exist but fail | 1–50 M at a time, for hours to weeks | a few times a decade at national scale; monthly at the scale of a valley or a city | whatever survives, then Starlink dishes where people own them | this is the case: capacity concentrated over one place for days |

A, B and C together are a few million people spread over a continent. D is tens of millions in one place for a few days. A fleet sized to cover 95 % of the region all year is sized for A and B, the populations it serves worst. A fleet sized to surge into D, with C as its standing customer, is sized for what it does that nothing else does.

## A. Residents outside coverage

Europe's mobile broadband coverage gap, the share of people living where no 3G-or-better signal reaches, is about 1 % (GSMA, Europe & Central Asia, 2024 data, down from 6 % in 2015). ITU's 2024 figures give 2 % of Europe's *rural* population as uncovered. Spot checks by country, population covered by at least one 4G network:

| Country | Population 4G coverage | Uncovered residents (estimate) | Source |
|---|---|---|---|
| Germany | not published as population; 97.5 % of land area has 4G, 2.1 % of area has no 4G or 5G, 0.2 % no 2G | under 0.4 M | Bundesnetzagentur, 2025 |
| France | 99.2–99.6 % "good coverage" by operator, end 2025 | 0.3–0.5 M | ARCEP, 2026 panorama |
| United Kingdom | about 99 % by at least one operator (area: 96 % with one operator, 89–90 % with all four) | 0.3–0.7 M | Ofcom Connected Nations 2025 |
| Ukraine | 96.2 % of the population in government-controlled territory (Kyivstar, end 2025); occupied territory unknown | about 1.2 M plus occupied areas | Kyivstar |
| Turkey | about 98 % (largest operator; others 93–95 %) | about 1.7 M | operator and third-party figures, not the regulator |
| EU-27 rural | 2 % of about 117 M rural residents (26 % of 450 M) | about 2.3 M | ITU 2024, Eurostat degree of urbanisation |

Adding EU rural, the UK, Ukraine and Turkey gives about 5–6 M, consistent with the 1 % regional figure. The band is 4–8 M because the per-country numbers mix "at least one operator" with "all operators" and population with households. A proper count needs ITU DataHub's per-country indicator and a population raster inside the service polygon; that is the next step and is not done here.

These people are the classic satellite market: scattered, low density, a few hundred per cell, and almost all of them already have a 2G voice signal. Direct-to-cell at tens of cents a month, or a dish for the households that want broadband, serves them for a small fraction of what any stratospheric layer costs. The layer should not be sold on them.

## B. People in uncovered areas

Coverage is measured on people, not land. The land without any 4G is 2 % of Germany, 4–11 % of the UK depending on whether one or all operators count, 1–16 % of France by operator, and larger shares of Norway, Sweden, Finland, the Alps, the Carpathians and the Balkans, where no comparable regulator figure was found. Taking 5–15 % of the region's roughly 7 M km² of land gives 0.35–1 M km² with no mobile broadband (estimate).

Who is in it: forestry and agricultural workers, mountain and coastal tourists (the Alps alone see well over a hundred million visitor arrivals a year, most within coverage), drivers on remote roads, fishers (the EU fleet employs about 130,000), and inland and coastal vessels. No source counts person-days in uncovered land. The order of magnitude is tens of millions of person-days a year, and the demand is voice, text and location, not data. Fire watch and search-and-rescue over these areas are real uses for a few balloons; a standing layer is not.

## C. Government and emergency users

| Group | Region (estimate) | Basis |
|---|---|---|
| Police | about 2.1 M | EU average 341 officers per 100,000 (Eurostat, 2020–22) on 450 M, plus UK, Ukraine and Turkey |
| Professional firefighters | about 0.5 M | 390,600 in the EU in 2024 (Eurostat), plus UK, Ukraine, Turkey |
| Volunteer firefighters | "millions"; Austria alone has about 200,000 | unions and Eurostat note; no primary EU total found |
| Ambulance and emergency medical staff | 0.3–0.6 M | no EU count found; estimate from national services |
| Armed forces | 2.5–3.5 M | EU about 1.3–1.9 M (older World Bank/IISS series), Ukraine about 0.9 M, Turkey 0.4–0.5 M |
| Civil protection, coast guard, utility and transport field crews | not counted | |

Call it 6–9 M people, perhaps 1–2 M on duty at any moment, operating from a few hundred thousand vehicles and stations. This is the population that pays for readiness in the funding note (`results/cost_funding_vs_starlink.md` §4): known users, priority access, directional terminals where jamming matters, and a legal basis for local control. It is also the population that already has resilient voice (TETRA and successors) and is buying data over commercial LTE, which is exactly what fails in D.

## D. People whose towers fail

This is where the numbers are large, and it is the case the article is really about.

- **Grid blackout, Iberia, 28 April 2025:** more than half of mobile users across large areas of Spain and Portugal lost service within hours as cell-site batteries ran down; one operator's customers were off for more than a day. Population in the affected area: over 50 M. Duration for most: under a day.
- **The repository's design case:** a 300 km zone, about 34 M people, without towers, fibre or grid (`outage_scenario.csv`). Voice and text for everyone active needs 254 balloons aloft at 2 Gbps each; degraded data needs 848.
- **Floods and fires:** Valencia, October 2024, hundreds of thousands without service for days; a large wildfire zone is tens of thousands of people for a week or two.
- **War damage:** millions in frontline regions for months; the case the series started from.
- **Earthquake:** Turkey and Syria, February 2023, on the order of 10 M people in the affected provinces, networks degraded for weeks.

Frequency: national-scale events a few times a decade across the region; regional events every year; local events every month somewhere.

## What this means for the design

Your framing is right and the data supports it: deploy what is needed, where it is needed, when it is needed, with a standing customer in C and a surge into D. Three consequences follow, and one limit.

1. **Size the fleet to the surge, not the map.** The permanent-layer costs in `cost_funding_vs_starlink.md` (€6.3 B a year for 95 % of the region) buy coverage for A and B, the populations the layer serves worst. The readiness capability (€0.2–0.5 B a year) buys C every day and D when it happens. The second is the product.
2. **Starlink's strength and limit, stated fairly.** A constellation is already overhead at baseline capacity everywhere, with no deployment time, which is why it is the right answer for A and for anyone in D who owns a dish and has power. What it cannot do is multiply capacity over one zone when demand concentrates, or place itself under local control. The balloon layer can do both. That is the sentence to use, not "Starlink can't deploy on demand."
3. **Direct-to-cell is the competitor for A, not for D.** It reaches phones everywhere at low rates. It does not add capacity to a stricken region either.
4. **The limit is time.** First coverage arrives 5–36 hours after launch, and winter needs 443 launches a day for voice alone. The Iberian blackout was over for most people before a balloon would have arrived. The layer's surge case is the multi-day event: floods, large fires, earthquakes, war damage, and any grid failure that runs past the first night. Say so in the article; a reader who remembers Iberia will otherwise say it for you.

## E. Contention and denial of service

Two questions that come up as soon as D is the case: do regions compete for Starlink's capacity, and is denial of service a concern? Yes to both, for both systems, in different ways.

**Contention.** Starlink's capacity is finite per satellite beam and per ground cell, and it is shared. The visible signs are "sold out" cells in dense areas, waitlists, congestion-based pricing, and priority tiers that put business and government traffic ahead of residential. Over this region the model attributes about 21 Tbps to Starlink in total and about 0.55 Tbps to a 300 km zone pro rata (`outage_scenario.csv`); beams can be re-pointed into a stricken zone, but only by taking capacity from neighbours, and the satellites overhead at any moment set a hard ceiling. In a national blackout everyone with a dish is a new user at once, and the first hours of a crisis are when the operator, not the affected state, decides whose traffic has priority. That allocation is made in California. This is the strongest form of the autonomy argument, and it is about capacity allocation under stress rather than an off-switch.

The balloon layer has the same contention within a balloon (2 Gbps shared across a footprint, if the radio exists) and a different answer to the regional ceiling: launch more. Capacity over one zone scales with launches, subject to spectrum reuse, backhaul and the 5–36 hour arrival time. It also puts the priority decision with the state that owns the fleet, which is the point.

**Denial of service.** There are three kinds, and they do not weigh the same for the two systems.

1. *Demand overload.* In an outage everybody calls at once. Every public network needs priority and pre-emption classes for responders (the UK's MTPAS and the US WPS are the models). The balloon layer must have this designed into its core from the start or C gets nothing when D happens; it is uncosted.
2. *Volumetric attacks on the network.* Gateways, points of presence and the core are internet-facing in both systems and are attacked the way any ISP's are. A satellite or balloon access network is more exposed than a fibre network because the access capacity is small and shared, so a flood that would be noise on terrestrial links can fill a beam. Mitigation is standard but costs money and staff, and it is not in either cost model.
3. *Radio denial.* Jamming is the physical-layer version and is covered in the article and in `cost_funding_vs_starlink.md` §5. Starlink has had to harden against it in Ukraine; the balloon layer's geometry helps on some links and hurts on others. Neither is immune.

A fourth risk is specific to the balloon layer and was raised in the external review: the fleet itself is a moving network under one command-and-control plane. Compromise of that plane is a denial-of-service and a safety problem at once, and it needs secure boot, key management, accredited operations and an anti-takeover design before anyone flies hundreds of these over populated land. It is a development line, not a caveat.

## What is not done

- Per-country uncovered residents from ITU DataHub and a population raster inside the service polygon (A).
- Any count of person-days in uncovered land (B).
- National responder headcounts beyond the EU aggregates (C).
- Priority and pre-emption design, DDoS mitigation and command-plane security for the layer (E), none of which is costed.
- A catalogue of outage events by population-days, which is what a readiness fleet should be sized against (D). The Iberian, Valencia and 2023 earthquake figures above are from press summaries, not an event database.

## Sources

- GSMA, The State of Mobile Internet Connectivity 2025, regional chart: Europe & Central Asia coverage gap 1 % (2024), usage gap 22 %.
- ITU, Facts and Figures 2024, mobile network coverage: Europe 5G 72 %; 2 % of Europe's rural population not covered by mobile broadband; world 4G 92 %, rural 82 %.
- Bundesnetzagentur, Mobilfunk-Monitoring (January and October 2025) and Messwoche 2025: 4G 97.5 % of area, white spots 2.1 % (May 2025) to 1.9 % (October 2025), 2G 99.8 %.
- ARCEP, Rapport annuel 2026 tome 2, Panorama de la connectivité mobile: 99.2–99.6 % of population with good coverage, end 2025.
- Ofcom, Connected Nations 2025 and Spring 2025 update: 4G on 89–90 % of UK landmass from all four operators, 96 % from at least one.
- Kyivstar, 2025 results: 4G population coverage 96.2 % in government-controlled territory.
- Turkey: Statista 2024 estimate and operator figures; no BTK coverage measurement found.
- European Commission, Digital Decade 2025 broadband coverage study: 5G 94.3 % of households, rural just under 80 % (2024).
- Eurostat: 390,600 professional firefighters in the EU, 2024; police officers 341 per 100,000, 2020–22 average; about 26 % of EU population in rural areas (2018 degree-of-urbanisation table, to be refreshed).
- World Bank/IISS series: EU armed forces personnel 1.91 M (2019).
- Broadband Breakfast (Ookla data) on the Iberian blackout, 28 April 2025.

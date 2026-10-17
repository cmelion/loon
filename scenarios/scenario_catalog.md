# Scenario catalog — "Westerlies" (working title), a graphic novel in the Kessler world

Eleven episodes. Each is built on one real simulated flight (site, date, seed) from this repository, replayed and logged in `epNN_*/flight.json`; every number in a beat is listed with its source in that episode's `facts.md`. The world rules are in `world_primer.md`. Characters are roles, not real people. UTC throughout.

Recurring cast (roles): the **Duty Controller** at the allied Network Operations Centre (NOC) in Vienna; a **Launch Chief** at the Lisbon site; a **Recovery Lead** who runs the glider sites and the gig pickup app; a **Regulator** from the joint airspace authority; a **Ship's Master** and launch crew on an Atlantic launch vessel; the **Adversary Jammer Crew** in Kaliningrad, seen only in silhouette and radio chatter.

| # | Episode | Flight (site, launch, seed) | Season / mode | Folder |
|---|---|---|---|---|
| 1 | Fourteen Hours | Bucharest, 2025-03-15, 31832 | winter westerlies | `ep01_westerlies` |
| 2 | Fire Watch | Bucharest, 2025-07-01, 32049 | 30-day summer flight | `ep02_fire_watch` |
| 3 | Grid Down | Lisbon, 2025-04-28, 428 (new run) | blackout backfill | `ep03_blackout` |
| 4 | No Fix | Brest, 2025-12-01, 8602 | GNSS jamming, Kaliningrad | `ep04_jammer` |
| 5 | The Flank | Dublin, 2025-01-01, 15839 | Black Sea surge | `ep05_flank` |
| 6 | Overflight | Bucharest, 2025-05-01, 418984 (multipass, fuel cell + thrust) | China drift | `ep06_overflight` |
| 7 | Polar Night | Bucharest, 2025-11-01, 419086 (multipass) | power death at 85 °N | `ep07_polar_night` |
| 8 | Westbound Launch | Vancouver, 2025-08-01, 119 (multipass, Canada set) | transatlantic crossing | `ep08_transatlantic` |
| 9 | Launch Deck | Ship 52N 13W, 2025-02-01, 71334 (approach mode) | ship launch/recovery | `ep09_ship` |
| 10 | Pickup | Brest, 2025-02-01, 7982 | envelope recovery, gig crews | `ep10_pickup` |
| 11 | Seventy Kilometres Short | Lisbon, 2025-11-01, 621 | glider vs headwind | `ep11_headwind` |

---

## Episode 1 — Fourteen Hours

**Logline.** On a March morning a Bucharest balloon crosses the whole Black Sea in eight hours and will be over Russia by dusk; the Duty Controller has until 16:00 to decide where it dies.

**Roles.** Duty Controller (Vienna NOC); Bucharest Launch Chief; Regulator on the phone; a Trabzon recovery team that will not be needed.

**Beats.**
1. 06:00, Bucharest pad: launch in a 25 m/s stratospheric westerly; the Launch Chief says what the board already shows: March mean dwell 1.5 days, this one will be shorter.
2. 08:00: the balloon clears Constanța at 28.9 °E. The controller's "slowest level" is 95.7 hPa, 16.5 km, and the slowest level is still 92 km/h.
3. Split panel: Constanța glider site still reachable at 07:00–08:00 (margin 194 → 137 km); by 09:00 nothing is reachable (Odesa −20 km). The window closes while the shift handover happens.
4. 12:00–16:00: eight hours of coverage across the open sea, 100 % battery, nothing to do but watch longitude tick 1.1° an hour.
5. 16:00: night comes, the balloon climbs to 74 hPa (18.1 km) to find 77 km/h instead of 92. The coast at Tuapse is 16 km away at 17:00.
6. The decision: the sim's rule would glide the radio to Sochi (13:00 release, 122 km, lands 14.7 km from the site). In this world Sochi is Russian; the Regulator says no.
7. 16:00: cut-down over the sea at 38 °E, two hours before the coast; the envelope joins the 13 % of the fleet's envelopes that land in the Black Sea; the radio is lost.
8. 20:00: the empty track crosses 42 °E on the board anyway (the "ghost" of the uncut balloon exiting at 43.8 °N 42.0 °E, 14 hours after launch). Closing caption: 1,871 launches a day to hold the region in winter.

**Problem → solution.** Problem: in winter there is no slow level, so every eastern launch is a 1–2 day sprint to the 42 °E wall and the recovery network's eastern sites are in or beside Russia. Solution shown: the "wall rule" (cut before the coast, accept sea landings) and a longer-term one named in dialogue: launch from Trabzon/Constanța-side sites and let the westerlies carry balloons *into* the recovery sites rather than past them. Facts: `ep01_westerlies/facts.md`.

---

## Episode 2 — Fire Watch

**Logline.** One balloon launched from Bucharest on 1 July stays up for the whole month, loops from the Ionian Sea to Vienna, Paris and the Irish Sea, and comes down over Castile the day before the fires start.

**Roles.** A Calabrian wildfire incident commander; the Duty Controller; a Dublin Recovery Lead; a Castilian forestry officer in the epilogue.

**Beats.**
1. 2–6 July, Ionian Sea: the balloon drifts at 15–19 km over Corfu, the Calabrian coast and Salento at 11 km/h, the slowest flight of the sweep. The incident commander's crews have phones but no towers; the balloon is their cell.
2. Technical panel: summer stratospheric easterlies: the balloon moves *west*, Bucharest to Spain, the opposite of Episode 1.
3. 8 July: over Vienna; the NOC watches its own balloon pass overhead. 10 July Brandenburg, 12 July Luxembourg, 14 July The Hague.
4. 17–20 July: Paris, Normandy, the English Midlands. Each day the glider desk marks which sites are reachable with 100 km margin: Bucharest, Budapest, Vienna, Berlin, Paris, London, Dublin in turn, 169 hours of the month.
5. 23 July 18:00–20:00: last reachable hour for Dublin (margin 114 km). The sim's rule releases the radio at 20:00 from 139 km; glide 2.1 h; it lands 9.6 km from the site. The Recovery Lead meets it.
6. The envelope flies on, empty, 7 more days: Celtic Sea, Biscay, Brittany, León.
7. 31 July 06:00: 30 days, 8,363 km; over Valladolid. Cut-down; the envelope lands 19 km away on dry Castilian farmland.
8. Epilogue caption: the August fires in León and Zamora began ten days later; summer coverage costs 453 launches/day for 95 %, 132 for 50 %.

**Problem → solution.** Problem: the one month the network is cheap is the month it is most needed, and even a 30-day flight wanders a continent. Solution: fire-season "summer service" (the repo's lever L6a: 25 % of the year at a quarter of the cost) plus hand-offs between recovery sites as the balloon tours Europe. Facts: `ep02_fire_watch/facts.md`.

---

## Episode 3 — Grid Down

**Logline.** At 12:33 local time on 28 April the Iberian grid collapses; a Lisbon balloon launched that morning is already over the Alentejo, and the NOC has to turn one balloon into a conveyor of 172 a day.

**Roles.** Lisbon Launch Chief; Duty Controller; a Portuguese grid-operator liaison; a Madrid hospital IT lead on a phone that only works when a balloon is overhead; the Regulator.

**Beats.**
1. 06:00 launch, routine; the balloon climbs to 19 km (64 hPa) and crosses the Alentejo at 19 km/h.
2. 10:33: the grid goes. Towers fall back to batteries. The balloon is near Évora, the only working cell in a 50 km circle.
3. The arithmetic panel: 58 M people inside a 430 km circle; April drift 14 km/h means one crossing takes 61 h; voice/text for everyone needs 435 balloons aloft and 172 launches a day; first coverage from upwind launches arrives in 14–35 h.
4. The Launch Chief's board: the site is built for 48 launches a day. Three more sites (ship, Brest, Dublin) are tasked; the Atlantic launcher of Episode 9 appears.
5. Night of 28–29 April: the balloon's battery falls to 55 % at 03:00; the hospital lead's call drops as the balloon moves east of Ciudad Real.
6. 29 April 06:00: Madrid glider site reachable with 100 km margin (the window ran 00:00–06:00). The Duty Controller chooses coverage over recovery and keeps the radio aloft.
7. 29 April evening: Alicante coast; the balloon leaves Spain after 29 hours over it and the grid is 99 % back. The balloon's 87-hour flight ends over Tunisia on 1 May.
8. Caption: the real backfill number is money per day, €2.1 M (voice) to €7.1 M (data), for as long as the lights are out; Starlink's pro-rata capacity in the same circle would have been 1.1 Tbps, if anyone still trusted it.

**Problem → solution.** Problem: balloons cannot park, so a regional outage is served by launch tempo, not by a stationed fleet. Solution: pre-planned upwind surge sites, laser edge trunks (44–145 of them) to intact gateways, and a service tier (voice/text first) that fits the launch rate. Facts: `ep03_blackout/facts.md`, `outage_case.json`.

---

## Episode 4 — No Fix

**Logline.** A December balloon from Brest reaches Masuria at 05:00 with its battery at 10 % and its radio due to glide to Warsaw, 157 km from Kaliningrad, where the GNSS jammers are on.

**Roles.** Recovery Lead at the Warsaw glider site; the glider's autopilot (as a voice); the Adversary Jammer Crew; the Regulator; a Polish air-traffic controller.

**Beats.**
1. 1–3 December: three nights at 184 W; the battery hits 14 %, 14 %, 10.5 % at each dawn. The balloon crawls at 30 km/h past Paris, Saarland, Thuringia, Poznań.
2. 4 December 02:00: tuned rule says release now (119 km from Warsaw, margin 103 km). The sim's older rule waits until 05:00 (135 km, margin 85 km). Either way the glider will fly two hours through a jammed sky.
3. Kaliningrad silhouette panel: more than 30 jamming sources operated here in 2025; the oblast border is 106 km north of the release point.
4. Release at 17.7 km. The glider's crab guidance assumes it knows its ground track. It doesn't: no fix. It flies heading and airspeed.
5. Arithmetic panel: an unknown 5 m/s wind over 2.05 h is a 37 km error; the recovery circle is 25 km. Dead reckoning alone loses the radio.
6. What the margin buys: 103 km of still-air range means the glider arrives over Warsaw with ~7 km of altitude to spare. The Recovery Lead switches on a ground beacon (not GNSS); the glider homes on it, spirals, lands at 15 m/s.
7. Monte Carlo panel in the briefing room: with a fix, 51/51 recoveries under 5 m/s wind errors; fleet-wide, 98 %.
8. The empty balloon drifts on over Minsk (18:00) and Smolensk, and exits at 42 °E on 6 December: the uncut track as a diplomatic footnote.

**Problem → solution.** Problem: the glider's 98 % depends on a position fix, and the Baltic frontier is where fixes fail. Solution: release with ≥100 km margin and home on a local beacon; the margin is the quantitative part, the beacon the engineering one. Facts: `ep04_jammer/facts.md`, `glide_cases.json`.

---

## Episode 5 — The Flank

**Logline.** New Year's Day: a Dublin balloon reaches the Turkish Black Sea coast in 38 hours, crossing England, Germany, the Carpathians and western Ukraine on the way, to give the eastern flank fifteen hours of coverage.

**Roles.** Duty Controller; a Trabzon recovery crew; a Romanian air-defence liaison; the Regulator; ground troops on exercise near the coast who are the "customers".

**Beats.**
1. 06:00 Dublin launch in a 96 km/h westerly; by 09:00 it is over Lincolnshire, by 12:00 the Netherlands.
2. 2 January 00:00–06:00: Zakarpattia to Odesa oblast, over a war zone the balloon cannot see or avoid; the Romanian liaison's phone call.
3. 06:00: dawn with the battery at 15 %, after a 15-hour night at 15.5 km.
4. 09:00–15:00: the Black Sea, passing 44 km from Sevastopol at 10:00. The Odesa glider window (margin to 160 km) came and went between 04:00 and 08:00.
5. The customers: for the troops on the Turkish coast the balloon is a cell for ~15 hours (from 27 °E to the exit). The Duty Controller shows the conveyor: 2.4-day January flights, 1,871 launches a day region-wide, each western launch a one-and-a-half-day dash.
6. 19:00: tuned rule releases to Trabzon from 62 km (margin 134 km); sim rule at 20:00 from 101 km. Glide 1.9 h, lands on the site.
7. Envelope cut at release lands in Artvin province, 19 km downwind, on land.
8. 21:36: the track reaches the Georgian border. Caption: the fastest flights of the year all start east of Vienna (14.0, 17.1, 18.5 h).

**Problem → solution.** Problem: a surge on the flank in winter is a conveyor from launchers 3,000 km upwind; coverage per launch is a day or less. Solution: forward recovery sites (Trabzon, Constanța) so radios are reused, and launch tasking from western sites timed to the jet. Facts: `ep05_flank/facts.md`.

---

## Episode 6 — Overflight

**Logline.** The network's first fuel-cell balloon, meant to live 150 days, is over Inner Mongolia on day six despite its corridor logic and propellers, and it will cross China twice before the summer is out.

**Roles.** A flight-systems engineer who designed the corridor; the Regulator; a foreign-ministry desk officer; the Duty Controller; the balloon's telemetry as a chorus.

**Beats.**
1. 1 May, Bucharest: launch of the long-life balloon (10 kWh store, 3 m/s thrust). Day 1.9 it leaves Europe over Saratov; nobody can stop it.
2. Days 2–6: 44 °E to 111 °E in four days at 15–19 km. The corridor floor is China's border plus 2.5°; the balloon is at 43 °N, 5° below it, and 3 m/s of thrust cannot climb that latitude against 15–25 m/s winds.
3. 7 May 07:36: "enter china" at 43.0 °N 111.0 °E. 1.85 days to the Heilongjiang exit.
4. The ministry panel: 30 % of the flight will be over Russia, Central Asia and China; fleet-wide 88 % of these balloons clip China.
5. Days 27–37: the balloon's first real Europe pass, Ireland to the Baltic, 10 days of service; 34 recovery opportunities in the whole flight, the engineer wants to use one.
6. 21–26 July: second China crossing from the Yellow Sea to Xi'an and out through Inner Mongolia, 5.4 days. The decision to cut it on the next Europe pass is made.
7. 17–24 September: Galicia to Poland, last recovery opportunity day 144.2, over northern Poland. Cut-down; the radio glides home; 19.3 Europe-days in 150.
8. Caption: launches ×0.49 at 30-day life, ×0.30 at 100 days; the envelope is only 15 % dearer for 25× the life; the cost is the sky it flies over.

**Problem → solution.** Problem: long-life flights are hemispheric and cannot be routed around China. Solution, partial and honest: fly them from the west (Episode 8) and terminate at the last allied recovery opportunity before 42 °E, accepting that a 150-day envelope gets 20–40 Europe-days. Facts: `ep06_overflight/facts.md`.

---

## Episode 7 — Polar Night

**Logline.** A November long-life balloon is lost twice: first to policy when it crosses Georgia on day one, then to physics when the Arctic winds take it to 85 °N where the sun no longer rises.

**Roles.** The Duty Controller on night shift; a NOAA-style forecaster on the allied weather desk; the Regulator; the balloon's telemetry.

**Beats.**
1. 1 November, Bucharest; 2 November 07:24 it leaves Europe over Georgia. Flagged as "abandoned: transponder only".
2. 4–5 November: clips the Altai and the Amur border, 2.2 hours over China in total. The ministry asks whether an unpowered balloon is an aircraft.
3. 6–9 November: Kamchatka, Chukotka, 72.5 °N north of Alaska, the Beaufort Sea, the Canadian Arctic. The forecaster's panel: the controller's latitude guard pushes south at 3 m/s; the wind is 10–20.
4. 10–13 November: down through Nunavut, Lake Michigan, Georges Bank, Newfoundland: a tour of allies who did not ask for it.
5. 18–20 November: the second Europe pass: Brittany, the Massif Central, Slovenia, Kyiv. Six recovery opportunities in the whole flight, the last at Kyiv on 20 November. The controller lets it go; the Regulator wanted it cut.
6. 20 November 12:24: out over Tambov. 23 November: Yakutia. 24 November 06:00: 105 W of sun, the last it will see.
7. 24–26 November: battery 100 → 63 → 41 → 19 → 0 %, stuck at 15.3 km because the power floor forbids pumping; thrust still pushing south at 3 m/s into a wind taking it north.
8. 26 November 16:20 UTC, 85.0 °N 129 °E: out of power. Black panel; the telemetry's last line.

**Problem → solution.** Problem: north of 60 °N in winter a balloon has no sun and the store that protects it also removes its steering. Solution (stated as a rule, not a fix): long-life flights are not launched from Europe between October and February, and any balloon that crosses the eastern wall is terminated at its last allied recovery point. Facts: `ep07_polar_night/facts.md`.

---

## Episode 8 — Westbound Launch

**Logline.** Launched from Vancouver into the worst-but-one Canadian fire season, a balloon serves British Columbia for a week, crosses the Atlantic in nine days, and spends three weeks over Europe before the Duty Controller has to choose Stockholm or Siberia.

**Roles.** A BC wildfire service comms officer; the Vancouver Launch Chief; the Duty Controller; a Lithuanian border-service radio operator; the Stockholm Recovery Lead.

**Beats.**
1. 1 August: launch; the balloon holds 54–56 °N over the BC interior for seven days at 18.9 km (the latitude hold working as designed, for once).
2. 8–12 August: Idaho, the Great Lakes, James Bay, Labrador; Canada-days 11.3.
3. 12–21 August: the crossing, with a four-day loiter NW of the Azores at 14.8 km; 9.1 days Labrador to Finisterre.
4. 21 August 06:33: landfall at Cape Finisterre; 22 August over León and Zamora where the fires are burning (≈340,000 ha by 19 August).
5. 25 August–1 September: Sardinia, Calabria, Belgrade, Lublin, the Suwałki region. The Lithuanian operator's panel: a cell that is not a satellite and not a tower.
6. 2–7 September: a week along the Lithuanian–Belarusian border at 55 °N, thrust pushing south to stay under the 56 °N guard.
7. 12 September 15:27: Stockholm, the last recovery opportunity (day 42.3). The controller cuts it; the radio glides home; 22.5 Europe-days and 11.3 Canada-days from one launch, 56 % useful time.
8. Caption, with the ghost track: uncut, it would have crossed Finland, Karelia and 8 days of Russia before coming back to BC on 27 September.

**Problem → solution.** Problem: Europe-only launches waste 74 % of a long-life balloon's life. Solution: launch from western Canada; 46 % useful time fleet-wide, all reach Europe by about day 10, and the Nordic recovery sites give a legal exit. Facts: `ep08_transatlantic/facts.md`.

---

## Episode 9 — Launch Deck

**Logline.** In a February gale 250 km off Kerry, a launch ship fires a balloon that reaches Vienna in 44 hours, while the crew learns that two launches in twenty-four never make it to Europe at all.

**Roles.** Ship's Master; Launch Crew (deck hands, hydrogen tech); the Duty Controller; the Vienna Recovery Lead; a naval liaison who wants the ship somewhere else.

**Beats.**
1. 06:00, 52 °N 13 °W: launch from the deck; 13.8 kg of hydrogen per balloon at €127, 0.3 % of the cost. The controller's first job is to "run for Europe".
2. 09:00: over Kerry, inside the region by 08:30; 12:00 the Irish Sea; 18:00 Lincolnshire. The Master's panel: of this station's 24 launches in 2025, two never arrived in five days, and arrivals averaged 4.5 days over the region, the best of the five ship stations.
3. Night one: battery to 23 % at dawn over the Dutch border.
4. 2 February: Frankfurt, Nuremberg; the Vienna site comes within glide range at 20:00 (margin 128 km at 00:00).
5. 3 February 02:00: release 120 km south of Vienna; glide 1.9 h, lands on the site. The Recovery Lead's crew has a radio launched from a ship two days earlier.
6. The empty balloon continues: Osijek, Vidin, Thrace, the Aegean; exits off Antalya on 4 February 07:18; envelope into the Mediterranean, 76 km from the cut point.
7. Fleet panel: ships match land sites (5.4 vs 4.6 days per arrival) but don't beat them; what they buy is not having a fixed address.
8. The naval liaison's request: move to 45 °N 18 °W for the Iberian surge (Episode 3). The ship turns south.

**Problem → solution.** Problem: land launch sites are fixed, few (30–80), and the best site changes with the date. Solution: relocatable launch (ships) as the flexible margin of a land network, accepting a 13 % never-arrive rate and a run-for-Europe approach rule. Facts: `ep09_ship/facts.md`.

---

## Episode 10 — Pickup

**Logline.** A radio glides into Paris from 147 km out while its 68 kg envelope parachutes into the Sologne, and a gig driver with an app, a van and a bounty from the €100–1,500 pickup budget goes to find it before the deer do.

**Roles.** Gig pickup driver; Recovery Lead (runs the pickup app); a Sologne landowner; a materials engineer at the envelope factory; the Duty Controller.

**Beats.**
1. 1 February 18:00: release over Loir-et-Cher at 15.6 km; the radio glider flies 154 km in 1.94 h and lands on the Paris site. Clean.
2. The envelope, cut at the same moment, takes 0.58 h to come down and drifts 14 km; the app drops a pin in the Sologne woods.
3. The driver's panel: €100–1,500 per pickup in the budget; the film itself is worth €4 as resin, the credit for a returned envelope €99 (8 % of its €1,068 cost). "You are not recycling. You are tidying."
4. Statistics on the van's screen: 66 % of envelopes land on land, 13 % in the Black Sea, 5 % in the Mediterranean, 13 % in the Atlantic; median drift 26 km.
5. The counterfactual panel (ghost track): had the balloon flown on to the region edge, its envelope would have come down in the Mediterranean off Antalya three days later, 68 km from the cut point; cutting at release keeps the Mediterranean share at 5 % instead of 16 %.
6. The factory: the redesigned envelope is 16 kg, 25 µm film, 46 gores, 1,640 m of seams, €1,068 at 400,000 a year; the cost is fittings, seams and labour, not film.
7. Scale panel: 27,000 tonnes a year of polyethylene coming down over Europe at base-case scale; burning at altitude scatters shreds over 200 km and is "not safer".
8. The driver finds it in a hedgerow; the landowner wants the tendons for fencing. Deal.

**Problem → solution.** Problem: a consumables network drops hundreds of tonnes of film a week on other people's land and sea. Solution: cut-down at radio release, a paid pickup network (budgeted as litter liability, not revenue), and the thin-film redesign that cuts mass ×4. Facts: `ep10_pickup/facts.md`.

---

## Episode 11 — Seventy Kilometres Short

**Logline.** A radio released 140 km east of Madrid into a 61 km/h headwind lands 70 km short; the next design, released two hours earlier and flying faster into the wind, makes it 96 times in 100.

**Roles.** Madrid Recovery Lead; the glider designer; the Duty Controller; a Guadalajara farmer who finds the first glider; the Regulator who signs off the new release rule.

**Beats.**
1. 1 November 06:00, Lisbon: launch; the balloon climbs to 19.4 km in three hours and crosses Spain at 61 km/h.
2. 13:00: Madrid is 92 km away and reachable with 177 km of margin. The old rule waits for the *last* hour within 150 km.
3. 15:00: release at 140 km, headwind 17 m/s. The light glider (16 kg/m², L/D 12) has 232 km of still-air range and goes nowhere near the bottom: it lands 70.7 km short, in Guadalajara province.
4. The designer's panel: ground speed is airspeed minus headwind; at 20 m/s best glide near the ground the glider is parked. Speed-to-fly: fly up to 1.8× best glide into wind, trade glide ratio for penetration.
5. Same release, new glider (20 kg/m², L/D 14, crab + speed-to-fly): 11 km from the site, no margin; under a 5 m/s wind error it fails 39 % of the time. Not good enough.
6. New rule: release at the last hour with ≥100 km margin: 13:00, 92 km out. Arrives 2.7 km off and spirals down; 49 of 51 wind-error cases recover; the worst miss is 46 km. Cost: two hours of coverage.
7. Fleet panel: 78 % → 98 % recovered; the payload line is 44 % of the budget. The two flights a year that never pass a site need a west-Ireland/Brittany station.
8. The balloon, now without its radio, drifts on over the Balearics, Sardinia, Sicily and the Peloponnese, and leaves the region south of Crete on 4 November; the farmer has the first glider on his kitchen table.

**Problem → solution.** Problem: a light glider cannot penetrate the winter jet, and the "last hour within 150 km" rule releases too late. Solution: heavier wing loading, speed-to-fly, and release on arrival margin rather than distance. Facts: `ep11_headwind/facts.md`, `glide_cases.json`.

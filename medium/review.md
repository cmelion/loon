# Review: "A Connectivity Layer No One Can Switch Off" (Claude Docs 33be12b7…, tab 0072609f-52f8, rev 21)

Checked against the repo on 2026-10-17: `README.md`, `results/*.md`, `results/*.csv`, `results/*.jsonl`, and fresh runs of `analyze_drift.py`, `analyze_multipass.py` (all five jsonl files), `combined_cost.py`, `outage_scenario.py`, `cost_reduction.py` (outputs identical to the committed `results/` files; no tracked file changed). Direct recomputation from `drift_2025.csv`, `ship_vs_land_2025.csv`, `ship_approach_2025.csv`, `coverage_2025.csv`, `data/gfs_europe_2025.npz` and the multipass jsonl files where the article's number is not printed by a script.

Verdict: the simulation numbers are almost all right. The fixes that matter are (a) the winter-dwell month range, (b) the Starlink-raw-capacity balloon count, (c) the outage-table cost basis, (d) four external claims that are overstated or mis-sourced (Starlink outage length, Iberian blackout, 1995 Belarus, dead ICAO link), and (e) an internal inconsistency between the Canada "26 %" and the jsonl.

Legend: **FACT** = must fix (wrong, inconsistent, overstated, or unsupported as sourced). **STYLE** = recommended for Medium.

---

## 1. Subtitle — STYLE
**Section:** Subtitle (italic line)
**Current:** "A year of real stratospheric winds says Europe and Canada could fly their own launch-free connectivity layer for about €3.4 billion a year — less than it costs to run Starlink's whole constellation, with no rockets, no dishes and no foreign off-switch."
**Problem:** 41 words in one sentence, and it leads with the comparison the article itself later calls unlike-for-like (regional layer vs global constellation). Lead with the test, not the verdict.
**Replacement:** "We flew 1,600 simulated balloons through a year of real stratospheric winds. The result: Europe and Canada could run their own phone-direct connectivity layer for about €3.4 billion a year, with no rockets, no dishes and no foreign off-switch. Here is what works, what it costs, and what is still unproven."

## 2. Byline/metadata line — STYLE
**Section:** Top of document
**Current:** "Oct 17, 2026 · @Charles"
**Problem:** Docs chip metadata; Medium supplies its own byline and date.
**Replacement:** (delete the line)

## 3. Intro — repo link — STYLE
**Section:** Intro, paragraph 3
**Current:** "The simulation code and results are in the project repository (`github.com/cmelion/loon`, private)."
**Problem:** A private link gives readers nothing and reads as if it were a source. Say what it is.
**Replacement:** "The simulation code and results live in a private repository; the scripts named below are available on request."

## 4. Intro — sourcing claim — FACT
**Section:** Intro, paragraph 3
**Current:** "Every number below comes from a simulation we ran, a physics calculation shown alongside it, or a cited figure."
**Problem:** Several numbers are unshown engineering estimates (fire-watch launch rate, 1,000 km laser range, 16 dBi panel gain, 20–30 dB side-lobe rejection, 2 Gbps per balloon). The article does label most of them later, but this sentence over-promises.
**Replacement:** "Every number below comes from a simulation we ran, a physics calculation, or a cited figure. Where a number is an engineering estimate or assumption, it says so."

## 5. Three single points of failure — Starlink outage — FACT
**Section:** "Three single points of failure", bullet 1
**Current:** "and in July 2025 the whole network went down for hours."
**Problem:** The 24 July 2025 outage lasted about 2.5 hours and was caused by an internal software failure (Reuters via Daily Maverick). "For hours" is loose; the cause is the point for a resilience argument.
**Replacement:** "and on 24 July 2025 an internal software failure took the whole network down for about two and a half hours."
**Source opened:** https://www.dailymaverick.co.za/article/2025-07-25-elon-musks-starlink-network-suffers-rare-global-outage/

## 6. Three single points of failure — Iberian blackout — FACT
**Section:** "Three single points of failure", bullet 2
**Current:** "mobile networks across Spain and Portugal failed within hours as backup batteries at cell sites ran out."
**Problem:** Overstated as a total failure. Ookla data: >50 % of users across extensive areas of Spain had no service at the 18:00 UTC peak; >60 % in the worst-hit areas of Portugal; one operator (Digi) lost >90 % of subscribers for over 24 h, while MEO, with deeper battery and generator backup, stayed largely up. The mechanism (batteries running down over hours) is correct.
**Replacement:** "more than half of mobile users across large areas of Spain and Portugal lost service within hours as cell-site batteries ran down; one operator's customers were offline for over a day."
**Source opened:** https://broadbandbreakfast.com/iberian-blackout-highlights-gaps-in-telecom-network-resiliency/

## 7. Three single points of failure — Ukraine and Kaliningrad sourcing — STYLE
**Section:** "Three single points of failure", bullets 1 and 3; "Methods" last paragraph
**Current:** "Its limits on use in Ukraine were widely reported" / "Satellite-navigation jamming around Kaliningrad and over the Black Sea is now routine." / "...are widely reported events, not linked here."
**Problem:** Both are true, but a Medium reader will want one link each. Add them to Sources.
**Replacement (Sources list additions):** "Starlink restrictions in Ukraine: CNN/Isaacson report via Mezha, https://mezha.ua/en/2023/09/07/elon-musk-thwarts-ukraine-s-attack-on-russian-fleet-in-crimea-cnn" and "GNSS interference, Kaliningrad and the Baltic: Spire, https://spire.com/blog/space-reconnaissance/gnss-interference-report-russia/". Then delete "not linked here" from the Methods paragraph.

## 8. How we tested it — STYLE
**Section:** "How we tested it", bullet 1
**Current:** "It models a Loon-class superpressure balloon: a 68.5 kg envelope, a 92.5 kg payload, a 3.06 kWh battery, six 210 W solar panels and an air pump that changes altitude."
**Problem:** Verified against BLE 1.0.1 source (68.5 kg, 92.5 kg, 3,058.56 Wh, 4+2 panels at 210 W). Fine as is; only the long list could be split.
**Replacement:** "It models a Loon-class superpressure balloon: 68.5 kg envelope, 92.5 kg payload, 3.06 kWh battery and six 210 W solar panels. An air pump changes altitude."

## 9. Finding 1 — wind numbers — FACT (minor)
**Section:** Finding 1, paragraph 3
**Current:** "the mean eastward wind ran from 17.7 m/s at 150 hPa to 31.7 m/s at 30 hPa."
**Problem:** Recomputed from `data/gfs_europe_2025.npz` at the 50°N row, January: 17.6 m/s at 150 hPa, 31.8 m/s at 30 hPa (and 24.4 at 50 hPa). The July 50 hPa value −2.8 m/s checks. Rounding only, but the article presents them as exact.
**Replacement:** "the mean eastward wind ran from about 18 m/s at 150 hPa to 32 m/s at 30 hPa."

## 10. Finding 1 — best pairs — STYLE
**Section:** Finding 1, paragraph 3
**Current:** "the best month-site pairs reached 0.33–0.37."
**Problem:** Checks (`coverage_2025.csv`: Paris Aug 0.37, Rome Apr 0.35, Bucharest Jul 0.34). The bare fraction reads oddly after percentages.
**Replacement:** "the best month-site pairs (Paris in August, Rome in April, Bucharest in July) reached 33–37 %."

## 11. Finding 2 — winter dwell — FACT
**Section:** Finding 2, paragraph after the chart
**Current:** "Winter is the hard season: every controller manages only 1.5–2 days in December–March, because there is no slow altitude to find."
**Problem:** `analyze_drift.py` monthly means: Jan–Mar are 1.3–1.9 days for all three controllers, but December is 2.3 (passive), 3.1 (home) and 3.4 (slow). The Dec–Mar mean for the slow controller is 2.3 days (harmonic 2.1 in `cost_comparison.md`).
**Replacement:** "Winter is the hard season. From January to March every controller managed only 1.3–1.9 days, because there is no slow altitude to find; December was 2–3 days."

## 12. Finding 2 — chart marker — STYLE
**Section:** Finding 2, embedded-content placeholder
**Current:** "&#91;embedded content: run\_drift.py · 360 one-way flights from Lisbon, Brest, Dublin, Vienna and Bucharest, 1st and 15th of each month, 2025 GFS winds\]"
**Problem:** Docs widget placeholder; Medium needs an image.
**Replacement:** "[CHART: dwell-by-month]" with caption "Days over the region per flight, by launch month and controller. 360 one-way flights from Lisbon, Brest, Dublin, Vienna and Bucharest, 2025 GFS winds."

## 13. Finding 2 — hindsight ratio — STYLE
**Section:** Finding 2, paragraph on launch position
**Current:** "raised the Little's-law-weighted dwell from 3.65 to 6.39 days, a factor of 1.75."
**Problem:** Recomputed from `drift_2025.csv` (harmonic mean of monthly means, best of five sites per launch date): 3.65 → 6.35, ×1.74. Within rounding of the article's figures, so no number change, but "Little's-law-weighted" needs a gloss for Medium.
**Replacement:** "raised the launch-rate-weighted dwell (the figure that sets how many launches a day you need) from 3.65 to 6.4 days, a factor of about 1.75."

## 14. Finding 2 — ships — FACT (omitted result)
**Section:** Finding 2, last paragraph
**Current:** "Ships, with a rule that runs for Europe at full speed before slowing down, matched the land sites (3.07 versus 3.31 days on rotation) but did not beat them (`run_ship.py`)."
**Problem:** 3.07 (ship, `ship_approach_2025.csv`) and 3.31 (land sites in the same comparison, `ship_vs_land_2025.csv`) check. But 13 % of ship launches never entered the region at all (README: "13% never arrive"), which the article omits, and the 3.31 land figure differs from the 3.65 quoted two paragraphs earlier because it comes from a different run. Say both.
**Replacement:** "Ships, with a rule that runs for Europe at full speed before slowing down, roughly matched the land sites (3.1 versus 3.3 days in that comparison) but did not beat them, and 13 % of ship launches never reached the region (`run_ship.py`)."

## 15. Finding 3 — table → list — STYLE
**Section:** Finding 3, table
**Current:** (3-row table: First design / Glide ratio 12, 29 kg/m² / Recommended)
**Problem:** Medium does not render tables. All three rows verified against `glider_tuning.md` and `glider_sizing.csv` (63.6 % MC / 78.3 % nominal; 93.9 % at 28.8 kg/m², 1.6 h; 98.0 %, 2.11 h).
**Replacement:**
"- **First design** (glide ratio 12, 16 kg/m², aim straight at the site, release at a fixed 150 km): 64 % recovered under wind errors, 78 % in perfect winds; about 2.1 h descent.
- **Heavier wing** (glide ratio 12, 29 kg/m²): 94 % in perfect winds; 1.6 h descent.
- **Recommended** (glide ratio 14, 20 kg/m², speed-to-fly guidance, reachability release): **98.0 %** under wind errors; 2.1 h descent."

## 16. Finding 3 — forecast-only caveat — STYLE
**Section:** Finding 3, last paragraph
**Current:** "A version using only forecasts recovers the same 98.2% but gives up 77–98 hours of coverage per flight instead of about 35."
**Problem:** Checks (`glider_tuning.md`: 98.2 % at 24 h horizon costing 98 h; 98.1 % at 72 h costing 77 h). Minor precision.
**Replacement:** "A version using only forecasts recovers 98.1–98.2 % but gives up 77–98 hours of coverage per flight instead of about 35."

## 17. Finding 4 — pressure wording — FACT (minor)
**Section:** Finding 4, paragraph after the table
**Current:** "Tendon load scales with internal pressure, so halving it allows much thinner film."
**Problem:** 2,380 → 1,000 Pa is a 58 % cut, not a halving.
**Replacement:** "Tendon and film loads scale with internal pressure, so cutting it from 2,380 to 1,000 Pa allows much thinner film."

## 18. Finding 4 — table → list — STYLE
**Section:** Finding 4, lever table
**Current:** (5-row table of levers)
**Problem:** Table. All values verified in `envelope_cost.md` §3 (−70 %, −37 %, −26 %, −8 %, €1,068).
**Replacement:**
"Each lever on its own, applied to today's roughly €10,000 envelope:
- Automated line at about 400,000 a year, same design: −70 % (€10k → about €3k).
- Lower internal pressure (1,000 Pa instead of 2,380) with 25–30 µm film: −37 %.
- Lighter payload, 92.5 → 40 kg: −26 %.
- Recovery and recycling credit: about −8 %.
- **All stacked: about €1,070 per envelope** (range €390–2,900)."

## 19. Finding 5 — chart marker — STYLE
**Section:** Finding 5, embedded-content placeholder
**Current:** "&#91;embedded content: combined\_cost.py mid case, built on cost\_model.py line items · unit costs are engineering assumptions\]"
**Replacement:** "[CHART: per-flight-bridge]" with caption "Cost per flight, baseline €37,100 to redesigned €11,100, by line item (`combined_cost.py` mid case; unit costs are engineering assumptions)."

## 20. Finding 5 — numbers — verified, no change
**Section:** Finding 5
`combined_cost.py` today: mid €11,132 per flight, fleet €3.4 B (best €1.5 B, worst €9.2 B), baseline €37,147; €127 + €1,267 + €156 + €320 = €1,870; DWELL_MULT (1.6, 1.35, 1.15); payload unit 0.7 × €35,000 mode; life 15; refurb 10 %; gig pickup ×0.5. All match.

## 21. Finding 6 — heading — STYLE
**Section:** Finding 6 heading
**Current:** "Finding 6: looping the hemisphere halves launches, but not legally"
**Problem:** "not legally" is ambiguous (it reads as if the halving is illegal).
**Replacement:** "Finding 6: looping the hemisphere halves launches, but most flights cross China"

## 22. Finding 6 — table → list — STYLE
**Section:** Finding 6, configuration table
**Current:** (3-row table)
**Problem:** Table. Values verified from the jsonl files via `analyze_multipass.py` and direct recomputation: launches ×0.77/0.68/0.62, ×0.53/0.41/0.32, ×0.49/0.37/0.30; reach China 100 %, 100 %, 88.3 %; time over China 7.4 %, 6.0 %, 2.1 %; median max latitude n/a, 82.6°N, 78.8°N; thrust energy median 51.5 kWh per 30 days.
**Replacement:**
"Launches needed, as a fraction of the one-way fleet, for 30 / 60 / 100-day envelopes:
- **Altitude steering only** (3 kWh battery): 0.77 / 0.68 / 0.62. Every flight entered Chinese airspace; 7.4 % of flight time over China.
- **Plus a fuel-cell power store** (10 kWh): 0.53 / 0.41 / 0.32. Every flight still entered China (6.0 % of time); median peak latitude 82.6°N.
- **Plus a 3 m/s latitude-holding propeller**: 0.49 / 0.37 / 0.30. 88 % of flights entered China, for 2.1 % of time; median peak latitude 78.8°N."

## 23. Finding 6 — shoot-downs — FACT
**Section:** Finding 6, "Two problems remain" paragraph
**Current:** "Unauthorised balloons have been shot down: by the United States in 2023, and fatally by Belarus in 1995."
**Problem:** The 1995 case was a crewed Gordon Bennett race balloon; race organisers and the FAI said Belarus had been notified and had authorised the flight, which Belarus disputed. Calling it "unauthorised" takes one side of a disputed record. The 2023 case (Chinese surveillance balloon, F-22, 4 Feb 2023, off South Carolina) checks.
**Replacement:** "States do shoot balloons down. The United States downed a Chinese surveillance balloon off South Carolina in February 2023. In September 1995 a Belarusian helicopter shot down a crewed race balloon, killing both pilots, in a dispute over whether it had clearance."
**Sources opened:** https://www.airandspaceforces.com/chinese-surveillance-balloon-shot-down-f-22/ ; https://www.rferl.org/a/belarus-american-balloonists-tragedy-25-years-shot-down/30975038.html

## 24. Finding 6 — Chicago Convention link — FACT
**Section:** Finding 6 and Sources
**Current:** "[Chicago Convention](https://www.icao.int/publications/Documents/7300_orig.pdf)"
**Problem:** The ICAO URL returns 404 (as do `7300_cons.pdf` and `7300_9ed.pdf`). The Article 8 text itself checks: "No aircraft capable of being flown without a pilot shall be flown without a pilot over the territory of a contracting State without special authorization by that State and in accordance with the terms of such authorization."
**Replacement:** "[Chicago Convention](https://en.wikisource.org/wiki/Convention_on_International_Civil_Aviation)" (Article 8; ICAO Doc 7300). Sources entry: "Convention on International Civil Aviation (Chicago, 1944), Article 8 — text at https://en.wikisource.org/wiki/Convention_on_International_Civil_Aviation (ICAO Doc 7300; the icao.int PDF link is currently dead)".

## 25. Finding 7 — Europe-only comparison — FACT
**Section:** Finding 7, first sentence
**Current:** "Balloons launched from western Canada spent 46% of their flight time over places the network serves, against 26% for Europe-only service, and every one reached Europe."
**Problem:** Canada: 45–46 % checks (36 flights, pooled 45.6 %, mean of per-flight 45.2 %; all 36 reached Europe). Europe-only, same fuel-cell + propeller configuration, same 60-day window: 24 % (per-flight mean 23.9 %, pooled 24.6 %); 26 % only appears at the 150-day cap (27 %) or as the mean Europe sector share (28 %). The README's 26 % is not reproducible at 60 days.
**Replacement:** "Balloons launched from western Canada spent 46 % of their flight time over places the network serves, against about 24 % for Europe-only service over the same 60 days, and every one reached Europe."

## 26. Finding 7 — table → list — STYLE
**Section:** Finding 7, median-days table
**Current:** (4-row table)
**Problem:** Table. Values verified from the Canada jsonl (medians 4.81 / 4.53 / 12.59 / 22.36; first arrival median day 10.5).
**Replacement:**
"Median days per 60-day flight:
- Over Canada: 4.8
- Over the North Atlantic shipping lanes: 4.5
- Over Europe (first arrival around day 10): 12.6
- **Useful total (median of per-flight totals): 22.4**"

## 27. Finding 7 — seasonal averages — FACT
**Section:** Finding 7, paragraph after the table
**Current:** "Summer launches averaged about 32 useful days, winter launches about 17."
**Problem:** From the jsonl: June–August launches averaged 35.4 useful days (median 35.5); December–February 15.8 (median 19.5). 32 only appears for May–August (31.7); 17 for Dec–Mar (16.7). State the months.
**Replacement:** "June–August launches averaged about 35 useful days; December–February launches about 16."

## 28. Finding 7 — China clipping — verified
**Section:** Finding 7
"China was still clipped on 72% of flights within the 60 days, for a median 0.7 days": 26/36 = 72.2 %; median china_days 0.66 over all flights. Checks.

## 29. Surgical — lead claim — FACT (overstated)
**Section:** "Being surgical where a constellation is a blanket", first sentence
**Current:** "Balloons can put about three times Starlink's capacity over a 300 km zone within hours, because they can be stacked over one place and satellites can't."
**Problem:** The 3× (1.7 vs 0.55 Tbps) checks, but it needs ~850 balloons and 472 launches a day in summer, and the model's own first-coverage time is 14–36 h in summer (5–11 h in winter). "Within hours" overstates.
**Replacement:** "Balloons can put about three times Starlink's capacity over a 300 km zone within a day or two, because they can be stacked over one place and satellites can't. The price is a surge of several hundred launches a day."

## 30. Surgical — population density — FACT
**Section:** "Being surgical", outage paragraph
**Current:** "about 34 million people at Italian density"
**Problem:** `outage_scenario.py` uses 120 people/km² (comment: "~Italy-like"). Italy's average is about 200/km²; 120 is close to France. 34 M checks for 120/km² over π·300².
**Replacement:** "about 34 million people at 120 per km², roughly France's average density"

## 31. Surgical — outage table → list, and cost basis — FACT
**Section:** "Being surgical", outage table
**Current:** (4-row table: 254 / 848 balloons; 141 / 472 / 443 / 1,476 launches; €1.8M / €5.9M / €5.5M / €18.3M; 14–36 h / 5–11 h)
**Problem:** All figures match `outage_scenario.csv`, but the cost column uses `PER_FLIGHT_EUR` mid = €12,400 (an earlier `combined_cost.py` run), not the €11,100 quoted in Finding 5. Costs are therefore ~10 % high relative to the article's own per-flight number. Either re-run `outage_scenario.py` with (5,981, 11,132, 25,397) or say so.
**Replacement:**
"For a 300 km zone (demand 0.5 Tbps for voice and text, 1.7 Tbps for degraded data):
- **Summer, voice and text:** 254 balloons aloft, 141 launches a day, about €1.8 M a day; first coverage in 14–36 h.
- **Summer, degraded data:** 848 balloons, 472 launches a day, about €5.9 M a day; 14–36 h.
- **Winter, voice and text:** 254 balloons, 443 launches a day, about €5.5 M a day; 5–11 h.
- **Winter, degraded data:** 848 balloons, 1,476 launches a day, about €18 M a day; 5–11 h.
Costs use €12,400 a flight, an earlier mid-case figure; at the €11,100 above they are about 10 % lower."

## 32. Surgical — fire-watch estimate — STYLE
**Section:** "Being surgical", last paragraph
**Current:** "Summer fire watch over a 300 km zone needs only about 1.3–2 launches a day for triple coverage, about €15–25k a day, because fire season is when stratospheric winds are slowest."
**Problem:** Not in any results file; it follows from the summer crossing time implied by the outage model (254 balloons ÷ 141 launches/day ≈ 43 h; 3 balloons × 24 / 43 ≈ 1.7 launches a day ≈ €20k). Label it as derived.
**Replacement:** "Summer fire watch over a 300 km zone needs only about 1.3–2 launches a day to keep three balloons overhead (the summer crossing takes about 43 hours), about €15–25k a day. Fire season is when stratospheric winds are slowest."

## 33. Jamming — heading — STYLE
**Section:** Jamming heading
**Current:** "Jamming: as good as Starlink, better in key ways"
**Problem:** Reads as a sales line; the section itself is balanced (phones are worse against a nearby jammer).
**Replacement:** "Jamming: where balloons beat Starlink, and where they don't"

## 34. Jamming — table → list — STYLE
**Section:** Jamming, threat table
**Current:** (7-row table)
**Replacement:**
"- **Distant ground jammer:** Starlink has little geometric edge; the balloon has about 20 dB. Balloons better.
- **Signal strength at a phone:** weak from orbit; about 29 dB stronger from 20 km. Balloons better.
- **Jammer next to the user:** Starlink's dish beam rejects it well; phones have no dish, but an optional panel rejects low-angle jammers by about 20–30 dB. Phones worse; with a directional terminal, even or better.
- **Backhaul:** laser cross-links on both. Even.
- **Losing a node:** many satellites vs an €11k flight with hundreds launched a day. Even.
- **Hardware refresh:** about five years for a satellite vs every flight cycle, in weeks. Balloons better.
- **Who can switch it off:** one foreign company vs an allied operator or authority. Balloons better."

## 35. Jamming — drift speed — FACT (minor)
**Section:** Jamming, "The target barely moves" bullet
**Current:** "A balloon drifts at 10–65 km/h (the 2025 runs)"
**Problem:** `drift_2025.csv`, slow controller: 5th–95th percentile 9–73 km/h, median 24, extremes 7–114.
**Replacement:** "A balloon typically drifts at 10–70 km/h (the 2025 runs; median 24 km/h)"

## 36. Capacity — table → list — STYLE
**Section:** "Capacity" table
**Current:** (4-row table)
**Replacement:**
"Over the Europe region:
- **Starlink, its share of network capacity:** about 21 Tbps (`cost_model.py`: ~600 Tbps network × regional share).
- **Starlink, traffic actually carried:** about 5 Tbps (25 % load factor, assumed).
- **Allied satellites by about 2030:** 1.5–3 Tbps. KONNECT VHTS, 500 Gbps over Europe, North Africa and the Middle East; IRIS², a reported 3.3 Tbps goal worldwide from 2030; Telesat Lightspeed, about 10 Tbps worldwide from 2028.
- **Balloon coverage fleet, about 3,850 balloons:** about 7.7 Tbps (2 Gbps per balloon, assumed)."

## 37. Capacity — KONNECT coverage — FACT (minor)
**Section:** Capacity table and Sources
**Current:** "KONNECT VHTS 500 Gbps over Europe"
**Problem:** The 500 Gbps Ka-band figure is for Europe, North Africa and the Middle East, not Europe alone. The businesswire link returns 403; use the CSI Magazine report or Eutelsat's own release.
**Replacement:** "KONNECT VHTS, 500 Gbps over Europe, North Africa and the Middle East" with link https://www.csimagazine.com/csi/Eutelsat-Konnect-VHTS-enters-service.php

## 38. Capacity — IRIS² figure — FACT (sourcing)
**Section:** Capacity table and Sources
**Current:** "IRIS² 3.3 Tbps goal globally from 2030"
**Problem:** The 3.3 Tbps figure appears only in Space Intel Report (paywalled; the figure is in the open intro, which I read). Official SpaceRISE/Eutelsat releases give ~290 satellites and 2030 but no total capacity. Keep, but mark as reported.
**Replacement:** "IRIS², a reported 3.3 Tbps goal worldwide from 2030 (Space Intel Report; official releases give no capacity figure)"

## 39. Capacity — Telesat source — FACT (dead link)
**Section:** Capacity table and Sources
**Current:** "[Telesat Lightspeed](https://www.marketbeat.com/instant-alerts/telesat-q2-earnings-call-highlights-2026-08-13/) ~10 Tbps globally from 2028" and the second marketbeat link
**Problem:** Both marketbeat URLs return server errors. The ~10 Tbps figure is Telesat's own ("something like 10 terabits", SpaceQ); the August 2026 expansion to 225 satellites raises capacity by more than 40 % and keeps Q1 2028 service (Runway Girl Network). So "~10 Tbps" is conservative.
**Replacement:** "Telesat Lightspeed, at least about 10 Tbps worldwide from early 2028" with links https://spaceq.ca/?p=31873 and https://runwaygirlnetwork.com/2026/09/telesat-restores-commercial-lightspeed-capacity-with-more-satellites/

## 40. Capacity — matching Starlink raw capacity — FACT
**Section:** "Capacity", last paragraph
**Current:** "Matching Starlink's full raw capacity rather than its traffic would take about 9,000 balloons and roughly €8 billion a year at 2 Gbps each (2.3 × the €3.4 billion fleet), or about €3.5 billion at 5 Gbps."
**Problem:** 21 Tbps ÷ 2 Gbps = 10,500 balloons = 2.7 × the 3,846-balloon fleet ≈ €9.3 B; at 5 Gbps, 4,200 balloons ≈ 1.1 × ≈ €3.7 B. The article's 9,000 / 2.3× / €8 B corresponds to 17.7 Tbps, not 21.
**Replacement:** "Matching Starlink's full raw capacity rather than its traffic would take about 10,500 balloons and roughly €9 billion a year at 2 Gbps each (2.7 × the €3.4 billion fleet), or about 4,200 balloons and €3.7 billion at 5 Gbps."

## 41. Cost both ways — table → list — STYLE
**Section:** "Cost against Starlink", table
**Current:** (2-row table)
**Replacement:**
"- **Starlink, whole constellation:** €6–10 billion a year (USD 7–12 billion: SpaceX's 2025 connectivity-segment costs plus estimated capex, in `cost_model.py`). Users need a dish, USD 300–600.
- **Balloon layer, about 95 % of the region, mid case:** €3.4 billion a year (€1.5–9.2 billion). Users need nothing: phones connect directly."

## 42. Cost both ways — long sentences — STYLE
**Section:** "Cost against Starlink", paragraph 2
**Current:** "A hybrid service with satellite backstop (50% balloon coverage, winter at 50%, populated land only) came to about 4.6 times in the cost-reduction study (cost\_reduction.py)."
**Problem:** Verified (`cost_reduction.md`: 4.6×, 3.0–7.2×), but the reader has not been told what "populated land only" means.
**Replacement:** "A thinner hybrid service came to about 4.6 times: balloons target 50 % coverage over populated land only, with satellites filling the gaps (`cost_reduction.py`)."

## 43. Risks — table → list, winter ratio — FACT
**Section:** "What is not solved yet", risk table, row 1
**Current:** "Winter winds | Flights last 1.5–2 days; winter needs about 3× the summer launch rate"
**Problem:** `cost_comparison.md`: winter 1,871 launches/day vs summer 453 at 95 % coverage = 4.1×; the outage model gives 3.1× (443 vs 141). Also see finding 11 on the day range.
**Replacement:** "**Winter winds.** January–March flights last 1.3–1.9 days; winter needs three to four times the summer launch rate. Mitigation: ship and mobile launch, the Canada loop."

## 44. Risks — envelope litter — FACT (minor)
**Section:** Risk table, "Envelope litter" row
**Current:** "~306,000 flights a year × ~17 kg ≈ 5,000 t of polyethylene; 34% landed at sea in today's routing"
**Problem:** Mid-case launches: 1,100 a day ÷ 1.35 ≈ 815 a day ≈ 297,000 a year. 306,000 is not reproducible from the model; ~300,000 is. 34 % sea landings and 5,000 t check.
**Replacement:** "**Envelope litter.** About 300,000 flights a year × about 17 kg ≈ 5,000 t of polyethylene; 34 % of today's simulated landings are at sea. Mitigation: steered cut-downs, paid pickup, recovery ships."

## 45. Risks — hydrogen threshold source — STYLE
**Section:** Risk table, "Hydrogen safety" row
**Current:** "EU major-hazard rules start at 5 t on one site"
**Problem:** Correct (Directive 2012/18/EU Annex I Part 2: hydrogen 5 t lower tier, 50 t upper tier), but name it.
**Replacement:** "**Hydrogen safety.** About 14 kg a flight; the EU Seveso III directive's lower tier starts at 5 t of hydrogen on one site. Mitigation: make hydrogen on ships, keep sites under 5 t."

## 46. Risks — WRC-23 source — STYLE
**Section:** Risk table, "Spectrum and borders" row; Programme, "Harmonise spectrum"
**Current:** "the WRC-23 high-altitude base-station rules"
**Problem:** Correct (WRC-23 identified 694–960 MHz, 1,710–1,885 MHz and 2,500–2,690 MHz for HIBS), but unexplained.
**Replacement:** "the WRC-23 rules for high-altitude IMT base stations (HIBS), which identified the 700/800/900 MHz, 1.8 GHz and 2.6 GHz mobile bands for platforms like these"

## 47. Burn paragraph — verified, no change
**Section:** "What is not solved yet", burn paragraph
19 % coupling = H_PYRO × M_PE / (M_H2 × LHV) = 4.5 × 68.5 / (13.77 × 120) = 18.7 %; median 90 % consumed, ~200 km strip, 215 kg CO₂ per README. Checks.

## 48. Programme — pilot arithmetic — verified; wording — STYLE
**Section:** "A phased NATO–EU programme", item 1
**Current:** "Three 300 km zones for one summer: 3 zones × 90 days × \~2 launches a day ≈ 540 flights, about €6 million of operations at \~€11k a flight, plus a development budget still to be scoped."
**Problem:** Arithmetic checks (540 × €11.1k = €6.0 M). One 36-word sentence.
**Replacement:** "Three 300 km zones for one summer: 3 zones × 90 days × about 2 launches a day ≈ 540 flights. That is about €6 million of operations at €11k a flight, plus a development budget still to be scoped."

## 49. Methods — scripts table → list — STYLE
**Section:** "Methods, assumptions and sources", scripts table
**Replacement:** a bullet list (see article.md), or drop the table entirely since the repository is private.

## 50. Sources — dead and replaced links — FACT
**Section:** Sources list
**Current:** businesswire KONNECT (403), spaceintelreport IRIS² (ok, paywalled), businesswire SpaceRISE (403), two marketbeat Telesat links (500), icao.int Doc 7300 (404).
**Replacement:** see article.md Sources: CSI Magazine (KONNECT), Eutelsat/mynewsdesk SpaceRISE release, SpaceQ + Runway Girl Network (Telesat), Wikisource (Chicago Convention), plus Daily Maverick (Starlink outage), Broadband Breakfast (Iberian blackout), Air & Space Forces Magazine (2023), RFE/RL (1995), Mezha/CNN (Ukraine), Spire (Kaliningrad), EUR-Lex (Seveso III).

## 51. Sentence length — STYLE (general)
Sentences over 25 words were split throughout `article.md`: the subtitle; intro paragraph 1; Finding 1 paragraph 2; Finding 3 paragraph 2 (the 48-word Monte Carlo sentence); Finding 5 paragraphs 2–3; Finding 6 paragraph 2; Finding 7 last paragraph; Jamming paragraphs 1, 3 and 5; Capacity last paragraph; Programme items 1 and 3 and the consortium bullet; Methods assumptions paragraph.

## 52. Repetition — STYLE (general)
"€3.4 billion" appears eight times; `article.md` keeps it in the subtitle, Finding 5, the cost section and the programme, and drops it elsewhere. The "Little's law" explanation appears in Findings 2 and 5; kept once. The "radios come home" point is made in Findings 3, 5, the Surgical list and the Jamming table; kept in 3 and 5.

---

## External claims: verification status

| Claim | Status | URL opened |
|---|---|---|
| Iberian blackout, 28 Apr 2025, mobile networks lost as batteries ran down | Supported, but "failed" overstated (see 6) | https://broadbandbreakfast.com/iberian-blackout-highlights-gaps-in-telecom-network-resiliency/ |
| Starlink global outage, July 2025, "for hours" | 24 Jul 2025, ~2.5 h, software failure (see 5) | https://www.dailymaverick.co.za/article/2025-07-25-elon-musks-starlink-network-suffers-rare-global-outage/ |
| Starlink limits on use in Ukraine | Supported (CNN/Isaacson, FT geofencing reports) | https://mezha.ua/en/2023/09/07/elon-musk-thwarts-ukraine-s-attack-on-russian-fleet-in-crimea-cnn |
| GNSS jamming around Kaliningrad routine | Supported | https://spire.com/blog/space-reconnaissance/gnss-interference-report-russia/ |
| KONNECT VHTS 500 Gbps | Supported; coverage is Europe + N. Africa + Middle East | https://www.csimagazine.com/csi/Eutelsat-Konnect-VHTS-enters-service.php |
| IRIS² 3.3 Tbps goal, ~290 satellites, 2030 | Supported by one trade source only (paywalled intro read) | https://www.spaceintelreport.com/eu-commission-on-iris2-multi-orbit-constellation-are-we-ready-to-compromise-no-but-well-accept-tradeoffs-if-needed |
| Telesat Lightspeed ~10 Tbps, 2028 | Supported (10 Tbps is Telesat's 2023-era figure; 225-sat expansion adds >40 %; Q1 2028) | https://spaceq.ca/?p=31873 ; https://runwaygirlnetwork.com/2026/09/telesat-restores-commercial-lightspeed-capacity-with-more-satellites/ |
| Chicago Convention Art. 8 | Text supported; article's ICAO link is dead | https://en.wikisource.org/wiki/Convention_on_International_Civil_Aviation |
| US shoot-down 2023 | Supported (4 Feb 2023, F-22, off South Carolina) | https://www.airandspaceforces.com/chinese-surveillance-balloon-shot-down-f-22/ |
| Belarus 1995 | Supported as fatal shoot-down; "unauthorised" is disputed (see 23) | https://www.rferl.org/a/belarus-american-balloonists-tragedy-25-years-shot-down/30975038.html |
| Seveso III hydrogen 5 t | Supported | https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32012L0018 |
| WRC-23 HIBS bands | Supported via search summaries of the CTU outcome PDF; the PDF itself was fetched (HTTP 200) but not machine-readable here | https://ctu.int/wp-content/uploads/2023/12/Main-WRC-23-Result-20.02.24.pdf |

Not independently verifiable from the repo (taken from README/results as reported): stock-BLE 38 % baseline (`baseline.py` not re-run), burn-sim medians (`burn_sim.py` not re-run), 66 %/34 % land/sea landings (`analyze_envelopes.py` not re-run), Starlink cost and 600 Tbps inputs (secondary analyses cited in `cost_comparison.md`).

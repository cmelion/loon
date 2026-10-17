# Launch-site mix: which sites earn their place, and whether Canada should carry the baseload

17 October 2026. A replay study on the tracks the engine has already flown; no new flights.
Every number is marked **measured** (read from a track or run file, or a replay of them) or
**estimated** (a proxy, an assumption, or a figure built on one). One wind year, 2025. Scripts:
`site_mix.py` (the replay and the sweep), `site_mix_report.py` (the tables below), both on top of
`replay.py`. Nothing here needs the engine.

## Summary

- Holding a layer of 50 balloons aloft over the region, the cheapest set of European launch sites is
  Brest, Dublin and Vienna: about 4,100 light-vehicle flights a year, €46 M, covering 8.5 % of the
  region's area within 80 km of a balloon at any hour, year round and in winter alike (measured replay,
  cost estimated at €11,100 a flight). The five original sites cost €53 M for 8.9 %.
- Northern coverage is bought cheaply from the west first. Adding Copenhagen to Brest, Dublin and Vienna
  costs €3.5 M a year (+8 %) and takes the northern box (54–59.5°N, 5–30°E) from 5.3 % to 9.2 % covered,
  with no hour of the year uncovered instead of 29 % of hours. Adding Gothenburg as well reaches 12.5 %
  for €52 M, less than the five original sites cost for 5.3 %. Riga is the third northern site worth
  buying; Tallinn is not.
- Tallinn never earns its place: adding it lowers coverage per euro in 97–98 % of the 255 sets that lack
  it. Riga lowers it in 80–90 %, Bucharest is neutral, and the four western and central sites plus
  Copenhagen and Gothenburg raise it in 80–100 % of sets.
- The Canada baseload fails on cost and does not help in the north. A Canada flight delivers one
  first pass over Europe of 3.35 launch-weighted days (measured), about the same as a Brest launch
  (4.3) or the five sites together (3.6). At the €33,000 a flight assumed here it costs three times a
  light flight, so 50 Canada balloons aloft cost €128 M a year for 5.9 % of the region against €53 M
  for 8.9 % from the five sites. The flight would have to cost €9,000–14,000, at or below the light
  disposable flight, to break even on area coverage per euro (estimated). Canada balloons enter at the
  jet's latitude under the 56°N guard and give the northern box 2 % coverage, nothing from January to May.
  Replacing half of any European set's layer with Canada lowered coverage per euro in 96–98 % of the
  511 sets; no Canada configuration is on the frontier. The hypothesis is rejected on 2025 winds for
  the simulated vehicle with termination over Europe; the conditions under which it could revive are
  listed in section 5.
- Population weighting was not possible: no population grid is on this machine, so every coverage figure
  is a share of area, with the share of 21 large cities as a crude check. `site_mix.py --pop <file>`
  adds a population column once a GHSL or GEOSTAT file is downloaded.
- For the M4: fly the five candidate sites added to `run_drift.py` as `LAUNCH_SET=candidates`
  (Aberdeen, Santiago, Belgrade, Warsaw, Ankara), log positions in the Canada runs so the proxy below can
  be retired, and re-fly the frontier sets on the light vehicle and on a second ERA5 year.

## 1. Method

**Tracks.** The light-vehicle library is the 216 slow-controller flights with hourly positions:
`results/slow_tracks.csv` (Lisbon, Brest, Dublin, Vienna, Bucharest, 24 launches each on the 1st and
15th of every month of 2025, GFS winds) and `results/slow_tracks_nordic.csv` (Copenhagen, Gothenburg,
Riga, Tallinn, 24 each). A flight ends when it leaves the region, fails, or reaches 30 days; service
ends with it (no glider release, as `results/deployable_now.md` now assumes). These are BLE's
Loon-class balloon, not the 40 kg light vehicle of the cost estimate, which has not flown yet.

**Schedules.** A layer of N balloons is held by Little's law: on each day the launch rate is
N × 24 divided by the mean service hours of the tracks a launch that day can fly, and every launch flies
a stored track from the same site launched within three weeks of it (`replay.py`). Launches are spread
through the day and shared equally between the sites of the set. The replay keeps site and season, not
the day's weather; launches in the same fortnight share two or three tracks, which strings balloons
along a few paths and overlaps their discs more than reality would. That is the conservative direction
for coverage, and it bites hardest where flights are fast and short. A month of warm-up launches before
1 January is replayed but not counted or costed.

**Two fixes to `replay.py` that real files forced.** The Little's-law rate ignored the chosen sites and
used the whole library's dwell, so a subset study held the wrong number aloft (123 for a nominal 100 on
the real files). And it used the launch month's mean dwell while the picks came from a six-week window,
so single-site layers ran at two to three times N in months whose window reached into a neighbouring
month of much longer flights (Lisbon in January: 180 aloft for a nominal 50). The rate now uses the
mean of the tracks the picker can choose, from the chosen sites; the replayed fleets below hold N within
a few per cent in every month (`replay.standing_launches`, `by='window'`; the old form is kept as
`by='month'`). `availability.py` inherits both fixes through `replay.py`; its own code ran unchanged on
the real track files with a synthetic population.

**Scoring.** Cells of 0.5° latitude by 1° longitude over the region 36–59.5°N, 10°W–42°E (2,444 cells,
10.09 M km², area-weighted). A cell is covered at an hour if any balloon aloft is within 80 km of its
centre (40 and 194 km as sensitivities). Reported by month, for December–February, June–August and the
year: the share of the region's area covered, the share of the northern box 54–59.5°N, 5–30°E (0.93 M
km², 9.2 % of the region), the share of 21 large cities (the recovery stations of `run_coverage.py`,
a proxy for where people are, not a population figure), balloons aloft, launches a year and cost. One
80 km disc is 0.2 % of the region, so 50 discs that never overlapped would cover 10.0 % and 100 would
cover 19.9 %; the ratio of achieved to that bound is reported as packing.

**Cost.** €11,100 a light flight, the `combined_cost.py` mid case the article quotes (an engineering
estimate). €33,000 a Canada flight, an **assumption** built from the same line items: a BLE-class
envelope designed for 60 days at a volume a Canada layer never reaches, €6,000 (between today's
€10,000 mode and the €3,900 a 400,000-a-year line would give); the payload line at the heavier unit
with 80 % recovery, €16,000 (the runs put a recovery station within 150 km on 89 % of first passes,
33 % in December; parachute success and pickup are not in the runs); fuel cell, propeller and 10 kWh
store consumed per flight, €3,500; launch €1,267, hydrogen €300 including about 3 kg for propulsion,
recovery pickup €1,175, network and regulatory €476; 15 % overhead. The sum is €33,000, and the range
a reader could defend is €20,000–45,000. Because the verdict turns on this number, section 5 gives the
break-even price instead of leaning on it.

**Subsets.** All 511 non-empty subsets of the nine European sites, at 50 and 100 aloft, each alone and
with Canada holding half the layer, plus Canada alone: 2,046 configurations, one seed
(`results/site_mix_scores.csv`). Single sites were also run at 25 and 200 aloft and at 40 and 194 km
(`results/site_mix_singles.csv`), and the Canada share was varied over 0, 25, 50, 75 and 100 % with five
seeds for the five original sites and all nine (`results/site_mix_shares.csv`; seed-to-seed spread of the
year-round region share is 0.1 percentage points, 0.3–0.5 in summer).

**The Canada proxy (estimated).** The Canada run files
(`results/multipass_2025_nochina_bat10000_thrust3_canada.jsonl` on NCEP and `_canada_era5.jsonl` on the
ERA5 band, 36 sixty-day flights each from Vancouver, Prince George and Calgary) log hours over Europe
by elapsed day, sector days, peak latitude and the days a recovery station was within reach. They do
not log positions. Two quantities are therefore measured for each of the 72 flights: the hour it enters
the region and the length of its first pass over Europe, both read from the daily Europe-hours
series. Every flight reached Europe. Under the premise that every flight terminates over Europe, the
later passes (a mean of 121 hours a flight, measured) are discarded. The path inside the region is
borrowed from a Dublin or Brest track launched in the month of entry (a westerly entry flown by the
same lowest-wind controller the multipass flights use once they are over the region), resampled in time
to the measured first-pass length, and clipped to 56°N, the multipass latitude guard; 11 % of proxy
hours sit on that clip. The 72 proxy tracks are in `results/site_mix_canada_proxy_tracks.csv` with the
source track named, and the per-flight measurements in `results/site_mix_canada_first_pass.csv`. The
proxy fixes the geometry, not the amount of service, and the cost comparison rests on the measured
amount; the geometry would change the packing figure, which section 5 bounds.

## 2. Inputs (measured)

Light-vehicle library, dwell by site. Launch-weighted dwell is the balloon-days one launch buys when
launches follow Little's law month by month; it is the number that sets the flight bill.

| site | flights | mean dwell d | launch-weighted d | DJF mean d | JJA mean d | shortest h | longest d |
|---|---|---|---|---|---|---|---|
| Lisbon | 24 | 4.57 | 1.50 | 2.28 | 6.83 | 4 | 30.0 |
| Brest | 24 | 5.67 | 4.30 | 3.36 | 8.83 | 37 | 25.8 |
| Dublin | 24 | 5.27 | 3.81 | 3.10 | 9.53 | 18 | 20.1 |
| Vienna | 24 | 5.79 | 3.03 | 2.87 | 9.44 | 16 | 21.6 |
| Bucharest | 24 | 5.57 | 1.70 | 1.03 | 14.90 | 14 | 30.0 |
| Copenhagen | 24 | 4.01 | 2.72 | 2.60 | 5.63 | 17 | 15.5 |
| Gothenburg | 24 | 3.93 | 1.95 | 2.42 | 4.16 | 9 | 24.3 |
| Riga | 24 | 3.29 | 1.52 | 1.32 | 4.56 | 7 | 11.5 |
| Tallinn | 24 | 1.84 | 1.09 | 1.22 | 2.62 | 0 | 9.5 |

The five original sites spend 6.6 % of their flight hours in the northern box, the Nordic four 33 %
(the rerun note's 7 % and 33 %).

Canada flights, first pass over Europe (72 flights, NCEP and ERA5 together; the two wind sets agree
to within the spread between flights, mean first pass 219 h on NCEP and 186 h on ERA5):

| season of launch | flights | transit d | first pass h, mean | first pass h, median | later passes h | recovery station in reach |
|---|---|---|---|---|---|---|
| DJF | 18 | 4.2 | 71 | 69 | 106 | 78 % |
| MAM | 18 | 12.1 | 218 | 248 | 130 | 89 % |
| JJA | 18 | 12.9 | 389 | 315 | 170 | 100 % |
| SON | 18 | 10.1 | 133 | 121 | 77 | 89 % |
| year | 72 | 9.8 | 203 | 113 | 121 | 89 % |

Launch-weighted first-pass dwell 3.35 days. No flight touched Chinese airspace before the end of its
first pass (0 of 72), so termination over Europe removes the China question entirely. Winter flights
cross the Atlantic in 2.7–5.5 days and cross Europe in three; summer flights take 5–20 days to arrive
and then linger two weeks.

## 3. Single sites

Each site holding 50 aloft on its own, 80 km radius. Region and north are shares of area covered,
averaged over the hours of the period. The Canada row is the proxy of section 1.

| site | launches/yr | €M/yr | region % year | DJF | JJA | north % year | DJF | JJA | cities % | packing | region % per €M | north % per €M |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Brest | 4,131 | 45.9 | 6.4 | 6.9 | 5.5 | 1.7 | 2.9 | 2.0 | 5.1 | 0.64 | 0.139 | 0.037 |
| Dublin | 4,476 | 49.7 | 6.3 | 6.6 | 6.3 | 3.5 | 5.2 | 3.1 | 10.2 | 0.64 | 0.128 | 0.071 |
| Vienna | 5,163 | 57.3 | 5.8 | 5.1 | 6.4 | 5.7 | 0.0 | 9.5 | 13.5 | 0.58 | 0.101 | 0.100 |
| Copenhagen | 5,961 | 66.2 | 5.3 | 6.0 | 4.7 | 15.7 | 14.6 | 18.9 | 8.0 | 0.54 | 0.081 | 0.237 |
| Gothenburg | 6,958 | 77.2 | 5.1 | 5.6 | 4.4 | 17.9 | 18.2 | 19.5 | 6.3 | 0.51 | 0.066 | 0.231 |
| Lisbon | 7,885 | 87.5 | 4.8 | 4.3 | 3.6 | 0.0 | 0.0 | 0.1 | 6.6 | 0.48 | 0.055 | 0.000 |
| Canada alone (est.) | 3,876 | 127.9 | 5.9 | 7.1 | 5.0 | 2.1 | 4.5 | 2.1 | 7.4 | 0.59 | 0.046 | 0.016 |
| Bucharest | 9,699 | 107.7 | 4.7 | 4.0 | 6.5 | 4.6 | 0.0 | 11.7 | 11.4 | 0.47 | 0.044 | 0.043 |
| Riga | 10,032 | 111.4 | 4.9 | 5.3 | 4.9 | 16.0 | 10.6 | 19.4 | 4.5 | 0.49 | 0.044 | 0.144 |
| Tallinn | 21,083 | 234.0 | 3.8 | 4.8 | 3.8 | 12.3 | 12.0 | 11.3 | 5.4 | 0.38 | 0.016 | 0.053 |

Two things the table says. First, at a fixed number aloft every site covers roughly the same area,
within a factor of 1.7; what separates them is the flight bill, which runs from 4,100 to 21,000
launches a year for the same layer. Coverage per euro is dwell per euro. Second, the northern box is
a geography question, not a dwell question: the three best sites by cost give it 2–6 %, the Nordic sites
12–18 %, and only the Nordic sites cover it in every hour of the year.

Northern-box coverage by month, single sites holding 50 aloft (% of the box's area):

| site | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | hours with none |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Lisbon | 0.0 | 0.0 | 0.0 | 0.0 | 0.1 | 0.2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 96 % |
| Brest | 0.9 | 0.0 | 0.0 | 0.0 | 3.3 | 4.3 | 1.7 | 0.0 | 0.0 | 0.0 | 2.6 | 7.7 | 66 % |
| Dublin | 0.0 | 0.0 | 0.0 | 0.0 | 3.4 | 7.6 | 1.9 | 0.1 | 0.4 | 2.0 | 11.6 | 15.1 | 57 % |
| Vienna | 0.0 | 0.0 | 0.8 | 11.8 | 12.9 | 9.3 | 5.5 | 13.6 | 14.6 | 0.0 | 0.0 | 0.0 | 50 % |
| Bucharest | 0.0 | 0.0 | 0.0 | 0.0 | 1.4 | 4.7 | 12.0 | 18.2 | 18.3 | 0.1 | 0.0 | 0.0 | 64 % |
| Copenhagen | 7.7 | 8.3 | 11.0 | 10.5 | 15.1 | 13.8 | 23.6 | 19.1 | 20.5 | 10.5 | 20.0 | 27.2 | 0 % |
| Gothenburg | 11.9 | 14.1 | 12.1 | 10.3 | 18.7 | 16.6 | 21.4 | 20.4 | 13.4 | 17.5 | 29.3 | 28.2 | 0 % |
| Riga | 10.2 | 11.9 | 11.3 | 12.8 | 25.0 | 14.7 | 18.0 | 25.4 | 28.2 | 13.4 | 11.0 | 9.8 | 0 % |
| Tallinn | 12.1 | 13.8 | 10.3 | 8.0 | 7.8 | 10.7 | 8.1 | 15.2 | 25.3 | 17.6 | 9.1 | 10.4 | 0 % |
| Canada alone (est.) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 3.2 | 3.1 | 0.0 | 0.2 | 0.0 | 4.7 | 13.2 | 71 % |

From January to March only the Nordic sites reach the box at all, as the rerun note found. Dublin and
Brest reach it in November and December, Vienna and Bucharest only from late spring to September.

Sensitivities, single sites, year (region % of area): at 40 km the sites sit at 1.4–2.1 % and at
194 km at 9–21 %, in the same order; the Canada proxy packs comparatively better at 194 km (21.1 %,
beside Brest's 21.5 %) because a wide disc hides the strung-out line of balloons. Doubling the layer
from 50 to 100 raises Brest's coverage from 6.4 to 9.0 % and Tallinn's from 3.8 to 4.3 %: the overlap
along a few paths saturates the weak sites first (`results/site_mix_singles.csv`).

## 4. Subsets: the frontier

The frontier is every set that no other set beats on both cost and coverage. European sets only,
50 aloft, year round:

| sites | launches/yr | €M/yr | region % | north % | cities % | region % per €M |
|---|---|---|---|---|---|---|
| Brest, Dublin, Vienna | 4,125 | 45.8 | 8.5 | 5.3 | 14.7 | 0.185 |
| + Lisbon | 4,386 | 48.7 | 8.8 | 4.3 | 15.4 | 0.180 |
| Brest, Dublin, Vienna, Copenhagen | 4,436 | 49.2 | 8.9 | 9.2 | 14.9 | 0.180 |
| Lisbon, Brest, Dublin, Vienna, Gothenburg | 4,578 | 50.8 | 9.0 | 8.7 | 14.7 | 0.176 |
| Lisbon, Brest, Dublin, Vienna, Copenhagen | 4,584 | 50.9 | 9.0 | 7.6 | 15.5 | 0.177 |
| Lisbon, Brest, Dublin, Vienna, Copenhagen, Gothenburg | 4,728 | 52.5 | 9.1 | 10.6 | 15.1 | 0.173 |
| Lisbon, Brest, Dublin, Vienna, Gothenburg, Riga | 4,944 | 54.9 | 9.1 | 11.0 | 14.3 | 0.165 |
| Brest, Dublin, Vienna, Copenhagen, Gothenburg, Riga | 5,032 | 55.9 | 9.1 | 15.5 | 13.7 | 0.163 |
| Lisbon, Brest, Dublin, Vienna, Bucharest, Gothenburg, Tallinn | 5,319 | 59.0 | 9.3 | 10.8 | 16.0 | 0.158 |

The five original sites (€53.1 M, 8.9 %, north 5.3 %) are not on it: Lisbon, Brest, Dublin, Vienna
and Copenhagen cost €2.2 M less and cover 9.0 % with 7.6 % of the north. All nine sites cost €62.2 M
for 9.1 % and 13.7 % of the north. The frontier at 100 aloft has the same members in the same order
(Brest, Dublin, Vienna at €91.7 M and 13.8 %; the five originals €105.7 M and 15.4 %; all nine €124.1 M
and 16.4 %), and the winter and summer frontiers keep the same head: Brest, Dublin and Vienna first,
Copenhagen or Gothenburg as the first addition. In winter Gothenburg is the better first northern
addition (Brest, Dublin, Gothenburg: €49.5 M, 8.9 % region, 11.4 % north in December–February); in summer
Copenhagen is. Full tables for both fleet sizes and all three periods come from `site_mix_report.py sweep`.

The frontier on the northern box, year, 50 aloft, reads as a price list for the north:

| sites | €M/yr | north % | region % | north % per €M |
|---|---|---|---|---|
| Brest, Dublin, Vienna | 45.8 | 5.3 | 8.5 | 0.12 |
| Brest, Dublin, Vienna, Copenhagen | 49.2 | 9.2 | 8.9 | 0.19 |
| Brest, Dublin, Vienna, Gothenburg | 49.4 | 10.4 | 8.7 | 0.21 |
| Brest, Dublin, Vienna, Copenhagen, Gothenburg | 51.9 | 12.5 | 8.8 | 0.24 |
| Brest, Dublin, Vienna, Copenhagen, Gothenburg, Riga | 55.9 | 15.5 | 9.1 | 0.28 |
| Dublin, Copenhagen, Gothenburg, Riga | 62.1 | 19.5 | 8.4 | 0.31 |
| Copenhagen, Gothenburg, Riga | 74.9 | 25.1 | 7.5 | 0.34 |
| Copenhagen, Gothenburg, Riga, Tallinn | 84.2 | 26.4 | 7.8 | 0.31 |

A layer that must serve the Baltic and Scandinavia buys Copenhagen and Gothenburg first, Riga third,
and stops there: Tallinn adds 1.3 points of northern coverage for €9.3 M a year and lowers both
efficiencies. Brest, Dublin, Vienna, Copenhagen and Gothenburg at €51.9 M is the set this study would
name as the standing layer's launch network on 2025 winds: cheaper than the five original sites,
8.8 % of the region and 12.5 % of the north year round, 10.7 % of the north in winter, and no hour of
the year with the north uncovered (the five originals leave it uncovered 62 % of winter hours).

Marginal value of each site, averaged over the 255 sets that lack it, 50 aloft, year:

| site | Δ region % | Δ north % | Δ €M/yr | Δ region % per €M | share of sets where coverage per euro rises |
|---|---|---|---|---|---|
| Brest | +0.56 | −2.8 | −10.3 | +0.026 | 100 % |
| Dublin | +0.53 | −2.0 | −10.3 | +0.025 | 100 % |
| Vienna | +0.43 | −0.8 | −5.8 | +0.015 | 100 % |
| Lisbon | +0.41 | −2.7 | −2.7 | +0.009 | 93 % |
| Copenhagen | +0.33 | +3.1 | −2.4 | +0.006 | 80 % |
| Gothenburg | +0.32 | +4.2 | −2.3 | +0.006 | 82 % |
| Bucharest | +0.33 | −0.5 | +2.5 | −0.002 | 26 % |
| Riga | +0.31 | +3.3 | +4.4 | −0.006 | 10 % |
| Tallinn | +0.17 | +2.2 | +8.0 | −0.014 | 2 % |

Adding a long-dwell site to a set lowers its cost because launches are shared equally and the set's
mean dwell rises; adding Tallinn raises it by €8 M a year. At 100 aloft the ordering is the same, with
Bucharest neutral (54 %) and Lisbon positive in every set.

Where the gaps are (per-cell shares in `results/site_mix_cells_cells.csv`, three sets at 50 aloft):
in winter the band north of 56°N is covered under 2 % of the time by the five original sites and
5–14 % with the Nordic sites; the south-east corner (36–44°N, 30–42°E, Turkey and the eastern Black Sea)
is covered 2–11 % of the time by every set in every season; Iberia is covered only by Lisbon, whose
winter flights exit south and west within a day (26 % of hours in the south-west corner, under 7 %
elsewhere in Iberia); the best-covered blocks in every set are France, the Alps and the Carpathian basin
in winter (15–30 %) and the British Isles and Biscay in summer (20–39 %), where the Dublin and Brest
summer flights loiter.

## 5. The Canada baseload

The hypothesis: the standing layer is launched from western Canada on the transatlantic conveyor and the
European sites are kept for surge and for the north. Measured and replayed on 2025, with the proxy of
section 1 for the geometry:

| layer of 50 aloft, year | launches/yr | €M/yr (est.) | region % | DJF | JJA | north % | DJF | JJA | cities % |
|---|---|---|---|---|---|---|---|---|---|
| five European sites, no Canada | 4,764 | 52.9 | 8.9 | 8.9 | 9.1 | 5.1 | 2.7 | 8.5 | 16.6 |
| five sites 75 %, Canada 25 % | 3,579 + 967 | 71.6 | 8.5 | 8.7 | 8.5 | 4.7 | 3.5 | 7.5 | 15.3 |
| five sites 50 %, Canada 50 % | 2,375 + 1,937 | 90.3 | 7.7 | 8.3 | 7.2 | 3.9 | 4.0 | 5.4 | 12.7 |
| five sites 25 %, Canada 75 % | 1,192 + 2,907 | 109.2 | 7.0 | 7.9 | 6.4 | 3.0 | 4.2 | 4.1 | 10.4 |
| Canada alone | 3,875 | 127.9 | 6.0 | 7.2 | 5.1 | 2.2 | 4.5 | 2.5 | 7.4 |
| all nine European sites, no Canada | 5,597 | 62.1 | 9.2 | 9.1 | 9.4 | 13.7 | 10.1 | 17.3 | 15.1 |
| all nine 50 %, Canada 50 % | 2,799 + 1,943 | 95.2 | 8.0 | 8.6 | 7.6 | 8.3 | 7.6 | 10.1 | 12.1 |

Five seeds each; the spread between seeds is 0.1 points of region coverage. At 100 aloft every row
doubles in cost and the ordering is unchanged (`results/site_mix_shares.csv`).

What the numbers say, in order of how much they depend on the proxy:

1. **The flight bill is a wash (measured).** Holding 50 aloft from Canada takes 3,875 first passes a
   year; from the five European sites 4,764 launches; from Brest alone 4,131. The conveyor delivers
   3.35 launch-weighted days of service per flight, against 3.6 for the five sites and 4.3 for Brest.
   Canada does not buy more balloon-days per launch; the heavier vehicle simply flies for nine days
   before it starts to serve. Those nine days are 46 % of a 60-day flight spent elsewhere, the rerun
   note's useful share, and with termination over Europe the flight ends when the useful 54 % would have
   begun its second pass.
2. **At any plausible flight price Canada loses on cost (estimated).** For the same area coverage per
   euro as the five European sites, a Canada flight would have to cost €9,200 at the packing the proxy
   gives it, or €13,900 if Canada balloons spread over Europe as well as the five sites' do; at 100
   aloft, €7,900 and €13,600. A sixty-day vehicle with a fuel cell, a propeller, a 10 kWh store and a
   transatlantic recovery chain is not going to undercut an €11,100 disposable flight, and at the
   €33,000 assumed here every Canada share from 25 % up lowers coverage per euro, in 96–98 % of the 511
   European sets at half share and in all of them for the five original sites and all nine.
3. **Canada gives nothing in the north (measured constraint, estimated amount).** The multipass
   controller holds the vehicle below 56°N and pushes it south with the propeller when it strays, so a
   Canada balloon enters Europe at the jet's latitude and the northern box sees 2 % coverage over the
   year and none from January to May. The surge and northern role the hypothesis gives the European
   sites is therefore the whole of the northern job, and the baseload Canada would carry is the part
   of the layer the western sites already supply most cheaply.
4. **Winter is the one season where Canada's geometry is not worse (estimated).** In December–February
   the Canada proxy covers 7.2 % of the region at 50 aloft against 8.9 % for the five sites, 0.142 against
   0.176 % per balloon; the winter conveyor is fast (2.7–5.5 days across the Atlantic, three across
   Europe) and the proxy strings the balloons along one or two jet paths. In summer the conveyor is slow
   (5–20 days of transit, mean 12.9) and the first pass lingers two weeks, 0.098 against 0.177 % per
   balloon aloft.
5. **As a surge source Canada is out of the question (measured).** A Canada launch reaches Europe after
   2.7 days at best in winter and 20 days at worst in summer; a European launch is over the region at
   once. The surge role belongs to the European sites in any season.

**Verdict.** On 2025 winds, for the simulated 10 kWh and 3 m/s vehicle, with every flight terminated
over Europe after its first pass, a Canada baseload costs two to three times what the same layer costs
from Brest, Dublin and Vienna, covers no more of the region per balloon, covers less of it per euro at
any flight price above about €9,000–14,000, and contributes nothing to the northern coverage that was
the European sites' assigned job. The hypothesis is rejected under those conditions. Conditions under
which it would need re-testing: (a) a Canada flight price near the light flight's, which only a loop
with several Europe passes could justify, and the loop is excluded (China on 69–72 % of looping flights,
and the W6 decision); (b) a controller that lets the conveyor enter north of 56°N, which the ERA5 run
shows the vehicle doing over the Atlantic (median peak 69°N) but the guard prevents over Europe; (c) a
reason outside coverage, such as launching from outside the region being served, which this study does
not measure; (d) positions logged in the Canada runs, which would replace the proxy and fix the packing
figure that moves the break-even between €9,000 and €14,000.

## 6. Sites that never earn their place, and candidates

**Never earns its place: Tallinn.** It lowers coverage per euro in 98 % of the sets that lack it at 50
aloft and 97 % at 100, adds 1.3 points of northern coverage to the three other Nordic sites for €9 M a
year, and sits so near the 59.5°N edge that its flights leave north or east within a day in most months
(launch-weighted dwell 1.09 days, one flight of zero hours). **Rarely earns its place: Riga**, worth
buying only once Copenhagen and Gothenburg are in and more northern coverage is wanted (it is the third
northern site on the northern frontier and never on the region frontier below €55 M). **Neutral:
Bucharest**, long summer flights (14.9 days) that cover the Balkans and the Black Sea in July–September,
one-day winter flights that make it the most expensive of the five original sites in launches; it
belongs to a summer-weighted network, not the standing layer. **Lisbon** is cheap to add but adds
nothing in the north and covers Iberia only in its south-west corner; it stays on the region frontier at
50 aloft because it lowers the shared launch rate in summer.

**Candidates worth flying next**, each upwind of a gap the replay shows, added to `run_drift.py` as
`LAUNCH_SET=candidates` (coordinates there; all under the 59.5°N limit; nothing has flown yet, so every
expectation below is a hypothesis):

- **Aberdeen (57.1°N, 2.1°W)**: a western feeder for the northern box in winter. The Nordic sites are
  blown east out of the region within a day from December to February; a launch 600–900 km upwind
  would spend its first day crossing the box. Dublin's 12–15 % of the box in November and December is the
  evidence that the western approach works in the cold half of the year.
- **Santiago de Compostela (42.9°N, 8.5°W)**: Iberia. Lisbon's winter flights exit south or west within
  hours (shortest flight 4 hours); a launch 450 km north-east of it on the same coast should ride the
  same winds across northern Iberia and France instead of out to sea.
- **Belgrade (44.8°N, 20.5°E)**: the Balkans and the Black Sea in winter, where Bucharest's one-day
  winter flights give nothing west of the launch; Belgrade is a day upwind.
- **Warsaw (52.2°N, 21.0°E)**: the band between the Nordic tracks and the Vienna tracks (52–56°N,
  14–30°E), covered 4–17 % of winter hours by the best sets.
- **Ankara (39.9°N, 32.9°E)**: the south-east corner, 36–44°N and 30–42°E, covered 2–11 % of the time by
  every set in every season. Winter flights will leave east fast; the question is whether the summer
  easterlies hold them over Anatolia.

## 7. What the M4 should fly

1. `LAUNCH_SET=candidates python track_slow.py` (120 flights; writes
   `results/slow_tracks_candidates.csv`), then `python site_mix.py --subsets all` extended to the new
   sites, or at least the frontier sets of section 4 with each candidate added. Expect the frontier to
   change in the north and the south-east, not at its head.
2. Log hourly positions in `run_multipass.py` for the Canada set (and for any loop study), so
   `site_mix.py` can replace the proxy; the companion-video note asks for the same log.
3. `python track_slow.py --vehicle light` for the frontier sets, because the whole library is BLE's
   Loon-class balloon and the costed vehicle has not flown; and the same on a second ERA5 year
   (`WIND_GRID=data/era5_europe_<year>.npz`), since the ranking rests on one year.
4. If the Canada question is kept open after this note, re-fly it with the latitude guard lifted over
   the Atlantic approach (`CORRIDOR_HI` and `LAT_HI` in `run_multipass.py`) so the conveyor can enter
   north of 56°N; that is the only version of the hypothesis that could reach the northern box.
5. Download a population grid (GHSL GHS-POP 2025 at 1 km, or Eurostat GEOSTAT 2021) and rerun
   `site_mix.py --pop <file>`; the area-based frontier will shift toward sites that cover the Rhine,
   Po and Danube basins, which probably favours Vienna and Brest further.

## 8. Caveats

One wind year; BLE's Loon-class balloon and its tropical-designed solar model; equal launches per site
(a tuned allocation would lower every set's cost, more so for mixed sets, and might move Riga and
Bucharest; the frontier compares sets under the same policy); the few-tracks clustering of the replay,
conservative for every set and most so for fast-transit sites and for the Canada proxy; the proxy's
geometry; the €33,000 Canada price; area rather than people; 80 km as the service radius, which stands
for a 20 Mbps class-L cell and would be 40 km for a denser service. The region frontier's head, Brest,
Dublin and Vienna, is robust to every one of these in the sense that the three sites lead on
launch-weighted dwell in the measured library by a wide margin; the northern frontier's ordering of
Copenhagen and Gothenburg over Riga over Tallinn is the same in every period and at both fleet sizes.

Files: `results/site_mix_scores.csv` (the sweep), `results/site_mix_singles.csv`,
`results/site_mix_shares.csv`, `results/site_mix_cells_cells.csv`, `results/site_mix_canada_first_pass.csv`,
`results/site_mix_canada_proxy_tracks.csv`; scripts `site_mix.py`, `site_mix_report.py`; `replay.py`
fixed as described; `run_drift.py` gains `LAUNCH_SET=candidates`. Nothing committed.

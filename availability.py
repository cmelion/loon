"""Rerun 6 (W24, W25): availability on population cells, and time to N balloons.

"95 % coverage" in results/cost_comparison.md is a footprint count under a
random-placement formula. This script replaces it with an hourly replay of a
launch schedule on the engine's own tracks (replay.py), over the people who
would be served:

  1. Population cells. GHSL GHS-POP or Eurostat GEOSTAT at 1 km, downloaded by
     the operator and passed as a path (replay.load_population accepts a
     lat,lon,pop CSV, a GEOSTAT CSV with pyproj, or a GeoTIFF with rasterio),
     aggregated to a working grid of --cell-km (default 10 km) inside the
     drift region 36-59.5 N, 10 W-42 E.
  2. The fleet. Either --launches-per-day (a surge rate, e.g. the launches_day
     column of results/outage_scenario_<gbps>.csv) or --standing N (a standing
     layer, launched at the Little's-law rate that holds N aloft each month).
     Launches are spread through the day over the launch sites and fly stored
     tracks of the same site and season (see replay.py for what that does and
     does not keep). Service ends at exit, or at the radio's release hour
     (--drift results/drift_<year>.csv for run_drift's hindsight release;
     --release-csv flight,release_h for a causal rule's).
  3. Each hour, each service radius (40, 80, 194 km): the cells inside each
     balloon's disc; the balloon's capacity split across its cells in
     proportion to population (so overlapping discs add); a cell is covered
     if any disc reaches it and served if the capacity it receives meets its
     demand (people x --mbps-per-person; 0.015 is outage_scenario's voice and
     text, 0.05 its degraded data).

Outputs (tag = year and schedule unless --tag):
  results/availability_<tag>.csv          by radius and month, plus DJF, JJA and
                                          the year: population-weighted covered
                                          and served shares, mean balloons aloft,
                                          launches per day.
  results/availability_<tag>_outages.csv  outage-duration tails: for every cell,
                                          every run of unserved hours, weighted by
                                          population, binned by duration and the
                                          season it began in; also the weighted
                                          p50 and p90 duration.
  results/availability_<tag>_cells.csv    per cell and radius: covered and served
                                          share of the year (for a map).
  results/time_to_n_<tag>.csv  (--time-to-n) the W24 replay: for each candidate
                                          zone (default: the 21 recovery stations,
                                          --zone-km around each) and each start
                                          hour (every --every-start-h through the
                                          year), hours from a cold start, and from
                                          50 or 100 balloons already aloft at
                                          random track positions, to 10, 50 and
                                          90 % of the balloons the zone needs
                                          (demand from the raster at
                                          --mbps-per-person and --balloon-gbps,
                                          with a geometric floor of one balloon
                                          per --footprint-km disc), launching at
                                          --surge-per-site-day from every site.
                                          Reported as median and p90 by season,
                                          with the share of starts that never got
                                          there within --horizon-h.

Every number is a replay of stored tracks, not a forecast; the winter rows
are the ones W25 expects to collapse, and the time-to-N rows are what W24
calls the honest metric. Nothing here needs BLE.

Usage:
  python availability.py --tracks results/slow_tracks.csv --pop data/pop_eu_1km.csv \\
      --standing 100 --radius-km 40,80,194 --drift results/drift_2025.csv
  python availability.py --tracks results/slow_tracks_2019.csv --pop data/ghs_pop_2025_1km.tif \\
      --launches-per-day 443 --radius-km 80 --balloon-gbps 0.2 --time-to-n
  python availability.py --help
"""
import argparse
import csv
import math
import os
import sys

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import replay as rp  # noqa: E402

DURATION_BINS_H = [0, 1, 3, 6, 12, 24, 48, 72, 168, 336, 1e9]
FRACS = (0.1, 0.5, 0.9)


class OutageTally:
  """Runs of unserved hours per cell, weighted by population, by season of onset."""

  def __init__(self, n_cells, pop, year):
    self.since = np.full(n_cells, -1.0)
    self.pop = pop
    self.year = year
    self.records = {s: ([], []) for s in rp.SEASONS}  # season -> (durations, weights)

  def step(self, t, served_now):
    newly_out = (self.since < 0) & ~served_now
    self.since[newly_out] = t
    back = (self.since >= 0) & served_now
    if back.any():
      self._record(t - self.since[back], self.pop[back], self.since[back])
      self.since[back] = -1.0

  def _record(self, durations, weights, onsets):
    seasons = np.array([rp.season_of(m) for m in rp.hours_to_month(onsets, self.year)])
    for s in rp.SEASONS:
      m = seasons == s
      if m.any():
        self.records[s][0].append(durations[m]); self.records[s][1].append(weights[m])

  def flush(self, t_end):
    open_ = self.since >= 0
    if open_.any():
      self._record(t_end - self.since[open_], self.pop[open_], self.since[open_])
      self.since[open_] = -1.0

  def table(self, radius, metric):
    rows = []
    for s, (ds, ws) in list(self.records.items()) + [('all', (sum([d for d, _ in self.records.values()], []),
                                                               sum([w for _, w in self.records.values()], [])))]:
      if not ds:
        continue
      d = np.concatenate(ds); w = np.concatenate(ws)
      hist, _ = np.histogram(d, DURATION_BINS_H, weights=w)
      hours, _ = np.histogram(d, DURATION_BINS_H, weights=w * d)
      order = np.argsort(d); cw = np.cumsum(w[order]) / w.sum()
      p50 = float(d[order][np.searchsorted(cw, 0.5)]); p90 = float(d[order][np.searchsorted(cw, 0.9)])
      for k in range(len(hist)):
        rows.append(dict(radius_km=radius, metric=metric, season=s, dur_lo_h=DURATION_BINS_H[k],
                         dur_hi_h=DURATION_BINS_H[k + 1] if DURATION_BINS_H[k + 1] < 1e8 else 'inf',
                         episode_share=hist[k] / hist.sum(), outage_hours_share=hours[k] / max(hours.sum(), 1e-9),
                         p50_h=p50, p90_h=p90))
    return rows


def disc_allocation(tree, cells_xyz, pop, bal_xyz, radius_km, gbps):
  """Capacity (Gbps) each cell receives and the number of discs over it."""
  n = len(pop)
  cap = np.zeros(n); hits = np.zeros(n, int)
  if len(bal_xyz) == 0:
    return cap, hits
  lists = tree.query_ball_point(bal_xyz, rp.chord(radius_km))
  lens = np.array([len(l) for l in lists])
  if lens.sum() == 0:
    return cap, hits
  cell_idx = np.concatenate([np.asarray(l, int) for l in lists if len(l)])
  bal_idx = np.repeat(np.arange(len(lists)), lens)
  p = pop[cell_idx]
  tot = np.bincount(bal_idx, weights=p, minlength=len(lists))
  share = np.where(tot[bal_idx] > 0, p / np.maximum(tot[bal_idx], 1e-12), 0.0)
  np.add.at(cap, cell_idx, gbps * share)
  np.add.at(hits, cell_idx, 1)
  return cap, hits


def run_availability(tracks, launches, cells, radii, gbps, mbps_pp, hours, year, dt_h):
  pop = cells['pop'].to_numpy(float)
  demand_gbps = pop * mbps_pp / 1e3
  cxyz = rp.xyz(cells.lat.to_numpy(), cells.lon.to_numpy())
  tree = cKDTree(cxyz)
  R = rp.Replay(tracks, launches)
  months = rp.hours_to_month(hours, year)
  per_hour = {r: dict(cov=np.zeros(len(hours)), srv=np.zeros(len(hours))) for r in radii}
  cell_cov = {r: np.zeros(len(pop)) for r in radii}
  cell_srv = {r: np.zeros(len(pop)) for r in radii}
  tallies = {(r, m): OutageTally(len(pop), pop, year) for r in radii for m in ('covered', 'served')}
  aloft = np.zeros(len(hours))
  ptot = pop.sum()
  for k, t in enumerate(hours):
    lat, lon, _, _ = R.aloft(t)
    aloft[k] = len(lat)
    bxyz = rp.xyz(lat, lon) if len(lat) else np.zeros((0, 3))
    for r in radii:
      cap, hits = disc_allocation(tree, cxyz, pop, bxyz, r, gbps)
      covered = hits > 0
      served_frac = np.where(demand_gbps > 0, np.minimum(1.0, cap / np.maximum(demand_gbps, 1e-12)), covered)
      per_hour[r]['cov'][k] = (pop * covered).sum() / ptot
      per_hour[r]['srv'][k] = (pop * served_frac).sum() / ptot
      cell_cov[r] += covered
      cell_srv[r] += served_frac
      tallies[(r, 'covered')].step(t, covered)
      tallies[(r, 'served')].step(t, served_frac >= 0.999)
  for k in tallies:
    tallies[k].flush(hours[-1] + dt_h)
  # tables
  rows = []
  groups = {m: months == m for m in range(1, 13)}
  groups.update({'DJF': np.isin(months, (12, 1, 2)), 'JJA': np.isin(months, (6, 7, 8)), 'year': np.ones(len(hours), bool)})
  n_launch = len(launches)
  for r in radii:
    for g, m in groups.items():
      if not m.any():
        continue
      span_days = m.sum() * dt_h / 24.0
      lm = ((launches.t >= hours[m].min()) & (launches.t < hours[m].max() + dt_h)).sum()
      rows.append(dict(radius_km=r, period=g, hours=int(m.sum()),
                       covered_pop_share=per_hour[r]['cov'][m].mean(),
                       served_pop_share=per_hour[r]['srv'][m].mean(),
                       aloft_mean=aloft[m].mean(), launches_per_day=lm / max(span_days, 1e-9)))
  cells_out = []
  for r in radii:
    cells_out.append(pd.DataFrame(dict(radius_km=r, lat=cells.lat, lon=cells.lon, pop=pop,
                                       covered_share=cell_cov[r] / len(hours), served_share=cell_srv[r] / len(hours))))
  outages = sum((tallies[(r, m)].table(r, m) for r in radii for m in ('covered', 'served')), [])
  return pd.DataFrame(rows), pd.concat(cells_out, ignore_index=True), pd.DataFrame(outages), n_launch


def zone_requirements(cells, zones, zone_km, gbps, mbps_pp, footprint_km, n_required=None):
  cxyz = rp.xyz(cells.lat.to_numpy(), cells.lon.to_numpy())
  tree = cKDTree(cxyz)
  out = []
  for name, (la, lo) in zones.items():
    idx = tree.query_ball_point(rp.xyz(la, lo), rp.chord(zone_km))
    pop = float(cells['pop'].to_numpy()[idx].sum())
    demand = pop * mbps_pp / 1e3                       # Gbps
    n_geo = (zone_km / footprint_km) ** 2              # discs to tile the zone area
    out.append(dict(zone=name, lat=la, lon=lo, zone_km=zone_km, pop_m=pop / 1e6,
                    demand_gbps=demand, n_required=n_required or max(demand / gbps, n_geo)))
  return pd.DataFrame(out)


def run_time_to_n(tracks, cells, zones_df, surge_per_site_day, warm_ns, starts, horizon_h, rng, window_h, sites):
  zxyz = rp.xyz(zones_df.lat.to_numpy(), zones_df.lon.to_numpy())
  zch = np.array([rp.chord(k) for k in zones_df.zone_km])
  nreq = zones_df.n_required.to_numpy()
  cases = ['cold'] + [f'warm{n}' for n in warm_ns]
  recs = []  # (zone_i, case, start_season, frac, hours or nan)
  for t0 in starts:
    season = rp.season_of(int(rp.hours_to_month(t0, tracks.year)[0]))
    surge = rp.make_launches(tracks, surge_per_site_day * len(sites), t0, t0 + horizon_h, rng, sites, window_h)
    for case, n_warm in zip(cases, [0] + list(warm_ns)):
      L = rp.Launches.concat(rp.warm_start(tracks, n_warm, t0, rng, window_h), surge)
      R = rp.Replay(tracks, L)
      hit = np.full((len(zones_df), len(FRACS)), np.nan)
      for h in range(horizon_h + 1):
        lat, lon, _, _ = R.aloft(t0 + h)
        if len(lat) == 0:
          continue
        d = np.linalg.norm(rp.xyz(lat, lon)[None, :, :] - zxyz[:, None, :], axis=-1)
        count = (d <= zch[:, None]).sum(1)
        for j, f in enumerate(FRACS):
          reached = (count >= np.maximum(1.0, f * nreq)) & np.isnan(hit[:, j])
          hit[reached, j] = h
      for zi in range(len(zones_df)):
        for j, f in enumerate(FRACS):
          recs.append((zi, case, season, f, hit[zi, j]))
  d = pd.DataFrame(recs, columns=['zi', 'case', 'season', 'frac', 'hours'])
  rows = []
  for (zi, case, frac), g in d.groupby(['zi', 'case', 'frac']):
    for season in list(rp.SEASONS) + ['all']:
      gg = g if season == 'all' else g[g.season == season]
      if not len(gg):
        continue
      h = gg.hours.to_numpy()
      got = h[~np.isnan(h)]
      z = zones_df.iloc[zi]
      rows.append(dict(zone=z.zone, zone_km=z.zone_km, pop_m=round(z.pop_m, 2), n_required=round(z.n_required, 1),
                       case=case, season=season, frac=frac, n_starts=len(h),
                       hours_median=float(np.median(got)) if len(got) else np.nan,
                       hours_p90=float(np.percentile(got, 90)) if len(got) else np.nan,
                       never_share=1.0 - len(got) / len(h)))
  return pd.DataFrame(rows)


def main(argv=None):
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument('--tracks', required=True, help='track CSV(s) from track_slow.py, comma-separated')
  ap.add_argument('--pop', required=True, help='population cells: lat,lon,pop CSV, GEOSTAT CSV or GHS-POP GeoTIFF')
  ap.add_argument('--pop-kind', choices=['csv', 'geostat', 'geotiff'], help='default: guessed from the file')
  ap.add_argument('--cell-km', type=float, default=10.0, help='working grid cell')
  ap.add_argument('--radius-km', default='40,80,194')
  sched = ap.add_mutually_exclusive_group(required=True)
  sched.add_argument('--launches-per-day', type=float, help='fleet-wide launch rate, spread over the sites')
  sched.add_argument('--standing', type=float, help="balloons to hold aloft (Little's law rate per month)")
  ap.add_argument('--sites', help='comma list of launch sites to use (default: all in the tracks)')
  ap.add_argument('--balloon-gbps', type=float, default=0.2, help='capacity per balloon (W11: 0.04-0.5)')
  ap.add_argument('--mbps-per-person', type=float, default=0.015,
                  help='demand per resident: 0.015 voice/text, 0.05 degraded data (outage_scenario.py)')
  ap.add_argument('--drift', help='results/drift_<year>.csv: service ends at the hindsight release hour')
  ap.add_argument('--release-csv', help='flight,release_h CSV: service ends at these hours (causal rule)')
  ap.add_argument('--every-h', type=int, default=1, help='replay every n-th hour (speed)')
  ap.add_argument('--window-days', type=float, default=21.0, help='track-picking window around the launch date')
  ap.add_argument('--seed', type=int, default=7)
  ap.add_argument('--time-to-n', action='store_true', help='also run the W24 time-to-N replay')
  ap.add_argument('--zones', help='CSV name,lat,lon of candidate zone centres (default: the 21 recovery stations)')
  ap.add_argument('--zone-km', type=float, default=300.0)
  ap.add_argument('--footprint-km', type=float, default=40.0, help='geometric floor: one balloon per disc of this radius')
  ap.add_argument('--surge-per-site-day', type=float, default=12.0, help='W23: 6-12 honest, 48 in the old model')
  ap.add_argument('--n-required', type=float, help='override the per-zone requirement with one balloon count')
  ap.add_argument('--warm', default='50,100', help='balloons already aloft at the start, besides the cold start')
  ap.add_argument('--horizon-h', type=int, default=168)
  ap.add_argument('--every-start-h', type=int, default=24)
  ap.add_argument('--tag')
  a = ap.parse_args(argv)

  rng = np.random.default_rng(a.seed)
  release = rp.release_hours_from_drift(a.drift) if a.drift else rp.release_hours_from_csv(a.release_csv)
  tracks = rp.Tracks(a.tracks.split(','), release_h=release or None)
  cells = rp.load_population(a.pop, a.cell_km, kind=a.pop_kind)
  radii = [float(x) for x in a.radius_km.split(',')]
  sites = a.sites.split(',') if a.sites else tracks.sites
  window_h = a.window_days * 24.0
  dt_h = float(a.every_h)
  hours = np.arange(0, tracks.period_h, a.every_h, dtype=float)
  if a.standing is not None:
    launches = rp.standing_launches(tracks, a.standing, -tracks.period_h / 12, tracks.period_h, rng, sites, window_h)
    sched = f'standing{a.standing:g}'
  else:
    launches = rp.make_launches(tracks, a.launches_per_day, -tracks.period_h / 12, tracks.period_h, rng, sites, window_h)
    sched = f'launch{a.launches_per_day:g}'
  tag = a.tag or f'{tracks.year}_{sched}_{a.balloon_gbps:g}gbps' + ('_release' if release else '')
  print(f'{len(tracks.flights)} tracks ({tracks.year}), {len(cells)} population cells of {a.cell_km:g} km '
        f'({cells["pop"].sum() / 1e6:.1f} M people), {len(launches)} launches (incl. a month of warm-up), '
        f'radii {radii} km, {a.balloon_gbps:g} Gbps a balloon, {a.mbps_per_person:g} Mbps a person, '
        f'service ends at {"release" if release else "exit"}')
  table, cells_out, outages, _ = run_availability(tracks, launches, cells, radii, a.balloon_gbps,
                                                  a.mbps_per_person, hours, tracks.year, dt_h)
  os.makedirs('results', exist_ok=True)
  table.to_csv(f'results/availability_{tag}.csv', index=False)
  cells_out.to_csv(f'results/availability_{tag}_cells.csv', index=False)
  outages.to_csv(f'results/availability_{tag}_outages.csv', index=False)
  pd.set_option('display.width', 200)
  show = table[table.period.isin(['DJF', 'JJA', 'year'])]
  print(show.round(3).to_string(index=False))
  if len(outages):
    print('\nOutage duration, population-weighted (p50 / p90 hours by season of onset):')
    print(outages.groupby(['radius_km', 'metric', 'season'])[['p50_h', 'p90_h']].first().round(1).to_string())
  print(f'wrote results/availability_{tag}.csv, _cells.csv, _outages.csv')
  if a.time_to_n:
    if a.zones:
      z = pd.read_csv(a.zones)
      zones = {str(r.name): (float(r.lat), float(r.lon)) for r in z.itertuples()}
    else:
      zones = rp.RECOVERY
    zdf = zone_requirements(cells, zones, a.zone_km, a.balloon_gbps, a.mbps_per_person, a.footprint_km, a.n_required)
    warm = [int(x) for x in a.warm.split(',') if x]
    starts = np.arange(0, tracks.period_h - a.horizon_h, a.every_start_h, dtype=float)
    ttn = run_time_to_n(tracks, cells, zdf, a.surge_per_site_day, warm, starts, a.horizon_h, rng, window_h, sites)
    ttn.to_csv(f'results/time_to_n_{tag}.csv', index=False)
    print(f'\nTime to N (zone {a.zone_km:g} km, {a.surge_per_site_day:g} launches a site a day from '
          f'{len(sites)} sites, {len(starts)} starts, horizon {a.horizon_h} h). Median hours to 10 % and '
          f'50 % of the requirement and the share of starts that never got there, all seasons:')
    s = ttn[(ttn.season == 'all') & (ttn.frac.isin([0.1, 0.5]))]
    wide = s.pivot(index=['zone', 'n_required'], columns=['case', 'frac'], values=['hours_median', 'never_share'])
    print(wide.round(2).to_string())
    print(f'wrote results/time_to_n_{tag}.csv')


if __name__ == '__main__':
  main()

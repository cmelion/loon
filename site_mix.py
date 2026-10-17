"""Launch-site combination study: which mix of sites covers Europe best per euro, by season.

Replays launch schedules on the hourly tracks the engine already flew (replay.py)
and scores every subset of the nine European sites, with and without a Canada
baseload, at a fixed number of balloons aloft. Nothing here needs BLE.

Inputs
  results/slow_tracks.csv          120 slow-controller flights, five western and central
                                   sites, 2025 GFS, hourly positions until the balloon
                                   leaves the region (light-vehicle library).
  results/slow_tracks_nordic.csv   96 flights from Copenhagen, Gothenburg, Riga, Tallinn.
  results/multipass_2025_nochina_bat10000_thrust3_canada{,_era5}.jsonl
                                   36 sixty-day flights each from Vancouver, Prince George
                                   and Calgary on the simulated 10 kWh / 3 m/s vehicle.
                                   These files log hours over Europe by elapsed day,
                                   sector days and recovery opportunities, NOT positions.

The Canada baseload is therefore an estimate built from two measured quantities and one
proxy: for each Canada flight the hour it enters the region and the length of its first
pass over Europe are read from daily_eu_h (every flight ends over Europe after that pass:
the hemispheric loop is out, so the later passes are discarded); its path inside the region
is borrowed from a Dublin or Brest track of the same month (a westerly entry flown by the
same slow controller the multipass flights use inside the region), resampled in time to
the measured first-pass length and clipped to 56°N, which is the multipass latitude guard.
The proxy tracks are written to results/site_mix_canada_proxy_tracks.csv so they can be
inspected; replace them with real positions when run_multipass.py logs them.

Scoring (area, not people: no population grid is on this machine; --pop accepts a
lat,lon,pop CSV, GEOSTAT CSV or GHS-POP GeoTIFF through replay.load_population and adds a
population-weighted column when given)
  * cells of 0.5° lat x 1° lon over the region 36-59.5°N, 10°W-42°E, area-weighted by cos(lat);
  * a cell is covered at hour t if any balloon aloft is within --radius-km (80) of its centre;
  * region share, northern-box share (54-59.5°N, 5-30°E) and the share of 21 large cities
    (run_coverage.STATIONS on land, a crude proxy for people) covered, averaged over the
    hours of each month, DJF, JJA and the year;
  * launches a year by vehicle (the warm-up month before 1 January is excluded) and cost at
    --light-eur (11,100) a light flight and --canada-eur (33,000, an assumption explained in
    results/site_mix.md) a Canada flight.
Schedules hold N balloons aloft by Little's law per month (replay.standing_launches), with
equal launches per site. "With Canada" means Canada holds half of N and the European
subset the other half; "Canada alone" holds all of N.

Usage
  python site_mix.py --subsets all --standing 50,100        # the sweep (results/site_mix_scores.csv)
  python site_mix.py --subsets singles --standing 25,50,100,200 --radius-km 40,80,194 --tag singles
  python site_mix.py --subsets "Lisbon,Brest,Dublin,Vienna,Bucharest;Brest,Vienna,Copenhagen" --seeds 7,8,9
"""
import argparse
import datetime as dt
import itertools
import json
import math
import os
import sys

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import replay as rp  # noqa: E402
from run_drift import LAUNCH as WEST_SITES, NORDIC, REGION  # noqa: E402
from run_coverage import STATIONS  # noqa: E402

EURO_SITES = list(WEST_SITES) + list(NORDIC)   # Lisbon, Brest, Dublin, Vienna, Bucharest, Copenhagen, Gothenburg, Riga, Tallinn
NORTH = dict(lat0=54.0, lat1=59.5, lon0=5.0, lon1=30.0)
CITIES = {k: v for k, v in STATIONS.items() if k != 'Black Sea (mid)'}
LIGHT_TRACKS = ['results/slow_tracks.csv', 'results/slow_tracks_nordic.csv']
CANADA_FILES = {'ncep': 'results/multipass_2025_nochina_bat10000_thrust3_canada.jsonl',
                'era5': 'results/multipass_2025_nochina_bat10000_thrust3_canada_era5.jsonl'}
PROXY_SITES = ('Dublin', 'Brest')
LAT_CAP = 56.0            # run_multipass.LAT_HI: the latitude guard the Canada vehicle flies under
PERIODS = [str(m) for m in range(1, 13)] + ['DJF', 'JJA', 'year']


# ---------------------------------------------------------------------------
# Canada: measured entry and first-pass length, proxy path
# ---------------------------------------------------------------------------

def canada_first_pass(path, year=2025):
  """Per flight: launch hour, hour of entry into the region, first-pass hours over Europe, recovery."""
  rows = []
  for line in open(path):
    r = json.loads(line)
    d = np.asarray(r['daily_eu_h'], float)         # cumulative Europe hours at the end of each elapsed day
    nz = np.nonzero(d > 0)[0]
    if len(nz) == 0:
      continue
    a = int(nz[0])
    k = a
    while k + 1 < len(d) and d[k + 1] > d[k]:
      k += 1
    first_h = float(d[k])
    start = dt.datetime.fromisoformat(r['start']).replace(hour=6)
    launch_h = (start - dt.datetime(year, 1, 1)).total_seconds() / 3600.0
    entry_h = launch_h + 24.0 * (a + 1) - d[a]      # continuous presence from entry to the end of day a
    rows.append(dict(site=r['site'], start=r['start'], seed=r['seed'], month=r['month'],
                     launch_h=launch_h, entry_h=entry_h, transit_days=(entry_h - launch_h) / 24.0,
                     first_pass_h=first_h, total_eu_h=float(d[-1]), passes=r['passes'],
                     end=r['end'], days=r['days'], max_lat=r['max_lat'], china_days=r['china_days'],
                     recoverable=len(r['recover_days']) > 0,
                     china_before_end_of_first_pass=(r['china_first_day'] is not None and r['china_first_day'] < k + 1)))
  return pd.DataFrame(rows)


def canada_proxy_tracks(light, cfp, rng, out_csv, lat_cap=LAT_CAP, year=2025):
  """Synthetic hourly tracks for the Canada flights' first pass: measured entry hour and length,
  path borrowed from a Dublin/Brest track of the entry month, resampled in time, clipped to lat_cap."""
  recs = []
  by_month = {}
  for f in range(len(light.flights)):
    if light.site[f] in PROXY_SITES and light.end_h[f] >= 6:
      by_month.setdefault(int(light.launch_month[f]), []).append(f)
  for r in cfp.itertuples():
    month = int(rp.hours_to_month(r.entry_h, year)[0])
    cands = by_month.get(month) or by_month[min(by_month, key=lambda m: min(abs(m - month), 12 - abs(m - month)))]
    f = int(rng.choice(cands))
    n = int(light.end_h[f])
    lat = light.lat[f, :n + 1]
    lon = light.lon[f, :n + 1]
    H = int(round(r.first_pass_h))
    u = np.linspace(0, n, H + 1)
    la = np.interp(u, np.arange(n + 1), lat)
    lo = np.interp(u, np.arange(n + 1), lon)
    la = np.minimum(la, lat_cap)
    fid = f'Canada_{r.site.replace(" ", "")}_{r.start}_{r.seed}_{r.Index}'
    for h in range(H + 1):
      recs.append(dict(flight=fid, site='Canada', start=str(np.datetime64(f'{year}-01-01T00', 'h')
                       + np.timedelta64(int(r.entry_h), 'h'))[:10], seed=r.seed, step=h * 20, h=h,
                       hours=r.entry_h + h, lat=round(float(la[h]), 4), lon=round(float(lo[h]), 4),
                       pa=np.nan, proxy=light.flights[f]))
  df = pd.DataFrame(recs)
  df.to_csv(out_csv, index=False)
  return df


# ---------------------------------------------------------------------------
# Grid and coverage bitsets
# ---------------------------------------------------------------------------

class Grid:
  def __init__(self, dlat=0.5, dlon=1.0, radius_km=80.0):
    lats = np.arange(REGION['lat0'] + dlat / 2, REGION['lat1'], dlat)
    lons = np.arange(REGION['lon0'] + dlon / 2, REGION['lon1'], dlon)
    LA, LO = np.meshgrid(lats, lons, indexing='ij')
    self.lat, self.lon = LA.ravel(), LO.ravel()
    self.w = np.cos(np.radians(self.lat))
    self.w /= self.w.sum()
    north = ((self.lat >= NORTH['lat0']) & (self.lat <= NORTH['lat1']) & (self.lon >= NORTH['lon0']) & (self.lon <= NORTH['lon1']))
    self.wn = np.where(north, np.cos(np.radians(self.lat)), 0.0)
    self.wn /= self.wn.sum()
    self.n_cells = len(self.lat)
    self.tree = cKDTree(rp.xyz(self.lat, self.lon))
    self.city_names = list(CITIES)
    self.city_tree = cKDTree(rp.xyz(np.array([v[0] for v in CITIES.values()]), np.array([v[1] for v in CITIES.values()])))
    self.radius_km = radius_km
    self.pop = None

  def bitsets(self, lat, lon):
    """packed cell bitsets (n, ceil(cells/8)) and city masks (n,) uint32 for balloon positions."""
    xyz = rp.xyz(lat, lon)
    lists = self.tree.query_ball_point(xyz, rp.chord(self.radius_km))
    bits = np.zeros((len(lat), self.n_cells), np.uint8)
    for i, l in enumerate(lists):
      bits[i, l] = 1
    packed = np.packbits(bits, axis=1)
    clists = self.city_tree.query_ball_point(xyz, rp.chord(self.radius_km))
    cm = np.zeros(len(lat), np.uint32)
    for i, l in enumerate(clists):
      for j in l:
        cm[i] |= np.uint32(1 << j)
    return packed, cm


class Library:
  """All valid (flight, age) rows of a Tracks object with their coverage bitsets."""

  def __init__(self, tracks, grid):
    self.tracks = tracks
    f, age = np.nonzero(~np.isnan(tracks.lat))
    keep = age <= tracks.end_h[f]
    f, age = f[keep], age[keep]
    self.index = np.full(tracks.lat.shape, -1, np.int64)
    self.index[f, age] = np.arange(len(f))
    self.bits, self.cities = grid.bitsets(tracks.lat[f, age], tracks.lon[f, age])
    self.n_rows = len(f)


def hourly_coverage(lib, launches, hours, every_h):
  """Per replay hour: packed OR of the bitsets of every balloon aloft, and the city mask."""
  L = launches
  n_h = len(hours)
  cells_cov = np.zeros((n_h, lib.bits.shape[1]), np.uint8)
  city_cov = np.zeros(n_h, np.uint32)
  aloft = np.zeros(n_h, int)
  if len(L.t) == 0:
    return cells_cov, city_cov, aloft
  # all (hour index, row) pairs
  h0 = np.ceil((L.t - hours[0]) / every_h).astype(int)
  h1 = np.floor((L.t_end - hours[0]) / every_h).astype(int)
  h0 = np.maximum(h0, 0)
  h1 = np.minimum(h1, n_h - 1)
  cnt = np.maximum(h1 - h0 + 1, 0)
  li = np.repeat(np.arange(len(L.t)), cnt)
  off = np.arange(cnt.sum()) - np.repeat(np.cumsum(cnt) - cnt, cnt)
  hi = h0[li] + off
  age = np.rint(hours[hi] - L.t[li]).astype(int)
  fl = L.flight[li]
  ok = (age >= 0) & (age < lib.index.shape[1])
  rows = np.full(len(li), -1, np.int64)
  rows[ok] = lib.index[fl[ok], age[ok]]
  ok = rows >= 0
  hi, rows = hi[ok], rows[ok]
  order = np.argsort(hi, kind='stable')
  hi, rows = hi[order], rows[order]
  uniq, starts = np.unique(hi, return_index=True)
  cells_cov[uniq] = np.bitwise_or.reduceat(lib.bits[rows], starts, axis=0)
  city_cov[uniq] = np.bitwise_or.reduceat(lib.cities[rows], starts)
  aloft[:] = np.bincount(hi, minlength=n_h)
  return cells_cov, city_cov, aloft


def popcount32(x):
  x = x.astype(np.uint32)
  c = np.zeros(len(x), int)
  for j in range(32):
    c += (x >> np.uint32(j)) & np.uint32(1)
  return c


def score(lib, grid, launches, hours, every_h, months, light_sites, pop_w=None):
  cells_cov, city_cov, aloft = hourly_coverage(lib, launches, hours, every_h)
  cov = np.unpackbits(cells_cov, axis=1)[:, :grid.n_cells].astype(float)
  region = cov @ grid.w
  north = cov @ grid.wn
  cities = popcount32(city_cov) / len(grid.city_names)
  pop = cov @ pop_w if pop_w is not None else None
  in_year = (launches.t >= hours[0]) & (launches.t < hours[0] + lib.tracks.period_h)
  is_can = np.asarray(lib.tracks.site[launches.flight] == 'Canada')
  n_light = int((in_year & ~is_can).sum())
  n_can = int((in_year & is_can).sum())
  groups = {str(m): months == m for m in range(1, 13)}
  groups['DJF'] = np.isin(months, (12, 1, 2)); groups['JJA'] = np.isin(months, (6, 7, 8))
  groups['year'] = np.ones(len(hours), bool)
  out = []
  for g, m in groups.items():
    row = dict(period=g, region=region[m].mean(), north=north[m].mean(), cities=cities[m].mean(),
               aloft=aloft[m].mean(), region_min_h=region[m].min(), north_zero_share=(north[m] == 0).mean())
    if pop is not None:
      row['pop'] = pop[m].mean()
    out.append(row)
  return pd.DataFrame(out), n_light, n_can


def parse_subsets(spec):
  if spec == 'all':
    subs = []
    for k in range(1, len(EURO_SITES) + 1):
      subs += [list(c) for c in itertools.combinations(EURO_SITES, k)]
    return subs
  if spec == 'singles':
    return [[s] for s in EURO_SITES]
  if spec == 'none':
    return []
  return [[x.strip() for x in s.split(',') if x.strip()] for s in spec.split(';') if s.strip()]


def main(argv=None):
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument('--subsets', default='all', help="all | singles | none | 'A,B;C,D' explicit sets")
  ap.add_argument('--standing', default='50,100', help='balloons aloft, comma list')
  ap.add_argument('--canada', default='both', choices=['both', 'era5', 'ncep', 'off'],
                  help='which Canada runs feed the baseload estimate (off: European sets only)')
  ap.add_argument('--canada-share', default='0.5', help='share of N held by Canada in the "with Canada" rows, comma list')
  ap.add_argument('--radius-km', default='80')
  ap.add_argument('--every-h', type=int, default=1)
  ap.add_argument('--seeds', default='7')
  ap.add_argument('--window-days', type=float, default=21.0)
  ap.add_argument('--light-eur', type=float, default=11_100)
  ap.add_argument('--canada-eur', type=float, default=33_000)
  ap.add_argument('--pop', help='population file for a population-weighted column (replay.load_population)')
  ap.add_argument('--tag', default='')
  a = ap.parse_args(argv)

  os.makedirs('results', exist_ok=True)
  rng0 = np.random.default_rng(1)
  light = rp.Tracks(LIGHT_TRACKS)
  files = []
  if a.canada != 'off':
    files = [CANADA_FILES[k] for k in (('ncep', 'era5') if a.canada == 'both' else (a.canada,))]
    cfp = pd.concat([canada_first_pass(p).assign(winds=os.path.basename(p).split('_')[-1].replace('.jsonl', '')) for p in files],
                    ignore_index=True)
    cfp.to_csv('results/site_mix_canada_first_pass.csv', index=False)
    proxy_csv = 'results/site_mix_canada_proxy_tracks.csv'
    canada_proxy_tracks(light, cfp, rng0, proxy_csv)
    tracks = rp.Tracks(LIGHT_TRACKS + [proxy_csv])
  else:
    tracks = light
  radii = [float(x) for x in a.radius_km.split(',')]
  Ns = [float(x) for x in a.standing.split(',')]
  shares = [float(x) for x in a.canada_share.split(',')]
  seeds = [int(x) for x in a.seeds.split(',')]
  subsets = parse_subsets(a.subsets)
  hours = np.arange(0, tracks.period_h, a.every_h, dtype=float)
  months = rp.hours_to_month(hours, tracks.year)
  window_h = a.window_days * 24.0
  t0 = -tracks.period_h / 12.0
  rows = []
  for radius in radii:
    grid = Grid(radius_km=radius)
    pop_w = None
    if a.pop:
      cells = rp.load_population(a.pop, cell_km=10.0)
      # population per grid cell
      i = np.floor((cells.lat - REGION['lat0']) / 0.5).astype(int)
      j = np.floor((cells.lon - REGION['lon0']) / 1.0).astype(int)
      nlon = int(round((REGION['lon1'] - REGION['lon0']) / 1.0))
      pw = np.zeros(grid.n_cells)
      np.add.at(pw, i * nlon + j, cells['pop'].to_numpy())
      pop_w = pw / pw.sum()
    lib = Library(tracks, grid)
    print(f'radius {radius:g} km: {lib.n_rows} library rows, {grid.n_cells} cells', flush=True)
    configs = []
    for N in Ns:
      for S in subsets:
        configs.append((N, S, 0.0))
        if a.canada != 'off':
          for sh in shares:
            configs.append((N, S, sh))
      if a.canada != 'off':
        configs.append((N, [], 1.0))
    for k, (N, S, sh) in enumerate(configs):
      for seed in seeds:
        rng = np.random.default_rng(seed)
        parts = []
        if S and sh < 1:
          parts.append(rp.standing_launches(tracks, N * (1 - sh), t0, tracks.period_h, rng, S, window_h))
        if sh > 0:
          parts.append(rp.standing_launches(tracks, N * sh, t0, tracks.period_h, rng, ['Canada'], window_h))
        L = rp.Launches.concat(*parts)
        tab, n_light, n_can = score(lib, grid, L, hours, a.every_h, months, S, pop_w)
        cost = n_light * a.light_eur + n_can * a.canada_eur
        tab = tab.assign(radius_km=radius, standing=N, canada_share=sh, sites='+'.join(S) if S else '(none)',
                         n_sites=len(S), seed=seed, launches_light=n_light, launches_canada=n_can,
                         cost_eur=cost, light_eur=a.light_eur, canada_eur=a.canada_eur)
        rows.append(tab)
      if (k + 1) % 50 == 0 or k + 1 == len(configs):
        print(f'  {k + 1}/{len(configs)} configurations', flush=True)
  out = pd.concat(rows, ignore_index=True)
  tag = a.tag or ('scores' if a.subsets == 'all' else a.subsets.replace(',', '-').replace(';', '_')[:40])
  path = f'results/site_mix_{tag}.csv'
  out.to_csv(path, index=False)
  print(f'wrote {path} ({len(out)} rows)')
  y = out[out.period == 'year'].copy()
  y['cov_per_meur'] = y.region / (y.cost_eur / 1e6)
  pd.set_option('display.width', 250); pd.set_option('display.max_rows', 60)
  print(y.sort_values('cov_per_meur', ascending=False)[['standing', 'canada_share', 'sites', 'region', 'north', 'cities',
                                                          'aloft', 'launches_light', 'launches_canada', 'cost_eur',
                                                          'cov_per_meur']].head(30).round(3).to_string(index=False))


if __name__ == '__main__':
  main()

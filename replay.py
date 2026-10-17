"""Replay a launch schedule on stored hourly balloon tracks (shared by reruns 6 and 7).

The engine flies one balloon at a time; a fleet is a schedule of launches, each
riding a track the engine already flew. track_slow.py writes those tracks
(results/slow_tracks.csv for 2025 GFS; results/slow_tracks_<year>[_light].csv
for the ERA5 years of rerun 4), one row per flight-hour with columns
flight, site, start, seed, step, h (hours since launch), hours (since the
grid epoch), lat, lon, pa. This module turns a schedule into "who is where
at hour t":

  Tracks        the library: positions by (flight, age) as 2-D arrays, service
                end per flight (exit, or the radio's release hour), launch
                hour and site per flight.
  make_launches a schedule at a rate of launches per day, spread evenly
                through each day and round-robin over the sites; each launch
                is given a stored track from the same site whose launch date
                lies within +-window of the launch (default 21 days, so a
                mid-January launch flies one of the 1 Jan, 15 Jan or 1 Feb
                tracks, chosen at random). The track's winds are those of its
                own date, not the launch's: the replay keeps the season and
                the site, not the day's weather. Launches in the same window
                therefore fly a few distinct tracks offset in time, which
                clusters balloons more than reality would and is the
                conservative direction for availability.
  standing_launches  the rate that holds N balloons aloft in each month by
                Little's law, N / mean dwell of that month's tracks.
  warm_start    N balloons already aloft at random points of random tracks
                (equivalent to launches at negative ages), for the W24 replay.
  Replay        aloft(t): positions of every balloon aloft at hour t.

Also here: population loading onto a working grid (load_population), the
unit-sphere geometry used for disc queries (xyz, chord), and the launch and
recovery sites (imported from run_drift.py, which has no engine imports at
module level). Nothing here needs BLE.
"""
import dataclasses
import datetime as dt
import math
import os

import numpy as np
import pandas as pd

from run_drift import LAUNCH, RECOVERY, REGION, gc_km  # noqa: F401  (no BLE at module level)

EARTH_KM = 6371.0
SEASONS = {'DJF': (12, 1, 2), 'MAM': (3, 4, 5), 'JJA': (6, 7, 8), 'SON': (9, 10, 11)}


def season_of(month):
  for name, months in SEASONS.items():
    if month in months:
      return name
  raise ValueError(month)


def hours_to_month(hours, year):
  """Month (1-12) of each hour-since-1-Jan value; wraps past the year end."""
  h = np.mod(np.atleast_1d(np.asarray(hours, float)), year_hours(year))
  t = np.datetime64(f'{year}-01-01T00', 'h') + h.astype('timedelta64[h]')
  return t.astype('datetime64[M]').astype(int) % 12 + 1


def year_hours(year):
  return 8784 if dt.date(year, 12, 31).timetuple().tm_yday == 366 else 8760


def xyz(lat_deg, lon_deg):
  la, lo = np.radians(lat_deg), np.radians(lon_deg)
  return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], axis=-1)


def chord(km):
  """Chord length on the unit sphere for a great-circle distance in km."""
  return 2.0 * math.sin(min(km / EARTH_KM, math.pi) / 2.0)


class Tracks:
  """Hourly tracks as arrays; positions(flight_idx, age_h) -> lat, lon (NaN after service end)."""

  def __init__(self, paths, year=None, release_h=None):
    paths = [paths] if isinstance(paths, str) else list(paths)
    df = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
    need = {'flight', 'site', 'h', 'hours', 'lat', 'lon'}
    if not need <= set(df.columns):
      raise SystemExit(f'track file needs columns {sorted(need)}, has {list(df.columns)}')
    df['h'] = np.rint(df.h).astype(int)
    df = df.sort_values(['flight', 'h']).drop_duplicates(['flight', 'h'])
    self.flights = np.array(sorted(df.flight.unique()))
    idx = {f: i for i, f in enumerate(self.flights)}
    n, hmax = len(self.flights), int(df.h.max())
    self.lat = np.full((n, hmax + 1), np.nan)
    self.lon = np.full((n, hmax + 1), np.nan)
    fi = df.flight.map(idx).to_numpy()
    self.lat[fi, df.h.to_numpy()] = df.lat.to_numpy()
    self.lon[fi, df.h.to_numpy()] = df.lon.to_numpy()
    first = df.groupby('flight').first()
    last = df.groupby('flight').h.max()
    self.site = first.site.reindex(self.flights).to_numpy()
    self.launch_hours = first.hours.reindex(self.flights).to_numpy(dtype=float)
    self.dwell_h = last.reindex(self.flights).to_numpy(dtype=float)  # to exit / termination
    self.end_h = self.dwell_h.copy()                                  # service end used by the replay
    if release_h:
      for f, h in release_h.items():
        if f in idx and h is not None and not (isinstance(h, float) and math.isnan(h)):
          self.end_h[idx[f]] = min(self.end_h[idx[f]], float(h))
    self.year = year or self._guess_year(first)
    self.period_h = year_hours(self.year)
    self.launch_month = hours_to_month(self.launch_hours, self.year)
    self.sites = sorted(set(self.site))
    self._by_site = {s: np.where(self.site == s)[0] for s in self.sites}

  @staticmethod
  def _guess_year(first):
    if 'start' in first.columns:
      return int(str(first.start.iloc[0])[:4])
    return 2025

  def mean_dwell_h(self, month=None, service=True, sites=None):
    """Mean service (or full) hours of the tracks launched in `month`, from `sites` (default all).

    A month with no track from the chosen sites falls back to those sites' all-year mean.
    (Before 2026-10-17 the sites were ignored, so a subset study held N aloft at the
    whole library's dwell: 123 aloft for a nominal 100 on the real 2025 files.)
    """
    h = self.end_h if service else self.dwell_h
    s = np.ones(len(h), bool) if sites is None else np.isin(self.site, list(sites))
    if not s.any():
      raise ValueError(f'no tracks from sites {sites}')
    m = s if month is None else (s & (self.launch_month == month))
    return float(h[m].mean()) if m.any() else float(h[s].mean())

  def window_mean_dwell_h(self, t, sites=None, window_h=21 * 24, service=True):
    """Mean service hours of the tracks pick() can choose at hour t: from `sites`, launched within
    +-window_h of t (circular in the year); the nearest track if none is in the window."""
    h = self.end_h if service else self.dwell_h
    sites = list(sites or self.sites)
    vals = []
    for s in sites:
      cand = self._by_site[s]
      d = np.abs((self.launch_hours[cand] - t + self.period_h / 2) % self.period_h - self.period_h / 2)
      near = cand[d <= window_h]
      if len(near) == 0:
        near = cand[[int(np.argmin(d))]]
      vals.append(h[near].mean())
    return float(np.mean(vals))   # equal launches per site: the sites' means weigh equally

  def pick(self, site, t_launch, rng, window_h=21 * 24):
    """A stored flight from `site` launched within +-window_h of t_launch (circular in the year)."""
    cand = self._by_site[site]
    d = np.abs((self.launch_hours[cand] - t_launch + self.period_h / 2) % self.period_h - self.period_h / 2)
    near = cand[d <= window_h]
    if len(near) == 0:
      near = cand[[int(np.argmin(d))]]
    return int(rng.choice(near))

  def positions(self, flight_idx, age_h):
    age = np.rint(np.asarray(age_h, float)).astype(int)
    f = np.asarray(flight_idx, int)
    ok = (age >= 0) & (age < self.lat.shape[1]) & (age <= self.end_h[f])
    lat = np.full(len(f), np.nan)
    lon = np.full(len(f), np.nan)
    lat[ok] = self.lat[f[ok], age[ok]]
    lon[ok] = self.lon[f[ok], age[ok]]
    return lat, lon


@dataclasses.dataclass
class Launches:
  t: np.ndarray        # launch hour (hours since 1 Jan of the track year; may be negative)
  flight: np.ndarray   # index into Tracks
  t_end: np.ndarray    # service end hour

  @staticmethod
  def concat(*parts):
    parts = [p for p in parts if p is not None and len(p.t)]
    if not parts:
      return Launches(np.zeros(0), np.zeros(0, int), np.zeros(0))
    return Launches(np.concatenate([p.t for p in parts]), np.concatenate([p.flight for p in parts]),
                    np.concatenate([p.t_end for p in parts]))

  def __len__(self):
    return len(self.t)


def make_launches(tracks, rate_per_day, t0, t1, rng, sites=None, window_h=21 * 24, by_hour=False):
  """Launches at `rate_per_day` (a number, a function of month, or with by_hour a function of the
  launch day's hour) from t0 to t1, round-robin over sites."""
  sites = list(sites or tracks.sites)
  ts, fs = [], []
  k = 0
  day = math.floor(t0 / 24.0)
  while day * 24 < t1:
    month = int(hours_to_month(day * 24, tracks.year)[0])
    if by_hour:
      r = rate_per_day(day * 24.0)
    else:
      r = rate_per_day(month) if callable(rate_per_day) else rate_per_day
    n = int(math.floor(r + rng.random()))  # fractional rates: Bernoulli on the remainder
    for j in range(n):
      t = day * 24 + (j + 0.5) * 24.0 / n
      if t0 <= t < t1:
        site = sites[k % len(sites)]
        k += 1
        ts.append(t)
        fs.append(tracks.pick(site, t, rng, window_h))
    day += 1
  t = np.array(ts, float)
  f = np.array(fs, int)
  return Launches(t, f, t + tracks.end_h[f] if len(f) else t)


def standing_launches(tracks, n_aloft, t0, t1, rng, sites=None, window_h=21 * 24, service=True, by='window'):
  """Little's law: launches/day = N * 24 / mean service hours of the tracks the launches will fly,
  from the chosen sites (equal launches per site, round-robin).

  by='window' (default): the mean over the tracks pick() can choose on that day, i.e. the same
  +-window_h of launch date, so the layer holds N in expectation. by='month': the launch month's
  mean, the original form; on the real 2025 files it ran single-site layers at two to three times N
  in months whose window reaches into a neighbouring month of much longer flights (Lisbon in
  January: 180 aloft for a nominal 50), because the rate and the picks used different track sets.
  """
  if by == 'month':
    rate = lambda m: n_aloft * 24.0 / max(tracks.mean_dwell_h(m, service, sites), 1.0)
    return make_launches(tracks, rate, t0, t1, rng, sites, window_h)
  rate = lambda t: n_aloft * 24.0 / max(tracks.window_mean_dwell_h(t, sites, window_h, service), 1.0)
  return make_launches(tracks, rate, t0, t1, rng, sites, window_h, by_hour=True)


def warm_start(tracks, n, t0, rng, window_h=21 * 24):
  """N balloons already aloft at t0, each at a random age of a random seasonal track (W24)."""
  if n <= 0:
    return None
  fs = np.array([tracks.pick(tracks.sites[i % len(tracks.sites)], t0, rng, window_h) for i in range(n)])
  age = rng.random(n) * tracks.end_h[fs]
  t = t0 - age
  return Launches(t, fs, t + tracks.end_h[fs])


class Replay:
  """Positions of every balloon aloft at hour t under a set of launches."""

  def __init__(self, tracks, launches):
    self.tracks = tracks
    order = np.argsort(launches.t)
    self.L = Launches(launches.t[order], launches.flight[order], launches.t_end[order])

  def aloft(self, t):
    """-> (lat, lon, launch_index, age_h) of balloons aloft at t, NaN positions dropped."""
    L = self.L
    hi = np.searchsorted(L.t, t, side='right')
    idx = np.arange(hi)[L.t_end[:hi] > t]
    if len(idx) == 0:
      e = np.zeros(0)
      return e, e, np.zeros(0, int), e
    age = t - L.t[idx]
    lat, lon = self.tracks.positions(L.flight[idx], age)
    ok = ~np.isnan(lat)
    return lat[ok], lon[ok], idx[ok], age[ok]

  def count_series(self, hours):
    return np.array([len(self.aloft(t)[0]) for t in hours])


# ---------------------------------------------------------------------------
# Population
# ---------------------------------------------------------------------------

def load_population(path, cell_km=10.0, region=REGION, kind=None):
  """Population cells -> DataFrame(lat, lon, pop) on a cell_km working grid inside region.

  path: a CSV with columns lat, lon, pop (any resolution; GHSL or GEOSTAT already
  converted), a GEOSTAT CSV (GRD_ID like CRS3035RES1000mN2684000E4334000 and
  TOT_P; needs pyproj), or a GHS-POP GeoTIFF (needs rasterio). kind: csv |
  geostat | geotiff, guessed from the file when None.
  """
  kind = kind or ('geotiff' if path.lower().endswith(('.tif', '.tiff')) else 'csv')
  if kind == 'geotiff':
    df = _read_geotiff(path)
  else:
    raw = pd.read_csv(path)
    cols = {c.lower(): c for c in raw.columns}
    if kind == 'geostat' or ('grd_id' in cols and 'lat' not in cols):
      df = _geostat_to_latlon(raw, cols)
    else:
      df = pd.DataFrame({'lat': raw[cols['lat']].astype(float), 'lon': raw[cols['lon']].astype(float),
                         'pop': raw[cols['pop'] if 'pop' in cols else cols['tot_p']].astype(float)})
  df = df[(df['pop'] > 0) & (df.lat >= region['lat0']) & (df.lat <= region['lat1'])
          & (df.lon >= region['lon0']) & (df.lon <= region['lon1'])]
  dlat = cell_km / 110.574
  dlon = cell_km / (111.320 * math.cos(math.radians(0.5 * (region['lat0'] + region['lat1']))))
  i = np.floor((df.lat - region['lat0']) / dlat).astype(int)
  j = np.floor((df.lon - region['lon0']) / dlon).astype(int)
  g = df.assign(i=i, j=j).groupby(['i', 'j']).agg(pop=('pop', 'sum'))
  g = g.reset_index()
  g['lat'] = region['lat0'] + (g.i + 0.5) * dlat
  g['lon'] = region['lon0'] + (g.j + 0.5) * dlon
  return g[['lat', 'lon', 'pop']].reset_index(drop=True)


def _geostat_to_latlon(raw, cols):
  try:
    from pyproj import Transformer
  except ImportError:
    raise SystemExit('GEOSTAT grid ids need pyproj (pip install pyproj), or convert to a lat,lon,pop CSV first')
  ids = raw[cols['grd_id']].astype(str)
  n = ids.str.extract(r'N(\d+)E')[0].astype(float)
  e = ids.str.extract(r'E(\d+)$')[0].astype(float)
  res = ids.str.extract(r'RES(\d+)m')[0].astype(float)
  tr = Transformer.from_crs('EPSG:3035', 'EPSG:4326', always_xy=True)
  lon, lat = tr.transform((e + res / 2).to_numpy(), (n + res / 2).to_numpy())
  return pd.DataFrame({'lat': lat, 'lon': lon, 'pop': raw[cols['tot_p']].astype(float)})


def _read_geotiff(path):
  try:
    import rasterio
    from rasterio.warp import transform
  except ImportError:
    raise SystemExit('GeoTIFF needs rasterio (pip install rasterio), or convert to a lat,lon,pop CSV first')
  with rasterio.open(path) as ds:
    a = ds.read(1).astype(float)
    a[a == ds.nodata] = 0.0
    rows, cols = np.nonzero(a > 0)
    xs, ys = rasterio.transform.xy(ds.transform, rows, cols)
    lon, lat = transform(ds.crs, 'EPSG:4326', list(xs), list(ys))
  return pd.DataFrame({'lat': lat, 'lon': lon, 'pop': a[rows, cols]})


def release_hours_from_drift(path, controller='slow'):
  """{flight_id: release_h} from a results/drift_<year>.csv (hindsight 'last' release of run_drift.py)."""
  if not path or not os.path.exists(path):
    return {}
  d = pd.read_csv(path)
  d = d[d.controller == controller]
  out = {}
  for r in d.itertuples():
    fid = f'{r.site}_{r.start}_{r.seed}'
    out[fid] = float(r.release_h) if r.recovered and not pd.isna(r.release_h) else None
  return out


def release_hours_from_csv(path):
  """{flight: release_h} from a two-column CSV (flight, release_h), e.g. a causal rule's output."""
  if not path:
    return {}
  d = pd.read_csv(path)
  return {str(f): (None if pd.isna(h) else float(h)) for f, h in zip(d.flight, d.release_h)}

"""Synthetic inputs for the replay-based tests: tracks in track_slow.py's layout, a population CSV."""
import datetime as dt
import math
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run_drift import LAUNCH, REGION  # noqa: E402

SITES = dict(LAUNCH)


def hours_since_jan1(year, month, day, hour=6):
  return (dt.datetime(year, month, day, hour) - dt.datetime(year, 1, 1)).total_seconds() / 3600.0


def synthetic_tracks(path, year=2025, speed_kmh=None, sites=None, days=(1, 15), seed=0):
  """Straight eastward drift from each site at a seasonal speed until the region's east edge.

  speed_kmh(month) -> km/h; default: 60 km/h in winter down to 15 km/h in summer, so
  winter dwell is short like the real runs. Rows: flight, site, start, seed, step, h, hours, lat, lon, pa.
  """
  rng = np.random.default_rng(seed)
  sites = sites or SITES
  speed_kmh = speed_kmh or (lambda m: 15.0 + 45.0 * (1 + math.cos(2 * math.pi * (m - 1) / 12)) / 2)
  rows = []
  for i, (site, (la, lo)) in enumerate(sites.items()):
    for j, (m, d) in enumerate([(m, d) for m in range(1, 13) for d in days]):
      seed_ = 7919 * i + 31 * j + 1
      fid = f'{site}_{year}-{m:02d}-{d:02d}_{seed_}'
      t0 = hours_since_jan1(year, m, d)
      v = speed_kmh(m) * (0.8 + 0.4 * rng.random())
      lat, lon, h = la, lo, 0
      while REGION['lon0'] <= lon <= REGION['lon1'] and REGION['lat0'] <= lat <= REGION['lat1'] and h <= 30 * 24:
        rows.append(dict(flight=fid, site=site, start=f'{year}-{m:02d}-{d:02d}', seed=seed_, step=h * 20, h=h,
                         hours=t0 + h, lat=round(lat, 4), lon=round(lon, 4), pa=6000.0))
        lon += v / (111.32 * math.cos(math.radians(lat)))
        lat += 0.02 * math.sin(h / 10.0)
        h += 1
  df = pd.DataFrame(rows)
  df.to_csv(path, index=False)
  return df


def synthetic_population(path, cell_km=25.0, seed=0, cities=None):
  """Cells over the region: a low rural floor plus Gaussian cities. Columns lat, lon, pop."""
  rng = np.random.default_rng(seed)
  cities = cities or {'Paris': (48.9, 2.3, 12e6), 'Madrid': (40.4, -3.7, 6e6), 'Berlin': (52.5, 13.4, 4e6),
                      'Rome': (41.9, 12.5, 4e6), 'Warsaw': (52.2, 21.0, 3e6), 'Kyiv': (50.4, 30.5, 3e6),
                      'Istanbul': (41.0, 29.0, 15e6), 'Vienna': (48.2, 16.4, 2.5e6), 'Lisbon': (38.7, -9.1, 2.8e6)}
  dlat = cell_km / 110.574
  lats = np.arange(REGION['lat0'] + dlat / 2, REGION['lat1'], dlat)
  rows = []
  for la in lats:
    dlon = cell_km / (111.32 * math.cos(math.radians(la)))
    for lo in np.arange(REGION['lon0'] + dlon / 2, REGION['lon1'], dlon):
      p = 30.0 * cell_km ** 2 * rng.random()  # rural floor, ~0-30 people per km^2
      for _, (cla, clo, cpop) in cities.items():
        dx = (lo - clo) * 111.32 * math.cos(math.radians(la)); dy = (la - cla) * 110.574
        p += cpop * math.exp(-(dx * dx + dy * dy) / (2 * 40.0 ** 2)) * cell_km ** 2 / (2 * math.pi * 40.0 ** 2)
      rows.append(dict(lat=round(la, 4), lon=round(lo, 4), pop=round(p, 1)))
  df = pd.DataFrame(rows)
  df.to_csv(path, index=False)
  return df

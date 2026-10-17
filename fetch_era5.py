"""Fetch ERA5 pressure-level winds and write them in the WindGrid npz layout.

Rerun 1 of results/mitigation_research.md: replace the single-year GFS and
NCEP files with ERA5, several years, full column where the descent needs it,
and a band to the pole where the hemispheric runs need it.

Two products, one file per year each:

  band    25-90N, all longitudes (ring), 150/100/70/50/30 hPa, 6-hourly.
          For run_multipass.py, run_ship.py and the border-crossing sizing
          (W6, W20). Replaces data/ncep_band_2025.npz.
  europe  25-72N, 20W-60E, 15 levels 1000-30 hPa, 6-hourly. For jet_test.py,
          forecast_release.py, glide.py and the descent-wind work (W7, W10),
          and, through the upper levels, for run_drift.py and run_coverage.py.
          Replaces data/ncep_europe_full_2025.npz; an upper-only copy
          (150-30 hPa) is written alongside, as subset_ncep_full.py did.

Why not 0.25 degrees everywhere: ERA5 at 0.25 deg, hourly, full column, for
one year over the band is about 35 billion values per wind component. The
grids below are what a laptop can hold and what the controllers can use; the
0.25 deg descent study for W10 is a separate one-winter, one-region pull
(--grid 0.25 --years 2024 --area 60,-15,40,20 --product europe).

Volume per year at the defaults (float32, two components):
  band   1.0 deg: 66 x 360 x 5 x 1460  ->  about 1.4 GB   (2.5 deg: 0.22 GB)
  europe 1.0 deg: 48 x 81 x 15 x 1460 ->  about 0.7 GB

Needs: a CDS account and ~/.cdsapirc (https://cds.climate.copernicus.eu/how-to-api),
pip install cdsapi xarray netCDF4. Downloads are queued by CDS; a year of one
product takes minutes to hours depending on the queue.

Usage:
  python fetch_era5.py --product band   --years 2010-2025 --grid 1.0
  python fetch_era5.py --product europe --years 2010-2025 --grid 1.0
  python fetch_era5.py --product europe --years 2024 --grid 0.25 --area 60,-15,40,20 --tag w10
Outputs: data/era5_<product>[_<tag>]_<year>.npz (and _upper_ for europe), each
with t0 set to 1 January of its year so europe_ble.WindGrid can place dates.
"""
import argparse
import os
import sys

import numpy as np

UPPER = [150, 100, 70, 50, 30]
FULL = [1000, 925, 850, 700, 600, 500, 400, 300, 250, 200, 150, 100, 70, 50, 30]
PRODUCTS = {
    # area is N, W, S, E as CDS wants it
    'band': dict(area=(90, -180, 25, 180), levels=UPPER, ring=True),
    'europe': dict(area=(72, -20, 25, 60), levels=FULL, ring=False),
}


def parse_years(s):
  out = []
  for part in s.split(','):
    if '-' in part:
      a, b = part.split('-')
      out += list(range(int(a), int(b) + 1))
    else:
      out.append(int(part))
  return out


def download(year, product, grid, area, out_nc, dt_h, months=range(1, 13)):
  import cdsapi
  levels = PRODUCTS[product]['levels']
  times = [f'{h:02d}:00' for h in range(0, 24, dt_h)]
  req = {
      'product_type': ['reanalysis'],
      'variable': ['u_component_of_wind', 'v_component_of_wind'],
      'pressure_level': [str(p) for p in levels],
      'year': [str(year)],
      'month': [f'{m:02d}' for m in months],
      'day': [f'{d:02d}' for d in range(1, 32)],
      'time': times,
      'area': list(area),
      'grid': [grid, grid],
      'data_format': 'netcdf',
      'download_format': 'unarchived',
  }
  print(f'CDS request {product} {year} grid {grid} area {area} -> {out_nc}', flush=True)
  cdsapi.Client().retrieve('reanalysis-era5-pressure-levels', req, out_nc)


def convert(nc, product, year, tag, dt_h, ring):
  import xarray as xr
  # nc is one file or a list of monthly files (CDS caps the size of one request)
  ds = (xr.open_dataset(nc) if isinstance(nc, str)
        else xr.concat([xr.open_dataset(f) for f in nc], dim='valid_time'
                       if 'valid_time' in xr.open_dataset(nc[0]).dims else 'time'))
  # CDS netCDF naming has changed over the years; accept both.
  tname = 'valid_time' if 'valid_time' in ds.dims else 'time'
  lname = 'pressure_level' if 'pressure_level' in ds.dims else 'level'
  u = ds['u'].rename({tname: 'time', lname: 'level'})
  v = ds['v'].rename({tname: 'time', lname: 'level'})
  u = u.sortby('latitude').sortby('level', ascending=False)
  v = v.sortby('latitude').sortby('level', ascending=False)
  if ring:
    # WindGrid wants longitudes increasing from lons[0] over a full ring; drop
    # a duplicated +180 column if CDS returned one.
    lons = u.longitude.values
    if lons[-1] - lons[0] >= 360.0 - 1e-6:
      u, v = u.isel(longitude=slice(0, -1)), v.isel(longitude=slice(0, -1))
  lats = u.latitude.values.astype(np.float64)
  lons = u.longitude.values.astype(np.float64)
  t = u.time.values
  t0 = str(np.datetime64(t[0], 'h'))
  step_h = float((t[1] - t[0]) / np.timedelta64(1, 'h'))
  if abs(step_h - dt_h) > 1e-6:
    sys.exit(f'time step in file is {step_h} h, expected {dt_h}')
  base = f'data/era5_{product}{"_" + tag if tag else ""}'
  sets = [(f'{base}_{year}.npz', list(u.level.values))]
  if product == 'europe':
    sets.append((f'{base}_upper_{year}.npz', UPPER))
  for path, levels in sets:
    uu = u.sel(level=levels).transpose('latitude', 'longitude', 'level', 'time').values.astype(np.float32)
    vv = v.sel(level=levels).transpose('latitude', 'longitude', 'level', 'time').values.astype(np.float32)
    np.savez_compressed(path, u=uu, v=vv, lats=lats, lons=lons,
                        levels_hpa=np.array(levels, dtype=np.float64),
                        dt_h=float(dt_h), t0=t0, ring=bool(ring))
    print(f'wrote {path} u{uu.shape} t0={t0} dt_h={dt_h} ring={ring} '
          f'nan={np.isnan(uu).mean():.4f}', flush=True)


def main():
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument('--product', choices=PRODUCTS, required=True)
  ap.add_argument('--years', required=True, help='e.g. 2010-2025 or 2019,2024')
  ap.add_argument('--grid', type=float, default=1.0, help='degrees (0.25, 0.5, 1.0, 2.5)')
  ap.add_argument('--dt-h', type=int, default=6, help='hours between samples (1, 3, 6)')
  ap.add_argument('--area', help='override N,W,S,E, e.g. 60,-15,40,20')
  ap.add_argument('--tag', default='', help='suffix for an override pull, e.g. w10')
  ap.add_argument('--keep-nc', action='store_true', help='keep the netCDF after conversion')
  ap.add_argument('--convert-only', action='store_true', help='skip the download; convert data/*.nc already present')
  a = ap.parse_args()
  spec = PRODUCTS[a.product]
  area = tuple(float(x) for x in a.area.split(',')) if a.area else spec['area']
  ring = spec['ring'] and not a.area
  os.makedirs('data', exist_ok=True)
  for year in parse_years(a.years):
    stem = f'data/era5_{a.product}{"_" + a.tag if a.tag else ""}_{year}'
    # One request per month: CDS refuses a year of 15 levels in one go
    # ("cost limits exceeded"). Each month is skipped if already downloaded.
    ncs = []
    for m in range(1, 13):
      nc = f'{stem}_{m:02d}.nc'
      ncs.append(nc)
      if a.convert_only or os.path.exists(nc):
        continue
      download(year, a.product, a.grid, area, nc, a.dt_h, months=[m])
    convert(ncs, a.product, year, a.tag, a.dt_h, ring)
    if not a.keep_nc:
      for nc in ncs:
        os.remove(nc)


if __name__ == '__main__':
  main()

"""Full-column NCEP/NCAR Reanalysis-1 winds over Europe for the glider jet test.

Panel review A3: the glider runs had no winds below 150 hPa and tapered the
150 hPa wind to the surface. This builds a Europe grid (25-70°N, 20°W-60°E,
2.5°, 6-hourly, 2025) with every pressure level from 1000 to 30 hPa, plus an
upper-only copy (150-30 hPa) of the same data, so the two can be compared on
identical winds.

Inputs: uwnd.2025.nc, vwnd.2025.nc from
https://downloads.psl.noaa.gov/Datasets/ncep.reanalysis/pressure/
Usage: python subset_ncep_full.py <dir with the two .nc files>
Outputs: data/ncep_europe_full_2025.npz, data/ncep_europe_upper_2025.npz
"""
import os
import sys

import numpy as np
import xarray as xr

FULL = [1000, 925, 850, 700, 600, 500, 400, 300, 250, 200, 150, 100, 70, 50, 30]
UPPER = [150, 100, 70, 50, 30]


def load(src, v):
  ds = xr.open_dataset(os.path.join(src, f'{v}.2025.nc'))
  da = ds[v].sel(level=FULL, lat=slice(70, 25)).sortby('lat')
  west = da.sel(lon=slice(340, 357.5))
  east = da.sel(lon=slice(0, 60))
  da = xr.concat([west.assign_coords(lon=west.lon - 360), east], 'lon')
  return da.transpose('lat', 'lon', 'level', 'time')


def main():
  src = sys.argv[1]
  u, v = load(src, 'uwnd'), load(src, 'vwnd')
  lats, lons = u.lat.values, u.lon.values
  for name, levels in (('full', FULL), ('upper', UPPER)):
    uu = u.sel(level=levels).values.astype(np.float32)
    vv = v.sel(level=levels).values.astype(np.float32)
    np.savez_compressed(f'data/ncep_europe_{name}_2025.npz', u=uu, v=vv, lats=lats,
                        lons=lons, levels_hpa=np.array(levels), dt_h=6.0)
    print(name, uu.shape)
  # Winter jet check at 50N 10E, January mean by level.
  j = u.sel(lat=50, lon=10, method='nearest').sel(time=slice('2025-01-01', '2025-01-31')).mean('time')
  print('Jan mean eastward wind at 50N 10E by level (hPa: m/s):',
        {int(l): round(float(x), 1) for l, x in zip(j.level.values, j.values)})


if __name__ == '__main__':
  main()

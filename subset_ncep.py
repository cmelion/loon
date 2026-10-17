"""Subset NCEP/NCAR Reanalysis-1 2025 winds to the northern mid-latitude band.

Input: uwnd.2025.nc and vwnd.2025.nc from
https://downloads.psl.noaa.gov/Datasets/ncep.reanalysis/pressure/ (2.5°, 6-hourly).
Output: data/ncep_band_2025.npz in WindGrid layout (u, v [lat, lon, level, t]),
with dt_h=6 and a full 0-357.5°E longitude ring.

Usage: python subset_ncep.py <dir containing the two .nc files>
"""
import os
import sys

import numpy as np
import xarray as xr

LEVELS = [150, 100, 70, 50, 30]  # hPa


def main():
  src = sys.argv[1]
  out = {}
  for v in ('uwnd', 'vwnd'):
    ds = xr.open_dataset(os.path.join(src, f'{v}.2025.nc'))
    da = ds[v].sel(level=LEVELS, lat=slice(70, 25)).sortby('lat')
    out[v] = da.transpose('lat', 'lon', 'level', 'time').values.astype(np.float32)
    lats, lons = da.lat.values, da.lon.values
    t0 = str(da.time.values[0])[:13]
    print(v, out[v].shape, t0, str(da.time.values[-1])[:13])
  np.savez_compressed('data/ncep_band_2025.npz', u=out['uwnd'], v=out['vwnd'],
                      lats=lats, lons=lons, levels_hpa=np.array(LEVELS),
                      dt_h=6.0, t0=t0, ring=True)


if __name__ == '__main__':
  main()

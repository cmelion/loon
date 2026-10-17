"""Sanity check for a wind file: the January box-mean eastward wind by level.

A single grid point can miss the jet in a month when the core sat north or
south of it. The box mean cannot. Over 30-60N, 0-20E in January the mean
eastward wind should rise from a few m/s near the surface to a peak of about
15-30 m/s near 200-300 hPa, with the core nearer 35-45N than 50N, and fall
again above 100 hPa. No peak at any latitude in the band means the level
axis, the components or the sign are wrong; a weak peak is the month.

usage: python profile_check.py data/era5_europe_2025.npz [--months 1] [--box 30,60,0,20]
Works on any WindGrid npz (GFS, NCEP, ERA5); the levels it reports are the
levels the file has.
"""
import argparse

import numpy as np


def main():
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument('npz')
  ap.add_argument('--months', default='1')
  ap.add_argument('--box', default='30,60,0,20', help='lat0,lat1,lon0,lon1')
  a = ap.parse_args()
  d = np.load(a.npz)
  lats, lons, lev = d['lats'], d['lons'], d['levels_hpa']
  dt_h = float(d['dt_h']) if 'dt_h' in d else 1.0
  t0 = np.datetime64(str(d['t0']) if 't0' in d else '2025-01-01T00', 'h')
  nt = d['u'].shape[-1]
  times = t0 + (np.arange(nt) * dt_h).astype('timedelta64[h]')
  mon = times.astype('datetime64[M]').astype(int) % 12 + 1
  it = np.where(np.isin(mon, [int(m) for m in a.months.split(',')]))[0]
  la0, la1, lo0, lo1 = (float(x) for x in a.box.split(','))
  lon_ring = (lons + 180) % 360 - 180
  ia = np.where((lats >= la0) & (lats <= la1))[0]
  ib = np.where((lon_ring >= lo0) & (lon_ring <= lo1))[0]
  if not (len(it) and len(ia) and len(ib)):
    raise SystemExit(f'empty selection: times {len(it)} lats {len(ia)} lons {len(ib)}')
  u = d['u'][np.ix_(ia, ib)][..., it]            # [lat, lon, level, t]
  v = d['v'][np.ix_(ia, ib)][..., it]
  ubar = np.nanmean(u, axis=(0, 1, 3))            # by level
  vbar = np.nanmean(v, axis=(0, 1, 3))
  zonal = np.nanmean(u, axis=(1, 3))              # [lat, level]
  print(f'{a.npz}: months {a.months}, box lat {la0}-{la1} lon {lo0}-{lo1}, {len(it)} steps, '
        f'{len(ia)}x{len(ib)} points, t0 {t0}')
  print(f'{"hPa":>6} {"mean u":>8} {"mean v":>8} {"lat of max u":>13} {"max u":>7}')
  for k in np.argsort(-lev):
    j = int(np.nanargmax(zonal[:, k]))
    print(f'{int(lev[k]):>6} {ubar[k]:>8.1f} {vbar[k]:>8.1f} {lats[ia[j]]:>13.1f} {zonal[j, k]:>7.1f}')
  k = int(np.nanargmax(ubar))
  print(f'peak of the box-mean eastward wind: {ubar[k]:.1f} m/s at {int(lev[k])} hPa')
  trop = np.where((lev >= 100) & (lev <= 500))[0]
  if len(trop):
    kt = trop[int(np.nanargmax(ubar[trop]))]
    jt = int(np.nanargmax(zonal[:, kt]))
    print(f'tropospheric jet (500-100 hPa): box mean {ubar[kt]:.1f} m/s at {int(lev[kt])} hPa; '
          f'core {zonal[jt, kt]:.1f} m/s at {lats[ia[jt]]:.1f}N')


if __name__ == '__main__':
  main()

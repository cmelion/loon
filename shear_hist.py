"""Rerun 2 (W1): is there anything to steer with in a mid-latitude winter?

For every grid point in a latitude band and every time step in the chosen
months, take the wind profile over the stratospheric levels a balloon can
reach (default 150-30 hPa) and compute:

  spread_deg  the largest angle between wind directions at any two levels in
              the profile (0 = every level blows the same way, 180 = some
              level blows back). A balloon steers by choosing a level; if the
              spread is small there is nothing to choose.
  slowest_ms  the smallest wind speed in the profile: how slowly a balloon
              that picks the best level is carried.
  best_u_ms   the eastward component at that slowest level, signed.

and from the slowest-level speed, an upper bound on dwell for a perfect
controller: a balloon that always sits at the slowest level crosses a region
of the given east-west width in width / mean(slowest speed). Real controllers
do worse (they cannot change level instantly, the forecast is wrong, and the
slowest level drifts north or south out of the band), so this is the ceiling
W1 asks for, not a prediction.

Works on any WindGrid npz (data/gfs_europe_2025.npz, data/ncep_band_2025.npz,
data/era5_band_<year>.npz, data/era5_europe_upper_<year>.npz).

Usage:
  python shear_hist.py data/era5_band_2019.npz [--months 12,1,2] [--lat 45,55]
                       [--lon -10,40] [--levels 150,30] [--width-km 3000]
                       [--tag era5_2019]
Outputs: results/shear_<tag>.csv (histograms) and a printed summary. Run it
once per year and compare the summaries; the histograms are what the article
should show instead of "winter westerlies leave nothing to steer with".
"""
import argparse
import csv
import os

import numpy as np


def profile_stats(u, v):
  """u, v: [..., level] -> spread_deg, slowest_ms, best_u_ms over the level axis."""
  ang = np.arctan2(v, u)                                    # radians, math convention
  d = np.abs(ang[..., :, None] - ang[..., None, :])          # pairwise over levels
  d = np.minimum(d, 2 * np.pi - d)
  spread = np.degrees(np.nanmax(d, axis=(-2, -1)))
  speed = np.hypot(u, v)
  k = np.nanargmin(np.where(np.isnan(speed), np.inf, speed), axis=-1)
  slowest = np.take_along_axis(speed, k[..., None], axis=-1)[..., 0]
  best_u = np.take_along_axis(u, k[..., None], axis=-1)[..., 0]
  return spread, slowest, best_u


def main():
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument('npz')
  ap.add_argument('--months', default='12,1,2')
  ap.add_argument('--lat', default='45,55')
  ap.add_argument('--lon', default='-10,40')
  ap.add_argument('--levels', default='150,30', help='pressure range hPa, high to low')
  ap.add_argument('--width-km', type=float, default=3000.0, help='east-west width of the region for the dwell bound')
  ap.add_argument('--tag', default=None)
  a = ap.parse_args()
  d = np.load(a.npz)
  lats, lons, lev = d['lats'], d['lons'], d['levels_hpa']
  dt_h = float(d['dt_h']) if 'dt_h' in d else 1.0
  t0 = np.datetime64(str(d['t0']) if 't0' in d else '2025-01-01T00', 'h')
  months = [int(m) for m in a.months.split(',')]
  la0, la1 = (float(x) for x in a.lat.split(','))
  lo0, lo1 = (float(x) for x in a.lon.split(','))
  p0, p1 = (float(x) for x in a.levels.split(','))
  nt = d['u'].shape[-1]
  times = t0 + (np.arange(nt) * dt_h).astype('timedelta64[h]')
  mon = times.astype('datetime64[M]').astype(int) % 12 + 1
  it = np.where(np.isin(mon, months))[0]
  ia = np.where((lats >= la0) & (lats <= la1))[0]
  lon_ring = (lons + 180) % 360 - 180
  ib = np.where((lon_ring >= lo0) & (lon_ring <= lo1))[0]
  ip = np.where((lev <= p0) & (lev >= p1))[0]
  if not (len(it) and len(ia) and len(ib) and len(ip)):
    raise SystemExit(f'empty selection: times {len(it)} lats {len(ia)} lons {len(ib)} levels {len(ip)}')
  u = d['u'][np.ix_(ia, ib, ip, it)].transpose(0, 1, 3, 2)  # [lat, lon, t, level]
  v = d['v'][np.ix_(ia, ib, ip, it)].transpose(0, 1, 3, 2)
  spread, slowest, best_u = profile_stats(u, v)
  tag = a.tag or os.path.splitext(os.path.basename(a.npz))[0]
  os.makedirs('results', exist_ok=True)
  sb = np.arange(0, 181, 15); vb = np.arange(0, 61, 5)
  hs, _ = np.histogram(spread[~np.isnan(spread)], sb)
  hv, _ = np.histogram(np.clip(slowest[~np.isnan(slowest)], 0, 59.99), vb)
  rows = [dict(kind='spread_deg', lo=sb[i], hi=sb[i + 1], count=int(hs[i]), share=hs[i] / hs.sum()) for i in range(len(hs))]
  rows += [dict(kind='slowest_ms', lo=vb[i], hi=vb[i + 1], count=int(hv[i]), share=hv[i] / hv.sum()) for i in range(len(hv))]
  with open(f'results/shear_{tag}.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
  s = np.nanmean(slowest); e = np.nanmean(np.maximum(best_u, 0))
  east_share = np.nanmean(best_u > 0)
  print(f'{tag}: months {months}, lat {la0}-{la1}, lon {lo0}-{lo1}, levels {lev[ip].astype(int).tolist()} hPa, '
        f'{len(it)} steps x {len(ia)}x{len(ib)} points')
  print(f'  direction spread across levels: median {np.nanmedian(spread):.0f} deg, '
        f'share below 30 deg {np.nanmean(spread < 30):.2f}, share above 90 deg {np.nanmean(spread > 90):.2f}')
  print(f'  slowest level: median {np.nanmedian(slowest):.1f} m/s, p10 {np.nanpercentile(slowest, 10):.1f}, '
        f'p90 {np.nanpercentile(slowest, 90):.1f}; it blows eastward {east_share:.2f} of the time')
  print(f'  perfect-controller crossing of {a.width_km:.0f} km at the mean slowest speed: '
        f'{a.width_km * 1e3 / (s * 86400):.1f} days (eastward component only: '
        f'{a.width_km * 1e3 / max(e, 1e-6) / 86400:.1f} days)')
  print(f'  wrote results/shear_{tag}.csv')


if __name__ == '__main__':
  main()

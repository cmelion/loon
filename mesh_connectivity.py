"""Rerun 7 (W15): mesh connectivity on the replayed tracks, 500 and 700 km links, gateways.

results/target_population.md section F sized the laser mesh for balloons
placed at random. This replays a standing layer (replay.py: launches at the
rate that holds N aloft each month, each flying a stored track of its site
and season) and, every --every-h hours, builds the graph:

  nodes   balloons aloft, plus gateway sites (default: the 21 recovery
          stations of run_drift.py; or --gateways name,lat,lon CSV; or
          --gateway-grid-km for a regular grid over the region's land box).
  edges   balloon-balloon at 500 and at 700 km great-circle (results/
          radio_and_backhaul.md: optical links clear the lower atmosphere at
          those ranges), balloon-gateway within --gateway-km (200 km ground
          radius, the runbook's figure; 194 km is the 5 deg elevation ring).

and reports, by month and by standing-layer size (25, 50, 100):
  aloft_mean               balloons aloft
  gw_connected_share       share of balloons with any path to a gateway
  largest_component_share  largest balloon-only connected component / aloft
  over_4_hops_share        balloons whose shortest path to a gateway is more
                           than four hops (or none at all)
  isolated_share           balloons with no neighbour in range
  mean_degree              balloon neighbours in range, mean

Weather-correlated gateway loss: --storm-box lat0,lat1,lon0,lon1 removes every
gateway inside the box (default 44-56 N, 12 W-8 E: an Atlantic low over the
western facade) and the same hours are evaluated again, so each row comes
twice, gateways=all and gateways=storm. Routing capacity, acquisition time
and the terminal count per balloon (mesh degree equals terminals carried) are
not modelled; this is the geometry only.

Usage:
  python mesh_connectivity.py --tracks results/slow_tracks.csv --standing 25,50,100 --every-h 6
  python mesh_connectivity.py --tracks results/slow_tracks_2019.csv --standing 50 --gateway-grid-km 350
Outputs: results/mesh_<tag>.csv (tag = year and standing sizes unless --tag). Nothing needs BLE.
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, shortest_path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import replay as rp  # noqa: E402

RANGES_KM = (500.0, 700.0)
MAX_HOPS = 4


def gateway_grid(spacing_km, region=rp.REGION):
  dlat = spacing_km / 110.574
  out = {}
  lat = region['lat0'] + dlat / 2
  k = 0
  while lat < region['lat1']:
    dlon = spacing_km / (111.320 * np.cos(np.radians(lat)))
    lon = region['lon0'] + dlon / 2
    while lon < region['lon1']:
      out[f'g{k}'] = (round(lat, 3), round(lon, 3)); k += 1
      lon += dlon
    lat += dlat
  return out


def hour_metrics(blat, blon, gw_xyz, range_km, gateway_km):
  n = len(blat)
  if n == 0:
    return dict(aloft=0, gw_connected_share=np.nan, largest_component_share=np.nan,
                over_4_hops_share=np.nan, isolated_share=np.nan, mean_degree=np.nan)
  bx = rp.xyz(blat, blon)
  d = np.linalg.norm(bx[:, None, :] - bx[None, :, :], axis=-1)
  adj = (d <= rp.chord(range_km)) & ~np.eye(n, dtype=bool)
  deg = adj.sum(1)
  _, labels = connected_components(coo_matrix(adj), directed=False)
  largest = np.bincount(labels).max() / n
  g = len(gw_xyz)
  if g:
    dg = np.linalg.norm(bx[:, None, :] - gw_xyz[None, :, :], axis=-1) <= rp.chord(gateway_km)
    big = np.zeros((n + g, n + g), bool)
    big[:n, :n] = adj
    big[:n, n:] = dg; big[n:, :n] = dg.T
    hops = shortest_path(coo_matrix(big), method='D', unweighted=True, indices=np.arange(n, n + g))
    hmin = hops.min(0)[:n] if g else np.full(n, np.inf)
  else:
    hmin = np.full(n, np.inf)
  return dict(aloft=n, gw_connected_share=float(np.isfinite(hmin).mean()),
              largest_component_share=float(largest),
              over_4_hops_share=float((hmin > MAX_HOPS).mean()),  # inf counts as over
              isolated_share=float((deg == 0).mean()), mean_degree=float(deg.mean()))


def run(tracks, standing_sizes, hours, gateways, storm_box, ranges, gateway_km, rng, window_h, sites):
  gnames = list(gateways)
  g_lat = np.array([gateways[k][0] for k in gnames]); g_lon = np.array([gateways[k][1] for k in gnames])
  gw_all = rp.xyz(g_lat, g_lon)
  if storm_box:
    la0, la1, lo0, lo1 = storm_box
    keep = ~((g_lat >= la0) & (g_lat <= la1) & (g_lon >= lo0) & (g_lon <= lo1))
    gw_storm = gw_all[keep]
  cases = {'all': gw_all}
  if storm_box:
    cases['storm'] = gw_storm
  months = rp.hours_to_month(hours, tracks.year)
  recs = []
  for N in standing_sizes:
    L = rp.standing_launches(tracks, N, -tracks.period_h / 12, tracks.period_h, rng, sites, window_h, service=False)
    R = rp.Replay(tracks, L)
    for t, m in zip(hours, months):
      lat, lon, _, _ = R.aloft(t)
      for r in ranges:
        for case, gw in cases.items():
          recs.append(dict(standing=N, range_km=r, gateways=case, month=int(m),
                           **hour_metrics(lat, lon, gw, r, gateway_km)))
  d = pd.DataFrame(recs)
  rows = []
  cols = ['gw_connected_share', 'largest_component_share', 'over_4_hops_share', 'isolated_share', 'mean_degree']
  for (N, r, case), g in d.groupby(['standing', 'range_km', 'gateways']):
    periods = {str(m): g[g.month == m] for m in range(1, 13)}
    periods.update({'DJF': g[g.month.isin((12, 1, 2))], 'JJA': g[g.month.isin((6, 7, 8))], 'year': g})
    for p, gg in periods.items():
      if not len(gg):
        continue
      row = dict(standing=N, range_km=r, gateways=case, period=p, hours=len(gg), aloft_mean=gg.aloft.mean())
      row.update({c: gg[c].mean() for c in cols})
      rows.append(row)
  return pd.DataFrame(rows), len(gnames), (len(gw_storm) if storm_box else len(gnames))


def main(argv=None):
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument('--tracks', required=True, help='track CSV(s) from track_slow.py, comma-separated')
  ap.add_argument('--standing', default='25,50,100', help='standing-layer sizes')
  ap.add_argument('--ranges-km', default='500,700')
  ap.add_argument('--gateway-km', type=float, default=200.0)
  ap.add_argument('--gateways', help='CSV name,lat,lon (default: the 21 recovery stations)')
  ap.add_argument('--gateway-grid-km', type=float, help='instead: a regular grid at this spacing over the region box')
  ap.add_argument('--storm-box', default='44,56,-12,8', help='lat0,lat1,lon0,lon1; "" for no storm case')
  ap.add_argument('--sites', help='launch sites to use (default: all in the tracks)')
  ap.add_argument('--every-h', type=int, default=6)
  ap.add_argument('--window-days', type=float, default=21.0)
  ap.add_argument('--seed', type=int, default=11)
  ap.add_argument('--tag')
  a = ap.parse_args(argv)
  rng = np.random.default_rng(a.seed)
  tracks = rp.Tracks(a.tracks.split(','))
  sizes = [int(x) for x in a.standing.split(',')]
  ranges = [float(x) for x in a.ranges_km.split(',')]
  if a.gateways:
    g = pd.read_csv(a.gateways)
    gateways = {str(r.name): (float(r.lat), float(r.lon)) for r in g.itertuples()}
  elif a.gateway_grid_km:
    gateways = gateway_grid(a.gateway_grid_km)
  else:
    gateways = dict(rp.RECOVERY)
  storm = tuple(float(x) for x in a.storm_box.split(',')) if a.storm_box else None
  sites = a.sites.split(',') if a.sites else tracks.sites
  hours = np.arange(0, tracks.period_h, a.every_h, dtype=float)
  table, ng, ns = run(tracks, sizes, hours, gateways, storm, ranges, a.gateway_km, rng, a.window_days * 24, sites)
  tag = a.tag or f'{tracks.year}_standing{"_".join(str(s) for s in sizes)}'
  os.makedirs('results', exist_ok=True)
  table.to_csv(f'results/mesh_{tag}.csv', index=False)
  pd.set_option('display.width', 220)
  print(f'{len(tracks.flights)} tracks ({tracks.year}), {ng} gateways ({ns} left in the storm case), '
        f'{len(hours)} hours sampled, links {ranges} km, gateway radius {a.gateway_km:g} km')
  print(table[table.period.isin(['DJF', 'JJA', 'year'])].round(3).to_string(index=False))
  print(f'wrote results/mesh_{tag}.csv')


if __name__ == '__main__':
  main()

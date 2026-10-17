"""Glider return cases for one flight: today's glider vs the tuned design, under
wind errors (stand-in for GNSS loss / forecast error), using glide.py physics.

Reads an episode flight.json (from fly_track.py). Cases:
  A. today's release rule (last hour within 150 km) + today's glider
     (L/D 12, 16 kg/m2 -> sink 1.5 m/s, point-at-target) = run_drift's number.
  B. same release, tuned glider (L/D 14, 20 kg/m2, crab + speed-to-fly).
  C. glide_tuning's recommended release: the last flight-hour at which some
     recovery site within 500 km is reachable with margin >= 100 km (tuned
     glider, nominal winds), as in glide_tuning.releases('last', 100).
  D. Monte Carlo on B and C: wind bias of 0..5 m/s in 8 directions and surface
     taper 0.1/0.3/1.0 (glide_tuning's perturbation ranges, deterministic grid
     instead of random draws) -> fraction recovered.
Writes <episode>/glide_cases.json and prints a summary.
Usage: python scenarios/tools/glide_cases.py scenarios/ep11_headwind
"""
import json
import math
import os
import sys
import warnings

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
warnings.filterwarnings('ignore')
os.chdir(ROOT)
import numpy as np  # noqa: E402
import glide  # noqa: E402
import glide_batch as gb  # noqa: E402
from europe_ble import T0, WindGrid  # noqa: E402
from run_drift import GLIDE, RECOVERY, gc_km  # noqa: E402
import datetime as dt  # noqa: E402

TODAY = dict(ld=GLIDE['ld'], sink_sl=GLIDE['sink_sl'])            # L/D 12, 1.5 m/s (16 kg/m2)
TUNED = dict(ld=14.0, sink_sl=gb.sink_for_wing_loading(20.0, 14.0))  # L/D 14, 20 kg/m2
MARGIN_KM, RANGE_KM = 100.0, 500.0
BIASES = [0.0, 2.5, 5.0]
DIRS = 8
TAPERS = [0.1, 0.3, 1.0]


def hours_of(tstr):
  return (dt.datetime.fromisoformat(tstr) - T0).total_seconds() / 3600


def guided(grid, lat, lon, hpa, hours, site, design, bias=(0, 0), taper=0.3):
  return glide.simulate_glide_guided(lat, lon, hpa * 100, hours, grid, RECOVERY[site],
                                     guidance='crab', stf=True, bias=bias, taper=taper, **design)


def mc(grid, lat, lon, hpa, hours, site, design):
  n = ok = 0
  worst = None
  for b in BIASES:
    for k in range(DIRS if b else 1):
      ang = 2 * math.pi * k / DIRS
      for tp in TAPERS:
        r = guided(grid, lat, lon, hpa, hours, site, design, (b * math.sin(ang), b * math.cos(ang)), tp)
        n += 1; ok += r['reached']
        if worst is None or r['dist_to_target_end_km'] > worst['miss_km']:
          worst = dict(bias_ms=b, bias_dir_deg=round(math.degrees(ang)), taper=tp,
                       miss_km=round(r['dist_to_target_end_km'], 1))
  return dict(n=n, recovered=ok, frac=round(ok / n, 3), worst=worst)


def main():
  ep = sys.argv[1]
  d = json.load(open(os.path.join(ep, 'flight.json')))
  grid = WindGrid(d.get('grid', 'data/gfs_europe_2025.npz'))
  out = dict(script='scenarios/tools/glide_cases.py (glide.py physics; designs/policy from glide_tuning.py)',
             today_design=TODAY, tuned_design=dict(TUNED, wing_kg_m2=20.0),
             margin_km=MARGIN_KM, range_km=RANGE_KM)
  rel = d['release']
  if rel:
    h = hours_of(rel['time'])
    a = glide.simulate_glide(rel['lat'], rel['lon'], rel['hpa'] * 100, h, grid,
                             target=RECOVERY[rel['site']], **TODAY)
    out['A_today_rule_today_glider'] = dict(site=rel['site'], release_h=rel['h'],
                                            miss_km=round(a['dist_to_target_end_km'], 1),
                                            duration_h=round(a['duration_s'] / 3600, 2),
                                            recovered=a['reached'])
    b = guided(grid, rel['lat'], rel['lon'], rel['hpa'], h, rel['site'], TUNED)
    out['B_today_rule_tuned_glider'] = dict(site=rel['site'], release_h=rel['h'],
                                            miss_km=round(b['dist_to_target_end_km'], 1),
                                            margin_km=round(b['margin_km'], 1),
                                            duration_h=round(b['duration_s'] / 3600, 2),
                                            recovered=b['reached'],
                                            mc=mc(grid, rel['lat'], rel['lon'], rel['hpa'], h, rel['site'], TUNED))
  # C: last hour with margin >= MARGIN to any site within RANGE (tuned glider)
  best_rows = []
  for r in d['track'][1:]:
    h = hours_of(r['t'])
    cands = [(s, gc_km((r['lat'], r['lon']), ll)) for s, ll in RECOVERY.items()]
    cands = [(s, km) for s, km in cands if km <= RANGE_KM]
    best = None
    for s, km in cands:
      g = guided(grid, r['lat'], r['lon'], r['hpa'], h, s, TUNED)
      if best is None or g['margin_km'] > best[1]:
        best = (s, g['margin_km'], km, g)
    if best:
      best_rows.append(dict(h=r['h'], t=r['t'], lat=r['lat'], lon=r['lon'], hpa=r['hpa'],
                            site=best[0], margin_km=round(best[1], 1), dist_km=round(best[2], 1),
                            miss_km=round(best[3]['dist_to_target_end_km'], 1),
                            duration_h=round(best[3]['duration_s'] / 3600, 2)))
  out['reachability_by_hour'] = best_rows
  ok = [x for x in best_rows if x['margin_km'] >= MARGIN_KM]
  if ok:
    c = ok[-1]
    h = hours_of(c['t'])
    out['C_tuned_rule_tuned_glider'] = dict(
        c, mc=mc(grid, c['lat'], c['lon'], c['hpa'], h, c['site'], TUNED),
        coverage_lost_h=round(d['summary']['flight_h'] - c['h'] - c['duration_h'], 1))
  else:
    out['C_tuned_rule_tuned_glider'] = None
  with open(os.path.join(ep, 'glide_cases.json'), 'w') as f:
    json.dump(out, f, indent=1)
  show = {k: v for k, v in out.items() if k != 'reachability_by_hour'}
  print(json.dumps(show, indent=1))
  print('\nreachability by hour (site / margin km / dist km):')
  for x in best_rows:
    print(f"  h={x['h']:6.1f} {x['site']:>10} margin={x['margin_km']:7.1f} dist={x['dist_km']:6.1f} miss={x['miss_km']:6.1f}")


if __name__ == '__main__':
  main()

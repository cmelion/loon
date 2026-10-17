"""Ship launches in the Atlantic vs land sites, on the same NOAA winds.

The Europe GFS grid stops at 15°W, so both sets run on the NCEP/NCAR
hemispheric band (data/ncep_band_2025.npz, 2.5°, 6-hourly) with the 'slow'
controller and run_drift.fly. Ship stations sit upwind of the region; their
flights count only time inside the region (run_drift handles the approach).

Usage: python run_ship.py
"""
import csv
import datetime as dt
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run_drift import LAUNCH  # noqa: E402

SHIPS = {'Ship 55N 20W': (55.0, -20.0), 'Ship 50N 20W': (50.0, -20.0),
         'Ship 45N 18W': (45.0, -18.0), 'Ship 40N 16W': (40.0, -16.0),
         'Ship 52N 13W': (52.0, -13.0)}


def init():
  sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
  import warnings
  warnings.filterwarnings('ignore')
  import europe_ble as eb
  import run_drift
  run_drift.fly.grid = eb.WindGrid('data/ncep_band_2025.npz')


def fly(job):
  import run_drift
  r = run_drift.fly(job)
  r['kind'] = 'ship' if r['site'].startswith('Ship') else 'land'
  return r


def main():
  starts = [dt.datetime(2025, m, d, 6, tzinfo=dt.timezone.utc)
            for m in range(1, 13) for d in (1, 15)]
  only_ships = os.environ.get('APPROACH_HOME') == '1'
  sites = list({**LAUNCH, **SHIPS}.items())
  jobs = [(n, la, lo, st, 'slow', 7919 * i + 31 * j + 1)
          for i, (n, (la, lo)) in enumerate(sites) for j, st in enumerate(starts)
          if not only_ships or n in SHIPS]
  procs = int(os.environ.get('PROCS', 4))
  t, rows = time.time(), []
  with mp.get_context('spawn').Pool(procs, initializer=init) as pool:
    for k, r in enumerate(pool.imap_unordered(fly, jobs)):
      rows.append(r)
      print(f'{k + 1}/{len(jobs)} {r["site"]:>13} {r["start"]} dwell={r["dwell_h"]:6.1f}h '
            f'{r["end"]} ({time.time() - t:.0f}s)', flush=True)
  out = 'results/ship_approach_2025.csv' if only_ships else 'results/ship_vs_land_2025.csv'
  with open(out, 'w') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


if __name__ == '__main__':
  main()

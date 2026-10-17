"""Year-round station-keeping sweep over Europe -> Black Sea with BLE.

For each station and each launch date (1st and 15th of every month, 2025)
we fly one BLE balloon for 2 days (BLE's standard 960 x 3-min steps) under
the StationSeeker controller and record TWR50: the fraction of time spent
within 50 km of the station.

Usage: python run_coverage.py [--quick]
"""
import csv
import datetime as dt
import multiprocessing as mp
import sys
import time

STATIONS = {
    'Lisbon': (38.7, -9.1), 'Madrid': (40.4, -3.7), 'Dublin': (53.3, -6.3),
    'London': (51.5, -0.1), 'Paris': (48.9, 2.3),
    # BLE's solar model asserts |lat| < 60, so Nordic sites sit at 58.5N.
    'Gothenburg': (58.5, 11.5), 'Stockholm': (58.5, 18.1),
    'Tallinn': (58.5, 24.9), 'Berlin': (52.5, 13.4),
    'Warsaw': (52.2, 21.0), 'Rome': (41.9, 12.5), 'Vienna': (48.2, 16.4),
    'Budapest': (47.5, 19.0), 'Athens': (38.0, 23.7), 'Bucharest': (44.4, 26.1),
    'Kyiv': (50.4, 30.5), 'Istanbul': (41.0, 29.0), 'Constanta': (44.2, 28.6),
    'Odesa': (46.5, 30.7), 'Sochi': (43.6, 39.7), 'Trabzon': (41.0, 39.7),
    'Black Sea (mid)': (43.2, 34.0),
}
STEPS = 960  # 2 days at 3-minute steps


def fly(job):
  name, lat, lon, start, seed = job
  import os
  sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
  import numpy as np
  from balloon_learning_environment.agents import station_seeker_agent
  from balloon_learning_environment.env.balloon import balloon, control
  from balloon_learning_environment.utils import units
  import europe_ble as eb

  grid = fly.grid if hasattr(fly, 'grid') else eb.WindGrid()
  fly.grid = grid
  arena = eb.EuropeArena(eb.EuropeWindField(grid, lat, lon), start, seed)
  agent = station_seeker_agent.StationSeekerAgent(3, None)
  obs = arena.feature_constructor.get_features()
  action = agent.begin_episode(obs)
  within, dists, status = 0, [], 'OK'
  for _ in range(STEPS):
    try:
      obs = arena.step(control.AltitudeControlCommand(action))
    except AssertionError:  # drifted past 60N, outside BLE's solar model
      status = 'PAST_60N'
      break
    s = arena.get_balloon_state()
    d = units.relative_distance(s.x, s.y).km
    dists.append(d)
    within += d <= 50.0
    if s.status != balloon.BalloonStatus.OK:
      status = s.status.name
      break
    action = agent.step(0.0, obs)
  return dict(station=name, lat=lat, lon=lon, start=start.date().isoformat(),
              month=start.month, seed=seed, twr50=within / STEPS,
              median_km=float(np.median(dists)), final_km=dists[-1],
              status=status)


def main():
  quick = '--quick' in sys.argv
  starts = [dt.datetime(2025, m, d, 6, tzinfo=dt.timezone.utc)
            for m in range(1, 13) for d in (1, 15)]
  if quick:
    starts = starts[::6]
  stations = list(STATIONS.items())[:3] if quick else STATIONS.items()
  jobs = [(n, la, lo, s, 1000 * i + j) for i, (n, (la, lo)) in
          enumerate(stations) for j, s in enumerate(starts)]
  out = 'results/coverage_quick.csv' if quick else 'results/coverage_2025.csv'
  t = time.time()
  with mp.get_context('spawn').Pool(8) as pool, open(out, 'w') as f:
    w = None
    for k, r in enumerate(pool.imap_unordered(fly, jobs)):
      if w is None:
        w = csv.DictWriter(f, fieldnames=list(r)); w.writeheader()
      w.writerow(r); f.flush()
      print(f'{k + 1}/{len(jobs)} {r["station"]:>16} {r["start"]} '
            f'TWR50={r["twr50"]:.2f} {r["status"]} ({time.time() - t:.0f}s)',
            flush=True)


if __name__ == '__main__':
  import warnings
  warnings.filterwarnings('ignore')
  main()

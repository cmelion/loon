"""Re-fly the 'slow' controller flights of run_drift.py, logging the hourly
balloon track (time, lat, lon, pressure) so release policies can be
evaluated after the fact (see glide_tuning.py).

Replicates run_drift.fly step for step (same job tuple, same seeds, same
controller) but never modifies run_drift.py. Output:
  results/slow_tracks.csv   one row per flight-hour
  results/slow_tracks_summary.csv  one row per flight (dwell_h, end), for
                                   checking against results/drift_2025.csv

Usage: python track_slow.py [--procs 2] [--limit N]
"""
import csv
import datetime as dt
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_drift as rd  # noqa: E402


def fly_track(job):
  site, lat0, lon0, start, kind, seed = job
  sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
  import warnings
  warnings.filterwarnings('ignore')
  from balloon_learning_environment.env.balloon import balloon, control, pressure_range_builder
  import europe_ble as eb

  grid = fly_track.grid if hasattr(fly_track, 'grid') else eb.WindGrid()
  fly_track.grid = grid
  wf = eb.EuropeWindField(grid, lat0, lon0)
  arena = eb.EuropeArena(wf, start, seed, feature_factory=rd.NullFeatures,
                         launch_radius_km=10.0)
  target, steps, end = None, 0, 'MAX_DAYS'
  max_steps = rd.MAX_DAYS * 24 * 60 // rd.STEP_MIN
  fid = f'{site}_{start.date().isoformat()}_{seed}'
  track = []

  def log(s):
    track.append(dict(flight=fid, site=site, start=start.date().isoformat(),
                      seed=seed, step=steps, h=steps * rd.STEP_MIN / 60,
                      hours=(s.date_time - eb.T0).total_seconds() / 3600,
                      lat=round(s.latlng.lat().degrees, 4),
                      lon=round(s.latlng.lng().degrees, 4),
                      pa=round(float(s.pressure), 1)))

  log(arena.get_balloon_state())
  while steps < max_steps:
    s = arena.get_balloon_state()
    if steps % rd.DECIDE_EVERY == 0:
      pr = pressure_range_builder.get_pressure_range(s, arena._atmosphere)
      target = rd.choose_pressure(kind, wf, s, pr, target)
    if s.pressure > target + 300:
      action = control.AltitudeControlCommand.UP
    elif s.pressure < target - 300:
      action = control.AltitudeControlCommand.DOWN
    else:
      action = control.AltitudeControlCommand.STAY
    try:
      arena.step(action)
    except AssertionError:
      end = 'EXIT_N'
      break
    steps += 1
    s = arena.get_balloon_state()
    if s.status != balloon.BalloonStatus.OK:
      end = s.status.name
      break
    lat, lon = s.latlng.lat().degrees, s.latlng.lng().degrees
    if steps % 20 == 0:
      log(s)
    if not rd.in_region(lat, lon):
      r = rd.REGION
      end = 'EXIT_' + ('W' if lon < r['lon0'] else 'E' if lon > r['lon1']
                       else 'S' if lat < r['lat0'] else 'N')
      break
  s = arena.get_balloon_state()
  summ = dict(flight=fid, site=site, start=start.date().isoformat(), seed=seed,
              dwell_h=round(steps * rd.STEP_MIN / 60, 2), end=end,
              end_lat=round(s.latlng.lat().degrees, 2),
              end_lon=round(s.latlng.lng().degrees, 2),
              end_hpa=round(s.pressure / 100, 1))
  return summ, track


def main():
  procs = int(sys.argv[sys.argv.index('--procs') + 1]) if '--procs' in sys.argv else 2
  limit = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else None
  starts = [dt.datetime(2025, m, d, 6, tzinfo=dt.timezone.utc)
            for m in range(1, 13) for d in (1, 15)]
  sites = list(rd.LAUNCH.items())
  kind = 'slow'
  jobs = [(n, la, lo, st, kind, 7919 * i + 31 * j + rd.SEED_C[kind])
          for i, (n, (la, lo)) in enumerate(sites) for j, st in enumerate(starts)]
  if limit:
    jobs = jobs[:limit]
  os.makedirs('results', exist_ok=True)
  t = time.time()
  with mp.get_context('spawn').Pool(procs) as pool, \
      open('results/slow_tracks.csv', 'w') as ft, \
      open('results/slow_tracks_summary.csv', 'w') as fs:
    wt = ws = None
    for k, (summ, track) in enumerate(pool.imap_unordered(fly_track, jobs)):
      if wt is None:
        wt = csv.DictWriter(ft, fieldnames=list(track[0])); wt.writeheader()
        ws = csv.DictWriter(fs, fieldnames=list(summ)); ws.writeheader()
      wt.writerows(track); ws.writerow(summ); ft.flush(); fs.flush()
      print(f'{k + 1}/{len(jobs)} {summ["site"]:>9} {summ["start"]} '
            f'dwell={summ["dwell_h"]:6.1f}h {summ["end"]} ({time.time() - t:.0f}s)',
            flush=True)


if __name__ == '__main__':
  main()

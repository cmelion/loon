"""Slow-traversal concept: how long can one balloon stay over the region?

Instead of station-keeping, each balloon is launched and flown until it
leaves the coverage region (Europe -> Black Sea box below), fails, or hits
MAX_DAYS. Three altitude controllers, all using the forecast winds (the
balloon flies in forecast + BLE simplex noise):
  passive : hold launch altitude (BLE STAY), a zero-effort baseline.
  slow    : every 15 min pick the reachable altitude with the lowest forecast
            wind speed ("slow the traversal").
  home    : pick the altitude whose forecast wind points most toward the
            region centre (region-scale station-keeping).
Radio recovery: every hour we note whether the balloon is within
RELEASE_KM of a recovery site (the 22 coverage stations). The radio is
released on a glider at the *last* such moment (glide.simulate_glide), so
'recover' dwell = time to that release + glide (still transmitting), versus
'full' dwell if the radio is simply flown until the balloon leaves.

Usage: python run_drift.py [--quick]
"""
import csv
import datetime as dt
import math
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REGION = dict(lat0=36.0, lat1=59.5, lon0=-10.0, lon1=42.0)  # 59.5: BLE solar limit
CENTRE = (47.5, 16.0)
LAUNCH = {'Lisbon': (38.7, -9.1), 'Brest': (48.4, -4.5), 'Dublin': (53.3, -6.3),
          'Vienna': (48.2, 16.4), 'Bucharest': (44.4, 26.1)}
from run_coverage import STATIONS
# Recovery network: the coverage stations on land (21 sites incl. Black Sea coast).
RECOVERY = {k: v for k, v in STATIONS.items() if k != 'Black Sea (mid)'}
RELEASE_KM = 150.0  # comfortably inside the ~250-400 km glide reach
GLIDE = dict(ld=12.0, sink_sl=1.5)  # small radio glider
CONTROLLERS = ('passive', 'slow', 'home')
MAX_DAYS = 30
STEP_MIN = 3
DECIDE_EVERY = 5  # steps (15 min)
PLAN_EVERY = 40  # steps (2 h) for the lookahead planner
APPROACH_HOME = os.environ.get('APPROACH_HOME') == '1'
SEED_C = {'passive': 0, 'slow': 1, 'home': 2, 'plan': 1}  # plan pairs with slow


def in_region(lat, lon):
  r = REGION
  return r['lat0'] <= lat <= r['lat1'] and r['lon0'] <= lon <= r['lon1']


def gc_km(a, b):
  la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
  h = (math.sin((la2 - la1) / 2) ** 2 +
       math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2)
  return 2 * 6371.0 * math.asin(math.sqrt(h))


class NullFeatures:
  """Skips BLE's (slow) GP feature construction; our controllers read winds."""

  def __init__(self, *unused):
    pass

  def observe(self, unused_obs):
    pass

  def get_features(self):
    return None


def choose_pressure(kind, wf, s, prange, current_target):
  import numpy as np
  from balloon_learning_environment.utils import units
  cands = np.linspace(prange.min_pressure, prange.max_pressure, 15)
  winds = wf.get_forecast_column(s.x, s.y, cands, s.time_elapsed)
  u = np.array([w.u.meters_per_second for w in winds])
  v = np.array([w.v.meters_per_second for w in winds])
  if kind == 'slow':
    score = -np.hypot(u, v)
  else:  # home: velocity component toward region centre
    lat, lon = s.latlng.lat().degrees, s.latlng.lng().degrees
    dy = CENTRE[0] - lat
    dx = (CENTRE[1] - lon) * math.cos(math.radians(lat))
    n = math.hypot(dx, dy) + 1e-9
    score = (u * dx + v * dy) / n
  best = int(np.argmax(score))
  if current_target is not None:  # 1 m/s hysteresis against dithering
    cur = int(np.argmin(abs(cands - current_target)))
    if score[best] - score[cur] < 1.0:
      return cands[cur]
  return cands[best]


def fly(job):
  site, lat0, lon0, start, kind, seed = job
  sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
  import warnings
  warnings.filterwarnings('ignore')
  from balloon_learning_environment.env.balloon import balloon, control, pressure_range_builder
  import europe_ble as eb
  try:
    import glide
  except ImportError:
    glide = None

  grid = fly.grid if hasattr(fly, 'grid') else eb.WindGrid()
  fly.grid = grid
  wf = eb.EuropeWindField(grid, lat0, lon0)
  arena = eb.EuropeArena(wf, start, seed, feature_factory=NullFeatures,
                         launch_radius_km=10.0)
  target, steps, end = None, 0, 'MAX_DAYS'
  path_km, prev = 0.0, (lat0, lon0)
  release = None  # (steps, lat, lon, pressure, date_time, site)
  # Ship launches start outside the region: count only time inside it, and
  # end when the balloon leaves after entering (or never arrives in 5 days).
  entered, in_steps = in_region(lat0, lon0), 0
  max_steps = MAX_DAYS * 24 * 60 // STEP_MIN
  while steps < max_steps:
    s = arena.get_balloon_state()
    if kind == 'passive':
      action = control.AltitudeControlCommand.STAY
    elif kind == 'plan':
      if steps % PLAN_EVERY == 0:
        import planner
        pr = pressure_range_builder.get_pressure_range(s, arena._atmosphere)
        target = planner.plan(grid, s.latlng.lat().degrees, s.latlng.lng().degrees,
                              (s.date_time - eb.T0).total_seconds() / 3600,
                              pr.min_pressure, pr.max_pressure, REGION)
      if s.pressure > target + 300:
        action = control.AltitudeControlCommand.UP
      elif s.pressure < target - 300:
        action = control.AltitudeControlCommand.DOWN
      else:
        action = control.AltitudeControlCommand.STAY
    else:
      if steps % DECIDE_EVERY == 0:
        pr = pressure_range_builder.get_pressure_range(s, arena._atmosphere)
        # Not yet over the region (ship launch): head for it, then slow down.
        mode = kind if entered or not APPROACH_HOME else 'home'
        target = choose_pressure(mode, wf, s, pr, target)
      if s.pressure > target + 300:
        action = control.AltitudeControlCommand.UP
      elif s.pressure < target - 300:
        action = control.AltitudeControlCommand.DOWN
      else:
        action = control.AltitudeControlCommand.STAY
    try:
      arena.step(action)
    except AssertionError:  # crossed 60N, outside BLE's solar model
      end = 'EXIT_N'
      break
    steps += 1
    s = arena.get_balloon_state()
    if s.status != balloon.BalloonStatus.OK:
      end = s.status.name
      break
    lat, lon = s.latlng.lat().degrees, s.latlng.lng().degrees
    if steps % 20 == 0:
      path_km += gc_km(prev, (lat, lon)); prev = (lat, lon)
      name, site_ll = min(RECOVERY.items(), key=lambda kv: gc_km((lat, lon), kv[1]))
      if gc_km((lat, lon), site_ll) <= RELEASE_KM:
        release = (steps, lat, lon, s.pressure, s.date_time, name)
    if in_region(lat, lon):
      entered = True
      in_steps += 1
    elif not entered:
      if steps >= 5 * 480:
        end = 'NEVER_ENTERED'
        break
    else:
      end = 'EXIT_' + ('W' if lon < REGION['lon0'] else 'E' if lon > REGION['lon1']
                       else 'S' if lat < REGION['lat0'] else 'N')
      break
  s = arena.get_balloon_state()
  lat, lon = s.latlng.lat().degrees, s.latlng.lng().degrees
  dwell_h = in_steps * STEP_MIN / 60
  row = dict(site=site, start=start.date().isoformat(), month=start.month,
             controller=kind, seed=seed, dwell_h=round(dwell_h, 2), end=end,
             end_lat=round(lat, 2), end_lon=round(lon, 2),
             end_hpa=round(s.pressure / 100, 1),
             mean_speed_kmh=round(path_km / max(dwell_h, 1e-6), 1))
  if glide is not None and release is not None:
    rs, rlat, rlon, rp, rt, name = release
    hours = (rt - eb.T0).total_seconds() / 3600
    g = glide.simulate_glide(rlat, rlon, rp, hours, grid,
                             target=RECOVERY[name], **GLIDE)
    e = glide.simulate_descent(rlat, rlon, rp, hours, grid)
    row.update(release_h=round(rs * STEP_MIN / 60, 2), recovery=name,
               release_lat=round(rlat, 3), release_lon=round(rlon, 3),
               env_a_lat=round(e['end_lat'], 3), env_a_lon=round(e['end_lon'], 3),
               glide_h=round(g['duration_s'] / 3600, 2),
               glide_end_km=round(g['dist_to_target_end_km'], 1),
               recovered=g['reached'])
  else:
    row.update(release_h=None, recovery=None, release_lat=None,
               release_lon=None, env_a_lat=None, env_a_lon=None, glide_h=None,
               glide_end_km=None, recovered=False)
  if glide is not None:  # envelope flown on to the end, then cut down
    e = glide.simulate_descent(lat, lon, s.pressure,
                               (s.date_time - eb.T0).total_seconds() / 3600, grid)
    row.update(env_b_lat=round(e['end_lat'], 3), env_b_lon=round(e['end_lon'], 3))
  return row


def main():
  quick = '--quick' in sys.argv
  ctrls = CONTROLLERS
  if '--controllers' in sys.argv:
    ctrls = sys.argv[sys.argv.index('--controllers') + 1].split(',')
  starts = [dt.datetime(2025, m, d, 6, tzinfo=dt.timezone.utc)
            for m in range(1, 13) for d in (1, 15)]
  sites = list(LAUNCH.items())
  if quick:
    starts, sites = starts[::8], sites[:2]
  jobs = [(n, la, lo, st, k, 7919 * i + 31 * j + SEED_C[k])
          for i, (n, (la, lo)) in enumerate(sites)
          for j, st in enumerate(starts) for k in ctrls]
  os.makedirs('results', exist_ok=True)
  out = 'results/drift_quick.csv' if quick else 'results/drift_2025.csv'
  if ctrls != CONTROLLERS:
    out = out.replace('.csv', '_' + '_'.join(ctrls) + '.csv')
  t, rows = time.time(), []
  with mp.get_context('spawn').Pool(8) as pool:
    for k, r in enumerate(pool.imap_unordered(fly, jobs)):
      rows.append(r)
      print(f'{k + 1}/{len(jobs)} {r["site"]:>9} {r["start"]} {r["controller"]:>7} '
            f'dwell={r["dwell_h"]:6.1f}h {r["end"]} ({time.time() - t:.0f}s)',
            flush=True)
  with open(out, 'w') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


if __name__ == '__main__':
  main()

"""Re-fly ONE one-way flight of run_drift.py / run_ship.py and log its track.

Replicates run_drift.fly step for step (same arena, seed, controller and
termination rules) and additionally records, every LOG_EVERY steps, the
balloon's position, pressure/altitude, battery, solar input and command, so
an episode can quote the real timeline, altitudes and power state. The
radio release point (last hour within RELEASE_KM of a recovery site), the
glide home and the envelope parachute descent are computed exactly as in
run_drift.fly. Nothing in run_drift.py is modified.

Usage:
  python scenarios/tools/fly_track.py --site Lisbon --date 2025-01-15 --seed 32 \
      --out scenarios/ep01/flight.json
  python scenarios/tools/fly_track.py --site "Ship 52N 13W" --lat 52 --lon -13 \
      --date 2025-02-01 --seed 71334 --grid data/ncep_band_2025.npz --approach-home ...
Options: --controller slow|home|passive (default slow), --max-days (default 30).
"""
import argparse
import datetime as dt
import json
import os
import sys
import warnings

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
warnings.filterwarnings('ignore')

LOG_EVERY = 20  # steps = 1 h


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument('--site', required=True)
  ap.add_argument('--lat', type=float)
  ap.add_argument('--lon', type=float)
  ap.add_argument('--date', required=True, help='YYYY-MM-DD, launch 06Z as in run_drift')
  ap.add_argument('--seed', type=int, required=True)
  ap.add_argument('--controller', default='slow')
  ap.add_argument('--grid', default='data/gfs_europe_2025.npz')
  ap.add_argument('--approach-home', action='store_true',
                  help='run_ship.py APPROACH_HOME=1: steer for Europe until inside')
  ap.add_argument('--max-days', type=int, default=30)
  ap.add_argument('--out', required=True)
  a = ap.parse_args()
  if a.approach_home:
    os.environ['APPROACH_HOME'] = '1'
  os.chdir(ROOT)
  import run_drift as rd
  import europe_ble as eb
  import glide
  from balloon_learning_environment.env.balloon import balloon, control, pressure_range_builder
  rd.MAX_DAYS = a.max_days
  lat0, lon0 = (a.lat, a.lon) if a.lat is not None else rd.LAUNCH[a.site]
  start = dt.datetime.fromisoformat(a.date).replace(hour=6, tzinfo=dt.timezone.utc)
  kind = a.controller
  grid = eb.WindGrid(a.grid)
  wf = eb.EuropeWindField(grid, lat0, lon0)
  arena = eb.EuropeArena(wf, start, seed=a.seed, feature_factory=rd.NullFeatures,
                         launch_radius_km=10.0)
  target, steps, end = None, 0, 'MAX_DAYS'
  path_km, prev = 0.0, (lat0, lon0)
  release = None
  entered, in_steps = rd.in_region(lat0, lon0), 0
  max_steps = a.max_days * 24 * 60 // rd.STEP_MIN
  track = []
  last_action = 'STAY'

  def log(s, action):
    track.append(dict(
        h=round(steps * rd.STEP_MIN / 60, 2), t=s.date_time.isoformat(),
        lat=round(s.latlng.lat().degrees, 3), lon=round(s.latlng.lng().degrees, 3),
        hpa=round(s.pressure / 100, 1), alt_km=round(glide.isa_altitude(s.pressure) / 1000, 2),
        batt_pct=round(100 * s.battery_charge.watt_hours / s.battery_capacity.watt_hours, 1),
        solar_w=round(s.solar_charging.watts, 0), load_w=round(s.power_load.watts, 0),
        superpressure_pa=round(s.superpressure, 0), amb_k=round(s.ambient_temperature, 1),
        in_region=rd.in_region(s.latlng.lat().degrees, s.latlng.lng().degrees),
        cmd=action))

  s = arena.get_balloon_state()
  log(s, 'LAUNCH')
  while steps < max_steps:
    s = arena.get_balloon_state()
    if kind == 'passive':
      action = control.AltitudeControlCommand.STAY
    else:
      if steps % rd.DECIDE_EVERY == 0:
        pr = pressure_range_builder.get_pressure_range(s, arena._atmosphere)
        mode = kind if entered or not a.approach_home else 'home'
        target = rd.choose_pressure(mode, wf, s, pr, target)
      if s.pressure > target + 300:
        action = control.AltitudeControlCommand.UP
      elif s.pressure < target - 300:
        action = control.AltitudeControlCommand.DOWN
      else:
        action = control.AltitudeControlCommand.STAY
    last_action = action.name
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
      path_km += rd.gc_km(prev, (lat, lon)); prev = (lat, lon)
      name, site_ll = min(rd.RECOVERY.items(), key=lambda kv: rd.gc_km((lat, lon), kv[1]))
      if rd.gc_km((lat, lon), site_ll) <= rd.RELEASE_KM:
        release = (steps, lat, lon, s.pressure, s.date_time, name)
    if steps % LOG_EVERY == 0:
      log(s, last_action)
    if rd.in_region(lat, lon):
      entered = True
      in_steps += 1
    elif not entered:
      if steps >= 5 * 480:
        end = 'NEVER_ENTERED'
        break
    else:
      R = rd.REGION
      end = 'EXIT_' + ('W' if lon < R['lon0'] else 'E' if lon > R['lon1']
                       else 'S' if lat < R['lat0'] else 'N')
      break
  s = arena.get_balloon_state()
  if steps % LOG_EVERY:
    log(s, end)
  lat, lon = s.latlng.lat().degrees, s.latlng.lng().degrees
  dwell_h = in_steps * rd.STEP_MIN / 60
  out = dict(
      script='scenarios/tools/fly_track.py (replicates run_drift.fly)',
      site=a.site, launch=dict(lat=lat0, lon=lon0, time=start.isoformat()),
      seed=a.seed, controller=kind, grid=a.grid, approach_home=a.approach_home,
      max_days=a.max_days, glider=rd.GLIDE, release_km=rd.RELEASE_KM,
      summary=dict(dwell_h=round(dwell_h, 2), flight_h=round(steps * rd.STEP_MIN / 60, 2),
                   end=end, end_lat=round(lat, 2), end_lon=round(lon, 2),
                   end_hpa=round(s.pressure / 100, 1),
                   end_time=s.date_time.isoformat(),
                   mean_speed_kmh=round(path_km / max(dwell_h, 1e-6), 1),
                   path_km=round(path_km, 0),
                   min_batt_pct=min(r['batt_pct'] for r in track),
                   max_alt_km=max(r['alt_km'] for r in track),
                   min_alt_km=min(r['alt_km'] for r in track[1:] or track)))
  if release is not None:
    rs, rlat, rlon, rp, rt, name = release
    hours = (rt - eb.T0).total_seconds() / 3600
    g = glide.simulate_glide(rlat, rlon, rp, hours, grid, target=rd.RECOVERY[name], **rd.GLIDE)
    e = glide.simulate_descent(rlat, rlon, rp, hours, grid)
    out['release'] = dict(h=round(rs * rd.STEP_MIN / 60, 2), time=rt.isoformat(),
                          lat=round(rlat, 3), lon=round(rlon, 3), hpa=round(rp / 100, 1),
                          alt_km=round(glide.isa_altitude(rp) / 1000, 2), site=name,
                          site_latlon=rd.RECOVERY[name],
                          dist_to_site_km=round(rd.gc_km((rlat, rlon), rd.RECOVERY[name]), 1))
    out['glide'] = dict(duration_h=round(g['duration_s'] / 3600, 2),
                        ground_km=round(g['ground_dist_km'], 1),
                        end_lat=round(g['end_lat'], 3), end_lon=round(g['end_lon'], 3),
                        miss_km=round(g['dist_to_target_end_km'], 1), recovered=g['reached'])
    out['envelope_cut_at_release'] = dict(duration_h=round(e['duration_s'] / 3600, 2),
                                          land_lat=round(e['end_lat'], 3), land_lon=round(e['end_lon'], 3),
                                          drift_km=round(rd.gc_km((rlat, rlon), (e['end_lat'], e['end_lon'])), 1))
  else:
    out['release'] = None
  e = glide.simulate_descent(lat, lon, s.pressure, (s.date_time - eb.T0).total_seconds() / 3600, grid)
  out['envelope_cut_at_end'] = dict(duration_h=round(e['duration_s'] / 3600, 2),
                                    land_lat=round(e['end_lat'], 3), land_lon=round(e['end_lon'], 3),
                                    drift_km=round(rd.gc_km((lat, lon), (e['end_lat'], e['end_lon'])), 1))
  out['track'] = track
  os.makedirs(os.path.dirname(a.out), exist_ok=True)
  with open(a.out, 'w') as f:
    json.dump(out, f, indent=1)
  print(json.dumps({k: v for k, v in out.items() if k != 'track'}, indent=1))


if __name__ == '__main__':
  main()

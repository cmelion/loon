"""Multi-pass flights: ride the westerlies around the hemisphere and return.

Instead of cutting a balloon down when it leaves Europe, keep it flying:
slow (lowest-wind altitude) over the region, fast eastward elsewhere, with a
latitude guard holding it in 35-56°N (BLE's solar model fails at 60°N).
Winds: NCEP/NCAR Reanalysis-1 2025, 25-70°N, full longitude ring, 6-hourly
(data/ncep_band_2025.npz from subset_ncep.py); time wraps after 31 Dec.

Each flight runs up to MAX_DAYS. We log, per flight, hours over Europe by
elapsed day and the times it is inside the region within RELEASE_KM of a
recovery site (a chance to end the flight and recover the radio), so
envelope lifetimes of 30/60/100/150 days can be evaluated from one run.

Usage: python run_multipass.py [--quick]
"""
import datetime as dt
import json
import math
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import canada  # noqa: E402
import china  # noqa: E402
from run_drift import (LAUNCH, RECOVERY, REGION, RELEASE_KM, NullFeatures,  # noqa: E402
                       gc_km, in_region)

MAX_DAYS = int(os.environ.get('MAX_DAYS', 150))
CANADA_LAUNCH = {'Vancouver': (49.3, -123.1), 'Prince George': (53.9, -122.7),
                 'Calgary': (51.0, -114.1)}
# Coarse overflight sectors by longitude (°E) for the 35-56°N band.
SECTORS = [('Europe', -10, 42), ('Russia/C.Asia/China', 42, 135),
           ('E.Asia/W.Pacific', 135, 180), ('E.Pacific', -180, -125),
           ('N.America', -125, -60), ('Atlantic', -60, -10)]
STEP_MIN = 3
DECIDE_EVERY = 5     # 15 min
REBASE_EVERY = 40    # 2 h: re-centre BLE's local x/y frame on the balloon
LAT_LO, LAT_HI = 35.0, 56.0
AVOID_CHINA = '--no-china-avoid' not in sys.argv
CORRIDOR_HI = 58.8
# Options (env): BATTERY_WH emulates a fuel cell's larger night energy store;
# THRUST_MS adds a northward push through the air (propeller) while a flight
# approaching China is below the safe corridor. Thrust is applied as a
# velocity added to the wind the balloon drifts in; its power is costed after
# the fact from drag (THRUST_POWER_W) and drawn from the lift gas, not BLE.
BATTERY_WH = float(os.environ.get('BATTERY_WH', 0)) or None
THRUST_MS = float(os.environ.get('THRUST_MS', 0))
RHO_20KM, CD, AREA_M2, ETA = 0.089, 0.4, 177.0, 0.6
THRUST_POWER_W = 0.5 * RHO_20KM * CD * AREA_M2 * THRUST_MS ** 3 / ETA
POWER_FLOOR = 0.45   # never pump below this battery fraction
NIGHT_FLOOR = 0.80   # at night only pump with plenty in hand


def choose(wf, s, prange, current, lat):
  import numpy as np
  cands = np.linspace(prange.min_pressure, prange.max_pressure, 15)
  w = wf.get_forecast_column(s.x, s.y, cands, s.time_elapsed)
  u = np.array([x.u.meters_per_second for x in w])
  v = np.array([x.v.meters_per_second for x in w])
  lon = s.latlng.lng().degrees
  lo, hi = LAT_LO, LAT_HI
  if AVOID_CHINA:
    floor = china.corridor_floor(((lon + 180) % 360) - 180)
    if floor is not None:  # route north of China, up to BLE's 60N limit
      lo, hi = max(lo, floor), CORRIDOR_HI
  # Proportional guard: push harder the further outside the band.
  guard = (max(0.0, lo + 2 - lat) - max(0.0, lat - (hi - 2))) / 2.0
  over_europe = in_region(lat, s.latlng.lng().degrees)
  score = (-np.hypot(u, v) if over_europe else u) + (8.0 if lo > LAT_LO else 4.0) * guard * v
  best = int(np.argmax(score))
  if current is not None:
    cur = int(np.argmin(abs(cands - current)))
    if score[best] - score[cur] < 1.0:
      return cands[cur]
  return cands[best]


def fly(job):
  site, lat0, lon0, start, seed = job
  sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
  import warnings
  warnings.filterwarnings('ignore')
  from balloon_learning_environment.env.balloon import balloon, control, pressure_range_builder
  from balloon_learning_environment.utils import units
  from s2sphere import LatLng
  import europe_ble as eb

  grid = fly.grid if hasattr(fly, 'grid') else eb.WindGrid('data/ncep_band_2025.npz')
  fly.grid = grid
  wf = eb.EuropeWindField(grid, lat0, lon0)
  wf.thrust_v = 0.0
  truth = wf.get_ground_truth

  def pushed(x, y, p, t):
    w = truth(x, y, p, t)
    return w if not wf.thrust_v else w.add(eb.wind_field.WindVector(
        units.Velocity(mps=0.0), units.Velocity(mps=wf.thrust_v)))
  wf.get_ground_truth = pushed
  arena = eb.EuropeArena(wf, start, seed, feature_factory=NullFeatures,
                         launch_radius_km=10.0)
  if BATTERY_WH:
    st = arena.get_balloon_state()
    st.battery_capacity = units.Energy(watt_hours=BATTERY_WH)
    st.battery_charge = units.Energy(watt_hours=0.95 * BATTERY_WH)
  thrust_steps, china_first, max_lat = 0, None, lat0
  target, steps, end = None, 0, 'MAX_DAYS'
  eu_steps, passes, was_in = 0, 0, False
  lon_travel, prev_lon = 0.0, lon0
  daily_eu_h, recover_days = [], []
  sector_steps = {name: 0 for name, _, _ in SECTORS}
  from global_land_mask import globe
  land_steps = 0
  china_steps = 0
  canada_steps, atlantic_steps = 0, 0
  max_steps = MAX_DAYS * 24 * 60 // STEP_MIN
  while steps < max_steps:
    s = arena.get_balloon_state()
    lat, lon = s.latlng.lat().degrees, s.latlng.lng().degrees
    if steps % REBASE_EVERY == 0 and steps:
      s.center_latlng = LatLng.from_degrees(lat, lon)
      s.x, s.y = units.Distance(m=0.0), units.Distance(m=0.0)
      wf.lat0, wf.lon0 = lat, lon
    if steps % DECIDE_EVERY == 0:
      pr = pressure_range_builder.get_pressure_range(s, arena._atmosphere)
      target = choose(wf, s, pr, target, lat)
      if THRUST_MS:  # two-way latitude hold inside the (corridor) band
        lo, hi = LAT_LO, LAT_HI
        floor = china.corridor_floor(((lon + 180) % 360) - 180) if AVOID_CHINA else None
        if floor is not None:
          lo, hi = max(lo, floor), CORRIDOR_HI
        wf.thrust_v = THRUST_MS if lat < lo + 1.0 else -THRUST_MS if lat > hi - 1.0 else 0.0
    thrust_steps += wf.thrust_v != 0
    frac = s.battery_charge.watt_hours / s.battery_capacity.watt_hours
    night = s.solar_charging.watts <= 0
    if frac < POWER_FLOOR or (night and frac < NIGHT_FLOOR):
      action = control.AltitudeControlCommand.STAY  # save charge for the night
    elif s.pressure > target + 300:
      action = control.AltitudeControlCommand.UP
    elif s.pressure < target - 300:
      action = control.AltitudeControlCommand.DOWN
    else:
      action = control.AltitudeControlCommand.STAY
    try:
      arena.step(action)
    except AssertionError:
      end = 'PAST_60N'
      break
    steps += 1
    s = arena.get_balloon_state()
    if s.status != balloon.BalloonStatus.OK:
      end = s.status.name
      break
    lat, lon = s.latlng.lat().degrees, s.latlng.lng().degrees
    max_lat = max(max_lat, lat)
    if lat < 20.0:
      end = 'SOUTH_20N'
      break
    lon_travel += ((lon - prev_lon + 180) % 360) - 180
    prev_lon = lon
    lon_w = ((lon + 180) % 360) - 180
    for name, a, b in SECTORS:
      if a <= lon_w < b:
        sector_steps[name] += 1
        break
    if steps % 20 == 0:
      land_steps += 20 * globe.is_land(lat, lon_w)
    canada_steps += canada.in_canada(lat, lon_w)
    atlantic_steps += canada.in_north_atlantic(lat, lon_w)
    if china.in_china(lat, lon_w):
      china_steps += 1
      if china_first is None:
        china_first = round(steps * STEP_MIN / 1440, 2)
    inside = in_region(lat, lon)
    eu_steps += inside
    passes += inside and not was_in
    was_in = inside
    if steps % 480 == 0:  # daily log
      daily_eu_h.append(round(eu_steps * STEP_MIN / 60, 1))
    if inside and steps % 40 == 0:
      d = min(gc_km((lat, lon), ll) for ll in RECOVERY.values())
      if d <= RELEASE_KM:
        recover_days.append(round(steps * STEP_MIN / 1440, 2))
  return dict(site=site, start=start.date().isoformat(), month=start.month,
              seed=seed, days=round(steps * STEP_MIN / 1440, 2), end=end,
              europe_days=round(eu_steps * STEP_MIN / 1440, 2), passes=passes,
              laps=round(lon_travel / 360, 2), daily_eu_h=daily_eu_h,
              land_frac=round(land_steps / max(steps, 1), 3),
              china_days=round(china_steps * STEP_MIN / 1440, 2),
              china_first_day=china_first, max_lat=round(max_lat, 1),
              canada_days=round(canada_steps * STEP_MIN / 1440, 2),
              atlantic_days=round(atlantic_steps * STEP_MIN / 1440, 2),
              thrust_h=round(thrust_steps * STEP_MIN / 60, 1),
              thrust_kwh=round(thrust_steps * STEP_MIN / 60 * THRUST_POWER_W / 1000, 1),
              sector_days={k: round(v * STEP_MIN / 1440, 2) for k, v in sector_steps.items()},
              recover_days=recover_days)


def main():
  quick = '--quick' in sys.argv
  starts = [dt.datetime(2025, m, 1, 6, tzinfo=dt.timezone.utc) for m in range(1, 13)]
  sites = list(LAUNCH.items())
  if os.environ.get('LAUNCH_SET') == 'canada':
    sites = list(CANADA_LAUNCH.items())
  if quick:
    starts, sites = starts[::6], sites[:1]
  jobs = [(n, la, lo, st, 104729 * i + 17 * j)
          for i, (n, (la, lo)) in enumerate(sites) for j, st in enumerate(starts)]
  out = 'results/multipass_quick.jsonl' if quick else 'results/multipass_2025.jsonl'
  if AVOID_CHINA:
    out = out.replace('.jsonl', '_nochina.jsonl')
  if BATTERY_WH:
    out = out.replace('.jsonl', f'_bat{int(BATTERY_WH)}.jsonl')
  if THRUST_MS:
    out = out.replace('.jsonl', f'_thrust{THRUST_MS:g}.jsonl')
  if os.environ.get('LAUNCH_SET') == 'canada':
    out = out.replace('.jsonl', '_canada.jsonl')
  t = time.time()
  with mp.get_context('spawn').Pool(int(os.environ.get('PROCS', 8))) as pool, open(out, 'w') as f:
    for k, r in enumerate(pool.imap_unordered(fly, jobs)):
      f.write(json.dumps(r) + '\n'); f.flush()
      print(f'{k + 1}/{len(jobs)} {r["site"]:>9} {r["start"]} {r["days"]:6.1f}d '
            f'europe={r["europe_days"]:5.1f}d passes={r["passes"]} laps={r["laps"]} '
            f'{r["end"]} ({time.time() - t:.0f}s)', flush=True)


if __name__ == '__main__':
  main()

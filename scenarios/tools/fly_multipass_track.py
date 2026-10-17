"""Re-fly ONE hemispheric multi-pass flight of run_multipass.py and log its track.

Replicates run_multipass.fly step for step (NCEP band winds, latitude guard,
China corridor, optional fuel-cell store BATTERY_WH and latitude-hold thrust
THRUST_MS, power floors) and additionally records every LOG_EVERY steps the
position, pressure/altitude, battery, solar input, thrust state, sector and
whether the balloon is over China / Canada / Europe. run_multipass.py is not
modified; its module-level options are set through the environment exactly
as in the original runs (BATTERY_WH, THRUST_MS, MAX_DAYS).

Usage (thrust3 run):
  BATTERY_WH=10000 THRUST_MS=3 MAX_DAYS=150 python scenarios/tools/fly_multipass_track.py \
      --site Bucharest --date 2025-05-01 --seed 418984 --out scenarios/ep06/flight.json
Canada run: LAUNCH_SET=canada MAX_DAYS=60 ... --site Vancouver --seed 119
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

LOG_EVERY = 40  # steps = 2 h


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument('--site', required=True)
  ap.add_argument('--date', required=True)
  ap.add_argument('--seed', type=int, required=True)
  ap.add_argument('--out', required=True)
  a = ap.parse_args()
  os.chdir(ROOT)
  import run_multipass as mp_
  import canada, china
  import europe_ble as eb
  import glide
  from run_drift import RECOVERY, RELEASE_KM, NullFeatures, gc_km, in_region
  from balloon_learning_environment.env.balloon import balloon, control, pressure_range_builder
  from balloon_learning_environment.utils import units
  from s2sphere import LatLng
  from global_land_mask import globe

  sites = {**mp_.LAUNCH, **mp_.CANADA_LAUNCH}
  lat0, lon0 = sites[a.site]
  start = dt.datetime.fromisoformat(a.date).replace(hour=6, tzinfo=dt.timezone.utc)
  grid = eb.WindGrid('data/ncep_band_2025.npz')
  wf = eb.EuropeWindField(grid, lat0, lon0)
  wf.thrust_v = 0.0
  truth = wf.get_ground_truth

  def pushed(x, y, p, t):
    w = truth(x, y, p, t)
    return w if not wf.thrust_v else w.add(eb.wind_field.WindVector(
        units.Velocity(mps=0.0), units.Velocity(mps=wf.thrust_v)))
  wf.get_ground_truth = pushed
  arena = eb.EuropeArena(wf, start, a.seed, feature_factory=NullFeatures, launch_radius_km=10.0)
  if mp_.BATTERY_WH:
    st = arena.get_balloon_state()
    st.battery_capacity = units.Energy(watt_hours=mp_.BATTERY_WH)
    st.battery_charge = units.Energy(watt_hours=0.95 * mp_.BATTERY_WH)
  thrust_steps, china_first, max_lat = 0, None, lat0
  target, steps, end = None, 0, 'MAX_DAYS'
  eu_steps, passes, was_in = 0, 0, False
  lon_travel, prev_lon = 0.0, lon0
  daily_eu_h, recover_days = [], []
  sector_steps = {name: 0 for name, _, _ in mp_.SECTORS}
  land_steps = china_steps = canada_steps = atlantic_steps = 0
  max_steps = mp_.MAX_DAYS * 24 * 60 // mp_.STEP_MIN
  track, events = [], []
  held = 'STAY'

  def sector(lon_w):
    for name, lo, hi in mp_.SECTORS:
      if lo <= lon_w < hi:
        return name
    return None

  def log(s, cmd, note=''):
    lat, lon = s.latlng.lat().degrees, s.latlng.lng().degrees
    lon_w = ((lon + 180) % 360) - 180
    track.append(dict(
        day=round(steps * mp_.STEP_MIN / 1440, 3), t=s.date_time.isoformat(),
        lat=round(lat, 3), lon=round(lon_w, 3), hpa=round(s.pressure / 100, 1),
        alt_km=round(glide.isa_altitude(s.pressure) / 1000, 2),
        batt_pct=round(100 * s.battery_charge.watt_hours / s.battery_capacity.watt_hours, 1),
        solar_w=round(s.solar_charging.watts, 0), load_w=round(s.power_load.watts, 0),
        thrust_ms=wf.thrust_v, sector=sector(lon_w),
        europe=in_region(lat, lon), china=china.in_china(lat, lon_w),
        canada=canada.in_canada(lat, lon_w), land=bool(globe.is_land(lat, lon_w)),
        cmd=cmd, note=note))

  s = arena.get_balloon_state()
  log(s, 'LAUNCH')
  prev_flags = dict(europe=in_region(lat0, lon0), china=False, canada=canada.in_canada(lat0, lon0))
  while steps < max_steps:
    s = arena.get_balloon_state()
    lat, lon = s.latlng.lat().degrees, s.latlng.lng().degrees
    if steps % mp_.REBASE_EVERY == 0 and steps:
      s.center_latlng = LatLng.from_degrees(lat, lon)
      s.x, s.y = units.Distance(m=0.0), units.Distance(m=0.0)
      wf.lat0, wf.lon0 = lat, lon
    if steps % mp_.DECIDE_EVERY == 0:
      pr = pressure_range_builder.get_pressure_range(s, arena._atmosphere)
      target = mp_.choose(wf, s, pr, target, lat)
      if mp_.THRUST_MS:
        lo, hi = mp_.LAT_LO, mp_.LAT_HI
        floor = china.corridor_floor(((lon + 180) % 360) - 180) if mp_.AVOID_CHINA else None
        if floor is not None:
          lo, hi = max(lo, floor), mp_.CORRIDOR_HI
        wf.thrust_v = mp_.THRUST_MS if lat < lo + 1.0 else -mp_.THRUST_MS if lat > hi - 1.0 else 0.0
    thrust_steps += wf.thrust_v != 0
    frac = s.battery_charge.watt_hours / s.battery_capacity.watt_hours
    night = s.solar_charging.watts <= 0
    if frac < mp_.POWER_FLOOR or (night and frac < mp_.NIGHT_FLOOR):
      action = control.AltitudeControlCommand.STAY
      held = 'STAY(power-floor)'
    elif s.pressure > target + 300:
      action = control.AltitudeControlCommand.UP; held = 'UP'
    elif s.pressure < target - 300:
      action = control.AltitudeControlCommand.DOWN; held = 'DOWN'
    else:
      action = control.AltitudeControlCommand.STAY; held = 'STAY'
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
    sec = sector(lon_w)
    if sec:
      sector_steps[sec] += 1
    if steps % 20 == 0:
      land_steps += 20 * globe.is_land(lat, lon_w)
    canada_steps += canada.in_canada(lat, lon_w)
    atlantic_steps += canada.in_north_atlantic(lat, lon_w)
    if china.in_china(lat, lon_w):
      china_steps += 1
      if china_first is None:
        china_first = round(steps * mp_.STEP_MIN / 1440, 2)
    inside = in_region(lat, lon)
    eu_steps += inside
    passes += inside and not was_in
    was_in = inside
    flags = dict(europe=inside, china=china.in_china(lat, lon_w), canada=canada.in_canada(lat, lon_w))
    for k in flags:
      if flags[k] != prev_flags[k]:
        events.append(dict(day=round(steps * mp_.STEP_MIN / 1440, 2), t=s.date_time.isoformat(),
                           lat=round(lat, 2), lon=round(lon_w, 2),
                           event=('enter ' if flags[k] else 'leave ') + k))
    prev_flags = flags
    if steps % 480 == 0:
      daily_eu_h.append(round(eu_steps * mp_.STEP_MIN / 60, 1))
    if inside and steps % 40 == 0:
      d = min(gc_km((lat, lon), ll) for ll in RECOVERY.values())
      if d <= RELEASE_KM:
        recover_days.append(round(steps * mp_.STEP_MIN / 1440, 2))
    if steps % LOG_EVERY == 0:
      log(s, held)
  s = arena.get_balloon_state()
  log(s, held, note=end)
  lat, lon = s.latlng.lat().degrees, s.latlng.lng().degrees
  lon_w = ((lon + 180) % 360) - 180
  summary = dict(site=a.site, start=start.date().isoformat(), seed=a.seed,
                 days=round(steps * mp_.STEP_MIN / 1440, 2), end=end,
                 end_time=s.date_time.isoformat(), end_lat=round(lat, 2), end_lon=round(lon_w, 2),
                 end_hpa=round(s.pressure / 100, 1),
                 europe_days=round(eu_steps * mp_.STEP_MIN / 1440, 2), passes=passes,
                 laps=round(lon_travel / 360, 2),
                 land_frac=round(land_steps / max(steps, 1), 3),
                 china_days=round(china_steps * mp_.STEP_MIN / 1440, 2), china_first_day=china_first,
                 max_lat=round(max_lat, 1),
                 canada_days=round(canada_steps * mp_.STEP_MIN / 1440, 2),
                 atlantic_days=round(atlantic_steps * mp_.STEP_MIN / 1440, 2),
                 thrust_h=round(thrust_steps * mp_.STEP_MIN / 60, 1),
                 thrust_kwh=round(thrust_steps * mp_.STEP_MIN / 60 * mp_.THRUST_POWER_W / 1000, 1),
                 sector_days={k: round(v * mp_.STEP_MIN / 1440, 2) for k, v in sector_steps.items()},
                 n_recover_opportunities=len(recover_days),
                 first_recover_day=recover_days[0] if recover_days else None,
                 last_recover_day=recover_days[-1] if recover_days else None,
                 min_batt_pct=min(r['batt_pct'] for r in track),
                 max_alt_km=max(r['alt_km'] for r in track))
  out = dict(script='scenarios/tools/fly_multipass_track.py (replicates run_multipass.fly)',
             options=dict(BATTERY_WH=mp_.BATTERY_WH, THRUST_MS=mp_.THRUST_MS, MAX_DAYS=mp_.MAX_DAYS,
                          AVOID_CHINA=mp_.AVOID_CHINA, LAT_BAND=[mp_.LAT_LO, mp_.LAT_HI],
                          CORRIDOR_HI=mp_.CORRIDOR_HI, THRUST_POWER_W=round(mp_.THRUST_POWER_W, 1),
                          winds='data/ncep_band_2025.npz (NCEP/NCAR Reanalysis-1, 6-hourly)'),
             launch=dict(lat=lat0, lon=lon0, time=start.isoformat()),
             summary=summary, events=events, daily_eu_h=daily_eu_h, recover_days=recover_days,
             track=track)
  os.makedirs(os.path.dirname(a.out), exist_ok=True)
  with open(a.out, 'w') as f:
    json.dump(out, f, indent=1)
  print(json.dumps(summary, indent=1))


if __name__ == '__main__':
  main()

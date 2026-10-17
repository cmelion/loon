"""Glide-back of a radio payload released from a stratospheric balloon.

At end of flight the radio is dropped on a small fixed-wing glider that
either steers toward a recovery point or simply rides the wind down.
This is a point-mass glider in real GFS winds (WindGrid from europe_ble):

  * Altitude from pressure via the ISA (troposphere, isothermal layer,
    lower stratosphere), density likewise.
  * Sink rate = sink_sl * sqrt(rho_sl / rho); true airspeed = L/D * sink.
    Glide ratio is held constant (no stall/Mach limits, no turns, no
    bank losses).
  * Winds: grid winds for 150-30 hPa (lookups are clamped to the data's
    edges in space, time and pressure). Below 150 hPa (~13.6 km) there is
    NO wind data; the 150 hPa wind is scaled linearly with altitude from
    1.0 at the 150 hPa level to 0.3 at the surface. This is a crude
    stand-in for the tropospheric jet/shear structure and is the dominant
    uncertainty in the ground track.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from europe_ble import WindGrid  # noqa: E402

EARTH_KM = 6371.0
G0, R_AIR = 9.80665, 287.05287
P_SL, T_SL, RHO_SL = 101325.0, 288.15, 1.225
P_TROPO = P_SL * (216.65 / T_SL) ** 5.25588          # 11 km
P_STRAT = P_TROPO * math.exp(-G0 * 9000.0 / (R_AIR * 216.65))  # 20 km
P_MIN, P_MAX = 3000.0, 15000.0                        # grid levels, Pa
REACH_KM = 25.0


def isa_altitude(p):
  """ISA geopotential altitude (m) for pressure p (Pa), valid to ~32 km."""
  if p > P_TROPO:
    return T_SL / 0.0065 * (1.0 - (p / P_SL) ** (1.0 / 5.25588))
  if p > P_STRAT:
    return 11000.0 + R_AIR * 216.65 / G0 * math.log(P_TROPO / p)
  return 20000.0 + 216.65 / 0.001 * ((p / P_STRAT) ** (-R_AIR * 0.001 / G0) - 1.0)


def isa_pressure(h):
  """Inverse of isa_altitude: pressure (Pa) at altitude h (m)."""
  if h < 11000.0:
    return P_SL * (1.0 - 0.0065 * h / T_SL) ** 5.25588
  if h < 20000.0:
    return P_TROPO * math.exp(-G0 * (h - 11000.0) / (R_AIR * 216.65))
  t = 216.65 + 0.001 * (h - 20000.0)
  return P_STRAT * (t / 216.65) ** (-G0 / (R_AIR * 0.001))


def isa_density(h):
  """ISA density (kg/m^3) at altitude h (m)."""
  if h < 11000.0:
    t = T_SL - 0.0065 * h
  elif h < 20000.0:
    t = 216.65
  else:
    t = 216.65 + 0.001 * (h - 20000.0)
  return isa_pressure(h) / (R_AIR * t)


ALT_150 = isa_altitude(P_MAX)


def haversine_km(lat1, lon1, lat2, lon2):
  p1, p2 = math.radians(lat1), math.radians(lat2)
  dl = math.radians(lon2 - lon1)
  a = (math.sin((p2 - p1) / 2) ** 2 +
       math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2)
  return 2 * EARTH_KM * math.asin(math.sqrt(a))


def bearing_rad(lat1, lon1, lat2, lon2):
  """Initial great-circle bearing, radians clockwise from north."""
  p1, p2 = math.radians(lat1), math.radians(lat2)
  dl = math.radians(lon2 - lon1)
  x = math.sin(dl) * math.cos(p2)
  y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
  return math.atan2(x, y)


def wind_at(grid, lat, lon, alt_m, hours):
  """(u, v) m/s at altitude; below 150 hPa scale that level's wind down."""
  p = isa_pressure(alt_m)
  if p <= P_MAX:
    u, v = grid.lookup(lat, lon, np.array([max(p, P_MIN)]), hours)
    return float(u[0]), float(v[0])
  u, v = grid.lookup(lat, lon, np.array([P_MAX]), hours)
  k = 0.3 + 0.7 * max(alt_m, 0.0) / ALT_150
  return k * float(u[0]), k * float(v[0])


def simulate_glide(lat, lon, pressure_pa, hours, grid, target=None, *,
                   ld=12.0, sink_sl=1.0, dt_s=10.0, cutoff_alt_m=0.0):
  """Integrate a glider from (lat, lon, pressure) down to cutoff_alt_m.

  hours: time since 2025-01-01T00Z (WindGrid convention). target: (lat, lon)
  to steer toward, else fly directly downwind. Returns a dict of summary
  numbers; reached is True if the end point is within 25 km of target.
  """
  alt = isa_altitude(pressure_pa)
  start_alt = alt
  t, dist_km = 0.0, 0.0
  d0 = haversine_km(lat, lon, *target) if target else None
  while alt > cutoff_alt_m:
    rho = isa_density(alt)
    sink = sink_sl * math.sqrt(RHO_SL / rho)
    tas = ld * sink
    wu, wv = wind_at(grid, lat, lon, alt, hours + t / 3600.0)
    if target:
      b = bearing_rad(lat, lon, *target)
    else:
      b = math.atan2(wu, wv) if (wu or wv) else 0.0
    gu, gv = tas * math.sin(b) + wu, tas * math.cos(b) + wv
    step = min(dt_s, (alt - cutoff_alt_m) / sink)
    lat += math.degrees(gv * step / (EARTH_KM * 1000.0))
    lon += math.degrees(gu * step / (EARTH_KM * 1000.0 * math.cos(math.radians(lat))))
    dist_km += math.hypot(gu, gv) * step / 1000.0
    alt -= sink * step
    t += step
  d1 = haversine_km(lat, lon, *target) if target else None
  return dict(duration_s=t, start_alt_m=start_alt, end_lat=lat, end_lon=lon,
              ground_dist_km=dist_km, dist_to_target_start_km=d0,
              dist_to_target_end_km=d1,
              reached=(d1 is not None and d1 < REACH_KM))


def max_return_km(lat, lon, pressure_pa, hours, grid, bearing_deg, **kw):
  """Ground distance made good along bearing_deg when flying that heading."""
  b = math.radians(bearing_deg)
  far = 3000.0 / EARTH_KM
  p0 = math.radians(lat)
  tl = math.asin(math.sin(p0) * math.cos(far) +
                 math.cos(p0) * math.sin(far) * math.cos(b))
  tn = lon + math.degrees(math.atan2(
      math.sin(b) * math.sin(far) * math.cos(p0),
      math.cos(far) - math.sin(p0) * math.sin(tl)))
  r = simulate_glide(lat, lon, pressure_pa, hours, grid,
                     target=(math.degrees(tl), tn), **kw)
  d = haversine_km(lat, lon, r['end_lat'], r['end_lon'])
  db = bearing_rad(lat, lon, r['end_lat'], r['end_lon'])
  return d * math.cos(db - b)


if __name__ == '__main__':
  grid = WindGrid('data/gfs_europe_2025.npz')
  bucharest, vienna, odesa = (44.43, 26.10), (48.21, 16.37), (46.48, 30.73)
  print('still-air check: 50 hPa alt %.0f m, ld*alt = %.0f km' %
        (isa_altitude(5000.0), 12.0 * isa_altitude(5000.0) / 1000.0))
  for day, hrs in (('2025-01-15', 14 * 24.0), ('2025-07-15', 195 * 24.0)):
    for name, tgt in (('downwind', None), ('Vienna', vienna), ('Odesa', odesa)):
      r = simulate_glide(*bucharest, 5000.0, hrs, grid, target=tgt)
      print('%s %-8s dur %.2f h  ground %.0f km  end (%.2f, %.2f)  '
            'to-target %s -> %s  reached=%s' % (
                day, name, r['duration_s'] / 3600.0, r['ground_dist_km'],
                r['end_lat'], r['end_lon'],
                None if r['dist_to_target_start_km'] is None
                else '%.0f' % r['dist_to_target_start_km'],
                None if r['dist_to_target_end_km'] is None
                else '%.0f' % r['dist_to_target_end_km'], r['reached']))
    print('  max_return_km by bearing:', ', '.join(
        '%d:%.0f' % (b, max_return_km(*bucharest, 5000.0, hrs, grid, b))
        for b in range(0, 360, 45)))


def simulate_descent(lat, lon, pressure_pa, hours, grid, *, sink_sl=5.0,
                     dt_s=10.0):
  """Drift of a terminated envelope coming down under a parachute.

  No airspeed of its own: ground velocity = wind. Sink rate is the
  sea-level descent rate sink_sl scaled by sqrt(rho_sl / rho), as for the
  glider. Same wind assumptions (and caveats) as simulate_glide.
  """
  alt = isa_altitude(pressure_pa)
  t = 0.0
  while alt > 0.0:
    sink = sink_sl * math.sqrt(RHO_SL / isa_density(alt))
    wu, wv = wind_at(grid, lat, lon, alt, hours + t / 3600.0)
    step = min(dt_s, alt / sink)
    lat += math.degrees(wv * step / (EARTH_KM * 1000.0))
    lon += math.degrees(wu * step / (EARTH_KM * 1000.0 * math.cos(math.radians(lat))))
    alt -= sink * step
    t += step
  return dict(duration_s=t, end_lat=lat, end_lon=lon)


# ---------------------------------------------------------------------------
# Wind-correcting guidance (added for glider_tuning; simulate_glide unchanged)
# ---------------------------------------------------------------------------
def crab_heading(track_rad, tas, wu, wv):
  """Heading (rad) that keeps the ground track on bearing track_rad.

  Solves tas*sin(heading - track) = -(cross-wind component). If the cross
  wind exceeds the airspeed the track cannot be held and the heading falls
  back to the track bearing itself (max closing speed on the target).
  Returns (heading_rad, held) where held is False for the fallback.
  """
  w_cross = wu * math.cos(track_rad) - wv * math.sin(track_rad)  # +ve to right
  s = -w_cross / tas if tas > 0 else 2.0
  if abs(s) <= 1.0:
    return track_rad + math.asin(s), True
  return track_rad, False


def speed_to_fly_ratio(headwind_ratio, max_ratio=1.8):
  """V/V_bestglide that maximises ground L/D against headwind h = hw/V_bg.

  Polar: sink(V) = sink_bg/2 * ((V/V_bg)^3 + V_bg/V) (parabolic drag, best
  glide at V_bg). Never slower than V_bg (tailwind case uses best glide).
  """
  xs = np.linspace(1.0, max_ratio, 81)
  g = (xs - headwind_ratio) * xs / (xs ** 4 + 1.0)
  return float(xs[int(np.argmax(g))])


def simulate_glide_guided(lat, lon, pressure_pa, hours, grid, target, *,
                          ld=12.0, sink_sl=1.0, dt_s=10.0, guidance='crab',
                          stf=False, bias=(0.0, 0.0), taper=0.3,
                          arrive_km=3.0, hold=True):
  """Like simulate_glide but with wind-correcting guidance and perturbations.

  guidance: 'crab' holds the great-circle track to the target; 'direct'
  reproduces simulate_glide's point-at-target behaviour. stf: fly faster
  than best glide into headwinds. bias: constant (u, v) wind error added
  to the grid wind (m/s). taper: surface wind fraction of the 150 hPa wind
  (simulate_glide uses 0.3). Once within arrive_km of the target the glider
  holds station overhead (hold=True) and spirals down; the altitude at that
  moment is the arrival margin. Returns a dict incl. margin_km =
  arrival altitude * L/D (still-air range in hand) or -miss distance.
  """
  alt = isa_altitude(pressure_pa)
  start_alt = alt
  t, dist_km, arr_alt, held_all = 0.0, 0.0, None, True
  tlat, tlon = target
  while alt > 0.0:
    rho = isa_density(alt)
    sink = sink_sl * math.sqrt(RHO_SL / rho)
    tas = ld * sink
    p = isa_pressure(alt)
    if p <= P_MAX:
      u, v = grid.lookup(lat, lon, np.array([max(p, P_MIN)]), hours + t / 3600.0)
      wu, wv = float(u[0]), float(v[0])
    else:
      u, v = grid.lookup(lat, lon, np.array([P_MAX]), hours + t / 3600.0)
      k = taper + (1.0 - taper) * max(alt, 0.0) / ALT_150
      wu, wv = k * float(u[0]), k * float(v[0])
    wu, wv = wu + bias[0], wv + bias[1]
    d = haversine_km(lat, lon, tlat, tlon)
    b = bearing_rad(lat, lon, tlat, tlon)
    if stf:
      hw = -(wu * math.sin(b) + wv * math.cos(b)) / tas
      x = speed_to_fly_ratio(hw)
      sink, tas = sink * 0.5 * (x ** 3 + 1.0 / x), tas * x
    if guidance == 'crab':
      hdg, ok = crab_heading(b, tas, wu, wv)
      held_all &= ok
    else:
      hdg = b
    gu, gv = tas * math.sin(hdg) + wu, tas * math.cos(hdg) + wv
    if arr_alt is None and d < arrive_km:
      arr_alt = alt
    if hold and arr_alt is not None:
      gu = gv = 0.0
    step = min(dt_s, alt / sink)
    lat += math.degrees(gv * step / (EARTH_KM * 1000.0))
    lon += math.degrees(gu * step / (EARTH_KM * 1000.0 * math.cos(math.radians(lat))))
    dist_km += math.hypot(gu, gv) * step / 1000.0
    alt -= sink * step
    t += step
  d1 = haversine_km(lat, lon, tlat, tlon)
  return dict(duration_s=t, start_alt_m=start_alt, end_lat=lat, end_lon=lon,
              ground_dist_km=dist_km, dist_to_target_end_km=d1,
              arrival_alt_m=arr_alt, track_held=held_all,
              margin_km=(arr_alt * ld / 1000.0 if arr_alt is not None else -d1),
              reached=d1 < REACH_KM)

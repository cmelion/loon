"""Vectorised version of glide.simulate_glide_guided for many gliders at once.

Used by glide_tuning.py to evaluate release policies (every flight-hour x
every recovery site within range), the robustness Monte Carlo and the
design sweep. Physics identical to glide.py (ISA, sink ~ sqrt(rho_sl/rho),
TAS = L/D * sink, grid winds 150-30 hPa, tapered 150 hPa wind below),
plus:
  * crab guidance (hold the great-circle track; fall back to pointing at
    the target when the cross wind exceeds the airspeed),
  * optional speed-to-fly into headwinds,
  * per-glider wind perturbations: constant bias (u, v), surface taper
    factor, and an AR(1) gust/forecast-noise term,
  * station-hold once within arrive_km of the target (arrival altitude ->
    margin_km = arrival altitude * L/D, or -miss distance if not reached).
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glide  # noqa: E402

G0, R_AIR = glide.G0, glide.R_AIR
P_SL, T_SL, RHO_SL = glide.P_SL, glide.T_SL, glide.RHO_SL
P_TROPO, P_STRAT = glide.P_TROPO, glide.P_STRAT
P_MIN, P_MAX, ALT_150 = glide.P_MIN, glide.P_MAX, glide.ALT_150
EARTH_M = glide.EARTH_KM * 1000.0
CL = 0.8


def isa_altitude(p):
  p = np.asarray(p, float)
  a0 = T_SL / 0.0065 * (1.0 - (p / P_SL) ** (1.0 / 5.25588))
  a1 = 11000.0 + R_AIR * 216.65 / G0 * np.log(P_TROPO / p)
  a2 = 20000.0 + 216.65 / 0.001 * ((p / P_STRAT) ** (-R_AIR * 0.001 / G0) - 1.0)
  return np.where(p > P_TROPO, a0, np.where(p > P_STRAT, a1, a2))


def isa_pressure(h):
  h = np.asarray(h, float)
  p0 = P_SL * np.clip(1.0 - 0.0065 * h / T_SL, 1e-6, None) ** 5.25588
  p1 = P_TROPO * np.exp(-G0 * (h - 11000.0) / (R_AIR * 216.65))
  t = 216.65 + 0.001 * (h - 20000.0)
  p2 = P_STRAT * (t / 216.65) ** (-G0 / (R_AIR * 0.001))
  return np.where(h < 11000.0, p0, np.where(h < 20000.0, p1, p2))


def isa_density(h):
  h = np.asarray(h, float)
  t = np.where(h < 11000.0, T_SL - 0.0065 * h,
               np.where(h < 20000.0, 216.65, 216.65 + 0.001 * (h - 20000.0)))
  return isa_pressure(h) / (R_AIR * t)


def haversine_km(lat1, lon1, lat2, lon2):
  p1, p2 = np.radians(lat1), np.radians(lat2)
  dl = np.radians(lon2 - lon1)
  a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
  return 2 * glide.EARTH_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def bearing_rad(lat1, lon1, lat2, lon2):
  p1, p2 = np.radians(lat1), np.radians(lat2)
  dl = np.radians(lon2 - lon1)
  x = np.sin(dl) * np.cos(p2)
  y = np.cos(p1) * np.sin(p2) - np.sin(p1) * np.cos(p2) * np.cos(dl)
  return np.arctan2(x, y)


def sink_for_wing_loading(wl_kg_m2, ld, cl=CL):
  """Sea-level sink (m/s) for wing loading W/S at best glide (glider_sizing)."""
  v = math.sqrt(2.0 * wl_kg_m2 * 9.81 / (RHO_SL * cl))
  return v / ld


class BatchGrid:
  """Vectorised lookup on a europe_ble.WindGrid (non-ring grids)."""

  def __init__(self, grid):
    self.u, self.v = grid.u, grid.v
    self.lats, self.lons = grid.lats, grid.lons
    self.logp = grid.logp  # decreasing
    self.nt = grid.nt
    self.dt_h = getattr(grid, 'dt_h', 1.0)
    # Pressure range the grid covers; below p_max (higher pressure) the old
    # taper applies, so a full-column grid (to 1000 hPa) uses real winds.
    self.p_min = float(np.exp(self.logp.min()))
    self.p_max = float(np.exp(self.logp.max()))
    self.alt_pmax = float(isa_altitude(np.array(self.p_max)))
    assert not getattr(grid, 'ring', False)

  @staticmethod
  def _idx(axis, val):
    if axis[0] > axis[-1]:
      axis, val = -axis, -val
    f = np.interp(val, axis, np.arange(len(axis)))
    i0 = np.minimum(np.floor(f).astype(int), len(axis) - 2)
    return i0, f - i0

  def lookup(self, lat, lon, p, hours):
    ia, wa = self._idx(self.lats, lat)
    ib, wb = self._idx(self.lons, lon)
    ip, wp = self._idx(self.logp, np.log(p))
    h = np.clip(hours / self.dt_h, 0, self.nt - 1.001)
    it = h.astype(int)
    wt = h - it
    out = []
    for g in (self.u, self.v):
      acc = 0.0
      for da, fa in ((0, 1 - wa), (1, wa)):
        for db, fb in ((0, 1 - wb), (1, wb)):
          for dp, fp in ((0, 1 - wp), (1, wp)):
            for dtt, ft in ((0, 1 - wt), (1, wt)):
              acc = acc + fa * fb * fp * ft * g[ia + da, ib + db, ip + dp, it + dtt]
      out.append(acc)
    return out


_STF_H = np.linspace(-1.0, 4.0, 251)
_STF_X = np.array([glide.speed_to_fly_ratio(h) for h in _STF_H])


def glide_batch(bg, lat, lon, pa, hours, tlat, tlon, *, ld, sink_sl,
                guidance='crab', stf=False, bias_u=0.0, bias_v=0.0, taper=0.3,
                noise_sd=0.0, noise_tau_s=900.0, rng=None, dt_s=30.0,
                arrive_km=3.0, hold=True, max_steps=4000):
  """Glide N payloads from (lat, lon, pa) toward (tlat, tlon).

  All position/time arguments are arrays of length N (or broadcastable);
  bias_u/v and taper may be arrays (per-glider perturbations). Returns a
  dict of length-N arrays: end_lat, end_lon, miss_km, arrived, arrival_alt,
  margin_km, duration_s, ground_km, held (crab never saturated).
  """
  lat = np.array(lat, float).copy(); lon = np.array(lon, float).copy()
  n = lat.size
  tlat = np.broadcast_to(np.asarray(tlat, float), (n,))
  tlon = np.broadcast_to(np.asarray(tlon, float), (n,))
  hours = np.broadcast_to(np.asarray(hours, float), (n,))
  bias_u = np.broadcast_to(np.asarray(bias_u, float), (n,))
  bias_v = np.broadcast_to(np.asarray(bias_v, float), (n,))
  taper = np.broadcast_to(np.asarray(taper, float), (n,))
  alt = isa_altitude(np.broadcast_to(np.asarray(pa, float), (n,))).copy()
  t = np.zeros(n); ground = np.zeros(n)
  arr_alt = np.full(n, np.nan); held = np.ones(n, bool)
  nu = np.zeros(n); nv = np.zeros(n)
  if noise_sd > 0:
    rng = rng or np.random.default_rng(0)
    a = math.exp(-dt_s / noise_tau_s)
    nu = rng.normal(0, noise_sd, n); nv = rng.normal(0, noise_sd, n)
  for _ in range(max_steps):
    active = alt > 0.0
    if not active.any():
      break
    rho = isa_density(np.maximum(alt, 0.0))
    sink = sink_sl * np.sqrt(RHO_SL / rho)
    tas = ld * sink
    p = isa_pressure(np.maximum(alt, 0.0))
    wu, wv = bg.lookup(lat, lon, np.clip(p, bg.p_min, bg.p_max), hours + t / 3600.0)
    k = np.where(p > bg.p_max,
                 taper + (1.0 - taper) * np.maximum(alt, 0.0) / bg.alt_pmax, 1.0)
    wu = k * wu + bias_u + nu
    wv = k * wv + bias_v + nv
    if noise_sd > 0:
      nu = a * nu + math.sqrt(1 - a * a) * rng.normal(0, noise_sd, n)
      nv = a * nv + math.sqrt(1 - a * a) * rng.normal(0, noise_sd, n)
    d = haversine_km(lat, lon, tlat, tlon)
    b = bearing_rad(lat, lon, tlat, tlon)
    sb, cb = np.sin(b), np.cos(b)
    if stf:
      hw = -(wu * sb + wv * cb) / tas
      x = np.interp(hw, _STF_H, _STF_X)
      sink = sink * 0.5 * (x ** 3 + 1.0 / x)
      tas = tas * x
    if guidance == 'crab':
      w_cross = wu * cb - wv * sb
      s = -w_cross / tas
      ok = np.abs(s) <= 1.0
      held &= ok | ~active
      hdg = b + np.where(ok, np.arcsin(np.clip(s, -1, 1)), 0.0)
    else:
      hdg = b
    gu = tas * np.sin(hdg) + wu
    gv = tas * np.cos(hdg) + wv
    newly = np.isnan(arr_alt) & (d < arrive_km) & active
    arr_alt[newly] = alt[newly]
    if hold:
      stop = ~np.isnan(arr_alt)
      gu = np.where(stop, 0.0, gu); gv = np.where(stop, 0.0, gv)
    step = np.where(active, np.minimum(dt_s, alt / sink), 0.0)
    lat += np.degrees(gv * step / EARTH_M)
    lon += np.degrees(gu * step / (EARTH_M * np.cos(np.radians(lat))))
    ground += np.hypot(gu, gv) * step / 1000.0
    alt -= sink * step
    t += step
  miss = haversine_km(lat, lon, tlat, tlon)
  arrived = ~np.isnan(arr_alt)
  margin = np.where(arrived, np.nan_to_num(arr_alt) * ld / 1000.0, -miss)
  return dict(end_lat=lat, end_lon=lon, miss_km=miss, arrived=arrived,
              arrival_alt=arr_alt, margin_km=margin, duration_s=t,
              ground_km=ground, held=held, reached=miss < glide.REACH_KM)

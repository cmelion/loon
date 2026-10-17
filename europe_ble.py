"""Run Google's Balloon Learning Environment over Europe with real 2025 winds.

Stock BLE uses synthetic (VAE-generated) winds and places balloons within
±10° of the equator. This module swaps in:
  * EuropeWindField: real hourly GFS winds (Open-Meteo archive, 2025) at
    150/100/70/50/30 hPa, interpolated in lat, lon, log-pressure and time.
    BLE's simplex noise is still added on top, so the agent's "forecast"
    differs from the "true" winds it actually flies in.
  * EuropeArena: a BalloonArena whose station sits at a chosen European
    lat/lng and whose episode starts at a chosen 2025 date-time (so solar
    power, day length and winds all follow the real season and latitude).
"""
import datetime as dt
import math

import jax
import numpy as np
from s2sphere import LatLng

from balloon_learning_environment.env import balloon_arena, features, wind_field
from balloon_learning_environment.env.balloon import balloon, control, stable_init
from balloon_learning_environment.utils import sampling, units

T0 = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)
EARTH_KM = 6371.0


class WindGrid:
  """Gridded u/v [lat, lon, level, t] with vectorised trilinear lookup.

  Optional npz keys: dt_h (hours per time step, default 1) and ring (lons
  form a full 360° ring: longitudes wrap and time wraps around the year, so
  flights running into 2026 reuse early-2025 winds).
  """

  def __init__(self, path='data/gfs_europe_2025.npz'):
    d = np.load(path)
    self.u, self.v = d['u'], d['v']
    self.lats, self.lons = d['lats'], d['lons']
    self.logp = np.log(d['levels_hpa'] * 100.0)  # Pa, decreasing
    self.dt_h = float(d['dt_h']) if 'dt_h' in d else 1.0
    self.ring = bool(d['ring']) if 'ring' in d else False
    if self.ring:  # close the ring and the year so interpolation wraps
      self.u = np.concatenate([self.u, self.u[:, :1]], axis=1)
      self.v = np.concatenate([self.v, self.v[:, :1]], axis=1)
      self.u = np.concatenate([self.u, self.u[..., :1]], axis=3)
      self.v = np.concatenate([self.v, self.v[..., :1]], axis=3)
      self.lons = np.append(self.lons, self.lons[0] + 360.0)
    self.nt = self.u.shape[-1]

  @staticmethod
  def _idx(axis, val):
    """Fractional index into a monotonic axis, clamped to its ends."""
    if axis[0] > axis[-1]:
      axis, val = -axis, -val
    f = np.interp(val, axis, np.arange(len(axis)))
    i0 = np.minimum(np.floor(f).astype(int), len(axis) - 2)
    return i0, f - i0

  def lookup(self, lat, lon, pressures, hours):
    pressures = np.atleast_1d(pressures)
    ia, wa = self._idx(self.lats, lat)
    if self.ring:
      lon = self.lons[0] + (lon - self.lons[0]) % 360.0
    ib, wb = self._idx(self.lons, lon)
    ip, wp = self._idx(self.logp, np.log(pressures))
    h = hours / self.dt_h
    h = h % (self.nt - 1) if self.ring else np.clip(h, 0, self.nt - 1.001)
    it, wt = int(h), h - int(h)
    out = []
    for g in (self.u, self.v):
      # Bilinear in space, linear in time -> profile over levels.
      blk = g[ia:ia + 2, ib:ib + 2, :, it:it + 2]
      blk = blk[..., 0] * (1 - wt) + blk[..., 1] * wt
      blk = blk[0] * (1 - wa) + blk[1] * wa
      prof = blk[0] * (1 - wb) + blk[1] * wb
      out.append(prof[ip] * (1 - wp) + prof[ip + 1] * wp)
    return out


def offset_to_latlng(lat0, lon0, x_km, y_km):
  heading = math.atan2(x_km, y_km)
  ang = math.hypot(x_km, y_km) / EARTH_KM
  p0 = math.radians(lat0)
  lat = math.asin(math.sin(p0) * math.cos(ang) +
                  math.cos(p0) * math.sin(ang) * math.cos(heading))
  dlon = math.atan2(math.sin(heading) * math.sin(ang) * math.cos(p0),
                    math.cos(ang) - math.sin(p0) * math.sin(lat))
  return math.degrees(lat), lon0 + math.degrees(dlon)


class EuropeWindField(wind_field.WindField):
  """Real-data wind field centred on a station; x=east, y=north."""

  def __init__(self, grid: WindGrid, lat0: float, lon0: float):
    super().__init__()
    self.grid, self.lat0, self.lon0 = grid, lat0, lon0
    self.start_hours = 0.0

  def reset_forecast(self, unused_key, date_time: dt.datetime) -> None:
    self.start_hours = (date_time - T0).total_seconds() / 3600.0

  def _uv(self, x, y, pressures, elapsed):
    lat, lon = offset_to_latlng(self.lat0, self.lon0, x.km, y.km)
    hours = self.start_hours + elapsed.total_seconds() / 3600.0
    return self.grid.lookup(lat, lon, pressures, hours)

  def get_forecast(self, x, y, pressure, elapsed_time):
    u, v = self._uv(x, y, pressure, elapsed_time)
    return wind_field.WindVector(units.Velocity(mps=float(u[0])),
                                 units.Velocity(mps=float(v[0])))

  def get_forecast_column(self, x, y, pressures, elapsed_time):
    u, v = self._uv(x, y, np.asarray(pressures, float), elapsed_time)
    return [wind_field.WindVector(units.Velocity(mps=float(a)),
                                  units.Velocity(mps=float(b)))
            for a, b in zip(u, v)]


class EuropeArena(balloon_arena.BalloonArena):
  """BalloonArena with a fixed station location and start time."""

  def __init__(self, wf: EuropeWindField, start: dt.datetime, seed: int,
               feature_factory=features.PerciatelliFeatureConstructor,
               launch_radius_km: float = 200.0):
    self._start = start
    self._launch_radius_km = launch_radius_km
    super().__init__(feature_factory, wf, seed)

  def reset(self, seed=None):
    self._rng = jax.random.PRNGKey(seed if isinstance(seed, int) else 0)
    self._rng, akey = jax.random.split(self._rng)
    self._atmosphere.reset(akey)
    self._balloon = self._init(self._start)
    self._rng, wkey = jax.random.split(self._rng)
    self._wind_field.reset(wkey, self._start)
    self.feature_constructor = self._feature_constructor_factory(
        self._wind_field, self._atmosphere)
    self.feature_constructor.observe(self.get_measurements())
    return self.feature_constructor.get_features()

  def _init(self, start):
    # Same as BLE's initialiser (launch within 200 km of station, random
    # bearing and pressure), but centred on the real European station.
    self._rng, *k = jax.random.split(self._rng, 5)
    r = units.Distance(km=self._launch_radius_km * jax.random.beta(k[0], 1.2, 2.0).item())
    th = jax.random.uniform(k[1], (), minval=0.0, maxval=2 * math.pi).item()
    b = balloon.Balloon(balloon.BalloonState(
        center_latlng=LatLng.from_degrees(self._wind_field.lat0,
                                          self._wind_field.lon0),
        x=math.cos(th) * r, y=math.sin(th) * r,
        pressure=sampling.sample_pressure(k[2], self._atmosphere),
        date_time=start,
        upwelling_infrared=sampling.sample_upwelling_infrared(k[3])))
    stable_init.cold_start_to_stable_params(b.state, self._atmosphere)
    return b

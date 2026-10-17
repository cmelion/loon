"""Forecast-lookahead altitude planner: maximise time over the region.

Every replanning step the balloon projects kinematic trajectories through
the forecast wind field (no balloon physics, just advection at a fixed
pressure per segment) for HORIZON_H hours, choosing one pressure level per
SEGMENT_H-hour segment with a beam search. A trajectory scores by how many
projected half-hour steps stay inside the region, tie-broken by its final
margin from the region boundary. The first segment's level is returned.
"""
import math

import numpy as np

SEGMENT_H = 6
HORIZON_H = 36
DT_H = 0.5
BEAM = 6
N_LEVELS = 8
KM_PER_DEG = 111.2


def margin_km(lat, lon, region):
  c = math.cos(math.radians(lat))
  return min((lat - region['lat0']) * KM_PER_DEG,
             (region['lat1'] - lat) * KM_PER_DEG,
             (lon - region['lon0']) * KM_PER_DEG * c,
             (region['lon1'] - lon) * KM_PER_DEG * c)


def _advect(grid, lat, lon, p, hours, n):
  inside = 0
  for _ in range(n):
    u, v = grid.lookup(lat, lon, np.array([p]), hours)
    lat += float(v[0]) * DT_H * 3.6 / KM_PER_DEG
    lon += float(u[0]) * DT_H * 3.6 / (KM_PER_DEG * math.cos(math.radians(lat)))
    hours += DT_H
    yield lat, lon, hours


def plan(grid, lat, lon, hours, p_min, p_max, region):
  """Return the pressure (Pa) to fly now."""
  levels = np.linspace(p_min, p_max, N_LEVELS)
  n = int(SEGMENT_H / DT_H)
  # beam entries: (inside_steps, lat, lon, hours, first_level, alive)
  beam = [(0, lat, lon, hours, None, True)]
  for _ in range(int(HORIZON_H / SEGMENT_H)):
    nxt = []
    for inside, la, lo, h, first, alive in beam:
      for p in levels:
        cnt, a, b, t, ok = inside, la, lo, h, alive
        for a2, b2, t2 in _advect(grid, la, lo, p, h, n):
          if not ok:
            break
          a, b, t = a2, b2, t2
          if margin_km(a, b, region) > 0:
            cnt += 1
          else:
            ok = False
        nxt.append((cnt, a, b, t, p if first is None else first, ok))
    nxt.sort(key=lambda e: (e[0], margin_km(e[1], e[2], region)), reverse=True)
    beam = nxt[:BEAM]
  return float(beam[0][4])

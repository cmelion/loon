"""Coarse China mask for routing balloons around it (35-60°N band only).

Northern border approximated by a piecewise-linear lat(lon) through points
read off a map (±~0.5°, enough for a 2.5° wind grid). South of that line and
between 73.5 and 135°E counts as China, except the Korean peninsula (east of
124.5°E, south of 43°N). Not a legal boundary.
"""
import numpy as np

_BORDER = np.array([
    (73.5, 39.5), (75, 40.5), (80, 43.0), (82.5, 45.0), (85, 47.0), (87, 49.2),
    (90, 47.8), (95, 44.5), (100, 42.5), (105, 41.8), (110, 42.5), (115, 45.0),
    (118, 47.5), (120, 50.5), (122, 52.5), (124, 53.5), (127, 52.5), (130, 48.5),
    (133, 48.3), (135, 48.4)])


def north_border(lon):
  """China's northern border latitude at lon (°E), or None outside 73.5-135°E."""
  if not _BORDER[0, 0] <= lon <= _BORDER[-1, 0]:
    return None
  return float(np.interp(lon, _BORDER[:, 0], _BORDER[:, 1]))


def in_china(lat, lon):
  b = north_border(lon)
  if b is None or lat > b or lat < 21.0:
    return False
  return not (lon > 124.5 and lat < 43.0)


def corridor_floor(lon, lookahead=45.0, margin=2.5):
  """Lowest safe latitude for the next `lookahead` degrees of eastward travel."""
  ahead = [north_border(l) for l in np.arange(lon, lon + lookahead + 0.1, 2.5)]
  ahead = [a for a in ahead if a is not None]
  return max(ahead) + margin if ahead else None

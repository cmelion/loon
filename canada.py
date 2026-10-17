"""Coarse Canada mask (south of 60°N) for counting balloon service time.

Southern border approximated by longitude bands (Pacific coast and prairies
at 49°N, Great Lakes/St Lawrence ~45°N, Maritimes ~43.5°N). Not a legal
boundary; good to ~1° for a 2.5° wind grid.
"""


def in_canada(lat, lon):
  if not -141.0 <= lon <= -52.0 or lat > 60.0:
    return False
  if lon < -95.0:
    return lat >= 49.0
  if lon < -67.0:
    return lat >= 45.0
  return lat >= 43.5


def in_north_atlantic(lat, lon):
  """Shipping-lane band between Canada and Europe (sea only, caller checks land)."""
  return 40.0 <= lat <= 60.0 and -52.0 < lon < -10.0

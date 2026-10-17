"""Where envelopes land (slow controller, results/drift_2025.csv), using the
same classification as analyze_envelopes.py (land mask + sea boxes) without
re-drawing its figure. Prints land/sea shares and parachute drift statistics.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from global_land_mask import globe  # noqa: E402


def where(lat, lon):  # copy of analyze_envelopes.where
  if np.isnan(lat):
    return None
  if globe.is_land(lat, lon):
    return 'land'
  if 40.5 <= lat <= 47.5 and 27.0 <= lon <= 42.0:
    return 'Black Sea'
  if 30.0 <= lat <= 46.0 and -6.0 <= lon <= 37.0:
    return 'Mediterranean'
  if lat >= 53.5 and 9.0 <= lon <= 31.0:
    return 'Baltic'
  if 50.0 <= lat and -4.0 <= lon <= 9.0:
    return 'North Sea'
  if 45.0 <= lat <= 48.0 and 46.0 <= lon <= 55.0:
    return 'Caspian'
  return 'Atlantic/other'


df = pd.read_csv('results/drift_2025.csv')
slow = df[df.controller == 'slow'].copy()
slow['a'] = [where(a, b) for a, b in zip(slow.env_a_lat, slow.env_a_lon)]
slow['b'] = [where(a, b) for a, b in zip(slow.env_b_lat, slow.env_b_lon)]
slow['a_or_b'] = slow.a.fillna(slow.b)
for col, name in [('a_or_b', 'A: cut down with radio release'), ('b', 'B: flown to region exit')]:
  print(f'\n{name} (n={len(slow)}):')
  print((slow[col].value_counts(normalize=True) * 100).round(1).to_string())
lat = slow.env_a_lat.fillna(slow.env_b_lat); lon = slow.env_a_lon.fillna(slow.env_b_lon)
d = np.hypot((lat - slow.release_lat) * 111, (lon - slow.release_lon) * 111 * np.cos(np.radians(lat)))
print(f'\nA: parachute drift during descent: median {np.nanmedian(d):.0f} km, '
      f'P10 {np.nanpercentile(d,10):.0f}, P90 {np.nanpercentile(d,90):.0f} km (n={np.isfinite(d).sum()})')
print(f'Radio recovered (today glider, fixed-150 rule): {slow.recovered.mean():.1%}; '
      f'flights with a release: {slow.release_h.notna().mean():.1%}')

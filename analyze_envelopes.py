"""Where do the envelopes come down? (results/drift_2025.csv)

A: envelope cut down at the radio-release point (one termination event).
B: envelope flown on until it leaves the region / ends, then cut down.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from global_land_mask import globe

ENVELOPE_KG = 68.5  # BLE's envelope mass
LAUNCHES_PER_DAY = 310  # slow controller, from analyze_drift.py


def where(lat, lon):
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
df['a'] = [where(a, b) for a, b in zip(df.env_a_lat, df.env_a_lon)]
df['b'] = [where(a, b) for a, b in zip(df.env_b_lat, df.env_b_lon)]
# Scenario A falls back to B for flights that never passed a recovery site.
df['a_or_b'] = df.a.fillna(df.b)
slow = df[df.controller == 'slow']

for col, name in [('a_or_b', 'A: cut down with radio release'),
                  ('b', 'B: flown to region exit')]:
  print(f'\n{name} (slow controller, n={len(slow)}):')
  print((slow[col].value_counts(normalize=True) * 100).round(0).to_string())

lat = slow.env_a_lat.fillna(slow.env_b_lat)
lon = slow.env_a_lon.fillna(slow.env_b_lon)
d = np.hypot((lat - slow.release_lat) * 111,
             (lon - slow.release_lon) * 111 * np.cos(np.radians(lat)))
print(f'\nA: median drift during parachute descent {np.nanmedian(d):.0f} km')
print(f'Envelope film per year at {LAUNCHES_PER_DAY}/day: '
      f'{LAUNCHES_PER_DAY * 365 * ENVELOPE_KG / 1000:,.0f} t')

# Map: land mask background + both scenarios.
la, lo = np.linspace(30, 66, 360), np.linspace(-20, 60, 800)
LO, LA = np.meshgrid(lo, la)
fig, ax = plt.subplots(figsize=(12, 6.5))
ax.imshow(globe.is_land(LA, LO), origin='lower', extent=[-20, 60, 30, 66],
          cmap='Greys', vmin=0, vmax=4, aspect=1.4)
ax.add_patch(plt.Rectangle((-10, 36), 52, 23.5, fill=False, ls='--', lw=1))
ax.scatter(slow.env_b_lon, slow.env_b_lat, s=14, c='#d62728', alpha=.6,
           label='B: flown to region exit')
ax.scatter(lon, lat, s=14, c='#1f77b4', alpha=.7,
           label='A: cut down at radio release')
ax.set_xlim(-20, 60); ax.set_ylim(30, 66)
ax.set_title('Envelope landing points, slow controller, 2025 '
             '(dashed = coverage region)')
ax.legend(loc='lower left'); fig.tight_layout()
fig.savefig('results/envelope_landings.png', dpi=150)

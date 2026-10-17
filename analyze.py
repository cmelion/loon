"""Summarise the BLE Europe sweep: heatmap + rough fleet-size estimate."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from run_coverage import STATIONS

df = pd.read_csv('results/coverage_2025.csv')
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct',
          'Nov', 'Dec']
order = sorted(STATIONS, key=lambda s: STATIONS[s][1])  # west -> east
tab = df.pivot_table(index='station', columns='month', values='twr50').loc[order]

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(tab.values, cmap='viridis', vmin=0, vmax=1, aspect='auto')
ax.set_xticks(range(12), months)
ax.set_yticks(range(len(order)), [f'{s} ({STATIONS[s][1]:.0f}°E)' for s in order])
for i in range(tab.shape[0]):
  for j in range(12):
    v = tab.values[i, j]
    ax.text(j, i, f'{v:.2f}', ha='center', va='center', fontsize=7,
            color='white' if v < 0.5 else 'black')
fig.colorbar(im, label='TWR50 (fraction of time within 50 km)')
ax.set_title('BLE StationSeeker over Europe, real 2025 GFS winds\n'
             '(mean of two 2-day flights per month; stations west→east)')
fig.tight_layout()
fig.savefig('results/twr50_heatmap.png', dpi=150)

# Rough fleet sizing: tile the region with 50 km-radius cells; a cell is
# covered by a balloon a fraction TWR50 of the time, so to keep every cell
# covered on average you need about cells / TWR50 balloons.
lat0, lat1, lon0, lon1 = 36.0, 62.0, -10.0, 42.0
area = (6371.0 ** 2 * math.radians(lon1 - lon0) *
        (math.sin(math.radians(lat1)) - math.sin(math.radians(lat0))))
cells = area / (1.5 * math.sqrt(3) * 50.0 ** 2)  # hexagon area, r = 50 km
monthly = df.groupby('month').twr50.mean()
print(tab.round(2).to_string())
print('\nMean TWR50 by month:', monthly.round(2).to_dict())
print(f'Overall mean TWR50 {df.twr50.mean():.2f}; failures:',
      df.status.value_counts().to_dict())
print(f'\nRegion {lat0}-{lat1}N, {lon0}-{lon1}E ~ {area / 1e6:.1f} M km^2 '
      f'= {cells:.0f} cells of r=50 km')
for m, p in monthly.items():
  print(f'  {months[m - 1]}: ~{cells / max(p, 1e-3):,.0f} balloons')

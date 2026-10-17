"""How heavy can the return glider be? Recovery vs wing loading.

For a glider at lift coefficient CL, sea-level airspeed V = sqrt(2 W/S /
(rho CL)) and sink = V / (L/D), so wing loading W/S = 0.5 rho (sink*L/D)^2 CL.
Heavier loading -> faster sink (shorter transmit time) but faster airspeed
(better penetration into headwinds); still-air range is set by L/D alone.
We re-fly every slow-controller radio release from results/drift_2025.csv
(release point, time; end-of-flight pressure as the release-altitude proxy).
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glide  # noqa: E402
from europe_ble import T0, WindGrid  # noqa: E402
from run_drift import RECOVERY  # noqa: E402

CL = 0.8
SINKS = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0]  # sea-level sink, m/s
LDS = [10.0, 12.0, 15.0]


def wing_loading(sink_sl, ld):
  return 0.5 * 1.225 * (sink_sl * ld) ** 2 * CL / 9.81  # kg/m^2


def main():
  grid = WindGrid()
  df = pd.read_csv('results/drift_2025.csv')
  df = df[(df.controller == 'slow') & df.release_lat.notna()]
  hours = ((pd.to_datetime(df.start).dt.tz_localize('UTC') - T0)
           .dt.total_seconds() / 3600 + df.release_h).values
  rows = []
  for ld in LDS:
    for sink in SINKS:
      res = [glide.simulate_glide(r.release_lat, r.release_lon, r.end_hpa * 100,
                                  h, grid, target=RECOVERY[r.recovery],
                                  ld=ld, sink_sl=sink)
             for (_, r), h in zip(df.iterrows(), hours)]
      rows.append(dict(
          ld=ld, sink_sl=sink, wing_kg_m2=round(wing_loading(sink, ld), 1),
          tas_20km_ms=round(sink * ld * np.sqrt(1.225 / glide.isa_density(20000)), 0),
          recovered=np.mean([g['reached'] for g in res]),
          median_miss_km=np.median([g['dist_to_target_end_km'] for g in res]),
          descent_h=np.median([g['duration_s'] for g in res]) / 3600))
  out = pd.DataFrame(rows)
  out.to_csv('results/glider_sizing.csv', index=False)
  print(f'n = {len(df)} releases\n')
  print(out.round(2).to_string(index=False))
  print('\nWing area needed (m^2) for glider all-up mass, by wing loading:')
  for wl in sorted(set(out.wing_kg_m2)):
    print(f'  {wl:5.1f} kg/m^2: ' + '  '.join(
        f'{m} kg -> {m / wl:.1f}' for m in (20, 40, 60, 80)))


if __name__ == '__main__':
  main()

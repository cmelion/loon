"""Winter power budgets: battery vs fuel cell on the lift gas (vented or kept water).

Reads the four WINTER=1, MAX_DAYS=60 runs of run_multipass.py (20 flights each:
5 European sites x Nov-Feb launches, China avoidance + 3 m/s latitude hold,
propeller power charged to the battery) and compares survival, end reasons,
hydrogen burned, darkness and polar time, envelope pressure margin and
Europe coverage.
"""
import glob
import json

import numpy as np
import pandas as pd

LABELS = {
    'thrustcharged_winter60d': '3 kWh battery (BLE)',
    'bat10000_thrust3_thrustcharged_winter60d': '10 kWh battery',
    'fcvent_winter60d': 'Fuel cell, water vented',
    'fcretain_winter60d': 'Fuel cell, 10 kg water kept',
}


def label(path):
  for key, name in sorted(LABELS.items(), key=lambda kv: -len(kv[0])):
    if path.endswith('_' + key + '.jsonl'):
      return name
  return None


def main():
  rows = []
  for f in sorted(glob.glob('results/multipass_2025_nochina*winter60d.jsonl')):
    name = label(f)
    if not name:
      continue
    for line in open(f):
      r = json.loads(line)
      r['setup'] = name
      rows.append(r)
  df = pd.DataFrame(rows)
  order = [v for v in LABELS.values() if v in set(df.setup)]
  g = df.groupby('setup')
  t = pd.DataFrame({
      'flights': g.size(),
      'median_days': g.days.median(),
      'mean_days': g.days.mean(),
      'survived_60d': g.days.apply(lambda d: (d >= 59.9).mean()),
      'europe_days_mean': g.europe_days.mean(),
      'dark_h_median': g.dark_h.median(),
      'polar_h_median': g.polar_h.median(),
      'h2_kg_median': g.h2_kg.median(),
      'gas_used_median': g.gas_used_frac.median(),
      'water_vented_kg_median': g.water_vented_kg.median(),
  }).loc[order]
  pd.set_option('display.width', 220)
  print(t.round(2).to_string())
  print('\nHow flights ended:')
  print(pd.crosstab(df.setup, df.end).loc[order].to_string())
  dead = df[df.end.isin(['ZEROPRESSURE', 'NO_SAFE_ALTITUDE'])]
  if len(dead):
    print('\nGas burned when the envelope gave out (fuel-cell runs): '
          f'{dead.gas_used_frac.min():.0%}-{dead.gas_used_frac.max():.0%} of the lift gas, '
          f'{dead.h2_kg.min():.2f}-{dead.h2_kg.max():.2f} kg H2')
  t.to_csv('results/winter_power_summary.csv')


if __name__ == '__main__':
  main()

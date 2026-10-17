"""Stress test for jet_test.py: scale NCEP winds below 150 hPa (x1.3, x1.6)
to stand in for jet cores that a 2.5-degree, 6-hourly reanalysis smooths out.
Output: results/jet_stress.csv"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glide_batch as gb  # noqa: E402
import glide_tuning as gt  # noqa: E402
from europe_ble import WindGrid  # noqa: E402
from jet_test import designs  # noqa: E402


def main():
  tr = gt.Tracks()
  rows = []
  for scale in (1.0, 1.3, 1.6):
    g = WindGrid('data/ncep_europe_full_2025.npz')
    low = np.exp(g.logp) > 15000 + 1  # levels below 150 hPa (higher pressure)
    g.u = g.u.copy(); g.v = g.v.copy()
    g.u[:, :, low, :] *= scale; g.v[:, :, low, :] *= scale
    bg = gb.BatchGrid(g)
    for dname, design in designs():
      r = gt.nominal_margins(bg, tr, design, 'crab', True)
      mats = gt.margin_matrix(tr, r)
      rel = gt.releases(tr, mats[0], 'causal120', 100.0)
      mc = gt.mc_eval(bg, tr, rel, design, 'crab', True)
      s = gt.summarise(tr, rel, mats, mc, 'causal120-100')
      rows.append(dict(low_wind_scale=scale, design=dname, recovered=s['mc_rec'],
                       p10=s['mc_p10'], p90=s['mc_p90'], worst=len(s['worst_flights'])))
      print(rows[-1], flush=True)
  pd.DataFrame(rows).to_csv('results/jet_stress.csv', index=False)


if __name__ == '__main__':
  main()

"""Blackout backfill sizing for a named zone, with outage_scenario.py's formulas
and constants (imported, not modified), for a population and month of choice.

  demand      = population x active share x per-user rate
  balloons    = max(demand / per-balloon capacity, one per 40 km cell)
  launches/d  = balloons x 24 / crossing hours (crossing = 2R / drift speed)
  cost/d      = launches/d x per-flight cost (combined_cost.py best/mid/worst)
Drift speed = median mean_speed_kmh of the 'slow' flights launched in the
given months (results/drift_2025.csv), as in outage_scenario.py.
Usage: python scenarios/tools/outage_case.py --name Iberia --pop-m 58 --radius-km 450 --months 4 5
"""
import argparse
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
import pandas as pd  # noqa: E402
import outage_scenario as osc  # noqa: E402


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument('--name', required=True)
  ap.add_argument('--pop-m', type=float, required=True)
  ap.add_argument('--radius-km', type=float, required=True)
  ap.add_argument('--months', type=int, nargs='+', required=True)
  ap.add_argument('--out')
  a = ap.parse_args()
  d = pd.read_csv('results/drift_2025.csv')
  speed = d[d.controller == 'slow'].groupby('month').mean_speed_kmh.median()
  v = speed.loc[a.months].mean()
  area = math.pi * a.radius_km ** 2
  cross_h = 2 * a.radius_km / v
  pop = a.pop_m * 1e6
  rows = []
  for svc, (share, mbps) in osc.SERVICE.items():
    demand_tbps = pop * share * mbps / 1e6
    for cap in osc.BALLOON_GBPS:
      n = max(demand_tbps * 1e3 / cap, area / (math.pi * 40 ** 2))
      launches = n * 24 / cross_h
      rows.append(dict(service=svc, balloon_gbps=cap, demand_tbps=round(demand_tbps, 2),
                       balloons=round(n), launches_day=round(launches),
                       cost_m_eur_day=round(launches * osc.PER_FLIGHT_EUR[1] / 1e6, 2),
                       cost_range_m_eur_day=[round(launches * osc.PER_FLIGHT_EUR[0] / 1e6, 1),
                                             round(launches * osc.PER_FLIGHT_EUR[2] / 1e6, 1)],
                       edge_trunks=math.ceil(demand_tbps * 1e3 / osc.TRUNK_GBPS)))
  out = dict(script='scenarios/tools/outage_case.py (outage_scenario.py formulas/constants)',
             zone=a.name, pop_m=a.pop_m, radius_km=a.radius_km, area_km2=round(area),
             months=a.months, drift_speed_kmh=round(v, 1),
             monthly_median_speed_kmh={int(k): round(float(x), 1) for k, x in speed.items()},
             crossing_h=round(cross_h, 1), first_cover_h=[round(200 / v), round(500 / v)],
             min_balloons_one_per_cell=round(area / (math.pi * 40 ** 2)),
             starlink_tbps_pro_rata=round(osc.STARLINK_REGION_TBPS * area / osc.REGION_KM2, 2),
             allied_sat_tbps_pro_rata=round(osc.ALLIED_SAT_REGION_TBPS * area / osc.REGION_KM2, 3),
             per_flight_eur=osc.PER_FLIGHT_EUR, service_defs=osc.SERVICE, rows=rows)
  print(json.dumps(out, indent=1))
  if a.out:
    json.dump(out, open(a.out, 'w'), indent=1)


if __name__ == '__main__':
  main()

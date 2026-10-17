"""Regional ground-network loss: what a balloon surge must and can deliver.

A circular zone loses towers, fibre and grid power. Balloons stream through
it from upwind launchers (they cannot hover: drift speed by month from the
'slow' controller runs, results/drift_2025.csv). Sizing:
  demand      = population x active share x per-user rate
  balloons    = demand / per-balloon capacity (and at least one per cell)
  launches/d  = balloons x 24 / crossing hours (crossing = 2R / drift speed)
  cost/d      = launches/d x per-flight cost (combined_cost.py mid/best/worst)
  backhaul    = laser trunks at the zone edge to reach intact gateways
Compared with Starlink's and allied satellites' pro-rata capacity in the zone.
All demand and capacity inputs are ASSUMPTIONS, set below.
"""
import math
import os

import pandas as pd

REGION_KM2 = 10.85e6
STARLINK_REGION_TBPS = 21.0      # cost_model, Starlink share over the region
ALLIED_SAT_REGION_TBPS = 2.0     # KONNECT VHTS + other GEO + OneWeb + IRIS² share (~2030)
# Per-balloon capacity, low/mid/high. The original run used 1, 2, 5 Gbps (a
# 5G phased array). Rerun 5 of results/mitigation_research.md (W11) asks for
# Loon-class figures: BALLOON_GBPS=0.04,0.2,0.5. The output file carries the tag.
BALLOON_GBPS = tuple(float(x) for x in os.environ.get('BALLOON_GBPS', '1,2,5').split(','))
TAG = os.environ.get('TAG', '' if BALLOON_GBPS == (1.0, 2.0, 5.0) else '_' + '_'.join(f'{g:g}' for g in BALLOON_GBPS))
PER_FLIGHT_EUR = (6_700, 12_400, 27_200)  # combined_cost.py best/mid/worst
TRUNK_GBPS = 20.0                # one balloon-to-balloon laser trunk
DENSITY_PER_KM2 = 120.0          # ~Italy-like population density
SERVICE = {'basic (voice/text)': (0.15, 0.1), 'degraded data': (0.05, 1.0)}  # (active share, Mbps)
ZONES_KM = (150, 300, 500)
SEASONS = {'summer (Jun-Aug)': (6, 7, 8), 'winter (Dec-Feb)': (12, 1, 2)}


def main():
  d = pd.read_csv('results/drift_2025.csv')
  speed = d[d.controller == 'slow'].groupby('month').mean_speed_kmh.median()
  rows = []
  for r_km in ZONES_KM:
    area = math.pi * r_km ** 2
    pop = area * DENSITY_PER_KM2
    for sname, months in SEASONS.items():
      v = speed.loc[list(months)].mean()
      cross_h = 2 * r_km / v
      for svc, (share, mbps) in SERVICE.items():
        demand_tbps = pop * share * mbps / 1e6
        for k, cap in enumerate(BALLOON_GBPS):
          n = max(demand_tbps * 1e3 / cap, area / (math.pi * 40 ** 2))
          launches = n * 24 / cross_h
          rows.append(dict(
              zone_km=r_km, season=sname, service=svc, balloon_gbps=cap,
              pop_m=round(pop / 1e6, 1), demand_tbps=round(demand_tbps, 2),
              balloons=round(n), launches_day=round(launches),
              cost_m_eur_day=round(launches * PER_FLIGHT_EUR[1] / 1e6, 2),
              cost_range=f'{launches * PER_FLIGHT_EUR[0] / 1e6:.1f}-'
                         f'{launches * PER_FLIGHT_EUR[2] / 1e6:.1f}',
              edge_trunks=math.ceil(demand_tbps * 1e3 / TRUNK_GBPS),
              starlink_tbps=round(STARLINK_REGION_TBPS * area / REGION_KM2, 2),
              allied_sat_tbps=round(ALLIED_SAT_REGION_TBPS * area / REGION_KM2, 3),
              first_cover_h=f'{200 / v:.0f}-{500 / v:.0f}'))
  t = pd.DataFrame(rows)
  t.to_csv(f'results/outage_scenario{TAG}.csv', index=False)
  pd.set_option('display.width', 250)
  mid = t[t.balloon_gbps == BALLOON_GBPS[1]]
  print(mid.drop(columns=['balloon_gbps']).to_string(index=False))
  print('\nSensitivity to per-balloon capacity (300 km zone, degraded data):')
  print(t[(t.zone_km == 300) & (t.service == 'degraded data')][
      ['season', 'balloon_gbps', 'balloons', 'launches_day', 'cost_m_eur_day']].to_string(index=False))


if __name__ == '__main__':
  main()

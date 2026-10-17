"""scenario_ledger.py on a synthetic results/ folder.

Run: python -m pytest tests/test_ledger.py   or   python tests/test_ledger.py
"""
import os
import sys
import tempfile

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import scenario_ledger as sl  # noqa: E402


def _synthetic_results(root):
  os.makedirs(os.path.join(root, 'results'), exist_ok=True)
  rng = np.random.default_rng(0)
  rows = []
  for site in ('Lisbon', 'Brest'):
    for m in range(1, 13):
      for d in (1, 15):
        for ctrl in ('slow', 'passive'):
          dwell = 24 * (1.5 + 6 * (1 - np.cos(2 * np.pi * (m - 1) / 12)) / 2) * (0.7 + 0.6 * rng.random())
          rec = rng.random() < 0.9
          rows.append(dict(site=site, start=f'2025-{m:02d}-{d:02d}', month=m, controller=ctrl, seed=1,
                           dwell_h=round(dwell, 2), end='EXIT_E', release_h=round(dwell * 0.8, 2) if rec else np.nan,
                           glide_h=2.0 if rec else np.nan, recovered=rec))
  pd.DataFrame(rows).to_csv(os.path.join(root, 'results/drift_2025.csv'), index=False)
  pd.DataFrame([dict(zone_km=300, season='winter (Dec-Feb)', service='basic (voice/text)', balloon_gbps=g,
                     pop_m=34, demand_tbps=0.51, balloons=b, launches_day=l, cost_m_eur_day=1)
                for g, b, l in ((0.04, 12700, 22000), (0.2, 2540, 4430), (0.5, 1016, 1770))]
               ).to_csv(os.path.join(root, 'results/outage_scenario_0.04_0.2_0.5.csv'), index=False)
  pd.DataFrame([dict(radius_km=80, period=p, hours=100, covered_pop_share=cv, served_pop_share=sv, aloft_mean=100,
                     launches_per_day=30) for p, cv, sv in (('year', 0.4, 0.05), ('DJF', 0.3, 0.02))]
               ).to_csv(os.path.join(root, 'results/availability_2025_standing100_0.2gbps.csv'), index=False)
  pd.DataFrame([dict(standing=100, range_km=500, gateways='all', period='year', hours=10, aloft_mean=100,
                     gw_connected_share=0.9)]).to_csv(os.path.join(root, 'results/mesh_2025_standing100.csv'), index=False)
  pd.DataFrame([dict(zone='Vienna', zone_km=300, pop_m=5, n_required=50, case=cs, season='all', frac=0.5,
                     n_starts=10, hours_median=h, hours_p90=h * 2, never_share=0.1)
                for cs, h in (('cold', 40), ('warm100', 20))]).to_csv(os.path.join(root, 'results/time_to_n_2025.csv'), index=False)


def test_ledger_builds_and_is_traceable():
  root = tempfile.mkdtemp(prefix='loon_ledger_')
  _synthetic_results(root)
  cwd = os.getcwd()
  os.chdir(root)
  try:
    df = sl.main(['--standing', '100', '--gbps', '0.2'])
    assert os.path.exists('results/scenario_ledger.csv') and os.path.exists('results/scenario_ledger.md')
    assert set(df.scenario) == {'pilot', 'readiness', 'planning'}
    assert (df.source.str.len() > 0).all()
    r = df[df.scenario == 'readiness'].set_index('metric').value
    # surge row picked at 0.2 Gbps
    assert r['launches_per_day_surge'] == 4430 and r['surge_balloons_aloft'] == 2540
    # Little's law and inventory
    assert abs(r['launches_per_day_standing'] - 100 / r['service_dwell_days']) < 1e-9
    assert r['payload_inventory'] == max(r['launches_per_day_standing'], 4430) * r['payload_circulation_days']
    # availability, mesh and time-to-N files found and quoted
    assert r['served_pop_share_year'] == 0.05 and r['mesh_gateway_connected_share_500km'] == 0.9
    assert r['hours_to_half_requirement_cold_median_over_zones'] == 40
    # mass flow at three recovery rates, all-recovered leaves nothing
    assert r['envelope_mass_unrecovered_all_recovered'] == 0
    assert r['envelope_mass_unrecovered_none'] > r['envelope_mass_unrecovered_third_at_sea'] > 0
    assert r['cost_total_eur_yr_low'] < r['cost_total_eur_yr'] < r['cost_total_eur_yr_high']
    p = df[df.scenario == 'planning'].set_index('metric').value
    assert p['balloons_aloft_standing'] > r['balloons_aloft_standing']
  finally:
    os.chdir(cwd)


def test_dwell_from_drift_uses_release_where_recovered():
  root = tempfile.mkdtemp(prefix='loon_ledger2_')
  _synthetic_results(root)
  dw = sl.dwell_from_drift(os.path.join(root, 'results/drift_2025.csv'))
  assert dw['service_days_harm'] < dw['dwell_days_harm']
  assert dw['winter_service_days'] < dw['service_days_harm']
  assert 0.8 < dw['recovered'] <= 1.0


if __name__ == '__main__':
  for name, fn in list(globals().items()):
    if name.startswith('test_'):
      fn(); print('ok', name)

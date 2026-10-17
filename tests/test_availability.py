"""availability.py on synthetic tracks and population.

Run: python -m pytest tests/test_availability.py   or   python tests/test_availability.py
"""
import os
import sys
import tempfile

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import availability as av  # noqa: E402
import replay as rp  # noqa: E402
import synth  # noqa: E402

TMP = tempfile.mkdtemp(prefix='loon_avail_')
TRACKS = os.path.join(TMP, 'tracks.csv')
POP = os.path.join(TMP, 'pop.csv')
synth.synthetic_tracks(TRACKS)
synth.synthetic_population(POP, cell_km=50)
TR = rp.Tracks(TRACKS)
CELLS = rp.load_population(POP, cell_km=50)
HOURS = np.arange(0, 8760, 24, dtype=float)


def _run(launches, radii=(80.0,), gbps=0.2, mbps=0.015):
  return av.run_availability(TR, launches, CELLS, list(radii), gbps, mbps, HOURS, 2025, 24.0)


def test_no_launches_means_nothing_served():
  table, cells, outages, n = _run(rp.Launches(np.zeros(0), np.zeros(0, int), np.zeros(0)))
  assert (table.covered_pop_share == 0).all() and (table.served_pop_share == 0).all()
  assert n == 0


def test_disc_allocation_splits_capacity_by_population():
  from scipy.spatial import cKDTree
  cells = pd.DataFrame(dict(lat=[50.0, 50.0, 55.0], lon=[10.0, 10.3, 10.0], pop=[1000.0, 3000.0, 500.0]))
  cxyz = rp.xyz(cells.lat.to_numpy(), cells.lon.to_numpy())
  cap, hits = av.disc_allocation(cKDTree(cxyz), cxyz, cells['pop'].to_numpy(), rp.xyz([50.0], [10.1]), 80.0, 1.0)
  assert hits.tolist() == [1, 1, 0]
  assert abs(cap[0] - 0.25) < 1e-9 and abs(cap[1] - 0.75) < 1e-9 and cap[2] == 0
  # two balloons over the same cells add up
  cap2, hits2 = av.disc_allocation(cKDTree(cxyz), cxyz, cells['pop'].to_numpy(), rp.xyz([50.0, 50.1], [10.1, 10.1]), 80.0, 1.0)
  assert hits2.tolist() == [2, 2, 0] and abs(cap2.sum() - 2.0) < 1e-9


def test_more_balloons_cover_more_people_and_bigger_discs_cover_more():
  rng = np.random.default_rng(0)
  small = _run(rp.standing_launches(TR, 20, -720, 8760, rng), radii=(80.0, 194.0))[0]
  big = _run(rp.standing_launches(TR, 200, -720, 8760, rng), radii=(80.0, 194.0))[0]
  s80 = small[(small.radius_km == 80) & (small.period == 'year')].covered_pop_share.iloc[0]
  s194 = small[(small.radius_km == 194) & (small.period == 'year')].covered_pop_share.iloc[0]
  b80 = big[(big.radius_km == 80) & (big.period == 'year')].covered_pop_share.iloc[0]
  assert 0 < s80 < s194 <= 1
  assert b80 > s80
  assert ((small.served_pop_share <= small.covered_pop_share + 1e-9)).all()


def test_huge_capacity_makes_served_equal_covered():
  rng = np.random.default_rng(0)
  L = rp.standing_launches(TR, 50, -720, 8760, rng)
  t = _run(L, gbps=1e6)[0]
  assert np.allclose(t.served_pop_share, t.covered_pop_share)


def test_outage_table_has_both_metrics_and_sums_to_one():
  rng = np.random.default_rng(0)
  _, _, outages, _ = _run(rp.standing_launches(TR, 50, -720, 8760, rng))
  assert set(outages.metric) == {'covered', 'served'}
  for (_, m, s), g in outages.groupby(['radius_km', 'metric', 'season']):
    assert abs(g.episode_share.sum() - 1.0) < 1e-6, (m, s)


def test_cells_output_shares_in_unit_interval():
  rng = np.random.default_rng(0)
  _, cells, _, _ = _run(rp.standing_launches(TR, 50, -720, 8760, rng))
  assert cells.covered_share.between(0, 1).all() and cells.served_share.between(0, 1).all()
  assert len(cells) == len(CELLS)


def test_time_to_n_warm_start_is_not_slower_than_cold():
  rng = np.random.default_rng(0)
  zdf = av.zone_requirements(CELLS, {'Vienna': rp.RECOVERY['Vienna'], 'Lisbon': rp.RECOVERY['Lisbon']},
                             300.0, 0.2, 0.015, 40.0, n_required=10)
  assert (zdf.n_required == 10).all() and (zdf.pop_m > 0).all()
  starts = np.array([24 * 10.0, 24 * 100.0, 24 * 200.0])
  ttn = av.run_time_to_n(TR, CELLS, zdf, 12.0, [100], starts, 72, rng, 21 * 24, TR.sites)
  assert set(ttn.case) == {'cold', 'warm100'}
  v = ttn[(ttn.zone == 'Vienna') & (ttn.season == 'all') & (ttn.frac == 0.1)].set_index('case')
  assert v.loc['warm100', 'hours_median'] <= v.loc['cold', 'hours_median']
  assert ttn.never_share.between(0, 1).all()


def test_cli_end_to_end(tmp_path=None):
  cwd = os.getcwd()
  os.chdir(TMP)
  try:
    av.main(['--tracks', TRACKS, '--pop', POP, '--cell-km', '50', '--standing', '30', '--radius-km', '80',
             '--every-h', '24', '--time-to-n', '--every-start-h', '2000', '--horizon-h', '48',
             '--n-required', '5', '--tag', 'cli'])
    for f in ('availability_cli.csv', 'availability_cli_cells.csv', 'availability_cli_outages.csv', 'time_to_n_cli.csv'):
      assert os.path.exists(os.path.join('results', f)), f
    t = pd.read_csv('results/availability_cli.csv')
    assert {'radius_km', 'period', 'covered_pop_share', 'served_pop_share', 'aloft_mean', 'launches_per_day'} <= set(t.columns)
  finally:
    os.chdir(cwd)


if __name__ == '__main__':
  for name, fn in list(globals().items()):
    if name.startswith('test_'):
      fn(); print('ok', name)

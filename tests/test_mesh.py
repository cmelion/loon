"""mesh_connectivity.py: graph metrics on hand-placed balloons, and the replay run on synthetic tracks.

Run: python -m pytest tests/test_mesh.py   or   python tests/test_mesh.py
"""
import os
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import mesh_connectivity as mc  # noqa: E402
import replay as rp  # noqa: E402
import synth  # noqa: E402


def test_chain_connectivity_and_hops():
  # five balloons in a line 400 km apart along 50N; one gateway under the first
  lon = np.array([0.0, 5.6, 11.2, 16.8, 22.4])      # ~400 km steps at 50N
  lat = np.full(5, 50.0)
  gw = rp.xyz([50.0], [0.0])
  m500 = mc.hour_metrics(lat, lon, gw, 500.0, 200.0)
  assert m500['aloft'] == 5
  assert m500['largest_component_share'] == 1.0
  assert m500['gw_connected_share'] == 1.0
  assert m500['isolated_share'] == 0.0
  # the fifth balloon is 1 + 4 hops from the gateway: over four
  assert abs(m500['over_4_hops_share'] - 0.2) < 1e-9
  # at 300 km links the chain breaks into singletons
  m300 = mc.hour_metrics(lat, lon, gw, 300.0, 200.0)
  assert m300['isolated_share'] == 1.0 and abs(m300['largest_component_share'] - 0.2) < 1e-9
  assert abs(m300['gw_connected_share'] - 0.2) < 1e-9


def test_no_gateway_means_nobody_connected():
  m = mc.hour_metrics(np.array([50.0, 50.0]), np.array([0.0, 1.0]), np.zeros((0, 3)), 500.0, 200.0)
  assert m['gw_connected_share'] == 0.0 and m['over_4_hops_share'] == 1.0 and m['mean_degree'] == 1.0


def test_empty_hour():
  m = mc.hour_metrics(np.zeros(0), np.zeros(0), rp.xyz([50.0], [0.0]), 500.0, 200.0)
  assert m['aloft'] == 0 and np.isnan(m['gw_connected_share'])


def test_gateway_grid_spacing():
  g = mc.gateway_grid(350.0)
  assert 50 < len(g) < 120, len(g)


def test_replay_run_bigger_layer_is_better_connected():
  tmp = tempfile.mkdtemp(prefix='loon_mesh_')
  path = os.path.join(tmp, 'tracks.csv')
  synth.synthetic_tracks(path)
  tr = rp.Tracks(path)
  rng = np.random.default_rng(0)
  hours = np.arange(0, 8760, 24 * 5, dtype=float)
  table, ng, ns = mc.run(tr, [25, 100], hours, dict(rp.RECOVERY), (44, 56, -12, 8), [500.0, 700.0], 200.0, rng,
                         21 * 24, tr.sites)
  assert ng == 21 and ns < ng
  y = table[table.period == 'year'].set_index(['standing', 'range_km', 'gateways'])
  assert y.loc[(100, 500.0, 'all'), 'gw_connected_share'] >= y.loc[(25, 500.0, 'all'), 'gw_connected_share']
  assert y.loc[(25, 700.0, 'all'), 'mean_degree'] > y.loc[(25, 500.0, 'all'), 'mean_degree']
  assert y.loc[(25, 500.0, 'storm'), 'gw_connected_share'] <= y.loc[(25, 500.0, 'all'), 'gw_connected_share'] + 1e-9
  assert {'DJF', 'JJA', 'year', '1', '12'} <= set(table.period)


if __name__ == '__main__':
  for name, fn in list(globals().items()):
    if name.startswith('test_'):
      fn(); print('ok', name)

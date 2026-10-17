"""replay.py on synthetic tracks: picking, Little's law, warm starts, population grid.

Run: python -m pytest tests/test_replay.py   or   python tests/test_replay.py
"""
import os
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import replay as rp  # noqa: E402
import synth  # noqa: E402

TMP = tempfile.mkdtemp(prefix='loon_replay_')
TRACKS = os.path.join(TMP, 'tracks.csv')
POP = os.path.join(TMP, 'pop.csv')
synth.synthetic_tracks(TRACKS)
synth.synthetic_population(POP, cell_km=50)


def test_tracks_load_shape_and_sites():
  t = rp.Tracks(TRACKS)
  assert len(t.flights) == 5 * 24
  assert set(t.sites) == set(synth.SITES)
  assert t.year == 2025 and t.period_h == 8760
  # positions at age 0 are the launch sites; after the end they are NaN
  lat, lon = t.positions([0], [0])
  assert abs(lat[0] - synth.SITES[t.site[0]][0]) < 0.01
  lat, lon = t.positions([0], [t.end_h[0] + 5])
  assert np.isnan(lat[0])


def test_winter_dwell_shorter_than_summer():
  t = rp.Tracks(TRACKS)
  assert t.mean_dwell_h(1) < 0.6 * t.mean_dwell_h(7)


def test_pick_stays_in_window_and_site():
  t = rp.Tracks(TRACKS)
  rng = np.random.default_rng(1)
  t_launch = synth.hours_since_jan1(2025, 1, 20)
  for _ in range(50):
    f = t.pick('Brest', t_launch, rng, 21 * 24)
    assert t.site[f] == 'Brest'
    assert abs(t.launch_hours[f] - t_launch) <= 21 * 24
  # year wrap: a launch on 30 December may pick a 1 January track
  f = t.pick('Brest', 8760 - 48, rng, 21 * 24)
  assert t.site[f] == 'Brest'


def test_standing_launches_hold_n_aloft():
  t = rp.Tracks(TRACKS)
  rng = np.random.default_rng(2)
  L = rp.standing_launches(t, 40, -720, 8760, rng)
  R = rp.Replay(t, L)
  counts = R.count_series(np.arange(24 * 40, 8760, 24 * 10, dtype=float))
  assert 25 < counts.mean() < 55, counts.mean()


def test_warm_start_puts_n_aloft_now():
  t = rp.Tracks(TRACKS)
  rng = np.random.default_rng(3)
  W = rp.warm_start(t, 60, 24 * 100.0, rng)
  n = len(rp.Replay(t, W).aloft(24 * 100.0)[0])
  assert n == 60
  assert rp.warm_start(t, 0, 0.0, rng) is None


def test_release_hours_cut_service():
  t0 = rp.Tracks(TRACKS)
  rel = {f: 5.0 for f in t0.flights}
  t1 = rp.Tracks(TRACKS, release_h=rel)
  assert t1.mean_dwell_h() <= 5.0 + 1e-9
  assert t1.mean_dwell_h(service=False) == t0.mean_dwell_h()


def test_population_grid_conserves_people():
  import pandas as pd
  raw = pd.read_csv(POP)
  cells = rp.load_population(POP, cell_km=100)
  assert abs(cells['pop'].sum() - raw['pop'].sum()) / raw['pop'].sum() < 1e-9
  assert len(cells) < len(raw)
  assert (cells.lat >= rp.REGION['lat0']).all() and (cells.lon <= rp.REGION['lon1']).all()


def test_month_and_season_helpers():
  assert list(rp.hours_to_month([0, 24 * 40, 8759], 2025)) == [1, 2, 12]
  assert rp.season_of(12) == 'DJF' and rp.season_of(7) == 'JJA'
  assert rp.year_hours(2024) == 8784


if __name__ == '__main__':
  for name, fn in list(globals().items()):
    if name.startswith('test_'):
      fn(); print('ok', name)

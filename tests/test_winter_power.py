"""winter_power.py: sun geometry and the budget arithmetic.

Run: python -m pytest tests/test_winter_power.py   or   python tests/test_winter_power.py
"""
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import winter_power as wp  # noqa: E402


def _budget(lat, date, model='tilt', area=3.0, day_w=300.0, night_w=300.0):
  return wp.day_budget(lat, date, model, 6000.0, area, 0.22, 35.0, 1.0, day_w, night_w)


def test_day_length_equator_equinox_is_about_twelve_hours():
  b = _budget(0.0, dt.date(2025, 3, 20))
  # BLE counts "day" down to -4.242 deg, so a little over 12 h
  assert 12.0 < b['day_h'] < 13.2, b['day_h']


def test_winter_night_at_50n_is_long_and_summer_night_short():
  jan = _budget(50.0, dt.date(2025, 1, 15))
  jun = _budget(50.0, dt.date(2025, 6, 21))
  assert 13.5 < jan['night_h'] < 15.5, jan['night_h']
  assert 5.5 < jun['night_h'] < 7.5, jun['night_h']
  assert jun['harvest_wh'] > 1.6 * jan['harvest_wh']


def test_polar_night_makes_nothing():
  b = _budget(75.0, dt.date(2025, 12, 21))
  assert b['harvest_wh'] == 0.0 and b['day_h'] == 0.0


def test_tracking_array_beats_tilted_beats_flat_in_winter():
  d = dt.date(2025, 1, 15)
  tr, ti, fl = (_budget(50.0, d, m)['harvest_wh'] for m in ('track', 'tilt', 'flat'))
  assert tr >= ti >= fl > 0


def test_loon_array_peak_is_in_the_kilowatt_class():
  b = _budget(50.0, dt.date(2025, 6, 21), 'loon')
  # 6 x 210 Wp with cosine losses and the balloon shadow: several hundred W to ~1.2 kW
  assert 600 < b['peak_w'] < 1300, b['peak_w']


def test_budget_closes_only_when_surplus_covers_the_night():
  b = _budget(50.0, dt.date(2025, 1, 15), area=2.0)
  c = wp.close_budget(b, None, 0.9, 0.8, 150.0, 3.0, 40.0)
  assert c['battery_needed_wh'] == b['night_need_wh'] / 0.8
  assert c['closes'] == (c['surplus_wh'] * 0.9 >= b['night_need_wh'])
  big = wp.close_budget(_budget(50.0, dt.date(2025, 1, 15), area=8.0), None, 0.9, 0.8, 150.0, 12.0, 40.0)
  assert big['closes']
  # a 300 W night at 50N in January needs a pack that does not fit a 40 kg payload at 150 Wh/kg (W5)
  assert c['battery_kg'] > 30 and c['payload_left_kg'] < 5


def test_cli_writes_csv(tmp_path=None):
  cwd = os.getcwd()
  out_dir = tmp_path or os.path.join(os.path.dirname(__file__), '_tmp_wp')
  os.makedirs(out_dir, exist_ok=True)
  os.chdir(out_dir)
  try:
    rows = wp.main(['--vehicle', 'light', '--lat', '50,40', '--dates', '2025-01-15', '--sweep-area', '2,4',
                    '--tag', 'test'])
    assert len(rows) == 4
    assert os.path.exists('results/winter_power_budget_test.csv')
  finally:
    os.chdir(cwd)
    if tmp_path is None:
      import shutil
      shutil.rmtree(out_dir, ignore_errors=True)


if __name__ == '__main__':
  for name, fn in list(globals().items()):
    if name.startswith('test_'):
      fn(); print('ok', name)

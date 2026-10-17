"""vehicle.py sizing against results/envelope_cost.md, without the engine.

Run: python -m pytest tests/test_vehicle.py   or   python tests/test_vehicle.py
"""
import dataclasses
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import vehicle  # noqa: E402


def test_light_vehicle_matches_envelope_note():
  d = vehicle.size(vehicle.LIGHT)
  # envelope_cost.md section 4: 678 m^3 for an 18 kg envelope and a 40 kg payload at 60 hPa
  assert abs(d['volume_m3'] - 678.0) / 678.0 < 0.02, d['volume_m3']
  # TECHNICAL_ISSUES.md section 5: the light vehicle carries about 5-7 kg of hydrogen (estimate)
  assert 3.5 < d['gas_kg'] < 7.0, d['gas_kg']
  assert d['dp_max_pa'] == 1000.0
  assert 0.3 < d['acs_scale'] < 0.45


def test_spare_lift_condition_holds_at_ceiling():
  s = vehicle.LIGHT
  d = vehicle.size(s)
  rho_air = s.ceiling_pa * vehicle.M_AIR / (vehicle.R_GAS * s.ceiling_temp_k)
  gross = rho_air * d['volume_m3']
  assert abs(gross / d['system_kg'] - (1 + s.spare_lift)) < 1e-6


def test_helium_needs_more_volume_than_hydrogen():
  h2 = vehicle.size(vehicle.LIGHT)
  he = vehicle.size(dataclasses.replace(vehicle.LIGHT, gas='he'))
  assert he['volume_m3'] > h2['volume_m3'] * 1.05
  assert he['gas_kg'] > 2 * h2['gas_kg']


def test_ble_defaults_reproduce_from_the_same_formula():
  # BLE's balloon as a spec: 92.5 + 68.5 kg, helium. The formula should land near 1,804 m^3
  # at a ceiling and temperature that make its 6,830 mol close; 60 hPa / 215 K gives 2,035 m^3
  # (the envelope note's own check), so only the order of magnitude is asserted here.
  spec = dataclasses.replace(vehicle.LIGHT, name='ble', payload_kg=92.5, envelope_kg=68.5, gas='he')
  d = vehicle.size(spec)
  assert 1500 < d['volume_m3'] < 2500
  assert 5000 < d['mols_gas'] < 8000


def test_env_overrides(monkeypatch=None):
  os.environ['ARRAY_WP'] = '900'
  os.environ['NIGHT_W'] = '320'
  try:
    s = vehicle.from_env(vehicle.LIGHT)
    assert s.array_wp == 900.0 and s.night_w == 320.0
    assert vehicle.size(s)['array_scale'] == 900.0 / 1260.0
  finally:
    del os.environ['ARRAY_WP'], os.environ['NIGHT_W']


if __name__ == '__main__':
  for name, fn in list(globals().items()):
    if name.startswith('test_'):
      fn(); print('ok', name)

"""Rerun 4 (W3): the light vehicle, sized for BLE and applied to a flying balloon.

Every trajectory in results/ was flown by BLE's Loon-class balloon: 68.5 kg
envelope, 92.5 kg payload, 1,804 m^3, 6,830 mol of helium, 2,380 Pa maximum
superpressure, a 3 kWh battery and a 1,260 Wp array. The cost case prices a
different vehicle (results/envelope_cost.md section 4): a low-dp pumpkin for a
40 kg payload, 16-18 kg of envelope, hydrogen, a 60 hPa ceiling and about
1,000 Pa of superpressure margin. This module

  1. sizes that vehicle from first principles (size()), so the numbers BLE
     needs (mols of gas, envelope volume, dv/dp, max superpressure) follow
     from payload, envelope mass, ceiling and spare lift and can be checked
     against the envelope note without the engine; and
  2. applies it to a BLE balloon state in a running arena (apply()), which is
     the part that needs the engine and has not been flown. run_drift.py and
     track_slow.py call apply() when --vehicle light is given.

What apply() changes in BLE, and how:
  * BalloonState fields: envelope_mass, payload_mass, envelope_volume_base,
    envelope_volume_dv_pressure, envelope_max_superpressure, mols_lift_gas,
    battery_capacity/charge, day and night hotel loads; then
    stable_init.cold_start_to_stable_params() is re-run so the ballonet, the
    internal temperature and the superpressure are consistent at the sampled
    launch pressure.
  * Lift gas: BLE books the lift gas as helium through constants.HE_MOLAR_MASS,
    which balloon.py and stable_init.py read at call time. For gas='h2' the
    module attribute is set to the H2 molar mass in the worker process. This is
    the same correction run_multipass.py applies after the fact for the fuel
    cell, applied before the fact here. TODO(flight): confirm on the engine that
    no other BLE module caches the constant (envelope_safety and
    pressure_range_builder read state fields, not the constant).
  * Pump: BLE's altitude control system is a fixed Loon pump (acs.py tables of
    power and mass flow against pressure ratio). A 676 m^3 envelope with the
    Loon pump would change altitude 2.7x faster per hour than BLE's balloon.
    acs_scale multiplies both the pump's power and its mass flow, so the
    light vehicle has the same fractional pumping authority per hour as BLE's
    balloon at acs_scale = V_light / V_ble (default). ASSUMPTION; set
    ACS_SCALE=1 to keep the Loon pump.
  * Array: BLE's solar model is a fixed six-panel Loon array (solar.solar_power).
    array_scale multiplies its output. The light vehicle's array is not sized
    anywhere in the repository yet; winter_power.py is the tool for that, and
    its result should be fed back through ARRAY_WP. Default 545 Wp (the Loon
    array scaled by payload mass), ASSUMPTION.

Where a flight is needed (TODO(flight), in order):
  a. Does the sized vehicle float at all in BLE's thermal model? A 1,000 Pa
     ceiling against the day-night supertemperature at 60 hPa is the first
     thing the engine will report, as BURST or ZEROPRESSURE at the first
     sunrise or sunset. If it bursts, raise dp_max_pa in LIGHT (the envelope
     note says 1,000 Pa buys about 20 K of supertemperature; BLE's thermal
     model may want more) and record the value the envelope must be rated to.
  b. The launch pressure. EuropeArena samples it for the Loon vehicle; the
     light vehicle's accessible band is narrower, and the altitude safety
     layer (50,000 ft floor) and the envelope safety layer sort it out in the
     first minutes. Check the first hour of a few tracks.
  c. The pump assumption (acs_scale) against a pump the light vehicle could
     carry, and the array/battery pair against winter_power.py's budget.
  d. Only then: re-fly results/drift_<year>.csv with --vehicle light and
     compare dwell and end modes with the Loon-class run of the same year.

Usage (sizing only, no engine):
  python vehicle.py                 # prints the light vehicle next to BLE's
  python vehicle.py --payload 55 --envelope 19.3 --dp-max 1000
Flying it (engine):
  VEHICLE=light WIND_GRID=data/era5_europe_upper_2025.npz python -I run_drift.py --vehicle light
Environment overrides read by apply(): ACS_SCALE, ARRAY_WP, BATTERY_WH, DAY_W, NIGHT_W, LIFT_GAS.
"""
import argparse
import dataclasses
import math
import os

R_GAS = 8.3144621            # J/(mol K), BLE constants.UNIVERSAL_GAS_CONSTANT
M_AIR = 0.028964922481160    # kg/mol, BLE constants.DRY_AIR_MOLAR_MASS
M_HE = 0.004002602           # kg/mol, BLE constants.HE_MOLAR_MASS
M_H2 = 0.002016              # kg/mol
MOLAR_MASS = {'h2': M_H2, 'he': M_HE}

# BLE's balloon (balloon.py defaults), for the ratios below and for --compare.
BLE = dict(payload_kg=92.5, envelope_kg=68.5, volume_m3=1804.0, dv_dp_m3_per_pa=0.0199,
           dp_max_pa=2380.0, mols_gas=6830.0, battery_wh=3058.56, array_wp=1260.0,
           day_w=120.4, night_w=183.7)


@dataclasses.dataclass
class VehicleSpec:
  """Inputs that define a vehicle; everything BLE needs is derived in size()."""
  name: str
  payload_kg: float
  envelope_kg: float
  ceiling_pa: float = 6000.0      # design ceiling, results/envelope_cost.md: 60 hPa
  ceiling_temp_k: float = 215.0   # stratosphere at the ceiling, envelope note
  spare_lift: float = 0.05        # free lift at the ceiling, envelope note
  dp_max_pa: float = 1000.0       # design superpressure, envelope note section 4
  gas: str = 'h2'
  # ASSUMPTION: film compliance scales with volume (BLE: 0.0199 m^3/Pa on 1,804 m^3).
  dv_dp_per_m3: float = BLE['dv_dp_m3_per_pa'] / BLE['volume_m3']
  battery_wh: float = 1500.0      # ASSUMPTION: 10 kg at 150 Wh/kg inside a 40 kg payload
  array_wp: float = BLE['array_wp'] * 40.0 / 92.5   # ASSUMPTION, see module docstring
  day_w: float = BLE['day_w']     # BLE hotel loads kept so the vehicle effect is isolated
  night_w: float = BLE['night_w']
  acs_scale: float = None         # None -> V / V_ble


# results/envelope_cost.md section 4: 30-day design 18 kg / 678 m^3; 4-day 16.3 kg / 661 m^3.
LIGHT = VehicleSpec('light', payload_kg=40.0, envelope_kg=18.0)
LIGHT4 = VehicleSpec('light4', payload_kg=40.0, envelope_kg=16.3)
PRESETS = {'light': LIGHT, 'light4': LIGHT4}


def size(spec):
  """Derive the BLE state fields from the spec.

  At the ceiling, with no air in the ballonet, the gas fills the envelope
  exactly, so gross lift = n * M_air and the spare-lift condition is
    n * M_air = (1 + s) * (m_sys + n * M_gas)
  which gives n, and the envelope volume is n R T / P_ceiling.
  """
  m_gas = MOLAR_MASS[spec.gas]
  m_sys = spec.payload_kg + spec.envelope_kg
  s = spec.spare_lift
  n = (1 + s) * m_sys / (M_AIR - (1 + s) * m_gas)
  v0 = n * R_GAS * spec.ceiling_temp_k / spec.ceiling_pa
  acs = spec.acs_scale if spec.acs_scale is not None else v0 / BLE['volume_m3']
  return dict(
      name=spec.name, gas=spec.gas, payload_kg=spec.payload_kg, envelope_kg=spec.envelope_kg,
      mols_gas=n, gas_kg=n * m_gas, volume_m3=v0,
      dv_dp_m3_per_pa=spec.dv_dp_per_m3 * v0, dp_max_pa=spec.dp_max_pa,
      system_kg=m_sys + n * m_gas,
      # superpressure at the ceiling if the gas were 5 % warmer than ambient, for a feel of margin
      sp_per_kelvin_pa=spec.ceiling_pa / spec.ceiling_temp_k,
      battery_wh=spec.battery_wh, array_wp=spec.array_wp, day_w=spec.day_w, night_w=spec.night_w,
      acs_scale=acs, array_scale=spec.array_wp / BLE['array_wp'])


def from_env(spec):
  """Copy of spec with the environment overrides apply() honours."""
  kw = {}
  if os.environ.get('ACS_SCALE'):
    kw['acs_scale'] = float(os.environ['ACS_SCALE'])
  if os.environ.get('ARRAY_WP'):
    kw['array_wp'] = float(os.environ['ARRAY_WP'])
  if os.environ.get('BATTERY_WH'):
    kw['battery_wh'] = float(os.environ['BATTERY_WH'])
  if os.environ.get('DAY_W'):
    kw['day_w'] = float(os.environ['DAY_W'])
  if os.environ.get('NIGHT_W'):
    kw['night_w'] = float(os.environ['NIGHT_W'])
  if os.environ.get('LIFT_GAS'):
    kw['gas'] = os.environ['LIFT_GAS'].lower()
  return dataclasses.replace(spec, **kw)


_PATCHED = set()


def _patch_engine(d):
  """Process-wide BLE patches: lift-gas molar mass, pump scale, array scale. Idempotent."""
  from balloon_learning_environment.env.balloon import acs, solar
  from balloon_learning_environment.utils import constants, units
  if 'gas' not in _PATCHED:
    constants.HE_MOLAR_MASS = MOLAR_MASS[d['gas']]
    _PATCHED.add('gas')
  if 'acs' not in _PATCHED and abs(d['acs_scale'] - 1.0) > 1e-9:
    k = d['acs_scale']
    power0, flow0 = acs.get_most_efficient_power, acs.get_mass_flow
    acs.get_most_efficient_power = lambda pr: units.Power(watts=power0(pr).watts * k)
    acs.get_mass_flow = lambda power, eff: flow0(units.Power(watts=power.watts / k), eff) * k
    _PATCHED.add('acs')
  if 'array' not in _PATCHED and abs(d['array_scale'] - 1.0) > 1e-9:
    k = d['array_scale']
    solar0 = solar.solar_power
    solar.solar_power = lambda el, p: units.Power(watts=solar0(el, p).watts * k)
    _PATCHED.add('array')


def apply(arena, spec_or_name):
  """Turn the Loon-class balloon in a europe_ble.EuropeArena into the light vehicle.

  Call right after the arena is built and before the first step. Needs BLE.
  TODO(flight): everything in the module docstring's list.
  """
  from balloon_learning_environment.env.balloon import stable_init
  from balloon_learning_environment.utils import units
  spec = PRESETS[spec_or_name] if isinstance(spec_or_name, str) else spec_or_name
  spec = from_env(spec)
  d = size(spec)
  _patch_engine(d)
  st = arena.get_balloon_state()
  st.envelope_mass = d['envelope_kg']
  st.payload_mass = d['payload_kg']
  st.envelope_volume_base = d['volume_m3']
  st.envelope_volume_dv_pressure = d['dv_dp_m3_per_pa']
  st.envelope_max_superpressure = d['dp_max_pa']
  st.mols_lift_gas = d['mols_gas']
  st.battery_capacity = units.Energy(watt_hours=d['battery_wh'])
  st.battery_charge = units.Energy(watt_hours=0.95 * d['battery_wh'])
  st.daytime_power_load = units.Power(watts=d['day_w'])
  st.nighttime_power_load = units.Power(watts=d['night_w'])
  # The envelope safety layer was built for 2,380 Pa in BalloonState.__post_init__.
  from balloon_learning_environment.env.balloon import envelope_safety
  st.envelope_safety_layer = envelope_safety.EnvelopeSafetyLayer(d['dp_max_pa'])
  stable_init.cold_start_to_stable_params(st, arena._atmosphere)
  return d


def describe(d):
  return (f"{d['name']}: payload {d['payload_kg']:.1f} kg, envelope {d['envelope_kg']:.1f} kg, "
          f"{d['gas'].upper()} {d['mols_gas']:,.0f} mol = {d['gas_kg']:.2f} kg, "
          f"volume {d['volume_m3']:,.0f} m^3, dv/dp {d['dv_dp_m3_per_pa']:.4f} m^3/Pa, "
          f"dp_max {d['dp_max_pa']:.0f} Pa ({d['dp_max_pa'] / d['sp_per_kelvin_pa']:.0f} K of "
          f"supertemperature at the ceiling), system {d['system_kg']:.1f} kg; "
          f"battery {d['battery_wh']:.0f} Wh, array {d['array_wp']:.0f} Wp "
          f"(x{d['array_scale']:.2f} BLE), pump x{d['acs_scale']:.2f} BLE, "
          f"hotel {d['day_w']:.0f}/{d['night_w']:.0f} W day/night")


def main():
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument('--preset', default='light', choices=sorted(PRESETS))
  ap.add_argument('--payload', type=float, help='kg, overrides the preset')
  ap.add_argument('--envelope', type=float, help='kg, overrides the preset')
  ap.add_argument('--dp-max', type=float, help='Pa, overrides the preset')
  ap.add_argument('--gas', choices=sorted(MOLAR_MASS))
  ap.add_argument('--ceiling-hpa', type=float)
  a = ap.parse_args()
  spec = PRESETS[a.preset]
  kw = {k: v for k, v in dict(payload_kg=a.payload, envelope_kg=a.envelope, dp_max_pa=a.dp_max,
                              gas=a.gas).items() if v is not None}
  if a.ceiling_hpa:
    kw['ceiling_pa'] = a.ceiling_hpa * 100.0
  d = size(from_env(dataclasses.replace(spec, **kw)))
  print(describe(d))
  b = dict(BLE, name='BLE (Loon-class)', gas='he', gas_kg=BLE['mols_gas'] * M_HE,
           system_kg=BLE['payload_kg'] + BLE['envelope_kg'] + BLE['mols_gas'] * M_HE,
           sp_per_kelvin_pa=6000.0 / 215.0, acs_scale=1.0, array_scale=1.0)
  print(describe(b))
  print(f"ratios light/BLE: volume {d['volume_m3'] / BLE['volume_m3']:.3f}, "
        f"system mass {d['system_kg'] / b['system_kg']:.3f}, gas mass {d['gas_kg'] / b['gas_kg']:.3f}")


if __name__ == '__main__':
  main()

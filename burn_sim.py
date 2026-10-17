"""Could the envelope be consumed by burning its hydrogen at float altitude?

First-principles screening model, run at every slow-controller termination
point from results/drift_2025.csv (radio-release point, else region exit):

1. Energy: igniting the lift gas releases m_H2 * 120 MJ/kg. Only a fraction
   eta reaches the polyethylene film (thin film, a brief fireball, thin air:
   most heat radiates or convects away). Destroying PE takes heating to
   pyrolysis plus gasification, H_PYRO MJ/kg. Burnt PE adds its own heat,
   but only if the film can keep burning in low-O2 air; that is set by
   p_self (chance the film flame sustains) and is applied to what is left.
2. Oxygen: report how much ambient air full combustion needs vs envelope size.
3. Products: oxidised PE -> CO2 + H2O; un-oxidised pyrolysate -> soot/waxes.
4. Debris: unburnt film falls as flutter fragments (sea-level sink 0.5-2 m/s)
   and the envelope hardware (end fittings, valve, ACS) as a tumbling lump;
   both drift in the real 2025 winds (glide.simulate_descent).
Compared against the baseline: parachute cut-down, one 5 m/s object.

All parameter ranges are assumptions, chosen to be generous to burning.
"""
import math
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glide  # noqa: E402
from europe_ble import T0, WindGrid  # noqa: E402
from global_land_mask import globe  # noqa: E402

M_H2 = 6830 * 0.002016   # kg, BLE's 6830 mol of lift gas as hydrogen
M_PE = 68.5              # kg, BLE envelope mass (polyethylene)
M_HW = 15.0              # kg, hardware left on the envelope (assumption)
LHV_H2, LHV_PE = 120.0, 46.0  # MJ/kg
H_PYRO = 4.5             # MJ/kg to heat PE ~700 K and gasify it
N = 2000                 # Monte Carlo draws per termination point
rng = np.random.default_rng(0)


def burn_fraction(n):
  eta = rng.uniform(0.02, 0.30, n)        # heat coupling to film
  p_self = rng.uniform(0.0, 0.3, n)       # film flame self-sustains?
  f_ox = rng.uniform(0.3, 0.9, n)         # pyrolysate fully oxidised
  first = np.minimum(1.0, eta * M_H2 * LHV_H2 / (H_PYRO * M_PE))
  sustained = rng.random(n) < p_self
  frac = np.where(sustained, first + (1 - first) * rng.uniform(.3, 1, n), first)
  return frac, f_ox


def main():
  grid = WindGrid()
  df = pd.read_csv('results/drift_2025.csv')
  df = df[df.controller == 'slow'].copy()
  df['tlat'] = df.release_lat.fillna(df.end_lat)
  df['tlon'] = df.release_lon.fillna(df.end_lon)
  df['t_h'] = (pd.to_datetime(df.start).dt.tz_localize('UTC') - T0
               ).dt.total_seconds() / 3600 + df.release_h.fillna(df.dwell_h)
  p_pa = df.end_hpa.values * 100  # termination pressure (end-of-flight proxy)

  frac, f_ox = burn_fraction(N * len(df))
  burnt = frac * M_PE
  print(f'Hydrogen {M_H2:.1f} kg -> {M_H2 * LHV_H2 / 1000:.2f} GJ; '
        f'destroying all {M_PE} kg PE needs {H_PYRO * M_PE / 1000:.2f} GJ '
        f'delivered to the film (coupling >= '
        f'{H_PYRO * M_PE / (M_H2 * LHV_H2):.0%}).')
  o2 = M_H2 / 0.002016 / 2 + M_PE / 0.014 * 1.5           # mol O2
  rho_o2 = 0.2095 * 6000 / (8.314 * 216.65)                # mol/m^3 at 60 hPa
  print(f'Full combustion needs {o2:,.0f} mol O2 = {o2 / rho_o2:,.0f} m^3 of '
        f'ambient air at 60 hPa ({o2 / rho_o2 / 1804:.0f}x the 1,804 m^3 '
        f'envelope), all mixed in within seconds.')
  q = np.percentile(frac, [10, 50, 90])
  print(f'\nEnvelope consumed: median {q[1]:.0%} (10-90%: {q[0]:.0%}-{q[2]:.0%});'
        f' fully consumed in {np.mean(frac > .99):.0%} of draws')
  ox = burnt * f_ox
  print(f'Per balloon (median): CO2 {np.median(ox * 44 / 14):.0f} kg, '
        f'H2O {np.median(ox * 18 / 14 + M_H2 * 9):.0f} kg '
        f'({M_H2 * 9:.0f} kg of it from the hydrogen), soot/waxes '
        f'{np.median(burnt * (1 - f_ox)):.0f} kg, unburnt film '
        f'{np.median(M_PE - burnt):.0f} kg + {M_HW:.0f} kg hardware')
  print(f'If PE burned completely: CO2 {M_PE * 44 / 14:.0f} kg, '
        f'H2O {M_PE * 18 / 14 + M_H2 * 9:.0f} kg per balloon')

  # Debris drift from each termination point.
  rows = []
  for (_, r), p in zip(df.iterrows(), p_pa):
    land = {}
    for name, sink in [('chute', 5.0), ('hardware', 15.0), ('film_fast', 2.0),
                       ('film_mid', 1.0), ('film_slow', 0.5)]:
      e = glide.simulate_descent(r.tlat, r.tlon, p, r.t_h, grid, sink_sl=sink)
      land[name] = (e['end_lat'], e['end_lon'], e['duration_s'] / 3600)
    pts = [land[k] for k in ('film_fast', 'film_mid', 'film_slow')]
    spread = max(glide.haversine_km(a[0], a[1], b[0], b[1])
                 for a in pts for b in pts)
    rows.append(dict(
        chute_km=glide.haversine_km(r.tlat, r.tlon, *land['chute'][:2]),
        film_km=glide.haversine_km(r.tlat, r.tlon, *land['film_mid'][:2]),
        hw_km=glide.haversine_km(r.tlat, r.tlon, *land['hardware'][:2]),
        film_spread_km=spread, film_fall_h=land['film_slow'][2],
        chute_land=globe.is_land(*land['chute'][:2]),
        film_land=np.mean([globe.is_land(a, b) for a, b, _ in pts]),
        hw_land=globe.is_land(*land['hardware'][:2])))
  d = pd.DataFrame(rows)
  print(f'\nDebris (n={len(d)} termination points):')
  print(f'  parachute cut-down : 1 object, drifts {d.chute_km.median():.0f} km,'
        f' lands on land {d.chute_land.mean():.0%}')
  print(f'  burn, hardware lump: drifts {d.hw_km.median():.0f} km,'
        f' lands on land {d.hw_land.mean():.0%}')
  print(f'  burn, film shreds  : drift {d.film_km.median():.0f} km, scattered '
        f'over a {d.film_spread_km.median():.0f} km-long swath (median), '
        f'up to {d.film_fall_h.median():.1f} h falling; '
        f'{d.film_land.mean():.0%} land on land')
  d.to_csv('results/burn_debris.csv', index=False)


if __name__ == '__main__':
  main()

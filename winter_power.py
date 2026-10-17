"""Rerun 4 (W5): winter power budget from latitude, date and array, not BLE's solar model.

analyze_power.py reads the multipass runs, in which BLE's solar model decides
how much power a fixed six-panel Loon array (1,260 Wp) makes. The question W5
asks is different: at 50 N in January, with the light vehicle's 40 kg payload
and an array that has to fit inside it, does the night close? This script
answers it from the sun's geometry alone, for any latitude, date, array and
load, so the answer does not depend on the engine or on a flight.

For each (latitude, date) it steps through the day in 3-minute steps (BLE's
stride), computes the solar elevation from the NOAA declination and hour-angle
relations in local solar time, the extraterrestrial flux (1,361 W/m^2 with the
orbital correction), BLE's own atmospheric attenuation at the float pressure
(small at 60 hPa), and the array output for one of four array models:

  loon   BLE's array exactly: 4 panels at 35 deg and 2 at 65 deg, 210 Wp each,
         facing the sun in azimuth, with BLE's balloon-shadow factor. Use it
         to tie this script to analyze_power.py's runs.
  tilt   A m^2 at efficiency eta, tilted --tilt-deg from horizontal, facing the
         sun in azimuth (the gondola turns), no shadow unless --shadow < 1.
  flat   A m^2 horizontal (cosine of the zenith angle).
  track  A m^2 kept normal to the sun (the ceiling for any array).

Then the daily budget: day and night lengths (night = elevation below BLE's
-4.242 deg), energy harvested, energy spent in the day, the surplus left to
charge, the night's need (night load x night hours), whether the day closes
the night (surplus x round-trip efficiency >= need), the largest night load
the array can carry, and the battery the night needs (Wh, and kg at the
specific energy given), the array mass, and what is left of the payload mass.
Cloud, frost on the panels and the attitude of a swinging gondola are not
modelled; every mass and efficiency is an ASSUMPTION set on the command line.

Usage:
  python winter_power.py --vehicle light --array tilt --area-m2 3 --night-w 300 --monthly 2025
  python winter_power.py --vehicle loon --array loon --lat 50 --dates 2025-01-15,2025-06-15
  python winter_power.py --vehicle light --array tilt --sweep-area 1,2,3,4,6,8 --lat 50 --dates 2025-01-15
Outputs: results/winter_power_budget_<tag>.csv, one row per (lat, date, area), and a
printed table. Compare with results/winter_power_summary.csv (analyze_power.py), where
BLE's 3 kWh battery flights survived a median 1.8 days in Nov-Feb launches.
"""
import argparse
import csv
import datetime as dt
import math
import os

import numpy as np

MIN_SOLAR_EL_DEG = -4.242   # BLE solar.MIN_SOLAR_EL_DEG: below this the array makes nothing
SOLAR_CONSTANT = 1361.0     # W/m^2
STEP_MIN = 3

# Hotel loads and stores. BLE values from balloon.py; light-vehicle values are
# ASSUMPTIONS to be replaced by the payload budget (results/radio_and_backhaul.md
# gives 300-600 W for the night radio, W5).
VEHICLES = {
    'loon': dict(payload_kg=92.5, day_w=120.4, night_w=183.7, battery_wh=3058.56, array='loon'),
    'light': dict(payload_kg=40.0, day_w=300.0, night_w=300.0, battery_wh=None, array='tilt'),
    # class M (results/radio_and_backhaul.md, results/deployable_now.md): 1 kW by day for the
    # array and radio, 300 W reduced night service, 3 kWh battery with the fuel cell for the
    # rest of the night; ASSUMPTIONS, matched to vehicle.HEAVY. Use --area-m2 for the solar array.
    'heavy': dict(payload_kg=100.0, day_w=1000.0, night_w=300.0, battery_wh=3000.0, array='tilt'),
}


def declination_deg(doy):
  """Spencer (1971) series, degrees. doy: day of year 1..366."""
  g = 2 * math.pi * (doy - 1) / 365.0
  d = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
       + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
  return math.degrees(d)


def toa_flux(doy):
  return SOLAR_CONSTANT * (1 + 0.033 * math.cos(2 * math.pi * doy / 365.0))


def elevation_deg(lat_deg, decl_deg, hour_angle_deg):
  lat, dec, h = (math.radians(x) for x in (lat_deg, decl_deg, hour_angle_deg))
  s = math.sin(lat) * math.sin(dec) + math.cos(lat) * math.cos(dec) * math.cos(h)
  return math.degrees(math.asin(max(-1.0, min(1.0, s))))


def attenuation(el_deg, pressure_pa):
  """BLE solar.solar_atmospheric_attenuation, verbatim in form."""
  if el_deg < MIN_SOLAR_EL_DEG:
    return 0.0
  t = 614.0 * math.sin(math.radians(el_deg))
  airmass = 0.34764 * (pressure_pa / 101325.0) * (math.sqrt(1229.0 + t * t) - t)
  return 0.5 * (math.exp(-0.65 * airmass) + math.exp(-0.95 * airmass))


def balloon_shadow(el_deg, panel_height_m):
  """BLE solar.balloon_shadow: 0.4392 when the sun is high enough to put the envelope over the panels."""
  r, h = 8.69275, 10.41603
  shadow_el = math.degrees(math.atan2(math.sqrt(panel_height_m * (h + panel_height_m)), r))
  return 0.4392 if el_deg >= shadow_el else 1.0


def array_watts(model, el_deg, pressure_pa, flux, area_m2, eff, tilt_deg, shadow):
  if el_deg < MIN_SOLAR_EL_DEG:
    return 0.0
  att = attenuation(el_deg, pressure_pa)
  if model == 'loon':
    return 210.0 * att * (4 * math.cos(math.radians(el_deg - 35)) * balloon_shadow(el_deg, 3.3)
                          + 2 * math.cos(math.radians(el_deg - 65)) * balloon_shadow(el_deg, 2.7))
  if model == 'tilt':
    cosi = max(0.0, math.cos(math.radians(el_deg - tilt_deg)))
  elif model == 'flat':
    cosi = max(0.0, math.sin(math.radians(el_deg)))
  elif model == 'track':
    cosi = 1.0
  else:
    raise ValueError(model)
  return area_m2 * eff * flux * att * cosi * shadow


def day_budget(lat, date, model, pressure_pa, area_m2, eff, tilt_deg, shadow, day_w, night_w):
  """One day at one latitude: lengths, energies, peak. Local solar time, 3-minute steps."""
  doy = date.timetuple().tm_yday
  dec, flux = declination_deg(doy), toa_flux(doy)
  n = 24 * 60 // STEP_MIN
  minutes = np.arange(n) * STEP_MIN + STEP_MIN / 2.0
  hour_angles = (minutes / 60.0 - 12.0) * 15.0
  el = np.array([elevation_deg(lat, dec, h) for h in hour_angles])
  w = np.array([array_watts(model, e, pressure_pa, flux, area_m2, eff, tilt_deg, shadow) for e in el])
  is_day = el > MIN_SOLAR_EL_DEG
  dt_h = STEP_MIN / 60.0
  day_h = float(is_day.sum() * dt_h)
  night_h = 24.0 - day_h
  return dict(day_h=day_h, night_h=night_h, peak_w=float(w.max()), harvest_wh=float(w.sum() * dt_h),
              day_load_wh=day_w * day_h, night_need_wh=night_w * night_h,
              max_el_deg=float(el.max()))


def close_budget(b, battery_wh, rt_eff, dod, wh_per_kg, array_kg, payload_kg):
  surplus = b['harvest_wh'] - b['day_load_wh']
  need = b['night_need_wh']
  battery_needed = need / dod if need > 0 else 0.0
  bat = battery_wh if battery_wh else battery_needed
  closes = surplus * rt_eff >= need and bat * dod >= need
  max_night_w = max(0.0, surplus * rt_eff / b['night_h']) if b['night_h'] > 0 else float('inf')
  bat_kg = bat / wh_per_kg
  return dict(surplus_wh=surplus, closes=closes, max_night_w=max_night_w,
              battery_wh=bat, battery_needed_wh=battery_needed, battery_kg=bat_kg,
              array_kg=array_kg, payload_left_kg=payload_kg - bat_kg - array_kg)


def parse_dates(a):
  if a.monthly:
    return [dt.date(a.monthly, m, 15) for m in range(1, 13)]
  return [dt.date.fromisoformat(s) for s in a.dates.split(',')]


def main(argv=None):
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument('--vehicle', default='light', choices=sorted(VEHICLES))
  ap.add_argument('--array', choices=['loon', 'tilt', 'flat', 'track'], help='default from the vehicle')
  ap.add_argument('--area-m2', type=float, default=3.0, help='array area for tilt/flat/track')
  ap.add_argument('--sweep-area', help='comma list of areas, one row each, e.g. 1,2,3,4,6,8')
  ap.add_argument('--eff', type=float, default=0.22, help='array efficiency at stratospheric temperature, ASSUMPTION')
  ap.add_argument('--tilt-deg', type=float, default=35.0)
  ap.add_argument('--shadow', type=float, default=1.0, help='envelope shadow factor for tilt/flat/track, 1 = none')
  ap.add_argument('--pressure-hpa', type=float, default=60.0, help='float pressure for the attenuation')
  ap.add_argument('--lat', default='50', help='comma list of latitudes, deg N')
  ap.add_argument('--dates', default='2025-01-15', help='comma list of ISO dates')
  ap.add_argument('--monthly', type=int, help='year: the 15th of every month instead of --dates')
  ap.add_argument('--day-w', type=float, help='daytime hotel + radio load, default from the vehicle')
  ap.add_argument('--night-w', type=float, help='night load, default from the vehicle')
  ap.add_argument('--battery-wh', type=float, help='installed store; default: what the night needs')
  ap.add_argument('--rt-eff', type=float, default=0.90, help='battery round-trip efficiency, ASSUMPTION')
  ap.add_argument('--dod', type=float, default=0.80, help='usable depth of discharge, ASSUMPTION')
  ap.add_argument('--wh-per-kg', type=float, default=150.0, help='pack specific energy incl. heating and housing, ASSUMPTION')
  ap.add_argument('--array-kg-m2', type=float, default=1.5, help='array areal mass incl. structure, ASSUMPTION')
  ap.add_argument('--tag', default=None)
  a = ap.parse_args(argv)
  v = VEHICLES[a.vehicle]
  model = a.array or v['array']
  day_w = a.day_w if a.day_w is not None else v['day_w']
  night_w = a.night_w if a.night_w is not None else v['night_w']
  battery = a.battery_wh if a.battery_wh is not None else v['battery_wh']
  areas = [float(x) for x in a.sweep_area.split(',')] if a.sweep_area else [a.area_m2]
  lats = [float(x) for x in a.lat.split(',')]
  dates = parse_dates(a)
  pressure_pa = a.pressure_hpa * 100.0
  rows = []
  for lat in lats:
    for date in dates:
      for area in areas:
        b = day_budget(lat, date, model, pressure_pa, area, a.eff, a.tilt_deg, a.shadow, day_w, night_w)
        arr_kg = 0.0 if model == 'loon' else area * a.array_kg_m2
        c = close_budget(b, battery, a.rt_eff, a.dod, a.wh_per_kg, arr_kg, v['payload_kg'])
        rows.append(dict(vehicle=a.vehicle, array=model, area_m2=area if model != 'loon' else 'loon',
                         lat=lat, date=date.isoformat(), month=date.month, day_w=day_w, night_w=night_w,
                         **{k: (round(x, 2) if isinstance(x, float) else x) for k, x in {**b, **c}.items()}))
  tag = a.tag or f'{a.vehicle}_{model}'
  os.makedirs('results', exist_ok=True)
  out = f'results/winter_power_budget_{tag}.csv'
  with open(out, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
  print(f'{a.vehicle} vehicle, {model} array'
        + (f' {areas} m^2 at eff {a.eff}' if model != 'loon' else '')
        + f', loads {day_w:.0f}/{night_w:.0f} W day/night, float {a.pressure_hpa:.0f} hPa')
  hdr = f'{"lat":>5} {"date":>10} {"area":>5} {"day h":>6} {"night h":>7} {"peak W":>7} {"harvest Wh":>10} ' \
        f'{"surplus Wh":>10} {"need Wh":>8} {"closes":>6} {"max night W":>11} {"batt kg":>7} {"left kg":>7}'
  print(hdr)
  for r in rows:
    print(f'{r["lat"]:5.1f} {r["date"]:>10} {str(r["area_m2"]):>5} {r["day_h"]:6.1f} {r["night_h"]:7.1f} '
          f'{r["peak_w"]:7.0f} {r["harvest_wh"]:10.0f} {r["surplus_wh"]:10.0f} {r["night_need_wh"]:8.0f} '
          f'{"yes" if r["closes"] else "no":>6} {r["max_night_w"]:11.0f} {r["battery_kg"]:7.1f} '
          f'{r["payload_left_kg"]:7.1f}')
  print(f'wrote {out}')
  return rows


if __name__ == '__main__':
  main()

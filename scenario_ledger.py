"""Rerun 9 (W27): the scenario ledger over the CSVs of reruns 4-7.

One table per scenario that ties launches a day, payload inventory and
circulation time, envelope mass flow, delivered capacity and cost a year
together, every row traceable to the file or the named constant it came from.
The readiness figure of EUR 0.2-0.5 B a year in results/cost_funding_vs_starlink.md
is withdrawn until this exists; this is the arithmetic it is replaced by.

Scenarios (results/deployable_now.md, results/target_population.md section F,
results/mitigation_research.md W27):
  pilot      Configuration B: 6-12 aloft on a contracted vehicle, two sites,
             one two-week surge exercise a year. Constants from deployable_now.md.
  readiness  a standing layer of --standing balloons all year (launched at the
             Little's-law rate from the drift set's service dwell), plus one
             surge a year of --surge-days to the balloon count and launch rate
             of outage_scenario's row for a --zone-km winter voice-and-text
             zone at --gbps a balloon; payload stock sized by circulation.
  planning   the permanent layer: enough balloons aloft all year for 95 % of the
             region's land under random placement at --footprint-km (the
             cost_model.py branch that availability.py replaces: when a
             results/availability_*.csv exists for a standing size, its served
             share is reported next to the formula).

Inputs, all discovered in results/ and all optional except the drift file:
  results/drift_<year>.csv (run_drift.py)           dwell and release by month, recovery share
  results/outage_scenario_<a>_<b>_<c>.csv           surge balloons and launches a day (rerun 5)
  results/availability_*.csv (rerun 6)              served and covered shares, standing layers
  results/time_to_n_*.csv (rerun 6)                 hours to 50 % of the requirement, cold vs warm
  results/mesh_*.csv (rerun 7)                      gateway-connected share by standing size
Named constants (per-flight cost, radio unit cost, envelope mass and cost, site
cost, turnaround days, recovery rates) are listed in CONSTANTS with their source
and are the only numbers not read from a file.

Usage:
  python scenario_ledger.py                       # defaults: 2025 drift, 0.2 Gbps, standing 100, 300 km zone
  python scenario_ledger.py --year 2019 --gbps 0.04 --standing 50 --turnaround-days 7
Outputs: results/scenario_ledger.csv (scenario, metric, value, unit, source) and
results/scenario_ledger.md (one table per scenario). Nothing here needs BLE.
"""
import argparse
import glob
import math
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

LAND_KM2 = 7.1e6   # target_population.md section F: the region's land
DAYS_IN_MONTH = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])

# (value, unit, source). Estimates and planning allowances, not quotations.
CONSTANTS = {
    'per_flight_eur': (12_400, 'EUR', 'outage_scenario.py PER_FLIGHT_EUR mid (combined_cost.py mid case); range 6,700-27,200'),
    'per_flight_eur_low': (6_700, 'EUR', 'outage_scenario.py PER_FLIGHT_EUR best'),
    'per_flight_eur_high': (27_200, 'EUR', 'outage_scenario.py PER_FLIGHT_EUR worst'),
    'radio_unit_eur': (24_500, 'EUR', 'cost_model.py PAYLOAD_EUR mode 35k x combined_cost.py PAYLOAD_UNIT mid 0.7'),
    'radio_life_flights': (15, 'flights', 'cost_model.py PAYLOAD_MAX_FLIGHTS mode'),
    'envelope_kg_light': (18.0, 'kg', 'results/envelope_cost.md section 4, 30-day design for a 40 kg payload'),
    'envelope_kg_ble': (68.5, 'kg', 'BLE balloon.py envelope_mass; every flown trajectory'),
    'envelope_eur_light': (1_068, 'EUR', 'combined_cost.py ENVELOPE_REDESIGN_EUR mode (391-2,879)'),
    'site_fixed_eur_yr': (3.0e6, 'EUR/yr', 'cost_model.py SITE_FIXED_EUR_YR mode (1.5-6 M)'),
    'launches_per_site_day': (12, '/site/day', 'mitigation_research.md W23: 6-12 honest; cost_model.py used 48'),
    'ops_centre_eur_yr': (30e6, 'EUR/yr', 'cost_funding_vs_starlink.md section 4: EUR 10-50 M'),
    'regulatory_eur_yr': (20e6, 'EUR/yr', 'cost_funding_vs_starlink.md section 4: EUR 5-40 M'),
    'turnaround_days': (5.0, 'days', 'mitigation_research.md W27: three-to-seven-day circulation'),
    'standing_sites_min': (5, 'sites', 'run_drift.py LAUNCH: the five simulated sites'),
    'pilot_aloft': (9, 'balloons', 'deployable_now.md Configuration B: 6-12 aloft'),
    'pilot_dwell_days': (100, 'days', 'deployable_now.md: Thunderhead missions near 100 days'),
    'pilot_exercise_flights': (60, 'flights/yr', 'deployable_now.md: 40-80 flights in a two-week surge exercise'),
    'pilot_mbps': (60, 'Mbps', 'deployable_now.md Configuration B: 20-100 Mbps a balloon'),
    'pilot_cost_eur_yr': (75e6, 'EUR/yr', 'deployable_now.md: EUR 30-120 M a year at the placeholder flight price'),
    'pilot_recovery': (0.90, 'share', 'deployable_now.md phase 2 gate: recovery above 90 % over 30+ flights'),
    'coverage_target': (0.95, 'share', 'cost_model.py BASE_COVERAGE'),
}

RECOVERY_RATES = {'all_recovered': 1.0, 'third_at_sea': 2.0 / 3.0, 'none': 0.0}  # runbook section 8 (W21)


def c(name):
  return CONSTANTS[name][0]


def src(name):
  return CONSTANTS[name][2]


class Ledger:
  def __init__(self):
    self.rows = []

  def add(self, scenario, metric, value, unit, source):
    self.rows.append(dict(scenario=scenario, metric=metric, value=value, unit=unit, source=source))

  def frame(self):
    return pd.DataFrame(self.rows)


def dwell_from_drift(path):
  """Service dwell (release where recovered, else exit) and full dwell, by month and harmonic over the year."""
  d = pd.read_csv(path)
  d = d[d.controller == 'slow'].copy()
  rec = d.recovered.fillna(False).astype(bool) & d.release_h.notna()
  d['service_h'] = np.where(rec, d.release_h + d.glide_h.fillna(0), d.dwell_h)
  by = d.groupby('month').agg(service_h=('service_h', 'mean'), dwell_h=('dwell_h', 'mean'))
  w = DAYS_IN_MONTH[by.index.values - 1]
  harm = lambda col: float(w.sum() / (w / by[col].values).sum() / 24.0)   # launches scale with 1/dwell
  return dict(by_month=by, service_days_harm=harm('service_h'), dwell_days_harm=harm('dwell_h'),
              winter_service_days=float(by.loc[[12, 1, 2], 'service_h'].mean() / 24.0),
              recovered=float(d.recovered.fillna(False).astype(bool).mean()), n=len(d))


def find_outage_row(paths, zone_km, gbps):
  for p in paths:
    t = pd.read_csv(p)
    m = t[(t.zone_km == zone_km) & (t.season.str.startswith('winter')) & (t.service.str.startswith('basic'))]
    if len(m):
      k = (m.balloon_gbps - gbps).abs().idxmin()
      return m.loc[k], p
  return None, None


def read_optional(pattern):
  out = {}
  for p in sorted(glob.glob(pattern)):
    try:
      out[p] = pd.read_csv(p)
    except Exception:  # noqa: BLE001  (a half-written file should not stop the ledger)
      pass
  return out


def availability_for(avail, standing):
  """(served_year, covered_year, served_djf, path) for the availability file whose tag names this standing size."""
  for p, t in avail.items():
    if f'standing{standing:g}' in os.path.basename(p):
      y = t[t.period == 'year']; w = t[t.period == 'DJF']
      if len(y):
        r = y.iloc[0]
        return dict(served_year=float(r.served_pop_share), covered_year=float(r.covered_pop_share),
                    served_djf=float(w.served_pop_share.iloc[0]) if len(w) else np.nan,
                    radius_km=float(r.radius_km), path=p)
  return None


def fleet_block(L, name, aloft, dwell_days, launches_day, surge_days, surge_launches_day, gbps, envelope_kg,
                recovery, turnaround_days, availability, env_source, dwell_source):
  """The common arithmetic; every value carries its formula or file in the source column."""
  flights_standing = launches_day * 365.0
  surge_flights = surge_launches_day * surge_days
  flights = flights_standing + surge_flights
  L.add(name, 'balloons_aloft_standing', aloft, 'balloons', dwell_source)
  L.add(name, 'service_dwell_days', dwell_days, 'days', dwell_source)
  L.add(name, 'launches_per_day_standing', launches_day, '/day', "Little's law: aloft / service dwell")
  if surge_launches_day:
    L.add(name, 'launches_per_day_surge', surge_launches_day, '/day', 'surge row (see surge_source)')
    L.add(name, 'surge_days_per_year', surge_days, 'days', 'command line --surge-days')
  L.add(name, 'flights_per_year', flights, 'flights', 'standing launches x 365 + surge launches x surge days')
  peak = max(launches_day, surge_launches_day)
  sites = max(c('standing_sites_min'), math.ceil(peak / c('launches_per_site_day')))
  L.add(name, 'launch_sites', sites, 'sites', f"peak launches/day / {c('launches_per_site_day')} ({src('launches_per_site_day')}), min {c('standing_sites_min')}")
  circ = dwell_days + turnaround_days
  L.add(name, 'payload_circulation_days', circ, 'days', f"service dwell + turnaround {turnaround_days} d ({src('turnaround_days')})")
  stock = peak * circ
  L.add(name, 'payload_inventory', stock, 'radios', "Little's law on the peak launch rate: launches/day x circulation days")
  lost = flights * (1 - recovery)
  retire = flights * recovery / c('radio_life_flights')
  L.add(name, 'payloads_consumed_per_year', lost + retire, 'radios/yr',
        f"flights x (1 - recovery {recovery:.2f}) + flights x recovery / {c('radio_life_flights')} flights of life ({src('radio_life_flights')})")
  L.add(name, 'envelope_stock_for_surge', surge_flights, 'envelopes', 'surge launches/day x surge days')
  L.add(name, 'envelope_mass_launched_per_year', flights * envelope_kg / 1e3, 't/yr', f'flights x {envelope_kg} kg ({env_source})')
  for k, r in RECOVERY_RATES.items():
    L.add(name, f'envelope_mass_unrecovered_{k}', flights * envelope_kg * (1 - r) / 1e3, 't/yr',
          f'launched mass x (1 - {r:.2f}); runbook section 8 recovery cases')
  gross = aloft * gbps
  L.add(name, 'capacity_aloft_gross', gross, 'Gbps', f'aloft x {gbps} Gbps a balloon (W11 rebased capacity)')
  if availability:
    L.add(name, 'served_pop_share_year', availability['served_year'], 'share', availability['path'])
    L.add(name, 'served_pop_share_DJF', availability['served_djf'], 'share', availability['path'])
    L.add(name, 'covered_pop_share_year', availability['covered_year'], 'share', availability['path'])
    L.add(name, 'capacity_delivered_estimate', gross * availability['served_year'], 'Gbps',
          'gross x served share of the year (availability.py); an estimate of what reaches people')
  cost_flights = flights * c('per_flight_eur')
  cost_sites = sites * c('site_fixed_eur_yr')
  cost_stock = stock * c('radio_unit_eur') / 5.0
  cost_fixed = c('ops_centre_eur_yr') + c('regulatory_eur_yr')
  total = cost_flights + cost_sites + cost_stock + cost_fixed
  L.add(name, 'cost_flights_eur_yr', cost_flights, 'EUR/yr', f"flights x EUR {c('per_flight_eur'):,} ({src('per_flight_eur')})")
  L.add(name, 'cost_sites_eur_yr', cost_sites, 'EUR/yr', f"sites x EUR {c('site_fixed_eur_yr'):,.0f} ({src('site_fixed_eur_yr')})")
  L.add(name, 'cost_payload_stock_eur_yr', cost_stock, 'EUR/yr', f"inventory x EUR {c('radio_unit_eur'):,} over 5 years ({src('radio_unit_eur')})")
  L.add(name, 'cost_fixed_eur_yr', cost_fixed, 'EUR/yr', f"ops centre + regulatory ({src('ops_centre_eur_yr')}; {src('regulatory_eur_yr')})")
  L.add(name, 'cost_total_eur_yr', total, 'EUR/yr', 'sum of the four cost lines; estimate, no overhead, no development')
  L.add(name, 'cost_total_eur_yr_low', total - cost_flights + flights * c('per_flight_eur_low'), 'EUR/yr', src('per_flight_eur_low'))
  L.add(name, 'cost_total_eur_yr_high', total - cost_flights + flights * c('per_flight_eur_high'), 'EUR/yr', src('per_flight_eur_high'))
  return total


def build(a):
  L = Ledger()
  drift_path = a.drift or f'results/drift_{a.year}.csv'
  if not os.path.exists(drift_path):
    raise SystemExit(f'{drift_path} not found; run run_drift.py (rerun 4) or pass --drift')
  dw = dwell_from_drift(drift_path)
  dwell_source = f'{drift_path}: slow controller, {dw["n"]} flights, day-weighted harmonic mean of monthly service dwell'
  env_kg = c('envelope_kg_light') if a.vehicle == 'light' else c('envelope_kg_ble')
  env_src = src('envelope_kg_light') if a.vehicle == 'light' else src('envelope_kg_ble')
  recovery = dw['recovered'] if a.recovery is None else a.recovery
  rec_src = f'{drift_path} recovered share' if a.recovery is None else 'command line --recovery'
  avail = read_optional('results/availability_*.csv')
  mesh = read_optional('results/mesh_*.csv')
  ttn = read_optional('results/time_to_n_*.csv')
  outage_paths = sorted(glob.glob('results/outage_scenario_*.csv')) + (['results/outage_scenario.csv'] if os.path.exists('results/outage_scenario.csv') else [])
  surge, surge_path = find_outage_row(outage_paths, a.zone_km, a.gbps)

  # --- pilot -------------------------------------------------------------
  name = 'pilot'
  aloft, dwell = c('pilot_aloft'), c('pilot_dwell_days')
  launches_day = aloft / dwell
  fleet_block(L, name, aloft, dwell, launches_day, 14, c('pilot_exercise_flights') / 14.0, c('pilot_mbps') / 1e3,
              0.0, c('pilot_recovery'), a.turnaround_days, None, 'contracted vehicle, envelope not ours (deployable_now.md)',
              src('pilot_dwell_days'))
  L.add(name, 'cost_quoted_eur_yr', c('pilot_cost_eur_yr'), 'EUR/yr', src('pilot_cost_eur_yr') + '; supersedes the formula lines above for this scenario')

  # --- readiness ----------------------------------------------------------
  name = 'readiness'
  aloft = a.standing
  dwell = dw['service_days_harm']
  launches_day = aloft / dwell
  L.add(name, 'winter_service_dwell_days', dw['winter_service_days'], 'days', f'{drift_path}: Dec-Feb mean')
  L.add(name, 'launches_per_day_standing_winter', aloft / dw['winter_service_days'], '/day', 'aloft / winter service dwell')
  if surge is not None:
    s_balloons, s_launches = float(surge.balloons), float(surge.launches_day)
    s_src = f'{surge_path}: zone {a.zone_km:g} km, winter, basic (voice/text), {surge.balloon_gbps:g} Gbps'
  else:
    s_balloons, s_launches, s_src = np.nan, 0.0, 'no outage_scenario CSV found; run rerun 5'
  L.add(name, 'surge_balloons_aloft', s_balloons, 'balloons', s_src)
  L.add(name, 'surge_source', 0, '', s_src)
  av_r = availability_for(avail, aloft)
  total_r = fleet_block(L, name, aloft, dwell, launches_day, a.surge_days, s_launches, a.gbps, env_kg, recovery,
                        a.turnaround_days, av_r, env_src, dwell_source)
  L.add(name, 'payload_recovery_share', recovery, 'share', rec_src)
  for p, t in mesh.items():
    y = t[(t.period == 'year') & (t.standing == aloft) & (t.gateways == 'all')]
    for r in y.itertuples():
      L.add(name, f'mesh_gateway_connected_share_{int(r.range_km)}km', r.gw_connected_share, 'share', p)
  for p, t in ttn.items():
    s = t[(t.season == 'all') & (t.frac == 0.5)]
    for case in ('cold', f'warm{aloft:g}'):
      g = s[s.case == case]
      if len(g):
        L.add(name, f'hours_to_half_requirement_{case}_median_over_zones', float(np.nanmedian(g.hours_median)), 'h', p)
        L.add(name, f'share_of_starts_never_reaching_half_{case}', float(g.never_share.mean()), 'share', p)
  L.add(name, 'cost_withdrawn_desk_estimate_eur_yr', 0.35e9, 'EUR/yr',
        'cost_funding_vs_starlink.md section 4: EUR 0.2-0.5 B, withdrawn by W27; shown for comparison only')

  # --- planning -------------------------------------------------------------
  name = 'planning'
  r = a.footprint_km
  aloft_p = -math.log(1 - c('coverage_target')) * LAND_KM2 / (math.pi * r ** 2)
  L.add(name, 'coverage_formula', c('coverage_target'), 'share',
        f"random placement 1 - exp(-N pi r^2 / land), r {r} km, land {LAND_KM2:.2e} km^2 (cost_model.py; target_population.md F)")
  av_p = None
  for p, t in avail.items():
    y = t[(t.period == 'year') & (t.radius_km == r)]
    if len(y):
      av_p = availability_for(avail, float(os.path.basename(p).split('standing')[1].split('_')[0])) if 'standing' in p else None
      break
  fleet_block(L, name, aloft_p, dwell, aloft_p / dwell, 0, 0.0, a.gbps, env_kg, recovery, a.turnaround_days, av_p,
              env_src, dwell_source)
  L.add(name, 'cost_planning_case_eur_yr', 6.3e9, 'EUR/yr',
        'cost_funding_vs_starlink.md section 1: 5-day forecast release planning case, for comparison')
  return L.frame(), dict(total_readiness=total_r)


def write_md(df, path, a):
  lines = [f'# Scenario ledger (W27)\n',
           f'*Generated by `scenario_ledger.py`: drift year {a.year}, {a.gbps:g} Gbps a balloon, standing layer '
           f'{a.standing:g}, surge zone {a.zone_km:g} km for {a.surge_days} days, turnaround {a.turnaround_days} d, '
           f'{a.vehicle} vehicle envelope. Every value is an estimate; the source column names the file or constant.*\n']
  for s in df.scenario.unique():
    lines.append(f'\n## {s}\n')
    lines.append('| metric | value | unit | source |\n|---|---|---|---|')
    for r in df[df.scenario == s].itertuples():
      v = r.value
      vs = f'{v:,.3g}' if isinstance(v, (int, float)) and not (isinstance(v, float) and math.isnan(v)) else str(v)
      if isinstance(v, (int, float)) and not math.isnan(float(v)) and abs(v) >= 1e6:
        vs = f'{v / 1e6:,.1f} M'
      lines.append(f'| {r.metric} | {vs} | {r.unit} | {r.source} |')
  with open(path, 'w') as f:
    f.write('\n'.join(lines) + '\n')


def main(argv=None):
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument('--year', type=int, default=2025, help='drift year: results/drift_<year>.csv')
  ap.add_argument('--drift', help='explicit drift CSV path')
  ap.add_argument('--gbps', type=float, default=0.2, help='capacity per balloon; picks the nearest outage_scenario row')
  ap.add_argument('--standing', type=float, default=100, help='standing layer for the readiness scenario')
  ap.add_argument('--zone-km', type=float, default=300)
  ap.add_argument('--surge-days', type=int, default=30, help='one surge a year of this length')
  ap.add_argument('--turnaround-days', type=float, default=CONSTANTS['turnaround_days'][0])
  ap.add_argument('--footprint-km', type=float, default=80, help='planning case service radius')
  ap.add_argument('--vehicle', choices=['light', 'ble'], default='light')
  ap.add_argument('--recovery', type=float, help='payload recovery share; default: the drift file')
  a = ap.parse_args(argv)
  df, info = build(a)
  os.makedirs('results', exist_ok=True)
  df.to_csv('results/scenario_ledger.csv', index=False)
  write_md(df, 'results/scenario_ledger.md', a)
  pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 90)
  show = df[df.metric.isin(['balloons_aloft_standing', 'launches_per_day_standing', 'launches_per_day_surge',
                            'flights_per_year', 'launch_sites', 'payload_inventory', 'envelope_mass_launched_per_year',
                            'capacity_aloft_gross', 'served_pop_share_year', 'cost_total_eur_yr'])]
  print(show.pivot(index='metric', columns='scenario', values='value').round(2).to_string())
  print(f'\nreadiness total EUR {info["total_readiness"] / 1e9:.2f} B/yr (estimate; the withdrawn desk figure was 0.2-0.5 B)')
  print('wrote results/scenario_ledger.csv and results/scenario_ledger.md')
  return df


if __name__ == '__main__':
  main()

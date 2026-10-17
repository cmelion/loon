"""Cost-reduction levers for the slow-traversal balloon fleet.

Builds on cost_model.py (imported, not modified): same region, same unit
costs, same Monte Carlo inputs and the same bootstrap over the 120 simulated
'slow' flights in results/drift_2025.csv. The fleet-cost formula is
re-implemented here at *monthly* resolution so a lever can change the
coverage target month by month (seasonal service) or the area served; with
every lever off it reproduces cost_model.balloon_model (checked at run time,
see `check_baseline`).

Levers (each with its range stated as an ASSUMPTION or source in LEVERS):
  1  envelope unit cost at ~400k units/yr (learning curve)
  2  envelope recovery: recycling credit + partial reuse of land landings
  3  payload recovery 94 % (29 kg/m^2 glider, results/glider_sizing.csv),
     longer service life, cheaper refurbishment
  4  fuel cell on lift gas instead of most of the battery -> lighter system
     -> smaller envelope
  5  longer dwell from a better controller (DWELL_MULT, placeholder 1.0)
  6  seasonal / partial service: summer-only, lower winter target,
     populated land only
  7  larger radio footprint (60-80 km) vs capacity per km^2
  8  hybrid: balloons at a 50 % target with a satellite backstop

Run:  PYTHONWARNINGS=ignore .venv/bin/python -I cost_reduction.py [--dwell-mult X]
Writes results/cost_reduction.md and results/cost_reduction.png.
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)                     # -I drops the script dir

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from global_land_mask import globe

import cost_model as cm                      # noqa: E402  (constants, sim loader, bootstrap)

OUT_MD = os.path.join(HERE, 'results', 'cost_reduction.md')
OUT_PNG = os.path.join(HERE, 'results', 'cost_reduction.png')
N = cm.N_DRAWS
rng = np.random.default_rng(cm.SEED + 1)
tri = cm.tri

# ----------------------------------------------------------------------------
# Lever 5, dwell from a smarter controller.
# DWELL_MULT = None  -> use the measured per-month dwell of the 36 h forecast
#                       look-ahead planner (planner.py, results/drift_2025_plan.csv,
#                       same 120 launches/seeds as 'slow'), incl. its 74 % radio
#                       recovery. This is the default when that file exists.
# DWELL_MULT = float -> a flat multiplier on every month's dwell (sensitivity;
#                       also settable with --dwell-mult X).
# The planner's headline "x1.22" is the ratio of per-flight harmonic means
# (2.31 vs 1.90 d). Cost, however, scales with launches/day = aloft / (mean
# dwell in that month) (Little's law), i.e. with the day-weighted harmonic of
# the *monthly means* - and on that metric the planner gives 3.63 vs 3.65 d,
# x0.99: winter (Dec-Mar) is unchanged and winter is where the launches are.
# Both are reported; the per-month profile drives the stacks.
# ----------------------------------------------------------------------------
DWELL_MULT = None
PLAN_CSV = os.path.join(HERE, 'results', 'drift_2025_plan.csv')
FLAT_DWELL_SWEEP = [1.22, 1.5, 2.0]      # 1.22 = the planner's per-flight figure
PLANNER_LABEL = 'planner, per-month (measured)'
PLACEHOLDER = False                      # set in main() if no planner data

DAYS = cm.DAYS_IN_MONTH.astype(float)
MONTHS = list(range(1, 13))
WINTER = cm.SEASONS['Winter (Dec-Mar)']
SUMMER = cm.SEASONS['Summer (Jun-Aug)']
BASE_COV = cm.COVERAGE_TARGETS[cm.BASE_COVERAGE]      # 0.95
GAS_KG = cm.H2_KG_PER_FLIGHT
SYSTEM_KG = cm.ENVELOPE_KG + cm.PAYLOAD_KG + GAS_KG   # lifted mass incl. gas
AIR_PER_H2 = 28.97 / 2.016 - 1.0                      # net lift kg per kg H2 (~13.4)

# ----------------------------------------------------------------------------
# Geography for levers 2 and 6 (computed from the repo's own data where possible)
# ----------------------------------------------------------------------------


def region_land_fraction():
  """Land share of the 36-62 N, 10 W-42 E box (global_land_mask, cos-lat weighted)."""
  la = np.arange(cm.LAT0 + 0.05, cm.LAT1, 0.1)
  lo = np.arange(cm.LON0 + 0.05, cm.LON1, 0.1)
  LO, LA = np.meshgrid(lo, la)
  w = np.cos(np.radians(LA))
  return float((globe.is_land(LA, LO) * w).sum() / w.sum())


def envelope_land_fraction(slow):
  """Scenario A of analyze_envelopes.py: envelope cut down at the radio release
  point (falls back to region exit when the flight never passed a site)."""
  lat = slow.env_a_lat.fillna(slow.env_b_lat).to_numpy()
  lon = slow.env_a_lon.fillna(slow.env_b_lon).to_numpy()
  ok = ~np.isnan(lat)
  return float(globe.is_land(lat[ok], lon[ok]).mean())


# Populated share of the region's *land*. No population raster in the repo.
# ASSUMPTION, rough reading of GHSL/GPW-style maps: interior Scandinavia, the
# Alps/Carpathians/Caucasus, Anatolian and Iberian interiors, Ukrainian/Russian
# steppe and the Maghreb margins are sparse; ~60 % of the land carries almost
# all of the population (density above ~10 /km^2).
POPULATED_LAND_SHARE = tri(0.45, 0.60, 0.75)
# How much of the fleet can actually be withheld from unpopulated area / sea.
# Drifting balloons cannot be confined to the populated cells: they cross the
# Mediterranean, Black Sea, Baltic and empty land on the way. 0 = no saving
# (fully random drift), 1 = perfect targeting. ASSUMPTION, needs the smarter
# controller's track statistics to pin down.
TARGETING_EFF = tri(0.2, 0.4, 0.7)

# ----------------------------------------------------------------------------
# Lever definitions. Each lever is a dict of scenario overrides; tri specs are
# sampled per Monte Carlo draw, scalars are fixed.
# ----------------------------------------------------------------------------
LEVERS = {}


def lever(key, name, group, **over):
  LEVERS[key] = dict(name=name, group=group, over=over)


# 1. Envelope cost at volume. cost_model's EUR 4-25k (mode 10k) is for a
# Loon-scale industry (~1-2k envelopes/yr). At ~400k/yr that is ~8 doublings;
# Wright-law learning rates for manufactured goods cluster at 80-90 % per
# doubling (Nagy et al. 2013, PLoS ONE; ASSUMPTION that balloon film follows
# them): 0.85^8 = 0.27 -> ~EUR 2.7k from the mode, bounded below by material
# (68.5 kg of co-extruded PE film at EUR 10-30/kg = EUR 0.7-2k + seams, QA,
# fittings). ASSUMPTION range EUR 2.5-7k, mode 4k.
lever('L1', 'Envelope cost at volume (learning curve)', 'unit cost',
      envelope=tri(2_500, 4_000, 7_000))

# 2. Envelope recovery. 66 % of envelopes land on land (computed below from
# results/drift_2025.csv). Of those, a collection fraction is found; of the
# collected, a small fraction of superpressure PE envelopes can be
# re-tensioned and reflown (ASSUMPTION 0-40 %, mode 15 %: Loon never reused an
# envelope; pinholes/creep after a parachute landing are the norm) at a refurb
# cost of 20-50 % of a new one. The rest is recycled: PE film scrap at
# EUR 0.1-0.4/kg (ASSUMPTION, European post-industrial LDPE scrap prices).
lever('L2', 'Envelope reuse / recycling credit (66 % land on land)', 'recovery',
      env_collected=tri(0.5, 0.75, 0.9), env_reusable=tri(0.0, 0.15, 0.40),
      env_refurb=tri(0.2, 0.35, 0.5), pe_scrap_eur_kg=tri(0.1, 0.25, 0.4))

# 3. Payload recovery 94 % with a 29 kg/m^2 glider (results/glider_sizing.csv:
# L/D 12, 2 m/s sink -> 0.939). Higher wing loading means a *smaller* wing
# for the same mass, so no envelope penalty, but a faster landing: intact
# fraction ASSUMPTION 0.85-0.98 (mode 0.93 vs 0.95 base). With a designed-for-
# reuse payload: service life 10-40 flights (mode 20 vs 15), refurbishment
# 5-15 % (mode 8 % vs 10 %). ASSUMPTION.
lever('L3', 'Payload recovery 94 % + designed for reuse', 'recovery',
      rec_frac=0.94, intact=tri(0.85, 0.93, 0.98),
      max_flights=tri(10, 20, 40), refurb=tri(0.05, 0.08, 0.15))

# 4. Fuel cell on lift gas. Battery ~15 kg (night energy ~1.2 kWh at ~100 W,
# ASSUMPTION) replaced by a ~5 kg PEM stack + regulator -> 10 kg saved, minus
# the lift lost to the H2 it burns: 1.2 kWh/day / (50 % x 33.3 kWh/kg) =
# 0.07 kg H2/day x 13.4 kg lift per kg = ~1 kg of lift per day, ~2 kg mean
# over a 3.7-day flight. Net lifted-mass saving ASSUMPTION 4-10 kg. The
# envelope scales with lifted mass (area ~ M^2/3, solved as a fixed point)
# and its cost is taken proportional to film mass. Payload cost: battery
# (EUR 1.5-3.8k at EUR 100-250/kg) out, fuel-cell system in (EUR 2-6k at
# volume, ASSUMPTION) -> net EUR -2k to +3k per payload. Extra H2 ~0.3 kg.
lever('L4', 'Fuel cell replaces battery (lighter, smaller envelope)', 'unit cost',
      mass_saving_kg=tri(4.0, 7.0, 10.0), payload_delta=tri(-2_000, 500, 3_000),
      extra_h2_kg=0.3)

# 5. Smarter controller (see DWELL_MULT above). The 'dwell' key is a marker;
# run() swaps in the planner's monthly dwell or a flat multiplier.
lever('L5', 'Smarter controller dwell', 'dwell', dwell='L5')

# 6. Seasonal / partial service.
lever('L6a', 'Summer-only service (Jun-Aug, 95 %)', 'service',
      cov_months={m: (BASE_COV if m in SUMMER else 0.0) for m in MONTHS})
lever('L6b', 'Winter target 50 % (Dec-Mar), 95 % otherwise', 'service',
      cov_months={m: (0.5 if m in WINTER else BASE_COV) for m in MONTHS})
lever('L6c', 'Populated land only (targeted drift)', 'service',
      area_mode='populated')

# 7. Larger footprint. 60-80 km radius from 20 km altitude = 18-14 deg
# minimum elevation, at the edge of what an unmodified handset's 23 dBm
# uplink can close; needs a multi-beam, higher-gain antenna (payload cost
# x1.1-1.6, ASSUMPTION). Capacity per balloon unchanged, so capacity per km^2
# falls as (45/r)^2. Loon's quoted ~40 km was the practical limit it reached.
lever('L7', 'Footprint radius 60-80 km (higher-gain antennas)', 'coverage',
      footprint_r=tri(60.0, 70.0, 80.0), payload_mult=tri(1.1, 1.3, 1.6))

# 8. Hybrid: balloons run at a 50 % availability target all year and a
# direct-to-cell satellite (or terrestrial) layer backstops the gaps. Random
# placement is far less wasteful at 50 % (-ln 0.5 = 0.69 vs 3.0 balloons per
# cell). The satellite layer's cost is not added (it exists anyway).
lever('L8', 'Hybrid: 50 % target, satellite backstop', 'service',
      cov_months={m: 0.5 for m in MONTHS})

STACK_ORDER = ['L1', 'L3', 'L7', 'L2', 'L4', 'L5', 'L6b', 'L6c', 'L8']
ENGINEERING = ['L1', 'L3', 'L7', 'L2', 'L4', 'L5']      # same service as today


# ----------------------------------------------------------------------------
# Monthly fleet-cost model (vectorised over Monte Carlo draws)
# ----------------------------------------------------------------------------
def monthly_inv_dwell(dwell_days, n):
  """Bootstrap 1/mean-dwell per month -> (12, n), as cost_model.inv_dwell_draws
  does but keeping the months separate."""
  out = np.empty((12, n))
  for i, m in enumerate(MONTHS):
    x = dwell_days[m]
    idx = rng.integers(0, len(x), (n, len(x)))
    out[i] = 1.0 / x[idx].mean(axis=1)
  return out


def envelope_mass_scale(saving_kg):
  """Envelope mass after removing `saving_kg` from the lifted mass. Film area
  ~ volume^(2/3) ~ (lifted mass)^(2/3), and the envelope is part of that mass."""
  m0, e0 = SYSTEM_KG, cm.ENVELOPE_KG
  e = np.full_like(np.asarray(saving_kg, dtype=float), e0)
  for _ in range(20):
    e = e0 * ((m0 - saving_kg - (e0 - e)) / m0) ** (2.0 / 3.0)
  return e / e0


def fleet_cost(p, inv_m, cov_m, rec_frac, land_frac, geometric=False):
  """Annual cost by line item at monthly resolution.
  p: dict of per-draw arrays (cost_model inputs + lever extras);
  inv_m: (12, n) 1/dwell draws; cov_m: (12, n) coverage target per month."""
  n = inv_m.shape[1]
  r = p['footprint_r']
  hex_area = 1.5 * math.sqrt(3) * r ** 2
  n_ideal = cov_m * cm.REGION_KM2 / hex_area
  n_random = -np.log(1 - np.minimum(cov_m, 0.999)) * cm.REGION_KM2 / (np.pi * r ** 2)
  aloft_m = ((1 - p['tiling']) * n_ideal + p['tiling'] * n_random) * p['area_frac']
  per_day_m = aloft_m * inv_m / p['dwell_mult']
  per_yr = (per_day_m * DAYS[:, None]).sum(0)
  aloft = (aloft_m * DAYS[:, None]).sum(0) / DAYS.sum()
  peak_day = per_day_m.max(0)
  sites = np.maximum(cm.MIN_SITES, np.ceil(peak_day / p['site_rate']))
  served = (cov_m > 0)
  time_frac = (served * DAYS[:, None]).sum(0) / DAYS.sum()

  rec = rec_frac * p['intact']
  if geometric:
    # expected flights per payload before loss or retirement
    e_fl = (1 - rec ** p['max_flights']) / (1 - rec)
    consumed = 1.0 / e_fl
  else:
    consumed = (1 - rec) + rec / p['max_flights']           # cost_model formula
  env_unit = p['envelope'] * p['env_mass_scale']
  env_reuse = land_frac * p['env_collected'] * p['env_reusable']
  env_recycle = land_frac * p['env_collected'] * (1 - p['env_reusable']) * \
      cm.ENVELOPE_KG * p['env_mass_scale'] * p['pe_scrap_eur_kg']
  env_per_flight = env_unit * (1 - env_reuse + env_reuse * p['env_refurb']) - env_recycle
  payload_unit = p['payload'] * p['payload_mult'] + p['payload_delta']
  h2_kg = (GAS_KG * p['env_mass_scale'] + p['extra_h2_kg']) * (1 + p['h2_loss'])
  items = {
    'Envelopes': per_yr * env_per_flight,
    'Payload (amortised)': per_yr * payload_unit * (consumed + rec * p['refurb']),
    'Green hydrogen': per_yr * h2_kg * p['h2_price'],
    'Launch sites & ops': per_yr * p['launch'] + sites * p['site_fixed'],
    'Recovery (payload + envelope)': per_yr * (rec * p['recovery'] + p['env_recovery']),
    'Ground network & backhaul': (cm.REGION_KM2 * p['area_frac'] / p['gw_area'] *
                                  p['gw_cost'] + p['core']),
    'Regulatory & insurance': per_yr * p['insurance'] + p['regulatory'],
  }
  items['G&A overhead'] = p['overhead'] * sum(items.values())
  total = sum(items.values())
  served_km2_yr = cm.REGION_KM2 * p['area_frac'] * time_frac
  gbps = aloft * p['mbps'] / 1e3
  return dict(items=items, total=total, aloft=aloft, per_day=per_yr / 365.0,
              per_yr=per_yr, sites=sites, per_km2=total / served_km2_yr,
              time_frac=time_frac, area_frac=p['area_frac'] * np.ones(n),
              gbps=gbps, gbps_per_mkm2=gbps / (cm.REGION_KM2 * p['area_frac'] / 1e6),
              pe_t=per_yr * cm.ENVELOPE_KG * p['env_mass_scale'] *
              (1 - env_reuse) / 1e3)


DEFAULT_EXTRAS = dict(area_frac=1.0, dwell_mult=None, env_mass_scale=1.0,
                      env_collected=0.0, env_reusable=0.0, env_refurb=0.0,
                      pe_scrap_eur_kg=0.0, payload_mult=1.0, payload_delta=0.0,
                      extra_h2_kg=0.0)


def run(levers, ctx, n=N, dwell_mult=None, planner=False, geometric=False):
  """Monte Carlo of the fleet with the given levers applied together.
  dwell_mult: None -> lever 5 (if present) uses DWELL_MULT (planner profile
  or flat); a float/tri -> flat multiplier on the 'slow' dwell regardless.
  planner=True forces the planner's measured per-month profile.
  Both RNGs are reseeded per call so every case uses the same paired draws
  (a lever that changes nothing then costs exactly nothing)."""
  global rng
  rng = np.random.default_rng(cm.SEED + 1)
  cm.rng = np.random.default_rng(cm.SEED)
  specs = dict(cm.BALLOON_INPUTS)
  extras = dict(DEFAULT_EXTRAS)
  cov = {m: BASE_COV for m in MONTHS}
  rec_frac = None
  area_mode = None
  mass_saving = None
  dwell_days = ctx['dwell_days']
  mult = 1.0
  if planner:
    dwell_days, rec_frac = ctx['dwell_days_plan'], ctx['rec_frac_plan']
  elif dwell_mult is not None:
    mult = dwell_mult
  elif 'L5' in levers:
    if DWELL_MULT is None and ctx['dwell_days_plan'] is not None:
      dwell_days = ctx['dwell_days_plan']        # measured per-month profile
      rec_frac = ctx['rec_frac_plan']            # planner's own radio recovery
    elif DWELL_MULT is not None:
      mult = DWELL_MULT
  for k in levers:
    for key, val in LEVERS[k]['over'].items():
      if key == 'rec_frac':
        rec_frac = val
      elif key == 'dwell':
        continue
      elif key == 'cov_months':
        cov = val
      elif key == 'area_mode':
        area_mode = val
      elif key == 'mass_saving_kg':
        mass_saving = val
      elif key in specs:
        specs[key] = val
      else:
        extras[key] = val
  p = {k: cm.sample(v, n) if isinstance(v, tuple) else np.full(n, float(v))
       for k, v in specs.items()}
  for k, v in extras.items():
    if k == 'dwell_mult':
      continue
    p[k] = cm.sample(v, n) if isinstance(v, tuple) else np.full(n, float(v))
  p['dwell_mult'] = cm.sample(mult, n) if isinstance(mult, tuple) else np.full(n, float(mult))
  if rec_frac is None:
    rec_frac = ctx['rec_frac']
  if mass_saving is not None:
    p['env_mass_scale'] = envelope_mass_scale(cm.sample(mass_saving, n))
  if area_mode == 'populated':
    pop = ctx['land_frac'] * cm.sample(POPULATED_LAND_SHARE, n)
    eff = cm.sample(TARGETING_EFF, n)
    p['area_frac'] = 1 - eff * (1 - pop)
  cov_m = np.array([[cov[m]] * n for m in MONTHS], dtype=float)
  inv_m = monthly_inv_dwell(dwell_days, n)
  out = fleet_cost(p, inv_m, cov_m, rec_frac, ctx['env_land_frac'], geometric)
  out['ratio_star'] = out['per_km2'] / ctx['star_km2']
  return out


def check_baseline(ctx):
  """With no levers the monthly model must match cost_model.balloon_model."""
  mine = run([], ctx)
  ref = cm.run_balloon(ctx['dwell_days'], ctx['rec_frac'], MONTHS, BASE_COV)[0]
  a, b = np.median(mine['total']), np.median(ref['total'])
  assert abs(a / b - 1) < 0.03, (a, b)
  return mine, ref


# ----------------------------------------------------------------------------
pct, fmt_eur, rng_str, num_str = cm.pct, cm.fmt_eur, cm.rng_str, cm.num_str


def tri_str(t):
  return f'{t[0]:.0%}–{t[2]:.0%} (mode {t[1]:.0%})'


def ratio_str(x):
  lo, mid, hi = pct(x)
  return f'{mid:.0f}× ({lo:.0f}–{hi:.0f}×)' if mid >= 10 else f'{mid:.1f}× ({lo:.1f}–{hi:.1f}×)'


def load_planner(dwell_days_slow):
  """Per-month dwell of the forecast-look-ahead planner, if its sweep exists.
  Returns (dwell_days, rec_frac, cost_mult, flight_harm_mult) or None."""
  if not os.path.exists(PLAN_CSV):
    return None
  df = pd.read_csv(PLAN_CSV)
  df = df[df.controller == 'plan']
  dd = {m: g.dwell_h.to_numpy() / 24.0 for m, g in df.groupby('month')}
  if set(dd) != set(MONTHS):
    return None
  harm = lambda d: 1.0 / cm.point_inv_dwell(d, MONTHS)[0]      # day-weighted, monthly means
  cost_mult = harm(dd) / harm(dwell_days_slow)
  slow_all = np.concatenate([dwell_days_slow[m] for m in MONTHS])
  plan_all = np.concatenate([dd[m] for m in MONTHS])
  flight_mult = (1 / np.mean(1 / plan_all)) / (1 / np.mean(1 / slow_all))  # per-flight harmonic
  return dd, float(df.recovered.mean()), float(cost_mult), float(flight_mult)


def main():
  global DWELL_MULT, PLACEHOLDER
  ap = argparse.ArgumentParser()
  ap.add_argument('--dwell-mult', type=float, default=None,
                  help='flat dwell multiplier for lever 5 instead of the planner\'s '
                       'measured per-month profile')
  args = ap.parse_args()
  if args.dwell_mult is not None:
    DWELL_MULT = args.dwell_mult

  slow, dwell_days, rec_frac = cm.load_sim()
  plan = load_planner(dwell_days)
  sysr = cm.run_systems()
  ctx = dict(dwell_days=dwell_days, rec_frac=rec_frac,
             dwell_days_plan=plan[0] if plan else None,
             rec_frac_plan=plan[1] if plan else None,
             plan_cost_mult=plan[2] if plan else None,
             plan_flight_mult=plan[3] if plan else None,
             land_frac=region_land_fraction(),
             env_land_frac=envelope_land_fraction(slow),
             star_km2=sysr['Starlink (LEO broadband)']['per_km2'])
  if DWELL_MULT is None and plan:
    dwell_label = (f'planner dwell, measured per month (×{plan[2]:.2f} on the cost '
                   f'metric; ×{plan[3]:.2f} per-flight)')
  elif DWELL_MULT is None:
    DWELL_MULT, PLACEHOLDER = 1.0, True
    dwell_label = '×1.0 PLACEHOLDER, no planner data'
  else:
    dwell_label = f'flat ×{DWELL_MULT:g} on every month'
  LEVERS['L5']['name'] = f'Smarter controller dwell ({dwell_label})'
  base, ref = check_baseline(ctx)
  star50 = np.median(ctx['star_km2'])

  # Individual levers
  single = {k: run([k], ctx) for k in LEVERS}
  sweep_keys = ([PLANNER_LABEL] if plan else []) + [f'flat ×{x:g}' for x in FLAT_DWELL_SWEEP]
  sweep_mult = {k: (None if k == PLANNER_LABEL else x)
                for k, x in zip(sweep_keys, ([None] if plan else []) + FLAT_DWELL_SWEEP)}

  def dwell_variants(levers):
    return {k: (run(levers, ctx, planner=True) if k == PLANNER_LABEL
                else run(levers, ctx, dwell_mult=sweep_mult[k])) for k in sweep_keys}

  dwell_sweep = dwell_variants(['L5'])
  # Model-formula note: geometric payload amortisation
  geo = run([], ctx, geometric=True)

  # Stacks (cumulative, in STACK_ORDER)
  cum = [('Baseline (95 %, year-round)', base)]
  applied = []
  for k in STACK_ORDER:
    applied.append(k)
    cum.append((LEVERS[k]['name'], run(list(applied), ctx)))
  stacks = {
    'Engineering only (same 95 % year-round service)': run(ENGINEERING, ctx),
    'Engineering + winter 50 % + populated land': run(ENGINEERING + ['L6b', 'L6c'], ctx),
    'Everything incl. hybrid 50 % target': run(STACK_ORDER, ctx),
  }
  stack_dwell = dwell_variants(STACK_ORDER)
  eng_dwell = dwell_variants(ENGINEERING)
  stack_80 = run(ENGINEERING + ['L6b', 'L6c'], ctx)   # for the 2-5x question

  make_chart(cum, star50)
  write_md(locals())
  print(f'Wrote {OUT_MD}\nWrote {OUT_PNG}')
  print(f'Baseline {rng_str(base["total"])}/yr  {ratio_str(base["ratio_star"])} Starlink')
  for k, r in single.items():
    print(f'  {k:4s} {LEVERS[k]["name"][:52]:52s} {rng_str(r["total"]):34s} '
          f'{100 * (1 - np.median(r["total"]) / np.median(base["total"])):5.1f} %  '
          f'{ratio_str(r["ratio_star"])}')
  for k, r in stacks.items():
    print(f'  {k:58s} {rng_str(r["total"]):34s} {ratio_str(r["ratio_star"])}')


# ----------------------------------------------------------------------------
INK, INK2, GRID, SURF = cm.INK, cm.INK2, cm.GRID, '#fcfcfb'
C_TOTAL, C_CUT, C_SERVICE, C_PLACE = cm.PAL[1], cm.PAL[0], cm.PAL[2], '#9a9994'


def make_chart(cum, star50):
  plt.rcParams.update({'font.size': 9, 'axes.edgecolor': INK2,
                       'axes.labelcolor': INK2, 'xtick.color': INK2,
                       'ytick.color': INK2, 'text.color': INK})
  fig, ax = plt.subplots(figsize=(13, 7.2), facecolor=SURF)
  meds = [np.median(r['total']) / 1e9 for _, r in cum]
  los = [np.percentile(r['total'], 10) / 1e9 for _, r in cum]
  his = [np.percentile(r['total'], 90) / 1e9 for _, r in cum]
  labels = []
  x = 0
  xs = []
  for i, (name, r) in enumerate(cum):
    key = STACK_ORDER[i - 1] if i else None
    if i == 0:
      ax.bar(x, meds[0], color=C_TOTAL, width=0.62)
      ax.errorbar(x, meds[0], yerr=[[meds[0] - los[0]], [his[0] - meds[0]]],
                  color=INK, capsize=4, lw=1.2)
      ax.text(x, his[0] + 0.3, f'€{meds[0]:.1f} B', ha='center', fontsize=8.5)
      labels.append('Baseline\n95 % year-round')
    else:
      top, bot = meds[i - 1], meds[i]
      grp = LEVERS[key]['group']
      placeholder = key == 'L5' and (PLACEHOLDER or abs(top - bot) < 0.05)
      col = C_PLACE if placeholder else (C_SERVICE if grp == 'service' else C_CUT)
      if placeholder:
        ax.bar(x, 0.25, bottom=top - 0.125, color='none', edgecolor=col, ls='--',
               width=0.62, lw=1.2)
        msg = ('placeholder\n×1.0 (awaiting\nsim result)' if PLACEHOLDER else
               f'{"+" if bot > top else "−"}€{abs(top - bot) * 1e3:.0f} M\n(planner: winter\ndwell unchanged)')
        ax.text(x, top + 0.4, msg, ha='center', fontsize=7.5, color=INK2)
      else:
        ax.bar(x, bot - top, bottom=top, color=col, width=0.62)
        ax.text(x, max(top, bot) + 0.3, f'{"+" if bot > top else "−"}€{abs(top - bot):.1f} B',
                ha='center', fontsize=8.5)
      ax.plot([x - 0.31, x + 0.31], [top, top], color=INK2, lw=0.6)
      ax.errorbar(x, bot, yerr=[[bot - los[i]], [his[i] - bot]], color=INK, capsize=3,
                  lw=0.9, alpha=0.7)
      short = name.split(' (')[0]
      labels.append(f'{key}\n' + '\n'.join(wrap(short, 18)))
    xs.append(x)
    x += 1
  # final total bar
  ax.bar(x, meds[-1], color=C_TOTAL, width=0.62)
  ax.errorbar(x, meds[-1], yerr=[[meds[-1] - los[-1]], [his[-1] - meds[-1]]],
              color=INK, capsize=4, lw=1.2)
  ax.text(x, his[-1] + 0.3, f'€{meds[-1]:.1f} B\n({np.median(cum[-1][1]["ratio_star"]):.1f}× Starlink\nper km² served)',
          ha='center', fontsize=8.5)
  labels.append('Best stacked\ncase')
  xs.append(x)
  ax.axhline(star50 * cm.REGION_KM2 / 1e9 * 5, color=INK2, lw=0.8, ls=':')
  ax.text(3.6, star50 * cm.REGION_KM2 / 1e9 * 5,
          '5× Starlink per km², whole region', va='bottom', ha='left', fontsize=8, color=INK2)
  ax.set_xticks(xs, labels, fontsize=7.8)
  ax.set_ylabel('Annual fleet cost, EUR billion (median; whiskers P10–P90 of the cumulative case)')
  ax.set_ylim(0, max(his) * 1.15)
  ax.grid(axis='y', color=GRID, lw=0.8); ax.set_axisbelow(True)
  for s in ('top', 'right'):
    ax.spines[s].set_visible(False)
  handles = [plt.Rectangle((0, 0), 1, 1, color=C_CUT, label='Engineering / unit-cost lever'),
             plt.Rectangle((0, 0), 1, 1, color=C_SERVICE, label='Service re-scoping lever (less delivered)'),
             plt.Rectangle((0, 0), 1, 1, fc='none', ec=C_PLACE, ls='--',
                           label=('Placeholder (dwell multiplier not yet measured)' if PLACEHOLDER
                                  else 'No net change (measured planner dwell)')),
             plt.Rectangle((0, 0), 1, 1, color=C_TOTAL, label='Total')]
  ax.legend(handles=handles, loc='upper right', frameon=False, fontsize=8)
  ax.set_title('Stacking the cost-reduction levers, Europe → Black Sea balloon fleet',
               loc='left', fontweight='bold')
  fig.tight_layout()
  fig.savefig(OUT_PNG, dpi=150, facecolor=SURF)
  plt.close(fig)


def wrap(s, w):
  out, line = [], ''
  for word in s.split():
    if len(line) + len(word) + 1 > w and line:
      out.append(line); line = word
    else:
      line = (line + ' ' + word).strip()
  out.append(line)
  return out


# ----------------------------------------------------------------------------
def write_md(v):
  base, single, stacks, cum, ctx = v['base'], v['single'], v['stacks'], v['cum'], v['ctx']
  star50 = v['star50']
  b50 = np.median(base['total'])
  L = []
  a = L.append

  def row(name, r, delivered=''):
    sav = 100 * (1 - np.median(r['total']) / b50)
    return (f'| {name} | {rng_str(r["total"])} | {-sav:+.0f} % | {num_str(r["per_day"])} | '
            f'{rng_str(r["per_km2"])} | {ratio_str(r["ratio_star"])} | {delivered} |')

  def delivered(r):
    tf, af = np.median(r['time_frac']), np.median(r['area_frac'])
    cap = np.median(r['gbps_per_mkm2']) / np.median(base['gbps_per_mkm2'])
    bits = []
    if tf < 0.999:
      bits.append(f'{tf:.0%} of the year')
    if af < 0.999:
      bits.append(f'{af:.0%} of the area')
    if abs(cap - 1) > 0.02:
      bits.append(f'capacity/km² ×{cap:.2f}')
    return ', '.join(bits) if bits else 'same as baseline'

  best = stacks['Everything incl. hybrid 50 % target']
  eng = stacks['Engineering only (same 95 % year-round service)']
  mid = stacks['Engineering + winter 50 % + populated land']
  hdr = ('| Case | Annual cost | vs baseline | Launches/day | EUR/km²/yr served | × Starlink per km² | Delivered |\n'
         '|---|---|---|---|---|---|---|')

  a('# Balloon fleet — cost-reduction levers\n')
  a(f'*Generated by `cost_reduction.py` on top of `cost_model.py` (same inputs, {N:,} Monte Carlo '
    f'draws, bootstrap over the {len(v["slow"])} simulated "slow" flights). Median (P10 – P90). '
    f'Lever 5 dwell: **{v["dwell_label"]}**'
    + '. EUR/km² is per km² of *served* area and time, so partial-service cases are normalised '
    'to what they deliver; a lower coverage target is not normalised (as in `cost_model.py`).*\n')

  a('## Verdict\n')
  a(f'Baseline: **{rng_str(base["total"])}/yr**, {ratio_str(base["ratio_star"])} Starlink per km². '
    f'Every engineering lever stacked (cheap envelopes, 94 % payload recovery, 70 km footprint, '
    f'envelope reuse, fuel cell, lever-5 dwell) but the *same* 95 % year-round service: '
    f'**{rng_str(eng["total"])}/yr, {ratio_str(eng["ratio_star"])} Starlink**. '
    f'Re-scoping the service as well (50 % target in winter, fleet concentrated on populated land): '
    f'**{rng_str(mid["total"])}/yr, {ratio_str(mid["ratio_star"])}**. '
    f'Going to a 50 % availability target all year with a satellite backstop: '
    f'**{rng_str(best["total"])}/yr, {ratio_str(best["ratio_star"])}**.')
  closes = np.median(best['ratio_star']) <= 5
  closes_eng = np.median(eng['ratio_star']) <= 5
  a('')
  if closes_eng:
    a('**Engineering alone gets within ~5× of Starlink per km² (median).**')
  elif closes:
    a('**No combination that keeps the 95 % year-round service gets within 5× of Starlink; only the '
      'hybrid case (50 % availability, satellite backstop, populated land, winter at 50 %) does, '
      'and it delivers a materially thinner service.** Honest reading: the balloons can be made '
      'roughly an order of magnitude cheaper, but what then competes with Starlink per km² is not '
      'the same product (nor is Starlink: it serves dishes, not phones).')
  else:
    a('**Nothing modelled here closes the gap to 2–5× Starlink per km².** The best stacked case '
      'is still '
      f'{np.median(best["ratio_star"]):.0f}× (P10 {np.percentile(best["ratio_star"], 10):.0f}×).')
  a('')
  e2, s2 = v['eng_dwell']['flat ×2'], v['stack_dwell']['flat ×2']
  e12, s12 = v['eng_dwell']['flat ×1.22'], v['stack_dwell']['flat ×1.22']
  if ctx['dwell_days_plan'] is not None:
    a(f'**The smarter controller does not move the cost.** The 36 h look-ahead planner '
      f'(`results/drift_2025_plan.csv`, same 120 launches) raises the per-flight harmonic-mean dwell '
      f'by ×{ctx["plan_flight_mult"]:.2f}, but launches/day are set by each month\'s *mean* dwell '
      f'(Little\'s law), and on that metric — the day-weighted harmonic of monthly means that '
      f'`cost_model.py` uses — the planner is ×{ctx["plan_cost_mult"]:.2f}: winter (Dec–Mar) dwell is '
      f'unchanged (2.2 d) and winter is where the launches go; the gain is in July–August, when '
      f'launches are already few. Its radio recovery also dipped to {ctx["rec_frac_plan"]:.0%} '
      f'(vs {ctx["rec_frac"]:.0%}). Lever 5 therefore contributes ~nothing in the stacks below. '
      f'For reference, if a flat ×1.22 held in every month the engineering stack would be '
      f'{rng_str(e12["total"])}/yr ({ratio_str(e12["ratio_star"])}) and the full stack '
      f'{rng_str(s12["total"])}/yr ({ratio_str(s12["ratio_star"])}); a flat ×2 would give '
      f'{rng_str(e2["total"])} and {rng_str(s2["total"])}. Only a controller that lengthens '
      f'*winter* flights changes the answer.\n')
  else:
    a(f'Dwell is the unmeasured input. A flat ×2 would take the engineering-only stack to '
      f'{rng_str(e2["total"])}/yr ({ratio_str(e2["ratio_star"])}) and the full stack to '
      f'{rng_str(s2["total"])}/yr ({ratio_str(s2["ratio_star"])}). See the dwell tables below.\n')
  a('The physics does not change: cost ≈ balloons aloft ÷ dwell × cost per flight. The levers that '
    'matter are the ones that touch the two big multipliers (cost per flight, and balloons needed '
    'per unit of useful coverage); recycling credits and hydrogen tweaks are noise.\n')
  a(f'![waterfall](cost_reduction.png)\n')

  a('## Levers one at a time\n')
  a('Each lever alone, all other inputs as in `cost_model.py`. "Delivered" flags what is given up.\n')
  a(hdr)
  a(row('Baseline (95 %, year-round, whole region)', base, 'same as baseline'))
  order = sorted(single, key=lambda k: np.median(single[k]['total']))
  for k in order:
    a(row(f'{k} {LEVERS[k]["name"]}', single[k], delivered(single[k])))
  a('')
  a('### Dwell multiplier sweep (lever 5 alone)\n')
  a('| Dwell × | Annual cost | vs baseline | Launches/day | × Starlink |')
  a('|---|---|---|---|---|')
  for x, r in v['dwell_sweep'].items():
    a(f'| {x} | {rng_str(r["total"])} | {-100 * (1 - np.median(r["total"]) / b50):+.0f} % | '
      f'{num_str(r["per_day"])} | {ratio_str(r["ratio_star"])} |')
  a('')
  a('Fixed costs are small, so cost falls almost exactly as 1/(monthly mean dwell). A flat '
    'doubling (3.7 → 7.4 d harmonic) would be worth about as much as every unit-cost lever '
    'combined — but the measured planner shows the gain where it is cheap to get (summer) and '
    'none where it would pay (winter). A controller that stretches *winter* flights is the '
    'result to chase.\n')

  a('## Stacked cases\n')
  a(hdr)
  for name, r in stacks.items():
    a(row(name, r, delivered(r)))
  a('')
  a('### Stacks under different dwell multipliers\n')
  a('| Dwell × | Engineering only (95 % year-round) | × Starlink | Everything incl. hybrid | × Starlink |')
  a('|---|---|---|---|---|')
  for x in v['sweep_keys']:
    e, s = v['eng_dwell'][x], v['stack_dwell'][x]
    a(f'| {x} | {rng_str(e["total"])} | {ratio_str(e["ratio_star"])} | '
      f'{rng_str(s["total"])} | {ratio_str(s["ratio_star"])} |')
  a('')
  a('### Waterfall steps (cumulative, in the order drawn)\n')
  a('| Step | Cumulative annual cost | Step saving (median) |')
  a('|---|---|---|')
  prev = None
  for name, r in cum:
    m = np.median(r['total'])
    step = ('' if prev is None else '≈ 0' if abs(prev - m) < 1e-3 * b50
            else f'−{fmt_eur(prev - m)}' if prev > m else f'+{fmt_eur(m - prev)}')
    a(f'| {name} | {rng_str(r["total"])} | {step} |')
    prev = m
  a('')

  a('## Which levers matter\n')
  ranked = sorted(single.items(), key=lambda kv: np.median(kv[1]['total']))
  a('Ranked by median saving when applied alone:\n')
  for k, r in ranked:
    sav = 100 * (1 - np.median(r['total']) / b50)
    a(f'* **{k} {LEVERS[k]["name"]}** — {sav:.0f} % ({rng_str(r["total"])}/yr). {NOTES[k]}')
  a('')
  l2_credit = np.median(base['items']['Envelopes'] / base['per_yr']) - \
      np.median(single['L2']['items']['Envelopes'] / single['L2']['per_yr'])
  a('Two things are notable by their absence. Envelope reuse plus the recycling credit (L2) is worth '
    f'~€{l2_credit:,.0f} per flight against ~€12k of envelope — 68.5 kg of scrap film is worth tens of euros, and reusing a '
    'superpressure envelope after a parachute landing is speculative. And the fuel cell (L4) '
    'saves a few percent of envelope at best, because the lift gas it burns gives back about '
    'a third of the mass saved and the stack costs about what the battery did.\n')

  a('## Assumptions (all flagged)\n')
  a(f'* Region land fraction {ctx["land_frac"]:.0%} (global_land_mask over 36–62°N, 10°W–42°E); '
    f'envelopes landing on land {ctx["env_land_frac"]:.0%} (scenario A of `analyze_envelopes.py`, '
    f'{len(v["slow"])} slow flights).')
  a(f'* Populated share of land {tri_str(POPULATED_LAND_SHARE)} — **ASSUMPTION**, no population raster in '
    'the repo; a GHSL/GPW cut at ~10 people/km² would pin this down.')
  a(f'* Targeting efficiency {tri_str(TARGETING_EFF)} — **ASSUMPTION**: how much of the fleet can be kept '
    'off sea and empty land by launch-site choice and steering. Drifting balloons cannot be '
    'confined to populated cells; the smarter controller\'s tracks should replace this.')
  for k in LEVERS:
    a(f'* **{k}** {ASSUMPTIONS[k]}')
  a('')

  a('## Notes on `cost_model.py`\n')
  g = v['geo']
  a(f'* **Payload amortisation formula.** `consumed = (1 − rec) + rec / max_flights` retires a '
    'fraction `rec/N` of payloads every flight, but only payloads that survive all N flights are '
    'retired; the expected flights per payload is geometric, `(1 − rec^N)/(1 − rec)`. With the '
    'base inputs the current formula overstates payload consumption by ~17 % and the total by '
    f'~{100 * (1 - np.median(g["total"]) / b50):.0f} % ({rng_str(g["total"])}/yr with the geometric '
    'form). Conservative, not verdict-changing; this file keeps the original formula so the '
    'baseline matches.')
  a('* **Envelope recovery cost is charged on every flight** (`per_yr * env_recovery`) although '
    'the report says sea landings (34 %) are largely unrecoverable; small (3 % line item).')
  a('* **Payload pickup cost** uses `rec_frac × intact` but a field team is dispatched for every '
    'glider that reaches a site, intact or not (`rec_frac`); negligible.')
  a('* **Lift gas**: `LIFT_GAS_MOL` is BLE\'s helium fill. The same mol count of H₂ gives ~7 % '
    'more net lift (molar mass 2 vs 4), so slightly less gas would do; hydrogen is 0.3 % of cost '
    'so it does not matter.')
  a('* `per_yr = per_day × 365` while `SEC_PER_YR` uses 365.25; cosmetic.')
  a('* The structure is sound for this purpose: `main()` is guarded, every input is a named '
    'triangular spec, and `balloon_model` is vectorised, so this file imports it unchanged.')
  a('')
  a('## Lever 5 settings\n')
  a('By default lever 5 uses the planner\'s measured per-month dwell from '
    '`results/drift_2025_plan.csv` (and its radio-recovery rate). Run `--dwell-mult X` or set '
    '`DWELL_MULT` to apply a flat multiplier to every month\'s dwell instead (a flat multiplier '
    'is generous, because it lengthens winter flights, which the planner did not manage). '
    'If the planner CSV is absent the script falls back to a ×1.0 placeholder and says so.')
  with open(OUT_MD, 'w') as f:
    f.write('\n'.join(L) + '\n')


NOTES = {
  'L1': 'Biggest unit-cost lever: envelopes are a third of spend and single-use.',
  'L2': 'Negligible: scrap value is tens of euros; reuse is speculative.',
  'L3': 'Second unit-cost lever: cuts the amortised payload line roughly in half.',
  'L4': 'Marginal: lift-gas burn and fuel-cell cost eat most of the saving.',
  'L5': 'Cost scales with 1/(monthly mean dwell); the measured planner leaves winter dwell '
        'unchanged, so it buys nothing here despite a ×1.22 per-flight harmonic mean.',
  'L6a': 'Large absolute saving, but it is 25 % of a service; per km²-year served it is the '
         'cheapest form of the fleet because summer dwell is 9 days.',
  'L6b': 'Winter is where the launches go; halving the winter target saves more than it looks.',
  'L6c': 'Depends on being able to keep balloons over people, which random drift does not allow.',
  'L7': 'Fewer balloons per km² (∝ 1/r²), at the cost of capacity per km² and a dearer payload.',
  'L8': 'Random placement at a 50 % target needs 4× fewer balloons than at 95 %; the gaps go to '
        'a satellite layer that already exists.',
}

ASSUMPTIONS = {
  'L1': 'Envelope €2.5–7k (mode €4k) vs €4–25k (mode €10k): Wright-law learning 80–90 %/doubling '
        'over ~8 doublings from Loon-scale volume to 400k/yr (Nagy et al. 2013 for the learning-rate '
        'band; its applicability to balloon film is an ASSUMPTION), floored by film material '
        '€0.7–2k (68.5 kg at €10–30/kg, ASSUMPTION).',
  'L2': 'Collected 50–90 % of land landings; 0–40 % (mode 15 %) refurbishable at 20–50 % of new '
        'cost; PE scrap €0.1–0.4/kg. All ASSUMPTION; Loon never reflew an envelope.',
  'L3': 'Recovery 0.939 from results/glider_sizing.csv (L/D 12, 2 m/s sink, 28.8 kg/m²); intact '
        '0.85–0.98 (mode 0.93, faster landing); life 10–40 flights (mode 20); refurb 5–15 % '
        '(mode 8 %). Intact/life/refurb are ASSUMPTION.',
  'L4': 'Net lifted-mass saving 4–10 kg (15 kg battery → ~5 kg stack, minus ~1 kg/day of lift '
        'lost to H₂ burnt at ~100 W night load, 50 % efficiency); envelope mass ∝ (lifted mass)^(2/3) '
        'and cost ∝ mass; payload −€2k to +€3k net. All ASSUMPTION.',
  'L5': 'Default: measured per-month dwell of the 36 h look-ahead planner (planner.py, '
        'results/drift_2025_plan.csv, same 120 launches/seeds as "slow"), with its 74 % radio '
        'recovery; bootstrapped like the baseline. `--dwell-mult X` substitutes a flat multiplier '
        'on the slow controller\'s months (the sweep uses 1.22, 1.5, 2.0).',
  'L6a': 'Service Jun–Aug only at the 95 % target; fixed costs (sites, NOC, regulatory) still '
         'paid for the whole year.',
  'L6b': 'Target 50 % Dec–Mar, 95 % otherwise (random-placement coverage formula as in '
         'cost_model.py).',
  'L6c': 'Served area = populated land (land fraction × populated share) with the targeting '
         'efficiency above; gateways scale with served area.',
  'L7': 'Footprint radius 60–80 km (mode 70) vs 40–50 km; payload cost ×1.1–1.6 for a multi-beam '
        'antenna; capacity per balloon unchanged. Minimum elevation 14–18° at the edge, marginal '
        'for handset uplink (ASSUMPTION that the link closes).',
  'L8': 'Coverage target 50 % every month; the backstop layer (direct-to-cell satellite or '
        'terrestrial) is assumed to exist and is not costed.',
}


if __name__ == '__main__':
  main()

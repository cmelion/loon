"""Cost model: slow-traversal balloon fleet vs satellite/HAPS connectivity.

Region: 36-62 N, 10 W-42 E (Europe -> Black Sea), the box used by analyze.py
(~10.9 M km^2 = 1,674 hexagonal cells of 50 km radius).

Balloon side is driven by our own simulation outputs (results/drift_2025.csv,
'slow' controller: real 2025 GFS winds, 5 launch sites x 24 dates):
  * monthly dwell time over the region per balloon -> launches needed,
  * fraction of radio payloads recovered by glider -> payload reuse.
Everything else is a named constant below with a source or ASSUMPTION tag.
Uncertain inputs are triangular (low, mode, high) and propagated by Monte
Carlo (plus a bootstrap over the simulated flights); results are reported
as P10 / P50 / P90, never as single numbers.

Satellite side normalises each system's annual cost (annualised capex +
opex) to the share attributable to this region, then to EUR per km^2 per
year and (where capacity is public) EUR per GB of deliverable capacity.

Run:  .venv/bin/python -I cost_model.py
Writes results/cost_comparison.md and results/cost_comparison.png.
"""
import math
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_MD = os.path.join(HERE, 'results', 'cost_comparison.md')
OUT_PNG = os.path.join(HERE, 'results', 'cost_comparison.png')
DRIFT_CSV = os.path.join(HERE, 'results', 'drift_2025.csv')

N_DRAWS = 20000
SEED = 2025
rng = np.random.default_rng(SEED)


def tri(lo, mode, hi):
  """Triangular uncertain input (low, most likely, high)."""
  return (lo, mode, hi)


# ----------------------------------------------------------------------------
# Geometry (analyze.py)
# ----------------------------------------------------------------------------
LAT0, LAT1, LON0, LON1 = 36.0, 62.0, -10.0, 42.0       # analyze.py region box
EARTH_R_KM = 6371.0
REGION_KM2 = (EARTH_R_KM ** 2 * math.radians(LON1 - LON0) *
              (math.sin(math.radians(LAT1)) - math.sin(math.radians(LAT0))))
SIM_CELL_R_KM = 50.0                                    # analyze.py cell radius
EARTH_KM2 = 4 * math.pi * EARTH_R_KM ** 2               # 510 M km^2

# ----------------------------------------------------------------------------
# Balloon physical parameters (BLE balloon.py defaults, used by europe_ble.py)
# ----------------------------------------------------------------------------
ENVELOPE_KG = 68.5          # BLE balloon.py envelope_mass
PAYLOAD_KG = 92.5           # BLE balloon.py payload_mass
LIFT_GAS_MOL = 6830.0       # BLE balloon.py mols_lift_gas (helium in BLE)
H2_KG_PER_MOL = 2.016e-3    # molar mass of H2
H2_KG_PER_FLIGHT = LIFT_GAS_MOL * H2_KG_PER_MOL         # ~13.8 kg
ELECTROLYSIS_KWH_PER_KG = tri(50.0, 52.5, 55.0)         # task brief; PEM/alkaline system
                                                        # efficiency (HHV 39.4 kWh/kg)

# ----------------------------------------------------------------------------
# Coverage model
# ----------------------------------------------------------------------------
# Radio footprint radius. Our sim cells assume 50 km; Loon publicly quoted
# ~5,000 km^2 per balloon (r ~ 40 km) [satcom.guru 2017, Loon/Google].
FOOTPRINT_R_KM = tri(40.0, 45.0, 50.0)
# Tiling efficiency: 0 = balloons perfectly tile the cells (one per cell),
# 1 = positions as good as random (Poisson coverage). The station-keeping
# runs (run_coverage.py: ~4 % time-within-50 km) show balloons cannot hold
# position, and all flights from one site ride the same wind stream, so we
# lean toward random. ASSUMPTION.
TILING_RANDOMNESS = tri(0.2, 0.6, 1.0)
COVERAGE_TARGETS = {'50 %': 0.50, '80 %': 0.80, '95 % (near-full)': 0.95}
BASE_COVERAGE = '95 % (near-full)'   # "keep every cell covered"; 100 % is
                                     # unreachable with drifting balloons

# ----------------------------------------------------------------------------
# Balloon unit costs (EUR, 2025-26)
# ----------------------------------------------------------------------------
# Envelope: 68.5 kg superpressure PE envelope, mass-produced. No public price;
# AFP reported a complete Loon balloon (envelope + payload) at "tens of
# thousands of dollars" [AFP via tbsnews/techcentral, Jan 2021]. ASSUMPTION.
ENVELOPE_EUR = tri(4_000, 10_000, 25_000)
# Radio payload incl. LTE eNodeB, solar, battery, avionics, cut-down and the
# recovery glider airframe. ASSUMPTION (same AFP order of magnitude).
PAYLOAD_EUR = tri(15_000, 35_000, 80_000)
# Glider recovery fraction comes from the sim (read below). Of those that
# glide home, fraction found intact and reusable. ASSUMPTION.
RECOVERED_INTACT = tri(0.85, 0.95, 1.00)
PAYLOAD_MAX_FLIGHTS = tri(5, 15, 30)            # service life, ASSUMPTION
PAYLOAD_REFURB_FRAC = tri(0.05, 0.10, 0.20)     # refurb cost per reuse / unit cost, ASSUMPTION
RECOVERY_EUR_PER_PAYLOAD = tri(200, 500, 1_500)  # field team pickup + transport, ASSUMPTION

# Green hydrogen. ACER 2025 market monitoring: average renewable H2
# production cost ~8 EUR/kg in 2024, country range 7-10 EUR/kg; HYDRIX index
# ~8.2 EUR/kg in 2025; best Observatory LCOH cases ~5.8-6 EUR/kg (DK wind,
# ES PV) [acer.europa.eu/monitoring/European-hydrogen-markets-2025;
# pv-magazine 2025-12-03].
H2_EUR_PER_KG = tri(5.8, 8.0, 10.0)
H2_FILL_LOSS = tri(0.05, 0.15, 0.30)   # purge, overfill, transfer losses, ASSUMPTION

# Launch operations. Reference: one radiosonde launch ~USD 325 all-in incl.
# labour [Ingleby/AMT 2019]; a Vaisala Autosonde station ~USD 0.8 M
# [Hawaii Tribune-Herald 2021]. A 13.8 kg-H2 superpressure balloon with a
# 92.5 kg payload needs a crane/autolauncher and crew, hence higher.
LAUNCH_EUR_PER_FLIGHT = tri(300, 700, 1_500)     # ASSUMPTION
LAUNCHES_PER_SITE_DAY = tri(24, 48, 96)          # 1-2 autolaunchers @ 30 min, ASSUMPTION
SITE_FIXED_EUR_YR = tri(1.5e6, 3.0e6, 6.0e6)     # amortised capex + staff + H2 storage, ASSUMPTION
MIN_SITES = 5                                    # the sim's 5 launch sites

# Envelope after cut-down: 68.5 kg of PE lands somewhere in the region (or
# the sea). Search, pickup and disposal per envelope. ASSUMPTION.
ENVELOPE_RECOVERY_EUR = tri(100, 400, 1_500)

# Ground network / backhaul. Loon backhauled through ground stations and
# balloon-to-balloon links (~100 km). ASSUMPTION.
GATEWAY_AREA_KM2 = tri(20_000, 40_000, 80_000)   # region area per gateway
GATEWAY_EUR_YR = tri(60_000, 120_000, 250_000)   # capex/10 yr + fibre + site rent
CORE_NOC_EUR_YR = tri(10e6, 25e6, 50e6)          # core network, fleet ops centre, ASSUMPTION
# Spectrum: assumed provided by partner MNOs (Loon model) -> excluded.

# Regulatory / insurance
INSURANCE_EUR_PER_FLIGHT = tri(50, 200, 600)     # third-party liability, ASSUMPTION
REGULATORY_EUR_YR = tri(5e6, 15e6, 40e6)         # ~30 states' ANSPs, licences, ASSUMPTION
OVERHEAD_FRAC = tri(0.10, 0.15, 0.25)            # G&A on all of the above, ASSUMPTION

# Capacity (for EUR/GB). Loon field tests: ~19 Mbps DL in Kenya, SRG
# measured high-teens sustained / ~40 Mbps PHY peak; Google claimed
# 22 Mbps per balloon [datacenterdynamics; signalsresearch; mobileworldlive].
BALLOON_MBPS = tri(10.0, 20.0, 40.0)
UTILISATION = tri(0.10, 0.25, 0.40)    # average load factor, applied to all systems, ASSUMPTION

USD_TO_EUR = 0.87                      # EURUSD ~1.15 (2025-26), ASSUMPTION

# ----------------------------------------------------------------------------
# Comparator systems. annual_cost in native currency per year (annualised
# capex + opex); served_frac = fraction of Earth's surface the system serves;
# lat_factor = capacity density over 36-62 N relative to the served-area
# average (inclined/polar shells bunch up at high latitude).
# ----------------------------------------------------------------------------
SYSTEMS = {
  'Starlink (LEO broadband)': dict(
    # 2025 Connectivity segment costs & expenses USD 6.96 B on 11.39 B
    # revenue (SpaceX S-1, via spacedaily 2026); upper end adds capex above
    # D&A (~9,600 sats, est. USD 0.8 M/sat + 0.65-0.87 M launch, 5 yr life).
    annual_cost=tri(7.0e9, 9.0e9, 12.0e9), cur='USD',
    served_frac=tri(0.80, 0.87, 1.00), lat_factor=tri(1.0, 1.5, 2.0),
    # ~600 Tbps total network capacity end-2025 (secondary: dishytech /
    # driveteslacanada); uncertain.
    capacity_gbps=tri(400e3, 600e3, 800e3),
    group='LEO broadband',
    # Launch ~0.65-0.87 M of ~1.5 M per V2-mini sat (analyst est.) and capex
    # ~half of annual cost -> launch share of annual cost. ASSUMPTION.
    launch_frac=tri(0.15, 0.25, 0.35),
    launcher='Falcon 9 / Starship (own vehicles)', spacex_dep='Total (vertically integrated)',
    delivers='100-300 Mbps/user, 25-60 ms; needs a dish terminal (USD 300-600); '
             'in service across Europe'),
  'Eutelsat OneWeb Gen1': dict(
    # Gen1 build ~USD 6 B (ASSUMPTION; ~USD 1.9 B financing = 80 % of 2021
    # need, plus pre-2020 spend) over 2022-2034; plus USD 5.07 B Eutelsat
    # LEO capex to 2034 [spaceintelreport]; FY25 revenue EUR 187 M.
    annual_cost=tri(0.6e9, 1.0e9, 1.4e9), cur='USD',
    served_frac=tri(0.95, 1.00, 1.00), lat_factor=tri(1.0, 1.3, 1.6),
    capacity_gbps=tri(1e3, 2e3, 4e3),   # not disclosed; ASSUMPTION, very uncertain
    group='LEO broadband',
    launch_frac=tri(0.20, 0.30, 0.40),   # ASSUMPTION
    # Soyuz launches halted in 2022 -> Falcon 9 (+ ISRO) to finish Gen1
    # [spaceflightnow 2022-03-21]; Gen1 replacement batch must find launches.
    launcher='Soyuz (until 2022), then Falcon 9 + ISRO LVM3',
    spacex_dep='High for replenishment (Falcon 9 completed Gen1)',
    delivers='~50-200 Mbps/terminal, 50-70 ms; enterprise/backhaul terminals only'),
  'IRIS² (EU, from ~2030)': dict(
    # EUR 10.6 B total (EUR 6.5 B public) for ~290 sats (since enlarged to
    # 348, Aug 2026; revised budget not found), 12-yr concession
    # [datacenterdynamics; SpaceRISE press release, Dec 2024]; opex ASSUMPTION.
    annual_cost=tri(0.95e9, 1.2e9, 1.6e9), cur='EUR',
    served_frac=None, region_share=tri(0.03, 0.10, 0.25),  # Europe-prioritised, ASSUMPTION
    capacity_gbps=None,
    group='LEO broadband',
    launch_frac=tri(0.15, 0.25, 0.35),   # ASSUMPTION
    # Plan: "launched by European rockets", Ariane 6 prioritised; enlarged to
    # 348 sats, first launches 2029 [thenextweb Aug 2026; satnews 2025-12-29].
    launcher='European launchers by policy (Ariane 6, Vega-C, future)',
    spacex_dep='None by policy; capped by Ariane 6 cadence',
    delivers='secure governmental + commercial broadband; not in service before 2030; '
             'terminals required'),
  'AST SpaceMobile (direct-to-cell)': dict(
    # ~90 Block-2 BlueBirds at USD 21-23 M all-in incl. launch [AST guidance
    # via spaceintelreport/alpha-sense 2025] = ~USD 2 B over 7-10 yr, plus
    # opex ~USD 0.2-0.4 B/yr (ASSUMPTION).
    annual_cost=tri(0.35e9, 0.55e9, 0.9e9), cur='USD',
    served_frac=tri(0.75, 0.82, 0.90), lat_factor=tri(1.0, 1.3, 1.6),
    capacity_gbps=None,
    group='Direct-to-cell',
    # AST all-in USD 21-23 M/sat incl. launch, raised after launch-price
    # increases [spaceintelreport]. ASSUMPTION share.
    launch_frac=tri(0.15, 0.25, 0.35),
    launcher='Falcon 9, ISRO LVM3, Blue Origin New Glenn',
    spacex_dep='Medium (several providers, Falcon 9 the most available)',
    delivers='unmodified phones, broadband-class peaks claimed; Europe via Vodafone '
             'JV, not yet commercial here'),
  'Starlink Direct to Cell': dict(
    # ~650 DTC sats [engadget]; incremental cost ASSUMPTION USD 1-2 M/sat
    # incl. launch share, ~5 yr life, + ops. Excludes the USD 17 B EchoStar
    # spectrum (US licences, not usable in Europe).
    annual_cost=tri(0.15e9, 0.3e9, 0.6e9), cur='USD',
    served_frac=tri(0.80, 0.87, 1.00), lat_factor=tri(1.0, 1.5, 2.0),
    capacity_gbps=None,   # ~4-18 Mbps per beam [FCC filings]; total not public
    group='Direct-to-cell',
    launch_frac=tri(0.30, 0.40, 0.50),   # incremental sats are mostly launch, ASSUMPTION
    launcher='Falcon 9 / Starship (own vehicles)', spacex_dep='Total (vertically integrated)',
    delivers='unmodified phones; text + low-rate data today (~4-18 Mbps per beam '
             'shared); needs an MNO spectrum partner per country'),
}
# Solar HAPS (AALTO Zephyr-class). 7,500 km^2 per aircraft (AALTO claim,
# aaltohaps.com/connect); 64-day record endurance [BEREC/AALTO 2024].
HAPS_KM2 = 7_500.0
HAPS_OVERLAP = tri(1.1, 1.2, 1.4)            # station overlap, ASSUMPTION
HAPS_FLEET_PER_STATION = tri(2.0, 3.0, 4.0)  # rotation/maintenance spares, ASSUMPTION
HAPS_AIRCRAFT_EUR = tri(1e6, 3e6, 8e6)       # no public price; ASSUMPTION
HAPS_LIFE_YR = tri(2.0, 4.0, 6.0)            # ASSUMPTION
HAPS_OPS_EUR_YR = tri(0.3e6, 0.6e6, 1.2e6)   # per aircraft, ASSUMPTION
HAPS_MBPS = tri(50.0, 100.0, 300.0)          # per aircraft, ASSUMPTION

# Launch-market concentration. SpaceX flew 165 of 325 orbital launches in
# 2025 (~51 %) [BryceTech via Satellite Today 2026-04-10] and >80 % of mass
# to orbit (S-1 via Motley Fool; single source). Ariane 6 flew ~4 times in
# 2025, targets 6-8 in 2026 and ~9-10/yr max [europeanspaceflight;
# behindtheblack]; ESA is studying 15+/yr before 2030 [spaceintelreport].
# Sensitivity: launch cost multiplier if the constellation must buy launch
# outside SpaceX (Ariane 6 ~EUR 70 M target for far less LEO mass than a
# reusable Falcon 9 ~USD 67-70 M) or if one supplier prices up. ASSUMPTION.
SPACEX_LAUNCH_SHARE_2025 = 165 / 325
ARIANE6_LAUNCHES_2025 = 4
ARIANE6_MAX_PER_YR = tri(9, 10, 15)
LAUNCH_PRICE_SHOCK = tri(1.5, 2.0, 3.0)

DAYS_IN_MONTH = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
SEASONS = {
  'Annual (Jan-Dec)': list(range(1, 13)),
  'Winter (Dec-Mar)': [12, 1, 2, 3],
  'Summer (Jun-Aug)': [6, 7, 8],
}
SEC_PER_YR = 365.25 * 86400


# ----------------------------------------------------------------------------
def sample(spec, n):
  lo, mode, hi = spec
  if lo == hi:
    return np.full(n, float(lo))
  return rng.triangular(lo, mode, hi, n)


def mode(spec):
  return float(spec[1])


def load_sim():
  df = pd.read_csv(DRIFT_CSV)
  slow = df[df.controller == 'slow']
  dwell_days = {m: g.dwell_h.to_numpy() / 24.0 for m, g in slow.groupby('month')}
  return slow, dwell_days, float(slow.recovered.mean())


def inv_dwell_draws(dwell_days, months, n):
  """Bootstrap the day-weighted mean of 1/dwell over `months` and the peak
  monthly 1/dwell. Launches/day = balloons aloft / dwell (Little's law), so
  the cost scales with the *harmonic* mean dwell: short winter flights
  dominate."""
  w = DAYS_IN_MONTH[np.array(months) - 1].astype(float)
  per_month = []
  for m in months:
    x = dwell_days[m]
    idx = rng.integers(0, len(x), (n, len(x)))
    per_month.append(1.0 / x[idx].mean(axis=1))
  per_month = np.array(per_month)                       # (months, n)
  return (w[:, None] * per_month).sum(0) / w.sum(), per_month.max(0)


def point_inv_dwell(dwell_days, months):
  w = DAYS_IN_MONTH[np.array(months) - 1].astype(float)
  inv = np.array([1.0 / dwell_days[m].mean() for m in months])
  return float((w * inv).sum() / w.sum()), float(inv.max())


BALLOON_INPUTS = dict(
  footprint_r=FOOTPRINT_R_KM, tiling=TILING_RANDOMNESS,
  envelope=ENVELOPE_EUR, payload=PAYLOAD_EUR, intact=RECOVERED_INTACT,
  max_flights=PAYLOAD_MAX_FLIGHTS, refurb=PAYLOAD_REFURB_FRAC,
  recovery=RECOVERY_EUR_PER_PAYLOAD, h2_price=H2_EUR_PER_KG,
  h2_loss=H2_FILL_LOSS, kwh_per_kg=ELECTROLYSIS_KWH_PER_KG,
  launch=LAUNCH_EUR_PER_FLIGHT, site_rate=LAUNCHES_PER_SITE_DAY,
  site_fixed=SITE_FIXED_EUR_YR, env_recovery=ENVELOPE_RECOVERY_EUR,
  gw_area=GATEWAY_AREA_KM2, gw_cost=GATEWAY_EUR_YR, core=CORE_NOC_EUR_YR,
  insurance=INSURANCE_EUR_PER_FLIGHT, regulatory=REGULATORY_EUR_YR,
  overhead=OVERHEAD_FRAC, mbps=BALLOON_MBPS, util=UTILISATION)

INPUT_LABELS = dict(
  footprint_r='Radio footprint radius', tiling='Tiling (perfect vs random)',
  envelope='Envelope unit cost', payload='Payload unit cost',
  intact='Recovered payload intact', max_flights='Payload service life',
  refurb='Payload refurbishment', recovery='Payload pickup cost',
  h2_price='Green H2 price', h2_loss='H2 fill losses',
  kwh_per_kg='Electrolysis kWh/kg', launch='Launch cost per flight',
  site_rate='Launches per site-day', site_fixed='Launch-site fixed cost',
  env_recovery='Envelope recovery/disposal', gw_area='Area per gateway',
  gw_cost='Gateway cost', core='Core network / NOC',
  insurance='Insurance per flight', regulatory='Regulatory fixed',
  overhead='G&A overhead', mbps='Throughput per balloon',
  util='Utilisation', dwell='Dwell time (bootstrap of sim flights)')

LINE_ITEMS = ['Envelopes', 'Payload (amortised)', 'Green hydrogen',
              'Launch sites & ops', 'Recovery (payload + envelope)',
              'Ground network & backhaul', 'Regulatory & insurance', 'G&A overhead']


def balloon_model(p, inv_dwell, peak_inv_dwell, coverage, rec_frac):
  """Vectorised annual cost (EUR/yr) by line item, plus fleet metrics.
  p: dict of scalars or arrays; inv_dwell: mean 1/days over the season."""
  r = p['footprint_r']
  hex_area = 1.5 * math.sqrt(3) * r ** 2
  n_ideal = coverage * REGION_KM2 / hex_area
  n_random = -np.log(1 - coverage) * REGION_KM2 / (np.pi * r ** 2)
  aloft = (1 - p['tiling']) * n_ideal + p['tiling'] * n_random
  per_day = aloft * inv_dwell
  per_yr = per_day * 365.0
  peak_day = aloft * peak_inv_dwell
  sites = np.maximum(MIN_SITES, np.ceil(peak_day / p['site_rate']))

  rec = rec_frac * p['intact']
  consumed = (1 - rec) + rec / p['max_flights']
  h2_kg = H2_KG_PER_FLIGHT * (1 + p['h2_loss'])
  items = {
    'Envelopes': per_yr * p['envelope'],
    'Payload (amortised)': per_yr * p['payload'] * (consumed + rec * p['refurb']),
    'Green hydrogen': per_yr * h2_kg * p['h2_price'],
    'Launch sites & ops': per_yr * p['launch'] + sites * p['site_fixed'],
    'Recovery (payload + envelope)': per_yr * (rec * p['recovery'] + p['env_recovery']),
    'Ground network & backhaul': REGION_KM2 / p['gw_area'] * p['gw_cost'] + p['core'],
    'Regulatory & insurance': per_yr * p['insurance'] + p['regulatory'],
  }
  items['G&A overhead'] = p['overhead'] * sum(items.values())
  total = sum(items.values())
  gbps = aloft * p['mbps'] / 1e3
  gb_yr = gbps * p['util'] * SEC_PER_YR / 8
  return dict(items=items, total=total, aloft=aloft, per_day=per_day,
              per_yr=per_yr, sites=sites, gbps=gbps, gb_yr=gb_yr,
              h2_t=per_yr * h2_kg / 1e3,
              h2_gwh=per_yr * h2_kg * p['kwh_per_kg'] / 1e6,
              pe_t=per_yr * ENVELOPE_KG / 1e3)


def run_balloon(dwell_days, rec_frac, months, coverage, n=N_DRAWS):
  p = {k: sample(v, n) for k, v in BALLOON_INPUTS.items()}
  inv, peak = inv_dwell_draws(dwell_days, months, n)
  return balloon_model(p, inv, peak, coverage, rec_frac), p


def run_systems(n=N_DRAWS):
  out = {}
  for name, s in SYSTEMS.items():
    fx = USD_TO_EUR if s['cur'] == 'USD' else 1.0
    cost = sample(s['annual_cost'], n) * fx
    if s.get('served_frac') is not None:
      share = (REGION_KM2 / (EARTH_KM2 * sample(s['served_frac'], n)) *
               sample(s['lat_factor'], n))
    else:
      share = sample(s['region_share'], n)
    reg_cost = cost * share
    shock = 1 + sample(s['launch_frac'], n) * (sample(LAUNCH_PRICE_SHOCK, n) - 1)
    o = dict(total=reg_cost, share=share, per_km2=reg_cost / REGION_KM2,
             per_km2_shock=reg_cost * shock / REGION_KM2,
             group=s['group'], delivers=s['delivers'], launcher=s['launcher'],
             spacex_dep=s['spacex_dep'])
    if s['capacity_gbps'] is not None:
      gbps = sample(s['capacity_gbps'], n) * share
      o['gbps'] = gbps
      o['eur_per_gb'] = reg_cost / (gbps * sample(UTILISATION, n) * SEC_PER_YR / 8)
    out[name] = o
  # Solar HAPS
  stations = REGION_KM2 / HAPS_KM2 * sample(HAPS_OVERLAP, n)
  fleet = stations * sample(HAPS_FLEET_PER_STATION, n)
  cost = fleet * (sample(HAPS_AIRCRAFT_EUR, n) / sample(HAPS_LIFE_YR, n) +
                  sample(HAPS_OPS_EUR_YR, n))
  gbps = stations * sample(HAPS_MBPS, n) / 1e3
  out['Solar HAPS (Zephyr-class)'] = dict(
    total=cost, per_km2=cost / REGION_KM2, per_km2_shock=cost / REGION_KM2,
    launcher='none (runway take-off)', spacex_dep='None',
    group='HAPS', gbps=gbps,
    eur_per_gb=cost / (gbps * sample(UTILISATION, n) * SEC_PER_YR / 8),
    delivers='unmodified phones (4G/5G D2D payload), ~7,500 km² each; solar '
             'aircraft cannot hold station at 36-62 N in winter today; pre-commercial',
    fleet=fleet)
  return out


def pct(x, q=(10, 50, 90)):
  return np.percentile(x, q)


def fmt_eur(x):
  a = abs(x)
  if a >= 1e9:
    return f'€{x / 1e9:.1f} B'
  if a >= 1e6:
    return f'€{x / 1e6:.0f} M'
  if a >= 10:
    return f'€{x:,.0f}'
  if a >= 0.1:
    return f'€{x:.2f}'
  return f'€{x:.3f}'


def rng_str(x, f=fmt_eur):
  lo, mid, hi = pct(x)
  return f'{f(mid)} ({f(lo)} – {f(hi)})'


def num_str(x, d=0):
  lo, mid, hi = pct(x)
  return f'{mid:,.{d}f} ({lo:,.{d}f} – {hi:,.{d}f})'


def tornado(dwell_days, rec_frac, months, coverage):
  """Swing in total annual cost when each input goes low->high with all
  others at their mode."""
  base_p = {k: mode(v) for k, v in BALLOON_INPUTS.items()}
  inv, peak = point_inv_dwell(dwell_days, months)
  base = float(balloon_model(base_p, inv, peak, coverage, rec_frac)['total'])
  rows = []
  for k, v in BALLOON_INPUTS.items():
    if k in ('mbps', 'util'):
      continue
    vals = []
    for x in (v[0], v[2]):
      p = dict(base_p); p[k] = float(x)
      vals.append(float(balloon_model(p, inv, peak, coverage, rec_frac)['total']))
    rows.append((INPUT_LABELS[k], min(vals), max(vals)))
  inv_b, peak_b = inv_dwell_draws(dwell_days, months, 4000)
  vals = [float(balloon_model(base_p, np.percentile(inv_b, q),
                              np.percentile(peak_b, q), coverage, rec_frac)['total'])
          for q in (10, 90)]
  rows.append((INPUT_LABELS['dwell'], min(vals), max(vals)))
  rows.sort(key=lambda r: r[2] - r[1])
  return base, rows


def best_case(dwell_days, rec_frac, months, coverage):
  """Every input at whichever end of its range is cheaper, and the P90
  (longest) bootstrap dwell: a floor on the balloon fleet's cost."""
  p = {k: mode(v) for k, v in BALLOON_INPUTS.items()}
  inv, peak = point_inv_dwell(dwell_days, months)
  for k, v in BALLOON_INPUTS.items():
    if k in ('mbps', 'util'):
      continue
    costs = []
    for x in (v[0], v[2]):
      q = dict(p); q[k] = float(x)
      costs.append((float(balloon_model(q, inv, peak, coverage, rec_frac)['total']), x))
    p[k] = float(min(costs)[1])
  inv_b, peak_b = inv_dwell_draws(dwell_days, months, 4000)
  return float(balloon_model(p, np.percentile(inv_b, 10), np.percentile(peak_b, 10),
                             coverage, rec_frac)['total'])


# ----------------------------------------------------------------------------
def main():
  slow, dwell_days, rec_frac = load_sim()
  mean_days = slow.dwell_h.mean() / 24
  monthly = {m: dwell_days[m].mean() for m in range(1, 13)}
  harm = {s: 1 / point_inv_dwell(dwell_days, ms)[0] for s, ms in SEASONS.items()}

  # Scenario grid: season x coverage.
  scen = {}
  for s, months in SEASONS.items():
    for c, f in COVERAGE_TARGETS.items():
      scen[(s, c)] = run_balloon(dwell_days, rec_frac, months, f)[0]
  base = scen[('Annual (Jan-Dec)', BASE_COVERAGE)]
  # The brief's sizing: one balloon per 50 km cell, arithmetic-mean dwell.
  brief_launches_day = 1674 / mean_days
  sysr = run_systems()
  t_base, t_rows = tornado(dwell_days, rec_frac, SEASONS['Annual (Jan-Dec)'],
                           COVERAGE_TARGETS[BASE_COVERAGE])

  b_km2 = base['total'] / REGION_KM2
  floor = {c: best_case(dwell_days, rec_frac, SEASONS['Annual (Jan-Dec)'], f)
           for c, f in COVERAGE_TARGETS.items()}
  star = sysr['Starlink (LEO broadband)']
  ratio_star = b_km2 / star['per_km2']
  best = scen[('Summer (Jun-Aug)', '50 %')]
  ratio_best = best['total'] / REGION_KM2 / star['per_km2']
  share_mean = {k: base['items'][k].mean() / base['total'].mean() for k in LINE_ITEMS}
  per_flight = base['total'] / base['per_yr']

  make_chart(scen, sysr, t_base, t_rows, base)
  write_md(locals())
  print(f'Wrote {OUT_MD}\nWrote {OUT_PNG}')
  print(f'Balloon fleet (annual, {BASE_COVERAGE}): {rng_str(base["total"])}/yr, '
        f'{rng_str(b_km2)}/km²/yr')
  for k, v in sysr.items():
    print(f'  {k:34s} {rng_str(v["per_km2"])}/km²/yr')


# ----------------------------------------------------------------------------
PAL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300',
       '#6250d6', '#e34948']
INK, INK2, GRID = '#0b0b0b', '#52514e', '#e4e3df'
GROUP_COL = {'Balloon': PAL[1], 'LEO broadband': PAL[0], 'Direct-to-cell': PAL[6],
             'HAPS': PAL[2]}


def make_chart(scen, sysr, t_base, t_rows, base):
  plt.rcParams.update({'font.size': 9, 'axes.edgecolor': INK2,
                       'axes.labelcolor': INK2, 'xtick.color': INK2,
                       'ytick.color': INK2, 'text.color': INK})
  fig = plt.figure(figsize=(15, 10.5), facecolor='#fcfcfb')
  gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.05], hspace=0.38, wspace=0.55)

  # (a) EUR / km^2 / yr, P10-P90
  ax = fig.add_subplot(gs[0, :])
  rows = [(f'Balloon fleet — {s.split(" (")[0].lower()}, {c} coverage',
           scen[(s, c)]['total'] / REGION_KM2, 'Balloon')
          for s, c in [('Winter (Dec-Mar)', BASE_COVERAGE),
                       ('Annual (Jan-Dec)', BASE_COVERAGE),
                       ('Annual (Jan-Dec)', '50 %'),
                       ('Summer (Jun-Aug)', '50 %')]]
  rows = [r + (None,) for r in rows]
  rows += [(k, v['per_km2'], v['group'], v['per_km2_shock']) for k, v in sysr.items()]
  rows.sort(key=lambda r: np.median(r[1]))
  for i, (lab, x, g, xs) in enumerate(rows):
    if xs is not None and g != 'HAPS':
      ax.plot(np.median(xs), i, 'o', ms=8, mfc='none', mec=GROUP_COL[g], mew=1.5)
    lo, mid, hi = pct(x)
    ax.plot([lo, hi], [i, i], color=GROUP_COL[g], lw=6, solid_capstyle='round',
            alpha=0.45)
    ax.plot(mid, i, 'o', ms=8, color=GROUP_COL[g], mec='#fcfcfb', mew=2)
    ax.text(hi * 1.15, i, f'{fmt_eur(mid)}', va='center', color=INK2, fontsize=8)
  ax.set_yticks(range(len(rows)), [r[0] for r in rows])
  ax.set_xscale('log')
  ax.set_xlabel('EUR per km² per year of coverage over 36–62°N, 10°W–42°E '
                '(dot = median, bar = P10–P90)')
  ax.grid(axis='x', color=GRID, lw=0.8); ax.set_axisbelow(True)
  for s in ('top', 'right'):
    ax.spines[s].set_visible(False)
  handles = [plt.Line2D([], [], marker='o', ls='', color=c, ms=8, label=g)
             for g, c in GROUP_COL.items()]
  handles.append(plt.Line2D([], [], marker='o', ls='', mfc='none', mec=INK2, ms=8,
                            label='Satellite median if launch costs ×1.5–3'))
  ax.legend(handles=handles, loc='lower right', frameon=False)
  ax.set_title('(a) Cost of covering the region, normalised per km² per year',
               loc='left', fontweight='bold')

  # (b) balloon line items by scenario (means, additive)
  ax = fig.add_subplot(gs[1, 0])
  keys = [('Summer (Jun-Aug)', '50 %'), ('Annual (Jan-Dec)', '50 %'),
          ('Summer (Jun-Aug)', BASE_COVERAGE), ('Annual (Jan-Dec)', BASE_COVERAGE),
          ('Winter (Dec-Mar)', BASE_COVERAGE)]
  labels = [f'{s.split(" (")[0]}\n{c.split(" (")[0]}' for s, c in keys]
  left = np.zeros(len(keys))
  for j, item in enumerate(LINE_ITEMS):
    vals = np.array([scen[k]['items'][item].mean() / 1e9 for k in keys])
    ax.barh(range(len(keys)), vals, left=left, color=PAL[j], label=item,
            edgecolor='#fcfcfb', linewidth=1.5, height=0.62)
    left += vals
  for i, k in enumerate(keys):
    ax.text(left[i] * 1.02, i, f'€{left[i]:.1f} B', va='center', color=INK2,
            fontsize=8)
  ax.set_yticks(range(len(keys)), labels)
  ax.set_xlim(0, left.max() * 1.18)
  ax.set_xlabel('EUR billion per year (mean of Monte Carlo; annualised rate)')
  ax.grid(axis='x', color=GRID, lw=0.8); ax.set_axisbelow(True)
  for s in ('top', 'right'):
    ax.spines[s].set_visible(False)
  ax.legend(loc='upper center', bbox_to_anchor=(0.45, -0.14), ncol=2,
            frameon=False, fontsize=8)
  ax.set_title('(b) Balloon fleet cost by line item: season × coverage target',
               loc='left', fontweight='bold')

  # (c) tornado
  ax = fig.add_subplot(gs[1, 1])
  top = t_rows[-10:]
  for i, (lab, lo, hi) in enumerate(top):
    ax.barh(i, (hi - lo) / 1e9, left=lo / 1e9, color=PAL[0], height=0.6)
  ax.axvline(t_base / 1e9, color=INK2, lw=1, ls='--')
  lo_x = min(r[1] for r in top) / 1e9
  hi_x = max(r[2] for r in top) / 1e9
  ax.set_xlim(lo_x - 0.05 * (hi_x - lo_x), hi_x + 0.05 * (hi_x - lo_x))
  ax.set_yticks(range(len(top)), [r[0] for r in top])
  ax.set_xlabel('Annual fleet cost, EUR billion (each input low→high, others at mode)')
  ax.grid(axis='x', color=GRID, lw=0.8); ax.set_axisbelow(True)
  for s in ('top', 'right'):
    ax.spines[s].set_visible(False)
  ax.set_title('(c) What drives balloon cost (annual, near-full coverage)',
               loc='left', fontweight='bold')

  fig.suptitle('Stratospheric balloon fleet vs satellite / HAPS connectivity over '
               'Europe → Black Sea', fontsize=13, fontweight='bold', x=0.06,
               ha='left')
  fig.savefig(OUT_PNG, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
  plt.close(fig)


# ----------------------------------------------------------------------------
def write_md(v):
  base, scen, sysr = v['base'], v['scen'], v['sysr']
  M = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct',
       'Nov', 'Dec']
  rs = lambda x: rng_str(x)
  L = []
  a = L.append
  r_star = pct(v['ratio_star'])
  r_best = pct(v['ratio_best'])
  b_gb = base['total'] / base['gb_yr']
  s_gb = sysr['Starlink (LEO broadband)']['eur_per_gb']
  a('# Balloon fleet vs satellite connectivity — cost comparison\n')
  a('*Generated by `cost_model.py` (Monte Carlo, '
    f'{N_DRAWS:,} draws + bootstrap over the {len(v["slow"])} simulated "slow" flights). '
    'Ranges are median (P10 – P90). EUR, 2025-26 prices.*\n')
  a('## Verdict\n')
  a(f'**The balloon fleet is not cost-competitive with satellite coverage of this region.** '
    f'Keeping ~95 % of the region covered year-round costs '
    f'**{rs(base["total"])} per year**, i.e. **{rs(v["b_km2"])} per km² per year** — '
    f'about **{r_star[1]:.0f}× Starlink\'s attributable cost** '
    f'({r_star[0]:.0f}–{r_star[2]:.0f}×), while delivering roughly '
    f'{pct(base["gbps"])[1]:,.0f} Gbps of radio capacity versus '
    f'~{pct(sysr["Starlink (LEO broadband)"]["gbps"])[1] / 1e3:,.0f} Tbps for Starlink\'s '
    f'share over the same area. Per GB of deliverable capacity the gap is '
    f'~{float(f"{pct(b_gb)[1] / pct(s_gb)[1]:.1g}"):,.0f}× ({rs(b_gb)} vs {rs(s_gb)}).\n')
  a(f'Even the most favourable case we model — **summer winds, 50 % coverage** — costs '
    f'{rs(scen[("Summer (Jun-Aug)", "50 %")]["total"])}/yr, still '
    f'{r_best[1]:.0f}× ({r_best[0]:.0f}–{r_best[2]:.0f}×) Starlink per km². '
    'The one thing balloons offer that broadband LEO does not is service to '
    '**unmodified phones** — but the direct-to-cell constellations '
    '(AST SpaceMobile, Starlink Direct to Cell) target exactly that at a far '
    'lower attributable cost per km², although with much less capacity per user '
    'today and not yet commercial in most of Europe.\n')
  a('Launch-market concentration (SpaceX flew about half of 2025\'s orbital '
    'launches; Ariane 6 manages a handful a year) is a real sovereignty and '
    'availability risk for the satellite options, and the balloon fleet\'s '
    'one structural advantage — it needs no launch vehicle. But stressing '
    'satellite launch costs ×1.5–3 moves them by under 2×, so it does not close '
    'the cost gap (see *Launch-market concentration* below).\n')
  a('**Why:** the fleet is a consumables business. Every flight '
    f'(harmonic-mean {v["harm"]["Annual (Jan-Dec)"]:.1f} days over the region) burns a '
    'whole envelope and about a quarter of a payload, so cost ≈ balloons aloft ÷ dwell '
    f'time × cost per flight ({rs(v["per_flight"])} all-in). That needs '
    f'**{num_str(base["per_day"])} launches/day** '
    f'({num_str(base["per_yr"] / 1e3)} k/yr) with '
    f'{num_str(base["aloft"])} balloons aloft.\n')

  a('### Key drivers\n')
  a('Season (winds) gives the largest swing across scenarios; within one '
    'scenario the biggest single-input swings are payload and envelope unit '
    'cost, then tiling and footprint (tornado, panel c).\n')
  a(f'1. **Dwell time, i.e. winter.** Launches scale with 1/dwell, so the year is '
    f'governed by the *harmonic* mean dwell ({v["harm"]["Annual (Jan-Dec)"]:.1f} d), '
    f'not the arithmetic mean ({v["mean_days"]:.1f} d) quoted in the brief. Winter '
    f'(Dec–Mar, harmonic {v["harm"]["Winter (Dec-Mar)"]:.1f} d; March '
    f'{v["monthly"][3]:.1f} d) runs at '
    f'{rs(scen[("Winter (Dec-Mar)", BASE_COVERAGE)]["total"])}/yr annualised vs '
    f'{rs(scen[("Summer (Jun-Aug)", BASE_COVERAGE)]["total"])}/yr in summer '
    f'(harmonic {v["harm"]["Summer (Jun-Aug)"]:.1f} d).')
  a('2. **Balloons cannot tile the region.** The brief\'s 310 launches/day assumes '
    'one balloon parked per 50 km cell. Station-keeping failed in our sims, so '
    'positions are closer to random; random coverage of 95 % needs '
    f'~3× as many balloons (−ln 0.05 ≈ 3.0). Footprint radius (Loon quoted '
    '~40 km, we simulated 50 km) adds up to another ~1.6×.')
  a('3. **Envelope and payload unit costs.** Together '
    f'{100 * (v["share_mean"]["Envelopes"] + v["share_mean"]["Payload (amortised)"]):.0f} % '
    'of spend. Glider recovery (78 % in the sim) helps the payload line but the '
    'envelope is single-use by design.')
  a(f'4. **Hydrogen is not a driver**: {100 * v["share_mean"]["Green hydrogen"]:.1f} % '
    f'of cost even at €8/kg green H₂ ({H2_KG_PER_FLIGHT:.1f} kg/flight + losses).')
  a('5. **Coverage target**: 50 % instead of 95 % cuts cost ~'
    f'{pct(scen[("Annual (Jan-Dec)", BASE_COVERAGE)]["total"])[1] / pct(scen[("Annual (Jan-Dec)", "50 %")]["total"])[1]:.1f}× '
    '(fewer balloons, and random placement is far less wasteful at low coverage).\n')

  a('![cost comparison](cost_comparison.png)\n')

  a('## Balloon fleet: scenarios\n')
  a('Annualised rate (EUR/yr) if every month looked like the season shown.\n')
  a('| Season | Coverage | Launches / day | Balloons aloft | Annual cost | EUR / km² / yr |')
  a('|---|---|---|---|---|---|')
  for (s, c), r in scen.items():
    a(f'| {s} | {c} | {num_str(r["per_day"])} | {num_str(r["aloft"])} | '
      f'{rs(r["total"])} | {rs(r["total"] / REGION_KM2)} |')
  a('')
  a(f'For reference, the brief\'s sizing (1,674 cells ÷ arithmetic-mean dwell '
    f'{v["mean_days"]:.2f} d, perfect tiling) gives {v["brief_launches_day"]:.0f} '
    'launches/day; the model above replaces both simplifications.\n')
  a('Simulated dwell per balloon ("slow" controller, mean days, n = 10 flights per month): ' +
    ', '.join(f'{M[m - 1]} {v["monthly"][m]:.1f}' for m in range(1, 13)) + '.\n')

  a('### Cost per flight (annual, near-full coverage)\n')
  a('| Line item | Share of cost (mean) | Per flight (median) |')
  a('|---|---|---|')
  for k in LINE_ITEMS:
    a(f'| {k} | {100 * v["share_mean"][k]:.1f} % | '
      f'{fmt_eur(np.median(base["items"][k] / base["per_yr"]))} |')
  a(f'| **Total** | 100 % | **{rs(v["per_flight"])}** |\n')

  a('### Physical footprint of the base case\n')
  a(f'* Green hydrogen: {num_str(base["h2_t"])} t/yr, needing '
    f'{num_str(base["h2_gwh"])} GWh/yr of renewable electricity '
    f'(~{pct(base["h2_gwh"])[1] * 1e3 / 8760:.0f} MW continuous electrolysis).')
  a(f'* **Polyethylene envelopes coming down: {num_str(base["pe_t"])} t/yr** '
    'across Europe, the Mediterranean and the Black Sea. This, not cost, may be '
    'the binding constraint (and is why burning at altitude, burn_sim.py, '
    'matters); envelope recovery is costed at €100–1,500 each but sea landings '
    'are largely unrecoverable.')
  a(f'* Launch sites: {num_str(base["sites"])} (sized for the peak month at '
    f'{mode(LAUNCHES_PER_SITE_DAY):.0f} launches/site/day nominal).\n')

  a('## Comparator systems\n')
  a('Annual cost = annualised capex + opex, attributed to this region by its share '
    'of each system\'s served area (weighted for satellites bunching at high '
    'latitude) — a generous allocation to the satellites because they also serve '
    'the rest of the world from the same spend.\n')
  a('| System | Region-attributable cost / yr | EUR / km² / yr | EUR / GB* | What it delivers |')
  a('|---|---|---|---|---|')
  a(f'| **Balloon fleet (annual, 95 %)** | {rs(base["total"])} | {rs(v["b_km2"])} | '
    f'{rs(b_gb)} | unmodified LTE phones, ~10–40 Mbps shared per balloon, ~20–40 ms; '
    'service gaps wherever balloons drift apart |')
  for k, r in sysr.items():
    gb = rs(r['eur_per_gb']) if 'eur_per_gb' in r else 'n/a (capacity not public)'
    a(f'| {k} | {rs(r["total"])} | {rs(r["per_km2"])} | {gb} | {r["delivers"]} |')
  a('')
  a(f'\\*EUR per GB of deliverable capacity at {mode(UTILISATION):.0%} '
    f'(range {UTILISATION[0]:.0%}–{UTILISATION[2]:.0%}) average utilisation. '
    'Capacity-based numbers for OneWeb and HAPS are rough assumptions.\n')
  ratios = [pct(v['b_km2'])[1] / pct(r['per_km2'])[1] for k, r in sysr.items()
            if r['group'] != 'HAPS']
  a(f'**Reading the table.** Per km², every satellite option is '
    f'{min(ratios):.0f}× to {max(ratios):,.0f}× cheaper than the balloon fleet '
    '(medians), and Starlink also delivers '
    f'~{pct(sysr["Starlink (LEO broadband)"]["gbps"])[1] / pct(base["gbps"])[1]:.0f}× more capacity. Solar HAPS land in the same cost range as '
    'the balloons and cannot yet fly a European winter. Direct-to-cell is the '
    'real like-for-like competitor (same phones), and it is cheap per km² '
    'because one satellite footprint is far larger than a balloon\'s — but its '
    'per-user throughput is currently low.\n')

  a('## Launch-market concentration: risk and availability\n')
  a(f'Satellite constellations need a launch vehicle for deployment *and* for '
    f'continual replenishment (LEO satellites last ~5-12 years). That market is '
    f'concentrated in one company: SpaceX flew {SPACEX_LAUNCH_SHARE_2025:.0%} of '
    f'the world\'s orbital launches in 2025 (165 of 325), and reportedly over 80 % '
    f'of the mass put into orbit. Europe\'s own heavy launcher, Ariane 6, flew '
    f'~{ARIANE6_LAUNCHES_2025} times in 2025, targets 6-8 in 2026 and has a stated '
    f'ceiling of ~9-10 per year, shared with Galileo, Copernicus, institutional '
    'and commercial customers (including Amazon\'s 18-launch Kuiper contract). '
    'This is a risk and availability dimension, not a reason to set the cost '
    'comparison aside:\n')
  a('* **Price.** Constellations not owned by SpaceX buy launch from a near-'
    'monopoly supplier or from slower, costlier alternatives. The table below '
    'stresses each system\'s launch share of annual cost by '
    f'×{LAUNCH_PRICE_SHOCK[0]}–{LAUNCH_PRICE_SHOCK[2]}. Because launch is only '
    '~15-50 % of annual cost, even a doubling or tripling moves satellites by '
    'well under 2× — not the 50×+ gap to the balloon fleet.')
  a('* **Sovereignty.** Starlink and Starlink Direct to Cell are wholly dependent '
    'on one non-European company for both service and launch; the service can be '
    'restricted by a single operator\'s decision. OneWeb lost its Soyuz '
    'launches in 2022 and finished Gen1 on Falcon 9 (plus ISRO). IRIS² is '
    'mandated to fly on European launchers, so its deployment (first launches '
    '2029, now 348 satellites) and future replenishment are paced by Ariane 6 '
    'cadence rather than by price.')
  a('* **Availability.** A launch failure, grounding or policy change at the '
    'dominant provider stalls replenishment for most Western constellations at '
    'once; Europe has no second heavy launcher yet.')
  a('* **Balloon fleet.** Needs no launch vehicle: ground launch from ~30-80 '
    'European sites with European-made hydrogen, and resupply in days. Its '
    'equivalent exposures are different: airspace approval from ~30 states, '
    'winter winds (panel b), envelope supply (~400k envelopes/yr in the base '
    'case, one specialist industry) and envelope debris.\n')
  a('| System | Launcher(s) | Dependence on SpaceX | EUR / km² / yr (base) | '
    'EUR / km² / yr if launch cost ×1.5–3 |')
  a('|---|---|---|---|---|')
  a(f'| **Balloon fleet (annual, 95 %)** | none (ground launch) | None | '
    f'{rs(v["b_km2"])} | unchanged |')
  for k, r in sysr.items():
    a(f'| {k} | {r["launcher"]} | {r["spacex_dep"]} | {rs(r["per_km2"])} | '
      f'{rs(r["per_km2_shock"]) if r["group"] != "HAPS" else "unchanged"} |')
  a('')
  a('**Net:** launch concentration is the strongest argument *for* a non-orbital '
    'European layer — balloons and solar HAPS are the only options here with no '
    'launch dependency at all — but it buys resilience, not cost: on the numbers above a sovereign '
    'balloon layer would cost tens of times more per km² than satellites even '
    'after a severe launch-price shock. A sovereign *satellite* option (IRIS²) '
    'stays one to two orders of magnitude cheaper per km² than balloons, but '
    'is availability-limited by Ariane 6 cadence until Europe has more heavy launchers.\n')
  a('## What would have to change for balloons to win\n')
  st50 = pct(sysr['Starlink (LEO broadband)']['per_km2'])[1]
  a('Put every balloon input at the cheap end of its range at once (cheapest '
    'envelope and payload, perfect tiling, 50 km footprint, longest bootstrap '
    'dwell, ...) and the year-round fleet still costs '
    + ', '.join(f'{fmt_eur(v["floor"][c])}/yr ({fmt_eur(v["floor"][c] / REGION_KM2)}/km², '
                f'{v["floor"][c] / REGION_KM2 / st50:.0f}× Starlink median) at {c}'
                for c in COVERAGE_TARGETS) +
    ' coverage. Closing the gap would need, at once: dwell measured in weeks (Loon\'s ~100+ day flights over '
    'the tropics, not 1.5–14 days in the westerlies), real station-keeping so '
    'balloons tile cells, and envelopes in the low thousands of euros. The '
    'westerlies over Europe make the first two unlikely. Niche uses that could '
    'still make sense: rapid, temporary coverage over a disaster or a few cells '
    'for days, where a handful of launches replaces nothing permanent.\n')

  a('## Caveats and flagged numbers\n')
  a('* **Envelope and payload prices are assumptions** (no public Loon/Aerostar '
    'pricing; AFP reported a complete Loon balloon at "tens of thousands of '
    'dollars"). They matter, but not enough to flip the verdict.')
  a('* Satellite costs are company-level, not Europe-specific; area attribution is '
    'a modelling choice. Starlink\'s figure is from the 2025 S-1 Connectivity '
    'segment plus estimated capex; OneWeb, IRIS² opex, AST opex and Starlink '
    'DTC incremental costs are partly assumptions.')
  a('* IRIS² is not in service before ~2030; AST and Starlink DTC are not yet '
    'commercial across Europe; Starlink DTC in Europe needs MNO spectrum partners '
    '(the USD 17 B EchoStar spectrum is US-only and excluded).')
  a('* Balloon spectrum is assumed supplied by partner MNOs (excluded), as is user '
    'equipment for all systems (Starlink dish USD 300–600 is a real user cost).')
  a(f'* Sim sample is small (10 flights/month, 5 launch sites, one year) and 3 flights '
    'hit the 30-day cap, so summer dwell is slightly underestimated. The bootstrap '
    'carries this into the ranges.')
  a('* The brief quoted the region as 36–59.5°N; the analysis scripts (analyze.py) '
    f'use 36–62°N, which is what gives {REGION_KM2 / 1e6:.1f} M km² / 1,674 cells, '
    'so this model uses 36–62°N.\n')

  a('## Sources\n')
  for s in [
    '[ACER — European hydrogen markets 2025 (renewable H₂ ~€8/kg, €7–10/kg range)](https://acer.europa.eu/monitoring/European-hydrogen-markets-2025)',
    '[pv magazine — Price gap between conventional and renewable hydrogen widens (2025-12-03)](https://www.pv-magazine.com/2025/12/03/price-gap-between-conventional-renewable-hydrogen-widens-in-europe/)',
    '[ACER CHEST — LCOH data items (DK wind ~€5.8/kg, ES PV ~€6/kg)](https://aegis.acer.europa.eu/chest/category/66/list)',
    '[SpaceDaily — Starlink Connectivity 61 % of revenue, only operating profit (S-1 segment figures)](https://spacedaily.com/t-spacex-starlink-connectivity-61-percent-revenue-only-operating-profit/)',
    '[Tom Tunguz — SpaceX S-1 analysis (Starlink revenue 2025, satellites, subscribers)](https://tomtunguz.com/spacex-s1-analysis)',
    '[Space Odyssey Hub — Starlink unit economics 2026 (analyst per-satellite cost estimates)](https://spaceodysseyhub.com/articles/starlink-unit-economics-2026)',
    '[DishyTech — Starlink 2025 review (network capacity)](https://www.dishytech.com/starlink-just-had-a-massive-2025-and-2026-could-be-even-bigger/)',
    '[ISPreview — Starlink V3 1 Tbps satellites](https://www.ispreview.co.uk/index.php/2025/01/starlink-2024-report-details-1tbps-speed-leo-v3-broadband-satellites.html)',
    '[DatacenterDynamics — EU launches €10.6 bn IRIS² programme](https://www.datacenterdynamics.com/en/news/eu-launches-106bn-space-internet-program-set-to-launch-in-2029/)',
    '[Eutelsat — SpaceRISE concession press release](https://www.mynewsdesk.com/eutelsat/pressreleases/spacerise-consortium-inks-agreement-as-concessionaire-for-the-european-unions-landmark-iris2-constellation-3360767)',
    '[Space Intel Report — OneWeb Gen1 to 2034, $5.07 B capex](https://www.spaceintelreport.com/eutelsat-we-signed-1st-oneweb-hosted-payload-oneweb-gen-1-to-operate-to-2034-then-iris2-5-07b-in-capex-to-2034/)',
    '[ISPreview — OneWeb LEO revenues (FY2026)](https://www.ispreview.co.uk/index.php/2026/08/oneweb-broadband-satellites-help-lift-leo-revenues-69-5-percent-at-eutelsat.html)',
    '[Space Intel Report — AST SpaceMobile launch costs, ~$22 M per Block-2 satellite](https://www.spaceintelreport.com/ast-spacemobile-launch-price-increases-mean-well-need-1-3-billion-to-launch-60-satellites-by-late-2026/)',
    '[AlphaSense — AST SpaceMobile Q4 2025 earnings summary](https://www.alpha-sense.com/earnings/asts)',
    '[Engadget — SpaceX completes first Direct to Cell constellation](https://www.engadget.com/science/space/spacex-completes-starlinks-first-direct-to-cell-constellation-212549713.html)',
    '[DatacenterDynamics — Starlink to use EchoStar spectrum](https://www.datacenterdynamics.com/en/news/starlink-looks-to-use-echostar-spectrum-for-thousands-of-new-satellites/)',
    '[AALTO — Zephyr direct-to-device payload, 7,500 km²](https://aaltohaps.com/connect)',
    '[BEREC — AALTO presentation (endurance, tower costs)](https://berec.europa.eu/system/files/2024-05/12.%20AALTO_0.pdf)',
    '[satcom.guru — Loon coverage ~5,000 km² per balloon](https://www.satcom.guru/2017/10/google-loon-floating-nest-of-radio.html)',
    '[Signals Research Group — Loon LTE performance test](https://signalsresearch.com/news/verizons-dss-performance-disappointing-says-srg-2/)',
    '[DatacenterDynamics — Loon over Kenya (19 Mbps DL measured)](https://www.datacenterdynamics.com/en/news/alphabets-loon-balloons-and-floating-over-kenya/)',
    '[Mobile World Live — End of Loon highlights economic issues](https://www.mobileworldlive.com/blog/intelligence-brief-end-of-loon-highlights-economic-issues)',
    '[TBS News / AFP — Alphabet shutting down Loon ("tens of thousands of dollars" per balloon)](https://www.tbsnews.net/node/189685)',
    '[Satellite Today — BryceTech: SpaceX 50 % of launches in 2025](https://satellitetoday.com/launch/2026/04/10/brycetech-report-shows-spacex-accounted-for-50-of-launches-in-2025/)',
    '[Motley Fool — space launch statistics (mass to orbit, from S-1)](https://fool.com/research/space-launch-statistics/)',
    '[European Spaceflight — Arianespace aiming for up to 8 Ariane 6 launches in 2026](https://europeanspaceflight.com/?p=5466)',
    '[Behind the Black — ArianeGroup targeting ~6 Ariane 6 launches in 2026](https://behindtheblack.com/?p=119135)',
    '[Space Intel Report — ESA studies Ariane 6 cadence of 15+/yr](https://www.spaceintelreport.com/esa-looking-at-what-it-would-take-to-increase-ariane-6-cadence-to-15-missions-or-more-per-year-before-2030/)',
    '[The Next Web — IRIS² moves to deployment, European launchers, 348 satellites](https://thenextweb.com/news/iris2-europe-sovereign-satellite-starlink-rival-deployment)',
    '[Satnews — SpaceRISE initiates IRIS² procurement (Ariane 6 prioritised)](https://news.satnews.com/2025/12/29/spacerise-consortium-initiates-iris%c2%b2-procurement-phase)',
    '[Spaceflight Now — OneWeb signs with SpaceX after Soyuz halt (2022)](https://spaceflightnow.com/2022/03/21/oneweb-signs-with-spacex-to-resume-launching-internet-constellation/)',
    '[AMT 2019 — radiosonde launch cost ~USD 325](https://amt.copernicus.org/articles/12/1311/2019/amt-12-1311-2019.xml)',
    '[Hawaii Tribune-Herald — Autosonde launcher ~USD 0.8 M](https://www.hawaiitribune-herald.com/2021/06/08/hawaii-news/machine-auto-launches-weather-balloons-twice-daily-from-hilo/)',
  ]:
    a(f'* {s}')
  a('\nAll other inputs are marked ASSUMPTION in `cost_model.py` with their ranges.')
  with open(OUT_MD, 'w') as f:
    f.write('\n'.join(L) + '\n')


if __name__ == '__main__':
  main()

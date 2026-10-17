"""Envelope mass and cost model for the balloon fleet (physics + bottom-up).

Reads nothing from the simulations except the multi-pass launch multipliers
(results/multipass_summary.csv, copied as constants) and cost_model.py's
baseline numbers. Single-process, runs in a few seconds.

Part 1  physics: lift balance with hydrogen at a design ceiling, required
        volume, film stress for a superpressure pumpkin (lobe radius
        r = sigma*t/dp, tendons carry the meridional load) vs a plain
        superpressure sphere (sigma = dp*R/(2t)) vs a zero-pressure balloon
        (no pressure load, but ballast every night). Envelope mass and film
        area vs payload mass.
Part 2  bottom-up cost per envelope: film, tendons, fittings, seams,
        labour, QA, packaging, yield, line capex, margin, at today's
        (Loon/Aerostar) volume and at 400k/yr; learning-curve cross-check.
Part 3  levers, one at a time and stacked, with low/mode/high ranges, and
        cost per Europe-day for 4/30/60/100-day envelope designs.

Every number that is not physics is tagged SOURCE or ASSUMPTION.

Run:  PYTHONWARNINGS=ignore .venv/bin/python -I envelope_cost.py
Writes results/envelope_cost.md and results/envelope_cost.png.
"""
import math
import os
from dataclasses import dataclass, replace

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_MD = os.path.join(HERE, 'results', 'envelope_cost.md')
OUT_PNG = os.path.join(HERE, 'results', 'envelope_cost.png')

# ----------------------------------------------------------------------------
# Reference numbers from the rest of the repo
# ----------------------------------------------------------------------------
BLE_ENVELOPE_KG = 68.5      # BLE balloon.py envelope_mass
BLE_PAYLOAD_KG = 92.5       # BLE balloon.py payload_mass
BLE_VOLUME_M3 = 1804.0      # BLE at float (task brief)
BLE_DP_MAX_PA = 2380.0      # BLE max superpressure
BLE_GAS_MOL = 6830.0
TODAY_ENVELOPE_EUR = 10_000.0          # cost_model.py ENVELOPE_EUR mode (tri 4k/10k/25k)
EUROPE_DAYS_PER_LAUNCH = 3.7           # cost_model harmonic-mean dwell, one-way flights
FLEET_ENVELOPES_PER_YR = 402_000       # cost_model base case
# Multi-pass launch multipliers vs one-way (results/multipass_summary.csv,
# README): free routing / China avoided without propulsion.
MULTIPASS = {4: (1.00, 1.00), 30: (0.62, 0.77), 60: (0.49, 0.68), 100: (0.42, 0.62)}
PASSIVE_DWELL_FACTOR = 5.4 / 3.2       # README: slow controller 5.4 d vs passive 3.2 d
                                       # -> a balloon with no altitude control needs x1.69 launches

# ----------------------------------------------------------------------------
# Atmosphere and gas
# ----------------------------------------------------------------------------
R_GAS = 8.314
M_AIR = 0.028965
M_H2 = 0.002016
M_HE = 0.0040026
T_STRAT_K = 215.0     # mid-latitude 18-21 km, annual mean ~ -58 C (ISA 216.65 K);
                      # winter 45-55N can reach 200 K (ASSUMPTION: use 215 K for sizing)
G = 9.81


def rho(p_pa, T, M):
  return p_pa * M / (R_GAS * T)


# ----------------------------------------------------------------------------
# Materials (documented)
# ----------------------------------------------------------------------------
# Balloon film: coextruded LLDPE (NASA/Aerostar "StratoFilm"-type). SOURCES:
#  * NASA superpressure balloons use ~38 um coextruded LLDPE film with PBO
#    (Zylon) tendons [Tensys/NTRS 20180007750; ICRC 2005 ULDB poster].
#  * Loon envelope reported as polyethylene "about 3 mil / 0.076 mm", made by
#    Raven Aerostar; 15 m wide at float [Wikipedia-derived text; stratocat
#    gives 15 m x 9 m at float]. Secondary source.
#  * Raven StratoFilm-430 zero-pressure film 10-20 um, three-layer coextruded
#    LLDPE [Raven "Ultra High Altitude Balloons 2002"]; 20 um was the
#    standard production gauge.
#  * LLDPE room-temperature yield ~10-12 MPa, ultimate 25-40 MPa with >500 %
#    elongation; at -60..-80 C yield rises to roughly 25-35 MPa and the film
#    stays ductile (Tg of PE ~ -110 C), while creep under sustained load is
#    the long-duration limit [Rand & Sterling, NASA 2004, 38 um LLDPE
#    time-dependent properties, NTRS 20040171572; exact values ASSUMPTION].
FILM_DENSITY = 920.0          # kg/m3, LLDPE
FILM_YIELD_COLD_MPA = 28.0    # ASSUMPTION within the 25-35 MPa band above
FILM_YIELD_WARM_MPA = 11.0    # ascent/ground (not governing: dp ~ 0 before float)
FILM_MIN_GAUGE_SP_UM = 25.0   # handling / pinhole floor for a pressurised envelope, ASSUMPTION
FILM_MIN_GAUGE_ZP_UM = 20.0   # Raven standard ZP gauge (10 um flown on ultra-high-altitude ZPs)
BALLONET_GAUGE_UM = 15.0      # internal air bag, unpressurised relative to lift gas, ASSUMPTION
PUMPKIN_AREA_FACTOR = 1.10    # lobed + oblate surface vs sphere of equal volume, ASSUMPTION
NATURAL_SHAPE_AREA_FACTOR = 1.18  # zero-pressure natural shape vs sphere, ASSUMPTION
SEAM_ALLOWANCE = 1.06         # seam overlap + caps + reinforcement, ASSUMPTION
GORE_WIDTH_PER_LOBE_RADIUS = 1.6  # gore width ~ 1.6 r_lobe (bulge half-angle ~53 deg), ASSUMPTION
MAX_GORE_WIDTH_M = 1.8        # blown-film roll width, ASSUMPTION
BALLONET_VOL_FRAC = 0.35      # air bag volume at the lowest float altitude (140 vs 60 hPa needs
                              # ~0.57 of the volume as air -> here 0.35 as a cheaper band), ASSUMPTION
# Tendons: UHMWPE braid (Dyneema-class) or PBO (Zylon, NASA). Fibre tenacity
# ~3.0-3.5 GPa, density 970 kg/m3 (UHMWPE); braid + termination efficiency
# ~0.6; creep of UHMWPE under sustained load is why the SF is high.
# ASSUMPTION for efficiency and SF.
TENDON_SIGMA_PA = 3.0e9
TENDON_DENSITY = 970.0
TENDON_EFF = 0.6
TENDON_LENGTH_FACTOR = 1.05   # lobed meridian vs pi*R
# Fittings: apex/base plates with tendon terminations, fill/vent fitting.
FITTING_BASE_KG = 1.5
FITTING_PER_GORE_KG = 0.02
ZP_LOADTAPE_SIGMA = 0.4e9     # polyester load tape for ZP, ASSUMPTION
ZP_LOADTAPE_DENSITY = 1380.0
ZP_BALLAST_HW_KG = 3.0        # hopper + valve for a ZP balloon, ASSUMPTION
# Zero-pressure night ballast: fraction of gross mass dropped per sunset.
# Long-duration ZP experience at mid-latitudes is ~5-8 %/night; long winter
# nights at 45-55N push it up. ASSUMPTION band.
ZP_BALLAST_FRAC_PER_NIGHT = (0.05, 0.075, 0.10)
# Superpressure needed to survive the diurnal cycle (gas supertemperature
# ~15-25 K by day in clear PE, slightly sub-ambient at night): dp ~ p*dT/T
# -> 60 hPa * 20/215 ~ 560 Pa, plus margin for altitude control pumping.
DP_MIN_SURVIVE_PA = 700.0     # ASSUMPTION (clear film, 60 hPa ceiling)


# ----------------------------------------------------------------------------
# Envelope design
# ----------------------------------------------------------------------------
@dataclass
class Design:
  name: str
  kind: str = 'pumpkin'        # 'pumpkin' | 'sphere' | 'zp'
  p_ceiling_hpa: float = 60.0  # lowest pressure the envelope must float at with no ballonet air
  dp_pa: float = BLE_DP_MAX_PA # design (max) superpressure
  film_gauge_um: float = 63.5  # None -> stress-limited with the min gauge floor
  film_yield_mpa: float = FILM_YIELD_COLD_MPA
  film_sf: float = 2.5         # safety factor on cold yield (creep for long flights)
  tendon_sf: float = 2.0       # on dp_max (already a limit)
  lift_margin: float = 0.05    # spare lift at the ceiling (control air, leaks), ASSUMPTION
  ballonet: bool = True        # altitude-control air bag
  life_days: float = 100.0
  uv_allowance: float = 0.0    # extra thickness fraction for UV/ozone over the life
  ballast_days: float = 0.0    # zp only
  ballast_frac_night: float = ZP_BALLAST_FRAC_PER_NIGHT[1]
  gas: str = 'H2'


def size_envelope(d: Design, payload_kg: float):
  """Iterate envelope mass <-> volume. Returns dict of masses/areas."""
  p = d.p_ceiling_hpa * 100.0
  M_gas = M_H2 if d.gas == 'H2' else M_HE
  rho_air = rho(p, T_STRAT_K, M_AIR)
  rho_gas = rho(p + (d.dp_pa if d.kind != 'zp' else 0.0), T_STRAT_K, M_gas)
  net_per_m3 = rho_air - rho_gas
  sigma_allow = d.film_yield_mpa * 1e6 / d.film_sf
  env = 20.0
  out = {}
  for _ in range(60):
    ballast = 0.0
    if d.kind == 'zp':
      # ballast for N nights: gross after N drops must still carry payload + envelope
      gross_needed = (payload_kg + env + ZP_BALLAST_HW_KG) / max(1e-6, 1.0 - d.ballast_days * d.ballast_frac_night)
      ballast = gross_needed - (payload_kg + env + ZP_BALLAST_HW_KG)
    lifted = (payload_kg + env + ballast + (ZP_BALLAST_HW_KG if d.kind == 'zp' else 0.0)) * (1 + d.lift_margin)
    V = lifted / net_per_m3
    R = (3 * V / (4 * math.pi)) ** (1 / 3)
    A_sph = 4 * math.pi * R ** 2
    if d.kind == 'pumpkin':
      # film gauge: given, or the thinnest that keeps a sensible lobe
      t = (d.film_gauge_um or FILM_MIN_GAUGE_SP_UM) * 1e-6 * (1 + d.uv_allowance)
      r_lobe = sigma_allow * t / d.dp_pa
      w_gore = min(GORE_WIDTH_PER_LOBE_RADIUS * r_lobe, MAX_GORE_WIDTH_M)
      n_gores = max(8, math.ceil(2 * math.pi * R / w_gore))
      A_film = A_sph * PUMPKIN_AREA_FACTOR * SEAM_ALLOWANCE
      film = A_film * t * FILM_DENSITY
      load = d.dp_pa * math.pi * R ** 2            # total meridional load
      L_t = math.pi * R * TENDON_LENGTH_FACTOR
      tendons = load * d.tendon_sf * L_t / (TENDON_SIGMA_PA * TENDON_EFF / TENDON_DENSITY)
      fittings = FITTING_BASE_KG + FITTING_PER_GORE_KG * n_gores
      seam_m = n_gores * L_t * 2                   # gore seams + tendon sleeves
      stress = d.dp_pa * r_lobe / t
    elif d.kind == 'sphere':
      # film takes the whole load: sigma = dp R / (2 t)
      t = max(d.dp_pa * R / (2 * sigma_allow), FILM_MIN_GAUGE_SP_UM * 1e-6) * (1 + d.uv_allowance)
      n_gores = max(8, math.ceil(2 * math.pi * R / MAX_GORE_WIDTH_M))
      A_film = A_sph * SEAM_ALLOWANCE
      film = A_film * t * FILM_DENSITY
      tendons = 0.0
      fittings = FITTING_BASE_KG + 0.5
      L_t = math.pi * R
      seam_m = n_gores * L_t
      stress = d.dp_pa * R / (2 * t)
      r_lobe = R
    else:  # zero pressure
      t = FILM_MIN_GAUGE_ZP_UM * 1e-6 * (1 + d.uv_allowance)
      n_gores = max(8, math.ceil(2 * math.pi * R / MAX_GORE_WIDTH_M))
      A_film = A_sph * NATURAL_SHAPE_AREA_FACTOR * SEAM_ALLOWANCE
      film = A_film * t * FILM_DENSITY
      L_t = math.pi * R * 1.1
      load = (payload_kg + ballast + ZP_BALLAST_HW_KG) * G * 3.0  # 3 g shock SF, ASSUMPTION
      tendons = load * 2.0 * L_t / (ZP_LOADTAPE_SIGMA / ZP_LOADTAPE_DENSITY)
      fittings = FITTING_BASE_KG + 0.5            # + duct/valve
      seam_m = n_gores * L_t * 2                  # gore seams + load-tape seams
      r_lobe = float('nan')
      stress = net_per_m3 * G * 2 * R * R / (2 * t) / 1e6 * 1e6  # gas head only (Pa)
    ballonet = 0.0
    if d.kind != 'zp' and d.ballonet:
      ballonet = (BALLONET_VOL_FRAC ** (2 / 3)) * A_sph * BALLONET_GAUGE_UM * 1e-6 * FILM_DENSITY * SEAM_ALLOWANCE
    new_env = film + tendons + fittings + ballonet
    out = dict(envelope_kg=new_env, film_kg=film, tendon_kg=tendons, fitting_kg=fittings,
               ballonet_kg=ballonet, volume_m3=V, radius_m=R, film_area_m2=A_film,
               gauge_um=t * 1e6, n_gores=n_gores, seam_m=seam_m, lobe_r_m=r_lobe,
               film_stress_mpa=stress / 1e6, ballast_kg=ballast,
               gas_kg=V * rho_gas, gross_lift_kg=V * rho_air, net_lift_kg=V * net_per_m3,
               sigma_allow_mpa=sigma_allow / 1e6)
    if not math.isfinite(new_env) or new_env > 50 * (payload_kg + 1):
      out['envelope_kg'] = float('inf')      # film mass per m3 exceeds net lift: infeasible
      out['infeasible'] = True
      return out
    if abs(new_env - env) < 1e-4:
      break
    env = new_env
  out['infeasible'] = False
  return out


def calibrate_gauge(d: Design, payload_kg: float, target_kg: float, lo=20.0, hi=120.0):
  """Film gauge (um) at which the design's envelope mass equals target_kg."""
  for _ in range(60):
    mid = 0.5 * (lo + hi)
    m = size_envelope(replace(d, film_gauge_um=mid), payload_kg)['envelope_kg']
    lo, hi = (lo, mid) if m > target_kg else (mid, hi)
  return 0.5 * (lo + hi)


# Named designs ---------------------------------------------------------------
_BLE_PROTO = Design('BLE/Loon-like pumpkin (today)', film_gauge_um=63.5, dp_pa=BLE_DP_MAX_PA,
                    film_sf=2.5, tendon_sf=2.0, life_days=100)
BLE_GAUGE_UM = calibrate_gauge(_BLE_PROTO, BLE_PAYLOAD_KG, BLE_ENVELOPE_KG)
BLE_DESIGN = replace(_BLE_PROTO, film_gauge_um=BLE_GAUGE_UM)
SP_4D = Design('Pumpkin, 4-day, low dp', dp_pa=1000.0, film_gauge_um=None, film_sf=1.5,
               tendon_sf=1.5, life_days=4)
SP_4D_NOCTRL = replace(SP_4D, name='Pumpkin, 4-day, no ballonet', ballonet=False)
SPHERE_LLDPE = Design('Sphere, LLDPE, dp 700 Pa', kind='sphere', dp_pa=DP_MIN_SURVIVE_PA,
                      film_sf=1.5, life_days=4, ballonet=True)
# PET/nylon bilaminate sphere (GHOST-balloon heritage: Mylar spheres flew
# 100-700+ days in the 1960s-70s). Biaxial PET yield ~100 MPa; brittle at
# cold with pinholes/creases -> SF 2.5. ASSUMPTION.
SPHERE_PET = Design('Sphere, PET laminate, dp 700 Pa', kind='sphere', dp_pa=DP_MIN_SURVIVE_PA,
                    film_yield_mpa=100.0, film_sf=2.5, life_days=4, ballonet=True)
ZP_4D = Design('Zero-pressure, 4 nights ballast', kind='zp', ballast_days=4, life_days=4, ballonet=False)


def life_design(days: float) -> Design:
  """Pumpkin designed for a given flight life: creep SF, UV allowance."""
  table = {4: (1.5, 0.00), 30: (1.9, 0.05), 60: (2.2, 0.08), 100: (2.5, 0.10)}  # ASSUMPTION
  sf, uv = table[days]
  return replace(SP_4D, name=f'Pumpkin, {days}-day', film_sf=sf, uv_allowance=uv,
                 tendon_sf=1.5 + 0.5 * (days > 4), life_days=days)


# ----------------------------------------------------------------------------
# Bottom-up cost per envelope
# ----------------------------------------------------------------------------
@dataclass
class CostParams:
  """(low, mode, high) = (cheap, central, dear). EUR 2025-26."""
  film_eur_kg: tuple          # balloon-grade coextruded LLDPE, delivered
  tendon_eur_kg: tuple        # UHMWPE braid incl. terminations
  fittings_eur: tuple         # plates, valve, fill fitting
  fittings_per_gore_eur: tuple
  seam_eur_m: tuple           # sealing cost per metre (machine + operator + energy)
  labour_h_fixed: tuple       # layout, folding, packing per envelope
  labour_h_per_100m2: tuple   # handling per 100 m2 of film
  labour_eur_h: tuple
  qa_eur: tuple               # inflation / leak test / pinhole scan
  packaging_eur: tuple
  scrap_frac: tuple           # rejected envelopes + film waste
  line_capex_eur_per_unit: tuple  # amortised plant & tooling
  margin: tuple               # supplier G&A + profit
  ballonet_eur_kg: tuple


# Today: Aerostar/Loon-era volume (~10^3/yr), manual table assembly.
# SOURCES/anchors: Aerostar tactical PE balloons (few kg) "a few thousand
# dollars"; Aerostar 2023 deck "cost per asset ~$50-500k" for HAB systems;
# NASA ZP missions $2-3 M (MIT Tech Review 2017); cost_model tri(4k,10k,25k).
TODAY = CostParams(
    film_eur_kg=(8, 15, 30),          # specialty film, short runs, ASSUMPTION
    tendon_eur_kg=(80, 150, 300),     # UHMWPE braid small lots, ASSUMPTION
    fittings_eur=(600, 1200, 2500),   # machined, low volume, ASSUMPTION
    fittings_per_gore_eur=(3, 6, 12),
    seam_eur_m=(0.3, 0.6, 1.2),       # manual heat-seal tables, ASSUMPTION
    labour_h_fixed=(10, 20, 40),
    labour_h_per_100m2=(2, 4, 8),
    labour_eur_h=(35, 45, 60),
    qa_eur=(300, 800, 2000),
    packaging_eur=(80, 150, 300),
    scrap_frac=(0.08, 0.15, 0.25),
    line_capex_eur_per_unit=(100, 300, 800),
    margin=(0.20, 0.30, 0.45),
    ballonet_eur_kg=(15, 25, 50))

# Volume: ~400k/yr, dedicated blown-film line (~10 kt/yr of film is one
# ordinary line), automated gore cutting + continuous sealing, inline
# leak/pinhole inspection.
# SOURCES: LLDPE Europe ~EUR 0.8-2.1/kg, mLLDPE ~USD 2.0-2.4/kg (2026);
# specialty coextruded film converting adds ~EUR 1-3/kg -> EUR 3-8/kg.
# Weather balloons (latex, ~1.2 kg) retail ~USD 60-130 ~ EUR 50-100/kg at
# ~1 M/yr world volume: a hand-dipped rubber product, an upper bound for a
# "consumable" balloon's EUR/kg.
VOLUME = CostParams(
    film_eur_kg=(3, 5, 9),
    tendon_eur_kg=(30, 60, 120),
    fittings_eur=(80, 200, 450),
    fittings_per_gore_eur=(0.5, 1.5, 4),
    seam_eur_m=(0.04, 0.10, 0.25),
    labour_h_fixed=(1.0, 2.0, 4.0),
    labour_h_per_100m2=(0.2, 0.5, 1.2),
    labour_eur_h=(30, 40, 55),
    qa_eur=(30, 70, 200),
    packaging_eur=(15, 30, 60),
    scrap_frac=(0.04, 0.08, 0.15),
    line_capex_eur_per_unit=(20, 50, 150),   # e.g. EUR 100 M over 5 yr / 400k
    margin=(0.12, 0.20, 0.30),
    ballonet_eur_kg=(6, 10, 18))


def pick(cp: CostParams, k: int) -> dict:
  return {f: getattr(cp, f)[k] for f in cp.__dataclass_fields__}


def cost_envelope(sz: dict, cp: CostParams, k: int = 1, qa_mult: float = 1.0,
                  scrap_add: float = 0.0, design_kind: str = 'pumpkin') -> dict:
  p = pick(cp, k)
  film = sz['film_kg'] * p['film_eur_kg']
  ballonet = sz['ballonet_kg'] * p['ballonet_eur_kg']
  tendon = sz['tendon_kg'] * (p['tendon_eur_kg'] if design_kind != 'zp' else p['tendon_eur_kg'] * 0.2)
  fittings = p['fittings_eur'] + p['fittings_per_gore_eur'] * sz['n_gores']
  seams = sz['seam_m'] * p['seam_eur_m']
  labour = (p['labour_h_fixed'] + p['labour_h_per_100m2'] * sz['film_area_m2'] / 100) * p['labour_eur_h']
  qa = p['qa_eur'] * qa_mult
  pack = p['packaging_eur']
  direct = film + ballonet + tendon + fittings + seams + labour + qa + pack
  scrap = direct * (p['scrap_frac'] + scrap_add)
  capex = p['line_capex_eur_per_unit']
  sub = direct + scrap + capex
  margin = sub * p['margin']
  total = sub + margin
  return dict(film=film, ballonet=ballonet, tendon=tendon, fittings=fittings, seams=seams,
              labour=labour, qa=qa, packaging=pack, scrap=scrap, capex=capex, margin=margin,
              total=total)


def cost3(sz, cp, **kw):
  return tuple(cost_envelope(sz, cp, k, **kw)['total'] for k in range(3))


def wright(cost0, n0, n1, lr):
  """Wright's law: cost at cumulative volume n1 given cost0 at n0, learning rate lr."""
  b = math.log(lr) / math.log(2)
  return cost0 * (n1 / n0) ** b


# ----------------------------------------------------------------------------
# Recovery / reuse credit
# ----------------------------------------------------------------------------
LAND_FRAC = 0.66                      # analyze_envelopes.py
COLLECTED_OF_LAND = (0.5, 0.7, 0.9)   # gig/reward scheme, ASSUMPTION
REFLY_PROB = (0.0, 0.10, 0.30)        # passes inspection for a second flight, ASSUMPTION
INSPECT_EUR = (150, 80, 40)           # per returned envelope (dear, mode, cheap) ASSUMPTION
RESIN_EUR_KG = (0.05, 0.25, 0.45)     # clean mono-PE film scrap; multilayer ~0, ASSUMPTION
FITTING_REUSE = (0.3, 0.6, 0.8)       # fittings/plates reusable after return, ASSUMPTION


def recovery_credit(env_cost, env_kg, fittings_eur, k):
  coll = LAND_FRAC * COLLECTED_OF_LAND[k]
  refly = REFLY_PROB[k]
  credit_refly = coll * refly * (env_cost - INSPECT_EUR[k])
  credit_resin = coll * (1 - refly) * env_kg * RESIN_EUR_KG[k]
  credit_fit = coll * (1 - refly) * FITTING_REUSE[k] * fittings_eur * 0.7   # 30 % refurb
  return credit_refly + credit_resin + credit_fit, coll


# ----------------------------------------------------------------------------
# Report
# ----------------------------------------------------------------------------
def eur(x):
  return f'€{x:,.0f}'


def rng(t):
  lo, mid, hi = sorted(t)
  return f'{eur(mid)} ({eur(lo)}–{eur(hi)})'


def main():
  lines = []
  a = lines.append

  # --- Part 1: calibration -----------------------------------------------
  ble = size_envelope(BLE_DESIGN, BLE_PAYLOAD_KG)
  ble3mil = size_envelope(replace(BLE_DESIGN, film_gauge_um=76.2), BLE_PAYLOAD_KG)
  ble25 = size_envelope(replace(BLE_DESIGN, film_gauge_um=63.5), BLE_PAYLOAD_KG)
  ble_he = size_envelope(replace(BLE_DESIGN, gas='He'), BLE_PAYLOAD_KG)
  a('# Envelope cost: physics-based mass model and bottom-up cost\n')
  a('*Generated by `envelope_cost.py`. EUR 2025-26. Ranges are (low–high) over the low/mode/high '
    'parameter sets; the central value is the mode set. All non-physics inputs are tagged ASSUMPTION '
    'or SOURCE in the script.*\n')
  a('## 1. Mass model and calibration\n')
  a(f'Lift balance at the design ceiling {BLE_DESIGN.p_ceiling_hpa:.0f} hPa, {T_STRAT_K:.0f} K, hydrogen: '
    f'ρ_air = {rho(6000, T_STRAT_K, M_AIR):.4f} kg/m³, ρ_H₂ = {rho(6000 + BLE_DP_MAX_PA, T_STRAT_K, M_H2):.4f} kg/m³, '
    f'net {rho(6000, T_STRAT_K, M_AIR) - rho(6000 + BLE_DP_MAX_PA, T_STRAT_K, M_H2):.4f} kg/m³ '
    f'(vs helium {rho(6000, T_STRAT_K, M_AIR) - rho(6000 + BLE_DP_MAX_PA, T_STRAT_K, M_HE):.4f}).')
  a(f'The BLE balloon (1,804 m³, 6,830 mol gas, 68.5 + 92.5 kg) only closes at a ceiling of about '
    f'60 hPa with 5 % spare lift: 6,830 mol at 60 hPa/215 K occupy {BLE_GAS_MOL * R_GAS * T_STRAT_K / 6000:,.0f} m³. '
    f'At 50 hPa the same volume lifts {1804 * (rho(5000, T_STRAT_K, M_AIR) - rho(5000, T_STRAT_K, M_H2)):.0f} kg '
    f'net, less than the 161 kg system, so the BLE float band "50–140 hPa" is reached by pumping air '
    f'in (lower) and only approaches 50 hPa with a lighter system. The model therefore sizes for a 60 hPa ceiling '
    f'(**ASSUMPTION**, the single most important sizing choice; a 80 hPa ceiling gives a 25 % smaller envelope).\n')
  a('**Calibration to BLE (92.5 kg payload, Δp_max 2,380 Pa):**\n')
  a('| Film gauge | Film | Ballonet | Tendons | Fittings | Envelope | Volume | Gores | Film stress |')
  a('|---|---|---|---|---|---|---|---|---|')
  for lab, s in ((f'{BLE_GAUGE_UM:.1f} µm ({BLE_GAUGE_UM / 25.4:.2f} mil), calibrated', ble),
                 ('63.5 µm (2.5 mil)', ble25), ('76.2 µm (3 mil, reported)', ble3mil),
                 (f'{BLE_GAUGE_UM:.1f} µm, helium', ble_he)):
    a(f'| {lab} | {s["film_kg"]:.1f} kg | {s["ballonet_kg"]:.1f} kg | {s["tendon_kg"]:.1f} kg | '
      f'{s["fitting_kg"]:.1f} kg | **{s["envelope_kg"]:.1f} kg** | {s["volume_m3"]:,.0f} m³ | '
      f'{s["n_gores"]} | {s["film_stress_mpa"]:.1f} MPa (allow {s["sigma_allow_mpa"]:.1f}) |')
  a('')
  a(f'How it was calibrated: the only free knob is the film gauge, solved by bisection so that the BLE design '
    f'(Δp_max 2,380 Pa, SF 2.5 on cold yield 28 MPa for a 100+ day creep life, tendons at SF 2.0 on the '
    f'2,380 Pa limit) gives exactly 68.5 kg at 92.5 kg payload: {BLE_GAUGE_UM:.1f} µm ({BLE_GAUGE_UM / 25.4:.2f} mil). '
    f'With the reported "3 mil" Loon film the same model gives {ble3mil["envelope_kg"]:.0f} kg and 2.5 mil gives '
    f'{ble25["envelope_kg"]:.0f} kg, so the reported gauge over-predicts BLE\'s mass by 10–30 %, which is the '
    f'honest accuracy of the model. The volume comes out at {ble["volume_m3"]:,.0f} m³ vs BLE\'s 1,804 '
    f'({100 * (ble["volume_m3"] / BLE_VOLUME_M3 - 1):+.0f} %, the 5 % lift margin). Other fixed choices: '
    f'2,380 Pa limit, a 1.10 pumpkin area factor, a 15 µm ballonet of 0.35 V, and 1.5 kg + 20 g/gore of '
    f'fittings. The split (film {100 * ble["film_kg"] / ble["envelope_kg"]:.0f} %, tendons '
    f'{100 * ble["tendon_kg"] / ble["envelope_kg"]:.0f} %, ballonet {100 * ble["ballonet_kg"] / ble["envelope_kg"]:.0f} %, '
    f'fittings {100 * ble["fitting_kg"] / ble["envelope_kg"]:.0f} %) is a modelling result, not a Loon datum. '
    f'The "3 mil" figure is a secondary source and BLE\'s 1,804 m³ is ~1.5× the volume implied by stratocat\'s '
    f'15 m × 9 m float dimensions, so a 10–30 % gap is within the data.\n')
  a(f'Pumpkin film stress: σ = Δp·r_lobe/t with r_lobe = {ble["lobe_r_m"]:.2f} m ({ble["n_gores"]} gores of '
    f'{2 * math.pi * ble["radius_m"] / ble["n_gores"]:.2f} m); the film carries only the lobe hoop load, the tendons '
    f'carry Δp·πR² = {BLE_DP_MAX_PA * math.pi * ble["radius_m"] ** 2 / 1e3:.0f} kN. A plain sphere of the same '
    f'volume at 2,380 Pa would need t = Δp·R/(2σ) = '
    f'{BLE_DP_MAX_PA * ble["radius_m"] / (2 * ble["sigma_allow_mpa"] * 1e6) * 1e6:.0f} µm of LLDPE, i.e. '
    f'{"infeasible (film mass per m³ exceeds the net lift)" if size_envelope(replace(BLE_DESIGN, kind="sphere"), BLE_PAYLOAD_KG)["infeasible"] else "feasible"}: a sphere\'s '
    f'film mass per m³ is 3Δp·ρ/(2σ), independent of size, so an LLDPE sphere only works at low Δp or with a '
    f'much stronger film.\n')

  # --- envelope mass vs payload ------------------------------------------
  payloads = np.arange(20, 101, 5)
  designs = [BLE_DESIGN, SP_4D, SP_4D_NOCTRL, SPHERE_LLDPE, SPHERE_PET, ZP_4D]
  mass_tab = {d.name: [size_envelope(d, m) for m in payloads] for d in designs}
  a('### Envelope mass vs payload mass (kg envelope, 60 hPa ceiling, hydrogen)\n')
  a('| Payload | ' + ' | '.join(d.name for d in designs) + ' |')
  a('|---|' + '---|' * len(designs))
  for i, m in enumerate(payloads):
    if m in (20, 30, 40, 55, 70, 92.5, 100) or m == 90:
      a(f'| {m:.0f} kg | ' + ' | '.join(
          f'{mass_tab[d.name][i]["envelope_kg"]:.1f} ({mass_tab[d.name][i]["volume_m3"]:,.0f} m³'
          + (f', +{mass_tab[d.name][i]["ballast_kg"]:.0f} kg ballast' if d.kind == 'zp' else '') + ')'
          for d in designs) + ' |')
  a('')
  s40 = {d.name: size_envelope(d, 40) for d in designs}
  a('At 40 kg payload: ' + '; '.join(
      f'{n}: {s["envelope_kg"]:.1f} kg, {s["film_area_m2"]:.0f} m² film at {s["gauge_um"]:.0f} µm, '
      f'{s["n_gores"]} gores, {s["seam_m"]:.0f} m of seams' for n, s in s40.items()) + '.\n')
  a('Notes: the 4-day pumpkin uses Δp 1,000 Pa (enough for a ~20 K supertemperature at 60 hPa plus '
    'control margin), film at the 25 µm handling floor with SF 1.5, tendons SF 1.5. Removing the ballonet '
    '(no altitude control) saves ~2–3 kg but the drift study shows passive balloons dwell 3.2 d instead of 5.4 d '
    '(×1.69 launches), which costs far more than the film. The LLDPE sphere at 700 Pa is stress-limited to '
    f'{s40[SPHERE_LLDPE.name]["gauge_um"]:.0f} µm film and is heavier than the pumpkin; a PET-laminate sphere '
    '(GHOST-balloon heritage, 100 MPa film, SF 2.5) is the lightest pressurised option but PET at −70 °C is '
    'crease- and pinhole-sensitive, is not heat-sealable (needs adhesive tape seams) and has no modern '
    'long-duration track record: an R&D option, not a baseline. The zero-pressure balloon is the lightest '
    'envelope but needs ~7.5 % of gross mass in ballast per night (5–10 %): 4 nights at 45–55°N costs '
    f'{s40[ZP_4D.name]["ballast_kg"]:.0f} kg of ballast on a 40 kg payload, and the balloon has no altitude '
    'steering (vent/ballast only), so launches ×1.69. Beyond ~8–10 nights a ZP balloon cannot carry its own ballast.\n')

  # ZP days feasible
  a('Zero-pressure endurance at 45–55°N (ballast = fraction b of gross per night; gross grows as 1/(1 − N·b)):\n')
  a('| Ballast/night | 2 nights | 4 nights | 6 nights | 8 nights | 10 nights |')
  a('|---|---|---|---|---|---|')
  for b in ZP_BALLAST_FRAC_PER_NIGHT:
    row = []
    for N in (2, 4, 6, 8, 10):
      if N * b >= 0.95:
        row.append('impossible')
      else:
        s = size_envelope(replace(ZP_4D, ballast_days=N, ballast_frac_night=b), 40)
        row.append(f'env {s["envelope_kg"]:.0f} kg + ballast {s["ballast_kg"]:.0f} kg, {s["volume_m3"]:,.0f} m³')
    a(f'| {100 * b:.1f} % | ' + ' | '.join(row) + ' |')
  a('')

  # --- Part 2: cost --------------------------------------------------------
  a('## 2. Bottom-up cost per envelope\n')
  c_today = [cost_envelope(ble, TODAY, k) for k in range(3)]
  c_vol_ble = [cost_envelope(ble, VOLUME, k) for k in range(3)]
  s4_40 = size_envelope(SP_4D, 40)
  c_vol_4d_40 = [cost_envelope(s4_40, VOLUME, k) for k in range(3)]
  a('Today = Loon/Aerostar-era volume (~10³/yr, manual table assembly). Volume = ~400k/yr dedicated line '
    '(blown-film line, automated gore cutting, continuous sealing, inline leak/pinhole inspection).\n')
  a('| Line | Today, BLE design 92.5 kg | Volume, BLE design 92.5 kg | Volume, 4-day pumpkin, 40 kg |')
  a('|---|---|---|---|')
  for key in ('film', 'ballonet', 'tendon', 'fittings', 'seams', 'labour', 'qa', 'packaging', 'scrap',
              'capex', 'margin', 'total'):
    a(f'| {key} | {rng([c[key] for c in c_today])} | {rng([c[key] for c in c_vol_ble])} | '
      f'{rng([c[key] for c in c_vol_4d_40])} |')
  a('')
  a(f'The bottom-up "today" figure {rng([c["total"] for c in c_today])} is somewhat above cost_model.py\'s '
    f'tri(€4k, €10k, €25k) at the mode but the ranges overlap, so the two agree on where we are to within the '
    f'uncertainty of hand-built balloon pricing. Cost per kg: today '
    f'{c_today[1]["total"] / ble["envelope_kg"]:.0f} €/kg, volume BLE design '
    f'{c_vol_ble[1]["total"] / ble["envelope_kg"]:.0f} €/kg, volume 4-day design '
    f'{c_vol_4d_40[1]["total"] / s4_40["envelope_kg"]:.0f} €/kg (a latex weather balloon retails at ~€50–100/kg).\n')
  # learning curve cross-check
  a('Learning-curve cross-check (Wright\'s law on the non-material part of today\'s cost, from a cumulative '
    '~5,000 Loon-era envelopes to 400k/yr):\n')
  a('| Learning rate | Cumulative 400k | Cumulative 2 M (5 yr) |')
  a('|---|---|---|')
  mat_today = c_today[1]['film'] + c_today[1]['tendon'] + c_today[1]['ballonet']
  non_mat = c_today[1]['total'] - mat_today
  for lr in (0.80, 0.85, 0.90):
    a(f'| {100 * lr:.0f} % | {eur(mat_today * 0.4 + wright(non_mat, 5000, 400e3, lr))} | '
      f'{eur(mat_today * 0.4 + wright(non_mat, 5000, 2e6, lr))} |')
  a(f'\n(material taken at 40 % of today\'s unit price at volume). The bottom-up volume estimate for the same '
    f'design, {rng([c["total"] for c in c_vol_ble])}, sits inside the 80–90 % band, so the two methods are '
    f'consistent; cost_reduction.py\'s L1 band (€2.5–7k, mode €4k) is the conservative end.\n')
  a('Sources and anchors: NASA SPB 38 µm coextruded LLDPE + PBO tendons (NTRS 20180007750, ICRC 2005); '
    'Raven StratoFilm-430 10–20 µm three-layer LLDPE (Raven 2002); Loon film "3 mil" PE by Raven Aerostar '
    '(secondary); Aerostar 2023 deck "HAB cost per asset ~$50–500k", tactical PE balloons "a few thousand '
    'dollars"; World View "hundreds of thousands vs $2–3 M for NASA" ZP missions (MIT Tech Review 2017); '
    'LLDPE Europe €0.8–2.1/kg and mLLDPE ~$2.0–2.4/kg in 2026 (Procurement Resource, Polymerupdate, '
    'BusinessAnalytiq); 1.2 kg latex weather balloon $129 retail (High Altitude Science). Everything per line '
    'in the cost table (seam €/m, labour hours, QA, scrap, capex, margin, tendon €/kg, fittings) is ASSUMPTION.\n')

  # --- Part 3: levers -------------------------------------------------------
  a('## 3. Levers\n')
  base_cost = TODAY_ENVELOPE_EUR
  # ratios from the bottom-up model, applied to today's €10k mode
  def tot(sz, cp, k=1, **kw):
    return cost_envelope(sz, cp, k, **kw)['total']

  levers = []  # (label, (lo, mid, hi) cost after lever alone, reference cost, launch multiplier)
  # a) lighter payload (same design, today's volume)
  for m in (55, 40, 30):
    s = size_envelope(BLE_DESIGN, m)
    levers.append((f'(a) payload {m} kg, same design, today\'s volume',
                   tuple(base_cost * tot(s, TODAY, k) / tot(ble, TODAY, k) for k in range(3)), base_cost, 1.0))
  # b) thinner film / lower SF / lower dp at 92.5 kg, today's volume
  sb = size_envelope(replace(SP_4D, name='x'), BLE_PAYLOAD_KG)
  levers.append(('(b) 4-day film (25 µm, SF 1.5) + Δp 1,000 Pa, 92.5 kg, today\'s volume',
                 tuple(base_cost * tot(sb, TODAY, k) / tot(ble, TODAY, k) for k in range(3)), base_cost, 1.0))
  sb2 = size_envelope(replace(BLE_DESIGN, film_gauge_um=38.0), BLE_PAYLOAD_KG)
  levers.append(('(b′) NASA-gauge 38 µm film only (Δp and SF unchanged), 92.5 kg',
                 tuple(base_cost * tot(sb2, TODAY, k) / tot(ble, TODAY, k) for k in range(3)), base_cost, 1.0))
  # c) design choice at 40 kg, volume
  s40_pump = size_envelope(SP_4D, 40)
  ref4 = tot(s40_pump, VOLUME, 1)
  for d in (SP_4D_NOCTRL, SPHERE_LLDPE, SPHERE_PET, ZP_4D):
    s = size_envelope(d, 40)
    mult = PASSIVE_DWELL_FACTOR if (d.kind == 'zp' or not d.ballonet) else 1.0
    levers.append((f'(c) {d.name} vs 4-day pumpkin, 40 kg, volume',
                   tuple(tot(s, VOLUME, k, design_kind=d.kind) for k in range(3)), ref4, mult))
  # d) volume manufacturing, BLE design
  levers.append(('(d) 400k/yr automated line, BLE design 92.5 kg',
                 tuple(tot(ble, VOLUME, k) for k in range(3)), base_cost, 1.0))
  # f) recovery credit on the 4-day 40 kg volume envelope
  c4 = [cost_envelope(s40_pump, VOLUME, k) for k in range(3)]
  cred = [recovery_credit(c4[k]['total'], s40_pump['envelope_kg'], c4[k]['fittings'], k) for k in range(3)]
  levers.append(('(f) recovery credit (refly/resin/fittings) on the 4-day 40 kg volume envelope',
                 tuple(c4[k]['total'] - cred[k][0] for k in range(3)), ref4, 1.0))
  # g) ceiling 80 hPa
  s80 = size_envelope(replace(SP_4D, p_ceiling_hpa=80), 40)
  levers.append(('(g) ceiling 80 hPa instead of 60 (smaller volume), 4-day 40 kg, volume',
                 tuple(tot(s80, VOLUME, k) for k in range(3)), ref4, 1.0))
  s_wide = size_envelope(replace(SP_4D, film_gauge_um=40.0), 40)
  levers.append(('(g) 40 µm film, fewer/wider gores (standard 1.8 m roll), 4-day 40 kg, volume',
                 tuple(tot(s_wide, VOLUME, k) for k in range(3)), ref4, 1.0))
  # g) standard 1.8 m gores — already in the model as max gore width; show lobe-limited vs roll-limited
  a('Each lever alone. Rows (a), (b), (d) are ratios from the bottom-up model applied to today\'s €10,000 mode '
    f'(reference €10,000); rows (c), (f), (g) are absolute bottom-up volume costs for a 40 kg payload, referenced '
    f'to the 4-day pumpkin at volume ({eur(ref4)}). €/Europe-day = cost × launch multiplier ÷ 3.7 d; designs '
    'without altitude control (no ballonet, zero-pressure) carry ×1.69 launches.\n')
  a('| Lever | Envelope cost | vs reference | Launches × | €/Europe-day |')
  a('|---|---|---|---|---|')
  for lab, t, ref, mult in levers:
    a(f'| {lab} | {rng(t)} | {100 * (sorted(t)[1] / ref - 1):+.0f} % | {mult:.2f} | '
      f'{eur(sorted(t)[1] * mult / EUROPE_DAYS_PER_LAUNCH)} |')
  a('')
  a(f'(f) detail: {LAND_FRAC:.0%} land × {COLLECTED_OF_LAND[1]:.0%} collected = {cred[1][1]:.0%} of envelopes come '
    f'back; refly probability {REFLY_PROB[1]:.0%} after a €{INSPECT_EUR[1]} inspection, resin €{RESIN_EUR_KG[1]}/kg, '
    f'{FITTING_REUSE[1]:.0%} of fittings reusable: credit {eur(cred[1][0])} ({eur(cred[0][0])}–{eur(cred[2][0])}) '
    f'per envelope, i.e. {100 * cred[1][0] / c4[1]["total"]:.0f} % of a {eur(c4[1]["total"])} envelope. The '
    f'{s40_pump["envelope_kg"]:.0f} kg of resin is worth ~€{s40_pump["envelope_kg"] * RESIN_EUR_KG[1]:.0f}; what '
    'the return scheme really buys is the fittings and litter avoidance, and cost_model.py already charges '
    '€100–1,500 per envelope for pickup, more than any credit here. Pay the gig pickup for debris reasons; do not '
    'count on it for money.\n')

  # Stacked
  a('### Stacked (per envelope, per flight)\n')
  stack = [('Today: cost_model mode, BLE design, 92.5 kg', (4000.0, 10_000.0, 25_000.0))]
  r_vol = [tot(ble, VOLUME, k) / tot(ble, TODAY, k) for k in range(3)]
  cur = tuple(base_cost * r for r in r_vol)
  stack.append(('+ (d) 400k/yr automated manufacturing', tuple(tot(ble, VOLUME, k) for k in range(3))))
  s_40_ble = size_envelope(BLE_DESIGN, 40)
  stack.append(('+ (a) payload 40 kg (30–55)',
                (tot(size_envelope(BLE_DESIGN, 30), VOLUME, 0), tot(s_40_ble, VOLUME, 1),
                 tot(size_envelope(BLE_DESIGN, 55), VOLUME, 2))))
  stack.append(('+ (b) 4-day film/SF and Δp 1,000 Pa',
                (tot(size_envelope(SP_4D, 30), VOLUME, 0), tot(s40_pump, VOLUME, 1),
                 tot(size_envelope(SP_4D, 55), VOLUME, 2))))
  c4s = [cost_envelope(size_envelope(SP_4D, m), VOLUME, k) for k, m in ((0, 30), (1, 40), (2, 55))]
  creds = [recovery_credit(c4s[k]['total'], size_envelope(SP_4D, m)['envelope_kg'], c4s[k]['fittings'], k)[0]
           for k, m in ((0, 30), (1, 40), (2, 55))]
  stack.append(('+ (f) recovery credit', tuple(c4s[k]['total'] - creds[k] for k in range(3))))
  s80s = [size_envelope(replace(SP_4D, p_ceiling_hpa=80), m) for m in (30, 40, 55)]
  c80 = [cost_envelope(s80s[k], VOLUME, k) for k in range(3)]
  cr80 = [recovery_credit(c80[k]['total'], s80s[k]['envelope_kg'], c80[k]['fittings'], k)[0] for k in range(3)]
  stack.append(('+ (g) ceiling 80 hPa (optional, needs re-simulation)', tuple(c80[k]['total'] - cr80[k] for k in range(3))))
  a('| Step | Envelope €/flight | €/Europe-day (÷3.7 d) |')
  a('|---|---|---|')
  for lab, t in stack:
    a(f'| {lab} | {rng(t)} | {rng(tuple(x / EUROPE_DAYS_PER_LAUNCH for x in t))} |')
  a('')
  final = stack[-2][1]
  a(f'Best realistic stack (without the 80 hPa option): **{rng(final)} per envelope, '
    f'{rng(tuple(x / EUROPE_DAYS_PER_LAUNCH for x in final))} per Europe-day**, against €10,000 and €2,700 today: '
    f'a ×{base_cost / sorted(final)[1]:.0f} reduction (×{base_cost / sorted(final)[2]:.0f}–×{base_cost / sorted(final)[0]:.0f}). '
    f'The ballonet is kept: it is the altitude control that the whole dwell result depends on.\n')
  # what dominates residual
  c_mid = cost_envelope(s40_pump, VOLUME, 1)
  order = sorted(((k, v) for k, v in c_mid.items() if k != 'total'), key=lambda kv: -kv[1])
  a('Residual cost breakdown of the mode 4-day 40 kg envelope: ' +
    ', '.join(f'{k} {eur(v)} ({100 * v / c_mid["total"]:.0f} %)' for k, v in order) + '. ')
  a(f'Film is only {100 * c_mid["film"] / c_mid["total"]:.0f} %: the residual is dominated by the things that '
    'scale with the number of parts and operations — fittings, seams × gores, labour, QA — plus margin and scrap. '
    'That is why gore count (lobe radius) and fitting design matter more than film price from here on.\n')

  # --- e) life design ------------------------------------------------------
  a('### (e) Designing for envelope life: 4 vs 30/60/100 days, cost per Europe-day\n')
  a('Longer life = higher creep SF on the film, UV/ozone allowance, tendon SF 2.0, tighter QA (×1.5–3) and '
    'more scrap (+2–8 pp). Launch multipliers from the multi-pass study: free routing ×0.62/0.49/0.42, '
    'China-avoidance without propulsion ×0.77/0.68/0.62. Europe-days per launch = 3.7 ÷ multiplier.\n')
  a('| Design life | Envelope kg (40 kg payload) | Film µm | €/envelope (volume) | €/Europe-day, free routing | '
    '€/Europe-day, avoid China |')
  a('|---|---|---|---|---|---|')
  life_rows = {}
  for days in (4, 30, 60, 100):
    d = life_design(days)
    s = size_envelope(d, 40)
    qa_mult = {4: 1.0, 30: 1.5, 60: 2.0, 100: 3.0}[days]
    scrap_add = {4: 0.0, 30: 0.02, 60: 0.05, 100: 0.08}[days]
    costs = tuple(tot(s, VOLUME, k, qa_mult=qa_mult, scrap_add=scrap_add) for k in range(3))
    mf, mc = MULTIPASS[days]
    ed_free = tuple(c * mf / EUROPE_DAYS_PER_LAUNCH for c in costs)
    ed_china = tuple(c * mc / EUROPE_DAYS_PER_LAUNCH for c in costs)
    life_rows[days] = (costs, ed_free, ed_china, s)
    a(f'| {days} d | {s["envelope_kg"]:.1f} | {s["gauge_um"]:.0f} | {rng(costs)} | {rng(ed_free)} | {rng(ed_china)} |')
  a('')
  a(f'A 100-day envelope costs about ×{sorted(life_rows[100][0])[1] / sorted(life_rows[4][0])[1]:.2f} a 4-day one '
    f'but is launched ×0.42 as often, so per Europe-day it is ×'
    f'{sorted(life_rows[100][1])[1] / sorted(life_rows[4][1])[1]:.2f} (free routing) or ×'
    f'{sorted(life_rows[100][2])[1] / sorted(life_rows[4][2])[1]:.2f} (China avoided). The envelope line therefore '
    'favours long-life designs mildly; the real argument for long flights is the payload/launch lines, which also '
    'scale with launches, and against it the payload recovery rate (multipass: 60 % recovered at 30 d, 32 % at 100 d) '
    'and the ~22 % of time over Russia/C. Asia/China. For the envelope alone, a 30-day design is the sweet spot: '
    f'{rng(life_rows[30][1])} per Europe-day vs {rng(life_rows[4][1])} for 4-day.\n')

  # --- Part 4: recommendation ---------------------------------------------
  a('## 4. Recommendation\n')
  s30 = life_rows[30][3]
  a(f'* **Target design:** superpressure pumpkin, hydrogen, 60 hPa ceiling, Δp_max ~1,000 Pa (not 2,380), '
    f'25–30 µm coextruded mLLDPE film at the handling floor, ~{s30["n_gores"]} gores of ~'
    f'{2 * math.pi * s30["radius_m"] / s30["n_gores"]:.2f} m (lobe radius {s30["lobe_r_m"]:.2f} m), UHMWPE tendons '
    f'(~{s30["tendon_kg"]:.1f} kg), 15 µm ballonet, moulded polymer end fittings, designed for 30 days (SF 1.9, 5 % UV '
    f'allowance). Envelope {s30["envelope_kg"]:.0f} kg for a 40 kg payload ({s30["volume_m3"]:,.0f} m³, '
    f'{s30["film_area_m2"]:.0f} m² of film). If the fleet stays one-way (3.7 d), the 4-day variant '
    f'({life_rows[4][3]["envelope_kg"]:.0f} kg) is marginally cheaper per envelope and the choice is driven by the '
    f'payload lines, not the envelope.')
  a(f'* **Cost:** {rng(life_rows[30][0])} per envelope at 400k/yr-class volume; '
    f'{rng(life_rows[30][1])} per Europe-day with free routing ({rng(life_rows[30][2])} if China must be avoided); '
    f'the 4-day one-way variant {rng(life_rows[4][0])} per envelope, {rng(life_rows[4][1])} per Europe-day. '
    f'Today\'s €10k mode is €2,700 per Europe-day.')
  a(f'* **Best realistic stack vs €10k:** volume manufacturing (×{r_vol[1]:.2f}) → lighter payload '
    f'(×{tot(s_40_ble, VOLUME, 1) / tot(ble, VOLUME, 1):.2f}) → low-Δp thin-film design '
    f'(×{tot(s40_pump, VOLUME, 1) / tot(s_40_ble, VOLUME, 1):.2f}) → recovery credit '
    f'(×{(c4[1]["total"] - cred[1][0]) / c4[1]["total"]:.2f}): {rng(final)}. Roughly ×8 in cost, '
    'of which volume is ×3, mass (payload + design) ×2.5, recovery ×0.9. In the fleet model (envelopes 33 % of '
    f'€38.7k) that is about −€11k per flight at the mode, ~−28 % of the all-in cost before overhead.')
  a('* **What dominates the residual:** fittings + per-gore terminations, seam metres (gores × meridian × 2), '
    'labour and QA — the "number of parts" costs — then margin and scrap; film resin is <10 %. Reducing gore count '
    '(larger lobe radius means thicker film: the trade is 25 µm/many gores vs 40 µm/fewer gores — roughly neutral '
    'on cost in this model), moulded one-piece end fittings, and continuous tendon-sleeve sealing are the next '
    'engineering targets. Reusing fittings from returned envelopes is worth more than the resin.')
  a('* **Biggest uncertainties:** (1) the design ceiling (60 vs 80 hPa changes volume by 25 %, and whether the '
    'drift results hold at a lower ceiling needs re-simulation); (2) whether 25–30 µm LLDPE holds 1,000 Pa for '
    '4–30 days without pinhole leaks at 400k units/yr quality (Loon\'s leak history says QA, folding and handling '
    'dominate, not film strength); (3) the cold-film allowable (25–35 MPa band) and creep SF; (4) the supplier '
    'margin/capex at 400k/yr, which no balloon maker has ever reached (Aerostar makes ~10³/yr); (5) tendon price; '
    '(6) the per-gore fitting and seam costs, which carry most of the residual.')
  a('* **Things in `cost_model.py` / `combined_cost.py` that look wrong or inconsistent:** `ENVELOPE_EUR` '
    'tri(4k,10k,25k) is a Loon-era low-volume price applied to a 400k/yr fleet (the baseline is internally '
    'inconsistent: that volume would itself bring the price down ~×3); `ENVELOPE_KG` is fixed at 68.5 regardless of '
    'payload mass, float band or flight life; cost_reduction.py\'s material floor "€10–30/kg film" is ~×3 too high '
    '(resin €1–2.4/kg, converted specialty film €3–9/kg); `combined_cost.py` scales envelope mass ∝ payload (0.74 kg/kg) '
    f'but film scales ∝ lift^(2/3) and only tendons ∝ lift, so a 40 kg payload with the same film gauge and Δp gives '
    f'{s_40_ble["envelope_kg"]:.0f} kg (ratio {s_40_ble["envelope_kg"] / 40:.2f}) not {0.74 * 40:.0f} kg — the '
    'lighter-hardware saving on the envelope is smaller than combined_cost.py assumes unless the design is changed too; the L2 envelope-reuse credit is costed as '
    'if 15 % of envelopes could be refurbished at 20–50 % of new cost, which for a thin-film consumable is a 0–30 % '
    'refly probability minus an inspection cost (net credit a few % of a €1–2k envelope); `ENVELOPE_RECOVERY_EUR` '
    '€100–1,500 is charged on sea landings too and will exceed the envelope cost itself once envelopes are ~€1k, '
    'so the pickup/reward scheme should be budgeted as a litter-liability line, not against envelope cost; and '
    'the BLE float band 50–140 hPa is not reachable by the BLE mass at 50 hPa with hydrogen (see §1).')
  a('')
  a('![envelope cost](envelope_cost.png)\n')
  a('## Assumption register (beyond the tags in the script)\n')
  a('* Stratosphere 215 K at the ceiling; ceiling 60 hPa; 5 % spare lift.')
  a('* LLDPE cold yield 28 MPa (band 25–35), density 920; film floor 25 µm (SP) / 20 µm (ZP); ballonet 15 µm, 0.35 V.')
  a('* Pumpkin area ×1.10 vs sphere, natural-shape ZP ×1.18, seams/caps ×1.06, gore width 1.6 × lobe radius, roll width 1.8 m.')
  a('* UHMWPE tendon 3.0 GPa, 970 kg/m³, braid/termination efficiency 0.6, SF 1.5–2.0 on Δp_max.')
  a('* ZP ballast 5–10 % of gross per night, 3 kg ballast hardware; ZP has no altitude steering → launches ×1.69 (README passive vs slow dwell).')
  a('* Cost parameter sets TODAY and VOLUME as listed in the script (film €/kg, tendon €/kg, fittings, seam €/m, labour, QA, packaging, scrap, capex, margin).')
  a('* Recovery: 66 % land (measured), 50–90 % collected, 0–30 % refly, inspection €40–150, resin €0.05–0.45/kg, fittings 30–80 % reusable at 70 % value.')
  a('* Life design: SF 1.5/1.9/2.2/2.5 and UV allowance 0/5/8/10 % for 4/30/60/100 days; QA ×1/1.5/2/3; scrap +0/2/5/8 pp.')

  os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
  with open(OUT_MD, 'w') as f:
    f.write('\n'.join(lines) + '\n')

  # --- figure --------------------------------------------------------------
  fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.5, 6))
  colors = ['#4C72B0', '#DD8452', '#55A868', '#C44E52', '#8172B3', '#937860']
  for d, col in zip(designs, colors):
    lo = [tot(size_envelope(d, m), VOLUME, 0, design_kind=d.kind) for m in payloads]
    mid = [tot(size_envelope(d, m), VOLUME, 1, design_kind=d.kind) for m in payloads]
    hi = [tot(size_envelope(d, m), VOLUME, 2, design_kind=d.kind) for m in payloads]
    ax1.plot(payloads, mid, color=col, label=d.name, lw=2)
    ax1.fill_between(payloads, lo, hi, color=col, alpha=0.12)
  today_mid = [base_cost * tot(size_envelope(BLE_DESIGN, m), TODAY, 1) / tot(ble, TODAY, 1) for m in payloads]
  ax1.plot(payloads, today_mid, color='k', ls='--', lw=1.5, label="BLE design at today's volume (scaled from €10k)")
  ax1.set_yscale('log')
  ax1.set_xlabel('Payload mass (kg)')
  ax1.set_ylabel('Envelope cost (€, log)')
  ax1.set_title('(a) Envelope cost vs payload, 400k/yr volume (bands: low–high parameter sets)')
  ax1.grid(True, which='both', alpha=0.3)
  ax1.legend(fontsize=7.5, loc='lower right')
  # waterfall
  labels = ['Today\n(cost_model mode)', '(d) volume\nmanufacturing', '(a) payload\n40 kg', '(b) 4-day film,\nΔp 1,000 Pa',
            '(f) recovery\ncredit', '(e) 30-day life\nper Europe-day\n(×0.62 launches)']
  vals = [base_cost, sorted(stack[1][1])[1], sorted(stack[2][1])[1], sorted(stack[3][1])[1], sorted(stack[4][1])[1]]
  per_ed_4 = sorted(stack[4][1])[1] / EUROPE_DAYS_PER_LAUNCH
  per_ed_30 = sorted(life_rows[30][1])[1]
  x = np.arange(len(labels))
  prev = vals[0]
  ax2.bar(0, vals[0], color='#999999')
  ax2.text(0, vals[0] * 1.05, eur(vals[0]), ha='center', fontsize=8)
  for i in range(1, len(vals)):
    ax2.bar(i, prev - vals[i], bottom=vals[i], color='#55A868')
    ax2.text(i, prev * 1.05, f'−{eur(prev - vals[i])}', ha='center', fontsize=8)
    prev = vals[i]
  ax2.bar(len(vals) - 1 + 0.0, 0)  # spacer no-op
  ax2.bar(len(vals), vals[-1], color='#4C72B0')
  ax2.text(len(vals), vals[-1] * 1.5, f'{eur(vals[-1])}/envelope\n{eur(per_ed_4)}/Europe-day', ha='center', fontsize=7.5)
  ax2.bar(len(vals) + 1, per_ed_30 * EUROPE_DAYS_PER_LAUNCH, color='#DD8452')
  ax2.text(len(vals) + 1, per_ed_30 * EUROPE_DAYS_PER_LAUNCH * 0.45,
           f'{eur(per_ed_30)}/Europe-day\n(×3.7 d shown)', ha='center', fontsize=7.5, color='white')
  ax2.set_xticks(list(x[:len(vals)]) + [len(vals), len(vals) + 1])
  ax2.set_xticklabels(labels[:len(vals)] + ['Stack\n(4-day)', labels[-1]], fontsize=7)
  ax2.set_yscale('log')
  ax2.set_ylim(100, 3e4)
  ax2.set_ylabel('€ per envelope (log)')
  ax2.set_title('(b) Lever waterfall, mode values')
  ax2.grid(True, axis='y', which='both', alpha=0.3)
  fig.tight_layout()
  fig.savefig(OUT_PNG, dpi=130)
  print('\n'.join(lines))
  print(f'\nwrote {OUT_MD} and {OUT_PNG}')


if __name__ == '__main__':
  main()

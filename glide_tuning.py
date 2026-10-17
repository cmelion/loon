"""Tune the radio-return glider: guidance law, release policy, robustness,
design point.

Inputs: results/slow_tracks.csv (hourly balloon tracks of the 'slow'
controller flights, from track_slow.py) and the GFS wind grid.

1. Guidance: point-at-target ('direct', today's simulate_glide) vs crab
   (hold the great-circle track) vs crab + speed-to-fly.
2. Release policy: at every flight-hour simulate the glide to every
   recovery site within RANGE_KM and record the arrival margin
   (arrival altitude x L/D in km, or -miss). Policies:
     fixed150   today's rule: last hour within 150 km of a site.
     last-M     hindsight: last hour at which some site has margin >= M
                (max time over Europe subject to a safe return).
     causalH-M  release when a site is reachable with margin >= M now and
                none is forecast reachable in the next H hours (the balloon
                flies on forecast winds, so an H h lookahead is on board).
3. Robustness Monte Carlo on each release: wind bias U(0,5) m/s in a random
   direction + AR(1) gust noise (1 m/s, 15 min) + surface taper U(0.1,1.0).
   The release decision uses the nominal (forecast) winds; the glider's
   crab law uses the perturbed (true) wind it measures in flight.
4. Design sweep L/D x wing loading (sink from glider_sizing's relation),
   recovery under the Monte Carlo vs descent time and landing speed.

Outputs: results/glider_tuning_policies.csv, results/glider_tuning_designs.csv,
results/glider_tuning.md, results/glider_tuning.png.
Usage: python glide_tuning.py [--procs 2] [--quick]
"""
import math
import multiprocessing as mp
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glide  # noqa: E402
import glide_batch as gb  # noqa: E402
from europe_ble import WindGrid  # noqa: E402
from run_drift import GLIDE, RECOVERY, RELEASE_KM  # noqa: E402

RANGE_KM = 500.0
MARGINS = [0.0, 10.0, 20.0, 30.0, 50.0, 75.0, 100.0]
MC_K = 40            # Monte Carlo samples per release
BIAS_MAX = 5.0       # m/s, uniform magnitude, random direction
NOISE_SD = 1.0       # m/s AR(1) gust / forecast noise
TAPER_RANGE = (0.1, 1.0)
SITES = list(RECOVERY.items())
SITE_LAT = np.array([v[0] for _, v in SITES])
SITE_LON = np.array([v[1] for _, v in SITES])
BASE = dict(ld=GLIDE['ld'], sink_sl=GLIDE['sink_sl'])      # today's 16 kg/m2
SWEEP_STF = True
SWEEP_GUIDANCE = 'crab+stf' if SWEEP_STF else 'crab'
LDS = [10.0, 12.0, 14.0, 16.0, 18.0]
WLS = [15.0, 20.0, 30.0, 45.0, 60.0]


def wing_loading(sink_sl, ld):
  return 0.5 * gb.RHO_SL * (sink_sl * ld) ** 2 * gb.CL / 9.81


# ----------------------------------------------------------------------------
# Tracks and candidate (hour, site) pairs
# ----------------------------------------------------------------------------
class Tracks:
  def __init__(self, path='results/slow_tracks.csv'):
    df = pd.read_csv(path)
    df = df.sort_values(['flight', 'step']).reset_index(drop=True)
    self.df = df
    self.flights = list(dict.fromkeys(df.flight))
    self.f_idx = {f: np.flatnonzero(df.flight.values == f) for f in self.flights}
    self.dwell = {f: df.h.values[ix[-1]] for f, ix in self.f_idx.items()}
    # distance from each row to each site
    self.dist = gb.haversine_km(df.lat.values[:, None], df.lon.values[:, None],
                                SITE_LAT[None, :], SITE_LON[None, :])
    cand = (self.dist <= RANGE_KM) & (df.step.values[:, None] > 0)
    self.rows, self.sites = np.nonzero(cand)

  def pairs(self):
    df = self.df
    r, s = self.rows, self.sites
    return (df.lat.values[r], df.lon.values[r], df.pa.values[r],
            df.hours.values[r], SITE_LAT[s], SITE_LON[s])


def nominal_margins(bg, tr, design, guidance, stf):
  """Margin (km), duration (s), ground (km) for every candidate pair."""
  lat, lon, pa, hrs, tl, tn = tr.pairs()
  r = gb.glide_batch(bg, lat, lon, pa, hrs, tl, tn, guidance=guidance, stf=stf,
                     **design)
  return r


def margin_matrix(tr, r):
  """Dense (rows x sites) arrays, -inf where not a candidate."""
  n, s = len(tr.df), len(SITES)
  M = np.full((n, s), -np.inf); D = np.full((n, s), np.nan); G = np.full((n, s), np.nan)
  R = np.zeros((n, s), bool)
  M[tr.rows, tr.sites] = r['margin_km']
  D[tr.rows, tr.sites] = r['duration_s']
  G[tr.rows, tr.sites] = r['ground_km']
  R[tr.rows, tr.sites] = r['reached']
  return M, D, G, R


# ----------------------------------------------------------------------------
# Release policies -> one (row, site) per flight (or None)
# ----------------------------------------------------------------------------
def releases(tr, M, policy, m=0.0):
  out = {}
  for f, ix in tr.f_idx.items():
    ix = ix[tr.df.step.values[ix] > 0]
    if len(ix) == 0:
      out[f] = None; continue
    if policy == 'fixed150':
      d = tr.dist[ix]
      near = d.argmin(axis=1)
      ok = d[np.arange(len(ix)), near] <= RELEASE_KM
      if ok.any():
        k = np.flatnonzero(ok)[-1]
        out[f] = (ix[k], near[k])
      else:
        out[f] = None
      continue
    best = M[ix].max(axis=1)
    bsite = M[ix].argmax(axis=1)
    ok = best >= m
    if policy == 'last':
      k = np.flatnonzero(ok)[-1] if ok.any() else (int(best.argmax()) if np.isfinite(best).any() else None)
    elif policy.startswith('causal'):
      # release when reachable now and no site is forecast reachable in the
      # next H hours (balloon flies on forecast winds, so H h lookahead is
      # available on board); hindsight 'last' is the H -> infinity limit.
      H = int(policy[6:])
      k = None
      for j in range(len(ix)):
        if ok[j] and not ok[j + 1:j + 1 + H].any():
          k = j; break
      if k is None and np.isfinite(best).any():
        k = int(best.argmax())
    else:
      raise ValueError(policy)
    out[f] = None if k is None else (ix[k], bsite[k])
  return out


def mc_eval(bg, tr, rel, design, guidance, stf, k=MC_K, seed=0):
  """Monte Carlo outcome of a set of releases. Returns per-flight arrays."""
  fl = [f for f in tr.flights if rel[f] is not None]
  rows = np.array([rel[f][0] for f in fl]); sites = np.array([rel[f][1] for f in fl])
  n = len(fl)
  rng = np.random.default_rng(seed)
  mag = rng.uniform(0, BIAS_MAX, (n, k)); ang = rng.uniform(0, 2 * np.pi, (n, k))
  taper = rng.uniform(*TAPER_RANGE, (n, k))
  df = tr.df
  rep = lambda a: np.repeat(a, k)
  r = gb.glide_batch(bg, rep(df.lat.values[rows]), rep(df.lon.values[rows]),
                     rep(df.pa.values[rows]), rep(df.hours.values[rows]),
                     rep(SITE_LAT[sites]), rep(SITE_LON[sites]),
                     guidance=guidance, stf=stf,
                     bias_u=(mag * np.sin(ang)).ravel(), bias_v=(mag * np.cos(ang)).ravel(),
                     taper=taper.ravel(), noise_sd=NOISE_SD, rng=rng, **design)
  reached = r['reached'].reshape(n, k)
  close = (r['miss_km'] < 5.0).reshape(n, k)
  return dict(flights=fl, reached=reached, close=close,
              duration=r['duration_s'].reshape(n, k), ground=r['ground_km'].reshape(n, k))


def summarise(tr, rel, mats, mc, label):
  M, D, G, R = mats
  nf = len(tr.flights)
  total_h = sum(tr.dwell.values())
  lost, glide_h, dist_rel, ground, nom_rec = [], [], [], [], 0
  for f in tr.flights:
    if rel[f] is None:
      continue
    row, s = rel[f]
    rel_h = tr.df.h.values[row]
    gh = D[row, s] / 3600.0
    lost.append(tr.dwell[f] - rel_h - gh)
    glide_h.append(gh); dist_rel.append(tr.dist[row, s]); ground.append(G[row, s])
    nom_rec += int(R[row, s])
  # MC: population recovery per sample -> P10/P50/P90 over samples
  per_sample = mc['reached'].sum(axis=0) / nf
  per_sample_close = mc['close'].sum(axis=0) / nf
  return dict(label=label, n_release=len(lost), nominal_rec=nom_rec / nf,
              mc_rec=per_sample.mean(), mc_p10=np.percentile(per_sample, 10),
              mc_p90=np.percentile(per_sample, 90), mc_close5km=per_sample_close.mean(),
              lost_h_mean=np.sum(lost) / nf, lost_pct=100 * np.sum(lost) / total_h,
              glide_h_med=np.median(glide_h) if glide_h else np.nan,
              release_dist_med=np.median(dist_rel) if dist_rel else np.nan,
              ground_med=np.median(ground) if ground else np.nan,
              worst_flights=[f for f, p in zip(mc['flights'], mc['reached'].mean(axis=1)) if p < 0.9],
              p_flight=dict(zip(mc['flights'], mc['reached'].mean(axis=1).round(3))))


# ----------------------------------------------------------------------------
# Workers
# ----------------------------------------------------------------------------
_CACHE = {}


TRACKS = os.environ.get('TRACKS', 'results/slow_tracks.csv')
OUT = os.environ.get('OUT', 'results/glider_tuning')


def _setup():
  if 'bg' not in _CACHE:
    _CACHE['bg'] = gb.BatchGrid(WindGrid())
    _CACHE['tr'] = Tracks(TRACKS)
  return _CACHE['bg'], _CACHE['tr']


def eval_design(job):
  """All policies for one (design, guidance, stf). Returns list of summaries."""
  design, guidance, stf, margins, k = job
  bg, tr = _setup()
  t = time.time()
  r = nominal_margins(bg, tr, design, guidance, stf)
  mats = margin_matrix(tr, r)
  out = []
  pol = [('fixed150', 0.0)] + [(p, m) for p in ('last', 'causal24', 'causal72') for m in margins]
  for p, m in pol:
    rel = releases(tr, mats[0], p, m)
    mc = mc_eval(bg, tr, rel, design, guidance, stf, k=k)
    s = summarise(tr, rel, mats, mc, f'{p}-{m:g}' if p != 'fixed150' else p)
    s.update(policy=p, margin=m, ld=design['ld'], sink_sl=design['sink_sl'],
             wing_kg_m2=wing_loading(design['sink_sl'], design['ld']),
             guidance=guidance + ('+stf' if stf else ''))
    out.append(s)
  # reachability ceiling: flights with any positive-margin hour
  anyreach = np.mean([np.isfinite(mats[0][ix]).any() and mats[0][ix].max() >= 0
                      for ix in tr.f_idx.values()])
  for s in out:
    s['ceiling'] = anyreach
  print(f'design ld={design["ld"]} sink={design["sink_sl"]:.2f} {guidance}{"+stf" if stf else ""} '
        f'done in {time.time() - t:.0f}s', flush=True)
  return out


def main():
  procs = int(sys.argv[sys.argv.index('--procs') + 1]) if '--procs' in sys.argv else 2
  quick = '--quick' in sys.argv
  k = 10 if quick else MC_K
  margins = [0.0, 30.0, 75.0] if quick else MARGINS
  t0 = time.time()
  # 1+2+3: guidance laws at today's design, all policies
  jobs = [(BASE, 'direct', False, margins, k), (BASE, 'crab', False, margins, k),
          (BASE, 'crab', True, margins, k)]
  # 4: design sweep with the best guidance (crab + speed-to-fly)
  designs = [dict(ld=ld, sink_sl=gb.sink_for_wing_loading(wl, ld))
             for ld in LDS for wl in WLS]
  if quick:
    designs = designs[::6]
  jobs += [(d, 'crab', SWEEP_STF, margins, k) for d in designs]
  rows = []
  with mp.get_context('spawn').Pool(procs) as pool:
    for res in pool.imap_unordered(eval_design, jobs):
      rows += res
      print(f'  {len(rows)} rows, {time.time() - t0:.0f}s', flush=True)
  df = pd.DataFrame(rows)
  df['worst_flights'] = df.worst_flights.apply(lambda l: ';'.join(l))
  df['p_flight'] = df.p_flight.apply(lambda d: ';'.join(f'{k}={v}' for k, v in d.items()))
  base_mask = (df.ld == BASE['ld']) & (np.isclose(df.sink_sl, BASE['sink_sl']))
  df[base_mask].to_csv(OUT + '_policies.csv', index=False)
  df[(df.guidance == SWEEP_GUIDANCE)].to_csv(OUT + '_designs.csv', index=False)
  print(f'total {time.time() - t0:.0f}s')


if __name__ == '__main__':
  main()

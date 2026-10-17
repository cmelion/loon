"""Report + figure for glide_tuning.py results.

Reads results/glider_tuning_policies.csv (today's design, guidance x policy)
and results/glider_tuning_designs.csv (crab guidance, design x policy), picks
a recommended design/policy, re-runs a larger Monte Carlo on it to classify
the residual failures, and writes results/glider_tuning.md / .png.
"""
import math
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glide_batch as gb  # noqa: E402
import glide_tuning as gt  # noqa: E402
from europe_ble import WindGrid  # noqa: E402

OUT = os.environ.get('OUT', 'results/glider_tuning')
TARGET = 0.99
CHUTE_MS = 15.0  # landing speed (with flaps, CL 1.5) above which a final chute is advised
BLUE, ORANGE, AQUA, YELLOW = '#2a78d6', '#eb6834', '#1baf7a', '#eda100'
INK, INK2, GRID = '#0b0b0b', '#52514e', '#e4e3df'


def landing(ld, sink_sl):
  v = sink_sl * ld                     # best-glide sea-level TAS at CL 0.8
  v_flap = v * math.sqrt(0.8 / 1.5)    # full-flap approach at CL 1.5
  return v, v_flap, 0.5 * v_flap ** 2  # J per kg


def pick_policy(d, ceiling):
  """Within one design: smallest margin reaching 99 % of the reachable
  flights under MC, else the best MC recovery; hindsight 'last' family."""
  d = d[d.policy == 'last'].sort_values('margin')
  ok = d[d.mc_rec >= TARGET * ceiling]
  return ok.iloc[0] if len(ok) else d.sort_values('mc_rec').iloc[-1]


def main():
  pol = pd.read_csv(OUT + '_policies.csv')
  des = pd.read_csv(OUT + '_designs.csv')
  tr = gt.Tracks(gt.TRACKS)
  nf = len(tr.flights)
  base = pol[pol.guidance == 'crab']
  f150 = {g: pol[(pol.guidance == g) & (pol.policy == 'fixed150')].iloc[0]
          for g in pol.guidance.unique()}

  # ---- design table ---------------------------------------------------
  rows = []
  ceiling = des.ceiling.max()  # flights that ever come within range of any design
  for (ld, wl), d in des.groupby(['ld', 'wing_kg_m2']):
    p = pick_policy(d, ceiling)
    v, vf, ke = landing(ld, p.sink_sl)
    rows.append(dict(ld=ld, wing_kg_m2=round(wl, 1), sink_sl=round(p.sink_sl, 2),
                     margin=p.margin, mc_rec=p.mc_rec, p10=p.mc_p10, p90=p.mc_p90,
                     nominal=p.nominal_rec, lost_h=p.lost_h_mean, lost_pct=p.lost_pct,
                     descent_h=p.glide_h_med, v_land=v, v_flap=vf, ke_j_kg=ke,
                     chute=vf > CHUTE_MS, ceiling=p.ceiling,
                     fixed150_mc=d[d.policy == 'fixed150'].mc_rec.iloc[0],
                     fixed150_nom=d[d.policy == 'fixed150'].nominal_rec.iloc[0]))
  dt = pd.DataFrame(rows).sort_values(['ld', 'wing_kg_m2'])
  target_abs = TARGET * ceiling            # 99 % of the flights that ever come within range
  dt['frac_reach'] = dt.mc_rec / ceiling
  good = dt[dt.mc_rec >= target_abs]
  # recommendation: among >=99% designs, the slowest landing (lightest wing
  # loading), tie-break by longer descent; else best recovery.
  nochute = good[~good.chute]
  if len(nochute):  # primary: best recovery among no-chute designs meeting the target
    rec = nochute.sort_values(['mc_rec', 'v_flap'], ascending=[False, True]).iloc[0]
  elif len(good):
    rec = good.sort_values(['v_flap', 'descent_h'], ascending=[True, False]).iloc[0]
  else:
    near = dt[dt.mc_rec >= dt.mc_rec.max() - 0.005]
    rec = near.sort_values('v_flap').iloc[0]
  # alternative: maximum recovery, then slowest landing
  dl = des[des.policy == 'last'].copy()
  dl['v_flap'] = dl.sink_sl * dl.ld * math.sqrt(0.8 / 1.5)
  a0 = dl[dl.mc_rec >= dl.mc_rec.max() - 1e-4].sort_values(['lost_h_mean', 'v_flap']).iloc[0]
  alt = dt[(dt.ld == a0.ld) & np.isclose(dt.wing_kg_m2, a0.wing_kg_m2)].iloc[0].copy()
  alt['mc_rec'], alt['p10'], alt['p90'], alt['margin'] = a0.mc_rec, a0.mc_p10, a0.mc_p90, a0.margin
  alt['descent_h'], alt['lost_h'] = a0.glide_h_med, a0.lost_h_mean
  rec_design = dict(ld=float(rec.ld), sink_sl=float(rec.sink_sl))
  rec_rows = des[(des.ld == rec.ld) & np.isclose(des.wing_kg_m2, rec.wing_kg_m2)]

  # ---- diagnosis on the recommended design/policy ----------------------
  bg = gb.BatchGrid(WindGrid())
  STF = gt.SWEEP_STF
  r = gt.nominal_margins(bg, tr, rec_design, 'crab', STF)
  mats = gt.margin_matrix(tr, r)
  rel = gt.releases(tr, mats[0], 'last', rec.margin)
  mc = gt.mc_eval(bg, tr, rel, rec_design, 'crab', STF, k=100, seed=1)
  pf = dict(zip(mc['flights'], mc['reached'].mean(axis=1)))
  never = [f for f in tr.flights if rel[f] is None or mats[0][rel[f]] < 0]
  low = [f for f in tr.flights if rel[f] is not None and 0 <= mats[0][rel[f]] < rec.margin]
  weak = [f for f in tr.flights if rel[f] is not None and mats[0][rel[f]] >= rec.margin
          and pf[f] < 0.99]
  diag = []
  for f in never + low + weak:
    if rel[f] is None:
      continue
    row, s = rel[f]
    m = mats[0][row, s]
    pa = tr.df.pa.values[row]
    wu, wv = bg.lookup(np.array([tr.df.lat.values[row]]), np.array([tr.df.lon.values[row]]),
                       np.array([max(pa, gb.P_MIN)]), np.array([tr.df.hours.values[row]]))
    wu, wv = float(wu[0]), float(wv[0])
    b = gb.bearing_rad(tr.df.lat.values[row], tr.df.lon.values[row], gt.SITE_LAT[s], gt.SITE_LON[s])
    head = -(wu * math.sin(b) + wv * math.cos(b))
    diag.append(dict(flight=f, site=gt.SITES[s][0], release_h=tr.df.h.values[row],
                     hours_to_exit=tr.dwell[f] - tr.df.h.values[row],
                     dist_km=tr.dist[row, s], margin_km=m, p_recover=pf[f],
                     wind_ms=math.hypot(wu, wv), headwind_ms=head,
                     kind=('never reachable' if f in never else
                           'below-margin (best effort)' if f in low else 'MC-fragile')))
  diag = pd.DataFrame(diag)
  pop = mc['reached'].sum(axis=0) / nf
  rec_mc, rec_p10, rec_p90 = pop.mean(), np.percentile(pop, 10), np.percentile(pop, 90)
  fail_per_sample = nf - mc['reached'].sum(axis=0)
  # failure attribution across all MC failures
  fails = ~mc['reached']
  n_fail = fails.sum()
  share_never = fails[[mc['flights'].index(f) for f in never if f in mc['flights']]].sum() / max(1, n_fail) if never else 0
  share_low = fails[[mc['flights'].index(f) for f in low]].sum() / max(1, n_fail) if low else 0
  share_weak = fails[[mc['flights'].index(f) for f in weak]].sum() / max(1, n_fail) if weak else 0

  # ---- figure --------------------------------------------------------
  plt.rcParams.update({'font.size': 9, 'axes.edgecolor': INK2, 'axes.labelcolor': INK,
                       'xtick.color': INK2, 'ytick.color': INK2, 'axes.titlecolor': INK,
                       'axes.spines.top': False, 'axes.spines.right': False,
                       'grid.color': GRID, 'axes.grid': True, 'grid.linewidth': 0.6})
  fig, ax = plt.subplots(2, 2, figsize=(11, 8.2), facecolor='#fcfcfb')
  # (a) recovery vs margin, today's design, guidance laws
  a = ax[0, 0]
  for g, c in (('direct', ORANGE), ('crab', BLUE), ('crab+stf', AQUA)):
    d = pol[(pol.guidance == g) & (pol.policy == 'last')].sort_values('margin')
    if len(d) == 0:
      continue
    a.plot(d.margin, 100 * d.mc_rec, '-o', color=c, lw=2, ms=4, label=f'{g}, Monte Carlo')
    if g == 'crab':
      a.fill_between(d.margin, 100 * d.mc_p10, 100 * d.mc_p90, color=c, alpha=0.15, lw=0)
      a.plot(d.margin, 100 * d.nominal_rec, '--', color=c, lw=1.2, label='crab, nominal winds')
    a.axhline(100 * f150[g].mc_rec, color=c, lw=1, ls=':',
              label='fixed 150 km rule, Monte Carlo' if g == 'direct' else None)
  a.axhline(100 * f150['direct'].nominal_rec, color=ORANGE, lw=1, ls='-.',
            label=f'today: fixed 150 km, direct, nominal ({100 * f150["direct"].nominal_rec:.0f}%)')
  a.axhline(100 * ceiling, color=INK2, lw=0.8, ls='--')
  a.text(0, 100 * ceiling + 0.4, f'reachability ceiling {100 * ceiling:.1f}%', fontsize=7, color=INK2)
  a.set_xlabel('release margin M (km of still-air range in hand on arrival)')
  a.set_ylabel('flights recovered (%)')
  a.set_title(f'(a) Today\'s glider (L/D {gt.BASE["ld"]:g}, {gt.wing_loading(gt.BASE["sink_sl"], gt.BASE["ld"]):.0f} kg/m²): '
              'guidance law and release margin', loc='left', fontsize=9.5)
  a.legend(fontsize=7.5, frameon=False, loc='lower right')
  a.set_ylim(40, 101)
  # (b) coverage lost vs margin, recommended design
  b = ax[0, 1]
  for p, c, lab in (('last', BLUE, 'hindsight (last reachable hour)'),
                    ('causal24', AQUA, 'on-board, 24 h lookahead'),
                    ('causal72', YELLOW, 'on-board, 72 h lookahead')):
    d = rec_rows[rec_rows.policy == p].sort_values('margin')
    b.plot(d.margin, d.lost_h_mean, '-o', color=c, lw=2, ms=4, label=lab)
  f = rec_rows[rec_rows.policy == 'fixed150'].iloc[0]
  b.axhline(f.lost_h_mean, color=ORANGE, ls='-.', lw=1.2, label='fixed 150 km rule')
  b.set_xlabel('release margin M (km)')
  b.set_ylabel('coverage hours lost per flight (dwell − release − glide)')
  b.set_title(f'(b) Coverage cost of the release, recommended glider', loc='left', fontsize=9.5)
  b.legend(fontsize=7.5, frameon=False)
  # (c) heatmap of MC recovery (best margin) over L/D x wing loading
  c = ax[1, 0]
  dsw = dt[dt.wing_kg_m2.round(1).isin(gt.WLS)]
  piv = dsw.pivot(index='ld', columns='wing_kg_m2', values='frac_reach')
  im = c.imshow(100 * piv.values, cmap='Blues', vmin=96, vmax=100, aspect='auto', origin='lower')
  c.set_xticks(range(len(piv.columns))); c.set_xticklabels([f'{w:g}' for w in piv.columns])
  c.set_yticks(range(len(piv.index))); c.set_yticklabels([f'{l:g}' for l in piv.index])
  c.grid(False)
  mp = dsw.pivot(index='ld', columns='wing_kg_m2', values='margin')
  for i in range(len(piv.index)):
    for j in range(len(piv.columns)):
      v = 100 * piv.values[i, j]
      c.text(j, i, f'{v:.1f}%\nM={mp.values[i, j]:g}', ha='center', va='center', fontsize=7,
             color='white' if v > 98.5 else INK,
             fontweight='bold' if v >= 100 * TARGET else 'normal')
  c.set_xlabel('wing loading (kg/m²)'); c.set_ylabel('L/D')
  c.set_title(f'(c) Recovery, % of reachable flights ({gt.SWEEP_GUIDANCE}); M = smallest margin for 99 %',
              loc='left', fontsize=9)
  fig.colorbar(im, ax=c, fraction=0.04, pad=0.02, label='recovered (% of reachable flights)')
  # (d) trade-off: landing speed vs recovery, descent time annotated
  d = ax[1, 1]
  d100 = des[(des.policy == 'last') & (des.margin == 100) & des.wing_kg_m2.round(1).isin(gt.WLS)].copy()
  d100['wing_kg_m2'] = d100.wing_kg_m2.round(1)
  d100['v_flap'] = d100.sink_sl * d100.ld * math.sqrt(0.8 / 1.5)
  for ld, grp in d100.groupby('ld'):
    grp = grp.sort_values('v_flap')
    shade = plt.cm.Blues(0.35 + 0.6 * (ld - min(gt.LDS)) / (max(gt.LDS) - min(gt.LDS)))
    d.plot(grp.v_flap, 100 * grp.mc_rec, '-o', color=shade, lw=1.5, ms=5, label=f'L/D {ld:g}')
    for _, g in grp.iterrows():
      if g.wing_kg_m2 in (15.0, 60.0) or (g.ld == rec.ld and g.wing_kg_m2 == rec.wing_kg_m2):
        d.annotate(f'{g.glide_h_med:.1f} h', (g.v_flap, 100 * g.mc_rec), textcoords='offset points',
                   xytext=(-14 if g.wing_kg_m2 == 15.0 else 14, 0), ha='center', va='center',
                   fontsize=6.5, color=INK2)
  d.axhline(100 * ceiling, color=INK2, lw=0.8, ls='--')
  d.text(12.6, 100 * ceiling + 0.08, f'reachability ceiling {100 * ceiling:.1f}% ({nf - round(ceiling * nf)} flights never in range)', fontsize=7, color=INK2)
  d.axhline(100 * target_abs, color=INK2, lw=0.8, ls=':')
  d.text(19.5, 100 * target_abs - 0.22, '99 % of reachable', fontsize=7, color=INK2)
  d.axvline(CHUTE_MS, color=ORANGE, lw=0.8, ls=':')
  d.text(CHUTE_MS + 0.3, 94.3, 'final chute advised →', color=ORANGE, fontsize=7.5)
  d.plot(rec.v_flap, 100 * rec.mc_rec, 'o', ms=12, mfc='none', mec=ORANGE, mew=2)
  d.set_xlabel('landing speed with flaps, sea level (m/s)')
  d.set_ylabel('recovered (%), Monte Carlo')
  d.set_title('(d) Recovery at M = 100 km vs landing speed (labels: descent time)',
              loc='left', fontsize=9)
  d.legend(fontsize=7.5, frameon=False, loc='lower right')
  d.set_ylim(94, 99)
  fig.tight_layout()
  fig.savefig(OUT + '.png', dpi=150, facecolor=fig.get_facecolor())

  # ---- markdown --------------------------------------------------------
  def pct(x):
    return f'{100 * x:.1f}%'
  L = []
  L.append('# Radio-return glider tuning\n')
  L.append(f'Inputs: {nf} slow-controller flights (results/slow_tracks.csv, hourly tracks reproduced '
           f'from run_drift.py), {len(tr.rows)} candidate (hour, site) glides within {gt.RANGE_KM:.0f} km. '
           f'Monte Carlo per release: wind bias U(0,{gt.BIAS_MAX:g}) m/s random direction, AR(1) gust '
           f'noise {gt.NOISE_SD:g} m/s (15 min), surface taper U{gt.TAPER_RANGE} (nominal 0.3); '
           f'K={gt.MC_K} samples in the sweeps, 100 for the final diagnosis. Recovery = landing '
           f'within 25 km of the site (as today); "close" = within 5 km.\n')
  crab0 = base[(base.policy == 'last') & (base.margin == 0)].iloc[0]
  dir0 = pol[(pol.guidance == 'direct') & (pol.policy == 'last') & (pol.margin == 0)].iloc[0]
  stf0 = pol[(pol.guidance == 'crab+stf') & (pol.policy == 'last') & (pol.margin == 0)].iloc[0]
  c24 = rec_rows[(rec_rows.policy == 'causal24') & (rec_rows.margin == rec.margin)].iloc[0]
  c72 = rec_rows[(rec_rows.policy == 'causal72') & (rec_rows.margin == rec.margin)].iloc[0]
  L.append('## Recommendation\n')
  v, vf, ke = landing(rec.ld, rec.sink_sl)
  L.append(f'- **Guidance**: crab-angle track hold (solve heading so ground velocity points along the '
           f'great circle to the site; fall back to pointing at the site when the cross wind exceeds '
           f'airspeed), plus speed-to-fly (fly up to 1.8x best-glide speed into headwinds, parabolic polar), '
           f'then hold station overhead and spiral down. Crab vs direct pointing is {100 * (crab0.mc_rec - dir0.mc_rec):+.1f} points '
           f'at today\'s design (within Monte Carlo noise: the losing cases are winds above airspeed, where no heading helps); '
           f'speed-to-fly is worth {100 * (stf0.mc_rec - crab0.mc_rec):+.1f} points and is the part of the guidance that matters.')
  L.append(f'- **Release policy**: at every hour simulate the glide to every site within {gt.RANGE_KM:.0f} km '
           f'using the forecast winds; release at the last hour at which some site is reachable with '
           f'arrival margin >= **M = {rec.margin:g} km** (arrival altitude x L/D). This is a hindsight rule; the '
           f'on-board version (release when nothing is forecast reachable in the next H hours) recovers '
           f'{pct(c24.mc_rec)} with H=24 h and {pct(c72.mc_rec)} with H=72 h but costs {c24.lost_h_mean:.0f} h / '
           f'{c72.lost_h_mean:.0f} h of coverage per flight because reachability often returns days later.')
  L.append(f'- **Design point**: **L/D {rec.ld:g}, wing loading {rec.wing_kg_m2:g} kg/m²** '
           f'(sea-level sink {rec.sink_sl:.2f} m/s, best-glide TAS {v:.0f} m/s at sea level, '
           f'{rec.sink_sl * rec.ld * math.sqrt(1.225 / gb.isa_density(20000)):.0f} m/s at 20 km): the '
           f'best-recovering design that needs no landing chute and recovers >= 99 % of the reachable flights. If a final chute is '
           f'acceptable, **L/D {alt.ld:g} @ {alt.wing_kg_m2:g} kg/m²** recovers {pct(alt.mc_rec)} '
           f'(P10–P90 {pct(alt.p10)}–{pct(alt.p90)}, i.e. every reachable flight in every sample) at M={alt.margin:g} km, '
           f'descent {alt.descent_h:.2f} h, coverage lost {alt.lost_h:.1f} h/flight, landing {alt.v_flap:.0f} m/s with flaps.')
  L.append(f'- **Ceiling**: only {pct(ceiling)} of flights ({round(ceiling * nf)}/{nf}) ever pass within glide range '
           f'(500 km, any design) of one of the 21 sites, so 99 % of all flights is not attainable with this '
           f'site network; targets below are 99 % of the reachable {round(ceiling * nf)}.')
  L.append(f'- **Achieved**: {pct(rec_mc)} of all {nf} flights recovered under the Monte Carlo '
           f'(P10–P90 across wind-error samples {pct(rec_p10)}–{pct(rec_p90)}; nominal winds {pct(rec.nominal)}), '
           f'vs today\'s fixed-150 km rule with direct pointing: {pct(f150["direct"].nominal_rec)} nominal, '
           f'{pct(f150["direct"].mc_rec)} under the same Monte Carlo.')
  L.append(f'- **Coverage cost**: {rec.lost_h:.1f} h per flight ({rec.lost_pct:.1f}% of balloon-hours) lost '
           f'between release and the balloon leaving the region, vs {f.lost_h_mean:.1f} h '
           f'({f.lost_pct:.1f}%) for the fixed-150 km rule; median glide home '
           f'{rec_rows[rec_rows.policy == "last"].iloc[0].ground_med:.0f} km, descent (transmit) time {rec.descent_h:.2f} h.')
  L.append(f'- **Landing**: {v:.0f} m/s at CL 0.8, {vf:.0f} m/s with full flaps (CL 1.5), '
           f'{ke:.0f} J/kg kinetic energy. {"A final small chute or net is advised (> %g m/s)." % CHUTE_MS if rec.chute else "Belly/flare landing feasible without a chute."}\n')

  L.append('## 1. Guidance law (today\'s design, L/D %g, %.0f kg/m², hindsight release)\n' %
           (gt.BASE['ld'], gt.wing_loading(gt.BASE['sink_sl'], gt.BASE['ld'])))
  L.append('| policy | guidance | releases | nominal | MC mean | P10–P90 | within 5 km | lost h/flight | glide home km |')
  L.append('|---|---|---|---|---|---|---|---|---|')
  for _, s in pol[pol.policy.isin(['fixed150', 'last'])].sort_values(['guidance', 'margin']).iterrows():
    L.append(f'| {s.label} | {s.guidance} | {s.n_release} | {pct(s.nominal_rec)} | {pct(s.mc_rec)} | '
             f'{pct(s.mc_p10)}–{pct(s.mc_p90)} | {pct(s.mc_close5km)} | {s.lost_h_mean:.1f} | {s.ground_med:.0f} |')
  L.append(f'\nAt M=0 under the Monte Carlo: direct {pct(dir0.mc_rec)}, crab {pct(crab0.mc_rec)}, '
           f'crab + speed-to-fly {pct(stf0.mc_rec)}. Crab angle alone is a small gain (the limiting cases are '
           f'head/cross winds above the glider\'s airspeed, where no heading helps); speed-to-fly helps the '
           f'light, slow glider because it trades glide ratio for penetration exactly in those cases. The '
           f'largest gains come from the release policy (release wherever a site is reachable, not only '
           f'within 150 km) and from the arrival margin.\n')

  L.append('## 2–3. Release margin and robustness (recommended design)\n')
  L.append('| policy | nominal | MC mean | P10–P90 | within 5 km | lost h/flight | lost % | release dist km | glide home km |')
  L.append('|---|---|---|---|---|---|---|---|---|')
  for _, s in rec_rows.sort_values(['policy', 'margin']).iterrows():
    L.append(f'| {s.label} | {pct(s.nominal_rec)} | {pct(s.mc_rec)} | {pct(s.mc_p10)}–{pct(s.mc_p90)} | '
             f'{pct(s.mc_close5km)} | {s.lost_h_mean:.1f} | {s.lost_pct:.1f} | {s.release_dist_med:.0f} | {s.ground_med:.0f} |')
  L.append('')
  L.append(f'## 4. Design sweep ({gt.SWEEP_GUIDANCE} guidance; per design the smallest M reaching 99 %, else the best M)\n')
  L.append('| L/D | W/S kg/m² | sink m/s | M km | MC recovery | P10–P90 | nominal | lost h/flight | descent h | V land / flaps m/s | KE J/kg | chute? | fixed-150 today |')
  L.append('|---|---|---|---|---|---|---|---|---|---|---|---|---|')
  for _, g in dt.iterrows():
    L.append(f'| {g.ld:g} | {g.wing_kg_m2:g} | {g.sink_sl:.2f} | {g.margin:g} | **{pct(g.mc_rec)}** | '
             f'{pct(g.p10)}–{pct(g.p90)} | {pct(g.nominal)} | {g.lost_h:.1f} | {g.descent_h:.2f} | '
             f'{g.v_land:.0f} / {g.v_flap:.0f} | {g.ke_j_kg:.0f} | {"yes" if g.chute else "no"} | {pct(g.fixed150_nom)} |')
  L.append('')
  L.append(f'Designs reaching >= {100 * TARGET:.0f}% of reachable flights (>= {pct(target_abs)} of all) under the Monte Carlo: ' +
           (', '.join(f'L/D {g.ld:g} @ {g.wing_kg_m2:g} kg/m² (M={g.margin:g}, {g.descent_h:.1f} h, {g.v_flap:.0f} m/s)'
                      for _, g in good.iterrows()) if len(good) else 'none') + '.\n')
  if os.path.exists(OUT + '_extra.csv'):
    ex = pd.read_csv(OUT + '_extra.csv')
    L.append('### Larger margins (hindsight policy)\n')
    L.append('| L/D | W/S | policy | MC mean | P10–P90 | within 5 km | lost h/flight | lost % |')
    L.append('|---|---|---|---|---|---|---|---|')
    for _, s in ex[ex.policy == 'last'].sort_values(['ld', 'wing_kg_m2', 'margin']).iterrows():
      L.append(f'| {s.ld:g} | {s.wing_kg_m2:.0f} | {s.label} | {pct(s.mc_rec)} | {pct(s.mc_p10)}–{pct(s.mc_p90)} | '
               f'{pct(s.mc_close5km)} | {s.lost_h_mean:.1f} | {s.lost_pct:.1f} |')
    L.append('Margins above 100 km buy no further recovery (the remaining losses are not margin-limited) and only cost coverage.\n')
  L.append('## What limits the last per cent\n')
  L.append(f'Reachability ceiling (some hour with a nominally reachable site): {pct(rec.ceiling)} of flights; '
           f'{len(never)} flight(s) never come within glide range of any site: {", ".join(never) or "-"}.')
  L.append(f'Recommended configuration, K=100: {pct(rec_mc)} mean, failures per sample {fail_per_sample.min():.0f}–{fail_per_sample.max():.0f} of {nf}. '
           f'Share of Monte Carlo failures: never-reachable {100 * share_never:.0f}%, released below margin (best effort) '
           f'{100 * share_low:.0f}%, wind-error losses on margin-satisfying releases {100 * share_weak:.0f}%.\n')
  if len(diag):
    L.append('| flight | kind | site | release h | h to exit | dist km | margin km | wind @release m/s | headwind m/s | P(recover) |')
    L.append('|---|---|---|---|---|---|---|---|---|---|')
    for _, g in diag.sort_values('p_recover').iterrows():
      L.append(f'| {g.flight} | {g.kind} | {g.site} | {g.release_h:.0f} | {g.hours_to_exit:.0f} | {g.dist_km:.0f} | '
               f'{g.margin_km:.0f} | {g.wind_ms:.0f} | {g.headwind_ms:.0f} | {g.p_recover:.2f} |')
  L.append(f'\nResidual failure modes: (1) **{100 * share_never:.0f}% of Monte Carlo failures** are the '
           f'{len(never)} flight(s) that leave the region without ever coming within glide range of a site '
           f'(Brest launches blown west/north over the Atlantic: nearest sites Dublin/London 450–490 km away '
           f'at the closest hour). No glider in the sweep fixes these; a recovery site in Ireland\'s west / '
           f'Cornwall / Brittany itself would. (2) **{100 * share_weak:.0f}%** are wind-error losses on releases '
           f'that nominally had >= {rec.margin:g} km in hand: {len(weak)} flights at P(recover) '
           f'{diag[diag.kind == "MC-fragile"].p_recover.min() if len(weak) else 1:.2f}–'
           f'{diag[diag.kind == "MC-fragile"].p_recover.max() if len(weak) else 1:.2f} (sites: '
           f'{", ".join(sorted(set(diag[diag.kind == "MC-fragile"].site))) if len(weak) else "-"}; release '
           f'{diag[diag.kind == "MC-fragile"].dist_km.min() if len(weak) else 0:.0f}–{diag[diag.kind == "MC-fragile"].dist_km.max() if len(weak) else 0:.0f} km out in '
           f'{diag[diag.kind == "MC-fragile"].wind_ms.min() if len(weak) else 0:.0f}–{diag[diag.kind == "MC-fragile"].wind_ms.max() if len(weak) else 0:.0f} m/s winds at release altitude); they fail '
           f'when the surface taper is near 1.0 and the 5 m/s bias is a headwind, i.e. the no-tropospheric-wind-data '
           f'assumption, not the aircraft. (3) **{100 * share_low:.0f}%** from releases forced below margin. Heavier '
           f'wing loading removes mode (2) (L/D 12 @ 30 kg/m² or any 60 kg/m² design recovers every reachable '
           f'flight) at the price of a 25 m/s landing (chute).\n')
  L.append('Caveats: ISA atmosphere, no stall/Mach/bank limits, constant L/D; the balloon tracks are the '
           'same BLE flights as drift_2025.csv (same seeds); the release decision assumes an on-board '
           'balloon forecast (the balloon already flies on forecast winds).\n')
  L.append(f'![glider tuning](glider_tuning.png)\n')
  open(OUT + '.md', 'w').write('\n'.join(L))
  dt.to_csv(OUT + '_design_table.csv', index=False)
  print('\n'.join(L[:12]))


if __name__ == '__main__':
  main()

"""Markdown tables for results/site_mix.md from the site_mix.py outputs. Run after site_mix.py.

  python site_mix_report.py            # prints every table; results/site_mix.md pastes them
"""
import itertools
import math
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import replay as rp  # noqa: E402
from site_mix import EURO_SITES, LIGHT_TRACKS, NORTH, REGION  # noqa: E402

R = 6371.0
def box_km2(b):
  return R * R * math.radians(b['lon1'] - b['lon0']) * (math.sin(math.radians(b['lat1'])) - math.sin(math.radians(b['lat0'])))
REGION_KM2 = box_km2(REGION)
NORTH_KM2 = box_km2(NORTH)
SHORT = {'Lisbon': 'Lis', 'Brest': 'Bre', 'Dublin': 'Dub', 'Vienna': 'Vie', 'Bucharest': 'Buc',
         'Copenhagen': 'Cop', 'Gothenburg': 'Got', 'Riga': 'Rig', 'Tallinn': 'Tal'}


def md(df, floatfmt='{:.1f}'):
  cols = list(df.columns)
  out = ['| ' + ' | '.join(str(c) for c in cols) + ' |', '|' + '---|' * len(cols)]
  for _, r in df.iterrows():
    cells = []
    for c in cols:
      v = r[c]
      if isinstance(v, (float, np.floating)):
        cells.append('' if np.isnan(v) else floatfmt.format(v))
      elif isinstance(v, (int, np.integer)):
        cells.append(f'{v:,}')
      else:
        cells.append(str(v))
    out.append('| ' + ' | '.join(cells) + ' |')
  return '\n'.join(out)


def ideal(n, radius_km, km2=REGION_KM2):
  return n * math.pi * radius_km ** 2 / km2


def enrich(d):
  d = d.copy()
  d['cost_meur'] = d.cost_eur / 1e6
  d['region_pct'] = 100 * d.region
  d['north_pct'] = 100 * d.north
  d['cities_pct'] = 100 * d.cities
  d['pct_per_meur'] = d.region_pct / d.cost_meur
  d['north_pct_per_meur'] = d.north_pct / d.cost_meur
  d['packing'] = d.region / ideal(d.standing, d.radius_km)
  d['launches'] = d.launches_light + d.launches_canada
  return d


def section(title):
  print(f'\n\n### {title}\n')


def inputs():
  t = rp.Tracks(LIGHT_TRACKS)
  rows = []
  for s in EURO_SITES:
    m = t.site == s
    h = t.end_h[m]
    mon = t.launch_month[m]
    djf = np.isin(mon, (12, 1, 2)); jja = np.isin(mon, (6, 7, 8))
    rows.append({'site': s, 'flights': int(m.sum()), 'mean dwell d': h.mean() / 24, 'Little-weighted d': len(h) / (24 / h.clip(1)).sum() * 24 / 24,
                 'DJF mean d': h[djf].mean() / 24, 'JJA mean d': h[jja].mean() / 24, 'shortest h': h.min(), 'longest d': h.max() / 24})
  df = pd.DataFrame(rows)
  # launch-weighted dwell as the drift notes use it: a balloon-year costs sum over months of
  # days_m * 24 / mean dwell of that month's tracks launches; the weighted dwell is 365 over that.
  def little(site):
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    launches = sum(days[m - 1] * 24.0 / max(t.mean_dwell_h(m, True, [site]), 1.0) for m in range(1, 13))
    return 365.0 / launches
  df['Little-weighted d'] = [little(s) for s in EURO_SITES]
  section('Light-vehicle library: dwell by site (measured, results/slow_tracks*.csv)')
  print(md(df, '{:.2f}'))
  c = pd.read_csv('results/site_mix_canada_first_pass.csv')
  c['season'] = c.month.map(lambda m: 'DJF' if m in (12, 1, 2) else 'MAM' if m in (3, 4, 5) else 'JJA' if m in (6, 7, 8) else 'SON')
  g = c.groupby('season').agg(flights=('site', 'size'), **{'transit d': ('transit_days', 'mean'), 'first pass h mean': ('first_pass_h', 'mean'),
                                                          'first pass h median': ('first_pass_h', 'median'), 'later passes h': ('total_eu_h', lambda x: 0.0)})
  g['later passes h'] = c.groupby('season').apply(lambda x: (x.total_eu_h - x.first_pass_h).mean(), include_groups=False)
  g['recoverable share'] = c.groupby('season').recoverable.mean()
  g = g.reindex(['DJF', 'MAM', 'JJA', 'SON']).reset_index()
  allrow = pd.DataFrame([{'season': 'year', 'flights': len(c), 'transit d': c.transit_days.mean(), 'first pass h mean': c.first_pass_h.mean(),
                          'first pass h median': c.first_pass_h.median(), 'later passes h': (c.total_eu_h - c.first_pass_h).mean(),
                          'recoverable share': c.recoverable.mean()}])
  section('Canada flights: measured first pass over Europe (results/site_mix_canada_first_pass.csv, 72 flights, NCEP and ERA5)')
  print(md(pd.concat([g, allrow], ignore_index=True), '{:.2f}'))
  print(f'\nLittle-weighted first-pass dwell {len(c) / (1 / (c.first_pass_h / 24)).sum():.2f} d; flights clipping China before the end of the first pass: {int(c.china_before_end_of_first_pass.sum())} of {len(c)}; by winds: NCEP mean first pass {c[c.winds == "canada"].first_pass_h.mean():.0f} h, ERA5 {c[c.winds == "era5"].first_pass_h.mean():.0f} h.')
  print(f'Region area {REGION_KM2 / 1e6:.2f} M km2; northern box {NORTH_KM2 / 1e6:.3f} M km2 ({100 * NORTH_KM2 / REGION_KM2:.1f} % of the region). One 80 km disc is {100 * math.pi * 80 ** 2 / REGION_KM2:.3f} % of the region, so 50 discs that never overlapped would cover {100 * ideal(50, 80):.1f} % and 100 would cover {100 * ideal(100, 80):.1f} %.')


def singles():
  s = enrich(pd.read_csv('results/site_mix_singles.csv'))
  s['site'] = np.where(s.canada_share == 1, 'Canada alone', s.sites)
  base = s[(s.radius_km == 80) & (s.standing == 50) & (s.canada_share.isin([0, 1]))]
  y = base[base.period == 'year'].set_index('site')
  djf = base[base.period == 'DJF'].set_index('site')
  jja = base[base.period == 'JJA'].set_index('site')
  df = pd.DataFrame({'site': y.index, 'aloft': y.aloft.round(0).astype(int), 'launches/yr': y.launches.astype(int), '€M/yr': y.cost_meur,
                     'region % year': y.region_pct, 'region % DJF': djf.region_pct, 'region % JJA': jja.region_pct,
                     'north % year': y.north_pct, 'north % DJF': djf.north_pct, 'north % JJA': jja.north_pct,
                     'cities % year': y.cities_pct, 'packing': y.packing, 'region % per €M': y.pct_per_meur, 'north % per €M': y.north_pct_per_meur})
  df = df.sort_values('region % per €M', ascending=False)
  section('Single sites holding 50 aloft, 80 km radius (replay on measured tracks; Canada row estimated)')
  print(md(df, '{:.2f}'))
  mon = base[~base.period.isin(['DJF', 'JJA', 'year'])].copy()
  mon['m'] = mon.period.astype(int)
  section('Northern-box coverage (% of its area) by month, single sites holding 50 aloft, 80 km')
  p = mon.pivot_table(index='site', columns='m', values='north_pct')
  p.columns = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  p = p.reindex(EURO_SITES + ['Canada alone'])
  p['hours with no north coverage %'] = 100 * base[base.period == 'year'].set_index('site').north_zero_share.reindex(p.index)
  print(md(p.reset_index(), '{:.1f}'))
  section('Region coverage (% of area) by month, single sites holding 50 aloft, 80 km')
  p = mon.pivot_table(index='site', columns='m', values='region_pct')
  p.columns = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  print(md(p.reindex(EURO_SITES + ['Canada alone']).reset_index(), '{:.1f}'))
  section('Radius and fleet-size sensitivity, single sites, year (region % of area)')
  d = s[(s.period == 'year') & (s.canada_share.isin([0, 1]))]
  p1 = d[d.standing == 50].pivot_table(index='site', columns='radius_km', values='region_pct')
  p1.columns = [f'{int(c)} km, 50 aloft' for c in p1.columns]
  p2 = d[(d.radius_km == 80) & (d.standing != 50)].pivot_table(index='site', columns='standing', values='region_pct')
  p2.columns = [f'80 km, {int(c)} aloft' for c in p2.columns]
  p3 = d[d.radius_km == 80].pivot_table(index='site', columns='standing', values='pct_per_meur')
  p3.columns = [f'% per €M, {int(c)} aloft' for c in p3.columns]
  print(md(pd.concat([p1, p2, p3], axis=1).reindex(EURO_SITES + ['Canada alone']).reset_index(), '{:.2f}'))


def shares():
  s = enrich(pd.read_csv('results/site_mix_shares.csv'))
  s['set'] = s.n_sites.map({5: 'five western and central', 9: 'all nine European', 0: 'Canada alone'})
  for per in ['year', 'DJF', 'JJA']:
    d = s[s.period == per]
    g = d.groupby(['standing', 'set', 'canada_share']).agg(**{'aloft': ('aloft', 'mean'), 'light launches': ('launches_light', 'mean'),
                                                              'Canada launches': ('launches_canada', 'mean'), '€M/yr': ('cost_meur', 'mean'),
                                                              'region %': ('region_pct', 'mean'), 'sd': ('region_pct', 'std'),
                                                              'north %': ('north_pct', 'mean'), 'cities %': ('cities_pct', 'mean'),
                                                              '% per €M': ('pct_per_meur', 'mean')}).reset_index()
    g = g.sort_values(['standing', 'set', 'canada_share'])
    g['canada_share'] = g.canada_share.map(lambda x: f'{int(100 * x)} %')
    g = g.rename(columns={'standing': 'aloft target', 'canada_share': 'Canada share'})
    section(f'Canada share of the layer, {per} (five seeds; Canada flight €33,000, estimated)')
    print(md(g, '{:.2f}'))
  # break-even
  y = s[(s.period == 'year')]
  for N in (50, 100):
    five = y[(y.set == 'five western and central') & (y.canada_share == 0) & (y.standing == N)]
    can = y[(y.set == 'Canada alone') & (y.standing == N)]
    eur_per_pct_five = (five.cost_eur / five.region_pct).mean()
    be = eur_per_pct_five * can.region_pct.mean() / can.launches_canada.mean()
    be_pack = eur_per_pct_five * (five.region_pct.mean() * can.aloft.mean() / five.aloft.mean()) / can.launches_canada.mean()
    print(f'\nBreak-even Canada flight price at {N} aloft, year-round area coverage per euro equal to the five sites: '
          f'€{be:,.0f} as replayed; €{be_pack:,.0f} if Canada balloons packed as well as the five sites\' (estimated).')
  for per in ('DJF', 'JJA'):
    d = s[s.period == per]
    five = d[(d.set == 'five western and central') & (d.canada_share == 0) & (d.standing == 50)]
    can = d[(d.set == 'Canada alone') & (d.standing == 50)]
    # seasonal: cost attributable to the season = launches in season * price; use coverage per aloft instead
    print(f'{per}: coverage per balloon aloft, five sites {100 * (five.region / five.aloft).mean():.3f} % of area, Canada {100 * (can.region / can.aloft).mean():.3f} %.')


def sweep():
  path = 'results/site_mix_scores.csv'
  if not os.path.exists(path):
    print('\n(no sweep file yet)')
    return
  s = enrich(pd.read_csv(path))
  s['label'] = s.sites.map(lambda x: '+'.join(SHORT.get(p, p) for p in x.split('+')) if x != '(none)' else 'Canada only')
  for N in (50, 100):
    for per in ('year', 'DJF', 'JJA'):
      d = s[(s.standing == N) & (s.period == per) & (s.canada_share == 0)].sort_values('cost_meur')
      # Pareto: increasing cost must bring increasing region coverage
      front, best = [], -1
      for _, r in d.iterrows():
        if r.region_pct > best + 1e-9:
          front.append(r); best = r.region_pct
      f = pd.DataFrame(front)
      section(f'Frontier, European sets only, {N} aloft, {per}: every set that is not beaten on both cost and region coverage')
      print(md(f[['label', 'n_sites', 'launches', 'cost_meur', 'region_pct', 'north_pct', 'cities_pct', 'pct_per_meur']]
               .rename(columns={'label': 'sites', 'n_sites': 'k', 'launches': 'launches/yr', 'cost_meur': '€M/yr', 'region_pct': 'region %',
                                'north_pct': 'north %', 'cities_pct': 'cities %', 'pct_per_meur': '% per €M'}), '{:.2f}'))
    # north frontier
    d = s[(s.standing == N) & (s.period == 'year') & (s.canada_share == 0)].sort_values('cost_meur')
    front, best = [], -1
    for _, r in d.iterrows():
      if r.north_pct > best + 1e-9:
        front.append(r); best = r.north_pct
    f = pd.DataFrame(front)
    section(f'Frontier on the northern box, European sets only, {N} aloft, year')
    print(md(f[['label', 'n_sites', 'launches', 'cost_meur', 'north_pct', 'region_pct', 'north_pct_per_meur']]
             .rename(columns={'label': 'sites', 'n_sites': 'k', 'launches': 'launches/yr', 'cost_meur': '€M/yr', 'north_pct': 'north %',
                              'region_pct': 'region %', 'north_pct_per_meur': 'north % per €M'}), '{:.2f}'))
    # best per size
    y = s[(s.standing == N) & (s.period == 'year') & (s.canada_share == 0)]
    djf = s[(s.standing == N) & (s.period == 'DJF') & (s.canada_share == 0)].set_index('sites')
    rows = []
    for k in range(1, 10):
      yk = y[y.n_sites == k]
      b = yk.loc[yk.pct_per_meur.idxmax()]
      bn = yk.loc[yk.north_pct_per_meur.idxmax()]
      rows.append({'k': k, 'best per €M': b.label, '€M/yr': b.cost_meur, 'region %': b.region_pct, 'north %': b.north_pct, 'DJF region %': djf.loc[b.sites].region_pct,
                   '% per €M': b.pct_per_meur, 'best north per €M': bn.label, 'its north %': bn.north_pct, 'its €M/yr': bn.cost_meur})
    section(f'Best set of each size, {N} aloft, year')
    print(md(pd.DataFrame(rows), '{:.2f}'))
    # marginal value of each site
    y = y.set_index('sites')
    rows = []
    for site in EURO_SITES:
      deltas_cov, deltas_cost, deltas_eff, deltas_north = [], [], [], []
      for sites, r in y.iterrows():
        parts = sites.split('+')
        if site in parts or len(parts) == 9:
          continue
        with_ = '+'.join(p for p in EURO_SITES if p in parts or p == site)
        if with_ not in y.index:
          continue
        w = y.loc[with_]
        deltas_cov.append(w.region_pct - r.region_pct); deltas_cost.append(w.cost_meur - r.cost_meur)
        deltas_eff.append(w.pct_per_meur - r.pct_per_meur); deltas_north.append(w.north_pct - r.north_pct)
      rows.append({'site': site, 'sets': len(deltas_cov), 'Δ region % (mean)': np.mean(deltas_cov), 'Δ north %': np.mean(deltas_north),
                   'Δ €M/yr': np.mean(deltas_cost), 'Δ % per €M': np.mean(deltas_eff), 'share of sets where % per €M rises': np.mean(np.array(deltas_eff) > 0)})
    section(f'Marginal value of adding a site to every set that lacks it, {N} aloft, year')
    print(md(pd.DataFrame(rows).sort_values('Δ % per €M', ascending=False), '{:.3f}'))
  # with-Canada rows: does adding Canada ever improve per-euro?
  for N in (50, 100):
    d = s[(s.standing == N) & (s.period == 'year')]
    a = d[d.canada_share == 0].set_index('sites'); b = d[d.canada_share == 0.5].set_index('sites')
    j = a.join(b, rsuffix='_c', how='inner')
    better = (j.pct_per_meur_c > j.pct_per_meur).mean()
    north_better = (j.north_pct_per_meur_c > j.north_pct_per_meur).mean()
    print(f'\n{N} aloft: replacing half of a European set\'s layer with Canada raises region coverage per euro in {100 * better:.0f} % of the {len(j)} sets and northern coverage per euro in {100 * north_better:.0f} %; mean change in region coverage {j.region_pct_c.mean() - j.region_pct.mean():+.2f} points, in cost {j.cost_meur_c.mean() - j.cost_meur.mean():+.1f} €M/yr.')
    # frontier including Canada rows
    dd = d.sort_values('cost_meur'); front, best = [], -1
    for _, r in dd.iterrows():
      if r.region_pct > best + 1e-9:
        front.append(r); best = r.region_pct
    f = pd.DataFrame(front)
    print(f'Frontier over all rows including Canada ones, {N} aloft, year: Canada appears in {int((f.canada_share > 0).sum())} of {len(f)} frontier points.')
  # never on frontier
  never = set(EURO_SITES)
  for N in (50, 100):
    for per in ('year', 'DJF', 'JJA'):
      for metric in ('region_pct', 'north_pct'):
        d = s[(s.standing == N) & (s.period == per) & (s.canada_share == 0)].sort_values('cost_meur')
        best = -1
        for _, r in d.iterrows():
          if r[metric] > best + 1e-9:
            best = r[metric]
            never -= set(r.sites.split('+'))
  print(f'\nSites on no frontier (region or north, year/DJF/JJA, 50 and 100 aloft): {sorted(never) or "none"}')
  # frontier appearances count
  cnt = {s_: 0 for s_ in EURO_SITES}; tot = 0
  for N in (50, 100):
    for per in ('year', 'DJF', 'JJA'):
      for metric in ('region_pct', 'north_pct'):
        d = s[(s.standing == N) & (s.period == per) & (s.canada_share == 0)].sort_values('cost_meur')
        best = -1
        for _, r in d.iterrows():
          if r[metric] > best + 1e-9:
            best = r[metric]; tot += 1
            for p in r.sites.split('+'):
              cnt[p] += 1
  print('Frontier appearances by site (of', tot, 'frontier points):', {k: v for k, v in sorted(cnt.items(), key=lambda kv: -kv[1])})




def markets():
  """Section 5b: split each Canada flight's pre-Europe days by market (estimated from day counts;
  the run files hold no positions) and the days-weighted cost split. Writes results/site_mix_canada_markets.csv."""
  import json
  rows = []
  for tag, path in [('ncep', 'results/multipass_2025_nochina_bat10000_thrust3_canada.jsonl'),
                    ('era5', 'results/multipass_2025_nochina_bat10000_thrust3_canada_era5.jsonl')]:
    for line in open(path):
      r = json.loads(line)
      d = np.asarray(r['daily_eu_h'], float)
      a = int(np.nonzero(d > 0)[0][0]); k = a
      while k + 1 < len(d) and d[k + 1] > d[k]:
        k += 1
      transit = (24 * (a + 1) - d[a]) / 24.0
      first = d[k] / 24.0
      canada_s = min(r['canada_days'], transit)                    # southern band, <= 60N (canada.py mask), capped at the first leg
      atlantic = min(r['atlantic_days'], transit - canada_s)       # 40-60N, 52-10W band
      other = transit - canada_s - atlantic                        # north of 60N, or the eastern Pacific
      rows.append(dict(winds=tag, site=r['site'], month=r['month'], transit_d=transit, europe_first_pass_d=first,
                       canada_south_d=canada_s, atlantic_d=atlantic, north_or_pacific_d=other,
                       max_lat=r['max_lat'], polar_h=r.get('polar_h', np.nan), passes=r['passes'], end=r['end']))
  m = pd.DataFrame(rows)
  m['season'] = m.month.map(lambda x: 'DJF' if x in (12, 1, 2) else 'MAM' if x in (3, 4, 5) else 'JJA' if x in (6, 7, 8) else 'SON')
  m.to_csv('results/site_mix_canada_markets.csv', index=False)
  cols = ['transit_d', 'canada_south_d', 'atlantic_d', 'north_or_pacific_d', 'europe_first_pass_d']
  g = m.groupby('season')[cols].mean().reindex(['DJF', 'MAM', 'JJA', 'SON'])
  g.loc['year'] = m[cols].mean()
  tot = m.groupby('season').apply(lambda x: x.europe_first_pass_d.sum() / (x.europe_first_pass_d + x.transit_d).sum(), include_groups=False)
  g['Europe share of days'] = tot.reindex(g.index)
  g.loc['year', 'Europe share of days'] = m.europe_first_pass_d.sum() / (m.europe_first_pass_d + m.transit_d).sum()
  section('Canada flight, days by market before termination over Europe (72 flights; Canada and Atlantic measured by mask, the split estimated)')
  print(md(g.reset_index().rename(columns={'season': 'season of launch', 'transit_d': 'transit d', 'canada_south_d': 'Canada south of 60N d',
                                           'atlantic_d': 'Atlantic 40-60N d', 'north_or_pacific_d': 'north of 60N or Pacific d',
                                           'europe_first_pass_d': 'Europe first pass d'}), '{:.2f}'))
  print(f"Peak latitude at or above 61.6N (needed to come within 200 km of Iceland): {100 * (m.max_lat >= 61.6).mean():.0f} % of flights "
        f"(ERA5 {100 * (m[m.winds == 'era5'].max_lat >= 61.6).mean():.0f} %, NCEP {100 * (m[m.winds == 'ncep'].max_lat >= 61.6).mean():.0f} %); "
        f"above the Arctic Circle {100 * (m.max_lat >= 66.5).mean():.0f} %; ERA5 flights spend {m[m.winds == 'era5'].polar_h.mean():.0f} h above 66.5N on average.")
  for name, b in [('Canada south band 49-60N, 141-52W', dict(lat0=49, lat1=60, lon0=-141, lon1=-52)),
                  ('Canadian Arctic 60-70N, 141-60W', dict(lat0=60, lat1=70, lon0=-141, lon1=-60)),
                  ('North Atlantic lanes 45-62N, 50-10W', dict(lat0=45, lat1=62, lon0=-50, lon1=-10)),
                  ('Iceland, Faroes, Greenland coast box 60-67N, 45-5W', dict(lat0=60, lat1=67, lon0=-45, lon1=-5)),
                  ('Atlantic mask of the run files 40-60N, 52-10W', dict(lat0=40, lat1=60, lon0=-52, lon1=-10)),
                  ('Grand Banks and Flemish Cap 42-49N, 52-42W', dict(lat0=42, lat1=49, lon0=-52, lon1=-42)),
                  ('Iceland and Faroes waters 60-67N, 30-3W', dict(lat0=60, lat1=67, lon0=-30, lon1=-3)),
                  ('Norwegian Sea 62-75N, 5W-20E', dict(lat0=62, lat1=75, lon0=-5, lon1=20))]:
    km2 = box_km2(b)
    print(f'{name}: {km2 / 1e6:.2f} M km2; one 80 km disc covers {100 * math.pi * 80 ** 2 / km2:.2f} % of it, a 200 km disc {100 * math.pi * 200 ** 2 / km2:.1f} %.')


if __name__ == '__main__':
  pd.set_option('display.width', 250)
  what = sys.argv[1:] or ['inputs', 'singles', 'shares', 'sweep', 'markets']
  for w in what:
    globals()[w]()

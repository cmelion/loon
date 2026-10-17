"""Multi-pass vs one-way flights: Europe coverage per flight and launch rate.

For an envelope life L, a flight ends at its first recovery opportunity over
Europe (within RELEASE_KM of a recovery site) at or after day L; if none comes
before the flight dies or the run ends, it ends there and the radio is lost.
Launch rate for a given number of balloons over Europe scales with
1 / (mean Europe-days per flight) (Little's law), so the cost ratio against
the one-way 'slow' flights in results/drift_2025.csv is the ratio of those
means, times any extra per-flight cost of a longer-lived envelope.
"""
import json
import sys

import numpy as np
import pandas as pd

LIVES = [30, 60, 100, 150]
EXTRA_COST = (1.0, 1.25, 1.5)  # per-flight cost multiplier for a long-life envelope, ASSUMPTION


def eu_days_at(daily, day):
  if day <= 0 or not daily:
    return 0.0
  i = min(int(day), len(daily)) - 1
  return daily[i] / 24 if i >= 0 else 0.0


def littles_mean(df, col):
  """Day-weighted harmonic mean over months of the per-month mean (as cost_model)."""
  m = df.groupby('month')[col].mean()
  days = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])[m.index - 1]
  return days.sum() / (days / m.values).sum()


def main():
  src = sys.argv[1] if len(sys.argv) > 1 else 'results/multipass_2025.jsonl'
  rows = [json.loads(l) for l in open(src)]
  one = pd.read_csv('results/drift_2025.csv')
  one = one[one.controller == 'slow'].assign(eu=lambda d: d.dwell_h / 24)
  base = littles_mean(one, 'eu')
  print(f'One-way slow flights: Little-weighted Europe-days/flight {base:.2f}, '
        f'radio recovered {one.recovered.mean():.0%}')
  df = pd.DataFrame(rows)
  print(f'\nMulti-pass runs: n={len(df)}; flight days median {df.days.median():.0f} '
        f'(max {df.days.max():.0f}); ends: {df.end.value_counts().to_dict()}')
  print(f'laps median {df.laps.median():.2f}; Europe passes median '
        f'{df.passes.median():.0f} (max {df.passes.max()})')
  sec = pd.DataFrame(list(df.sector_days)).div(df.days, axis=0)
  print('Share of flight time by sector (mean):',
        (sec.mean() * 100).round(0).to_dict(), f'| over land {df.land_frac.mean():.0%}')

  out = []
  for L in LIVES:
    ends, eu, rec = [], [], []
    for r in rows:
      opp = [d for d in r['recover_days'] if d >= L]
      if opp and opp[0] <= r['days']:
        e, ok = opp[0], True
      else:
        e, ok = r['days'], False
      ends.append(e); rec.append(ok); eu.append(eu_days_at(r['daily_eu_h'], e))
    d = df.assign(end_day=ends, eu=eu, recovered=rec)
    lm = littles_mean(d, 'eu')
    out.append(dict(life_days=L, flight_days=np.median(ends),
                    europe_days_mean=d.eu.mean(), europe_days_little=lm,
                    duty_frac=d.eu.sum() / d.end_day.sum(),
                    recovered=d.recovered.mean(),
                    launches_vs_oneway=base / lm,
                    **{f'cost_vs_oneway_x{c}': c * base / lm for c in EXTRA_COST},
                    fleet_aloft_vs_oneway=(d.end_day.sum() / d.eu.sum())))
  t = pd.DataFrame(out)
  pd.set_option('display.width', 200)
  print('\n', t.round(2).to_string(index=False))
  win = [r for r in rows if r['month'] in (12, 1, 2, 3)]
  sm = [r for r in rows if r['month'] in (6, 7, 8)]
  for name, g in (('winter launches', win), ('summer launches', sm)):
    print(f'{name}: median laps {np.median([r["laps"] for r in g]):.2f}, '
          f'Europe-days at 60 d {np.mean([eu_days_at(r["daily_eu_h"], 60) for r in g]):.1f}')
  t.to_csv(src.replace('.jsonl', '_summary.csv'), index=False)


if __name__ == '__main__':
  main()

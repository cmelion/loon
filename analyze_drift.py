"""Summarise the slow-traversal + glide-return sweep (results/drift_2025.csv)."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CELLS = 1674  # 50 km-radius hexes covering the region (see analyze.py)
M = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct',
     'Nov', 'Dec']
COL = {'passive': '#8c8c8c', 'slow': '#1f77b4', 'home': '#d62728'}

df = pd.read_csv('results/drift_2025.csv')
df['recover_h'] = np.where(df.recovered, df.release_h + df.glide_h, np.nan)
df['radio_h'] = df.dwell_h  # radio flown to exit, not recovered

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
for k, g in df.groupby('controller'):
  m = g.groupby('month')
  axes[0].plot(range(1, 13), m.dwell_h.median() / 24, '-o', color=COL[k], label=k)
  axes[0].fill_between(range(1, 13), m.dwell_h.quantile(.25) / 24,
                       m.dwell_h.quantile(.75) / 24, color=COL[k], alpha=.12)
  axes[1].plot(range(1, 13), m.recovered.mean(), '-o', color=COL[k], label=k)
for ax, t in zip(axes, ['Days over region per balloon (median, IQR band)',
                        'Fraction of radios recovered by glider']):
  ax.set_xticks(range(1, 13), M); ax.set_title(t); ax.grid(alpha=.3)
axes[0].set_ylabel('days'); axes[1].set_ylim(0, 1); axes[0].legend()
fig.suptitle('Slow-traversal balloons over Europe→Black Sea, real 2025 winds '
             '(5 launch sites × 24 dates)')
fig.tight_layout(); fig.savefig('results/drift_summary.png', dpi=150)

pd.set_option('display.width', 200)
print(df.pivot_table(index='controller', columns='month', values='dwell_h',
                     aggfunc='median').div(24).round(1).to_string())
s = df.groupby('controller').agg(
    median_days=('dwell_h', lambda x: x.median() / 24),
    mean_days=('dwell_h', lambda x: x.mean() / 24),
    max_days=('dwell_h', lambda x: x.max() / 24),
    recovered=('recovered', 'mean'),
    days_lost_to_recovery=('dwell_h', lambda x: np.nan),
    glide_h=('glide_h', 'median'))
rec = df[df.recovered]
s['days_lost_to_recovery'] = (rec.dwell_h - rec.recover_h).groupby(
    rec.controller).median() / 24
s['launches_per_day'] = CELLS / s.mean_days
print('\n', s.round(2).to_string())
print('\nEnd modes:\n', df.pivot_table(index='controller', columns='end',
                                       values='seed', aggfunc='count',
                                       fill_value=0).to_string())
print('\nBy launch site (slow, median days):',
      (df[df.controller == 'slow'].groupby('site').dwell_h.median() / 24)
      .round(1).to_dict())

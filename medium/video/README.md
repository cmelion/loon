# Loon Over Europe — video for the Medium draft

Preview page (private until shared): https://claude.ai/artifact/7QxZbrJQWCuUiqrsRwmWF9
File: `loon-tracks.mp4` (1:32, 1920×1080, 30 fps, narrated, captioned). Build scripts in this folder; `bake.mjs` reads `../../results/` after `npm install`, `gen.py` needs the per-segment WAVs from `vo.py` (not committed), `render.py` needs Playwright.

## What it shows, and where each number comes from

| Scene | On screen | Source in cmelion/loon |
|---|---|---|
| A year of real winds | 5 launch sites, the study region, all 120 slow-controller tracks as a faint web | `results/slow_tracks.csv`, `run_drift.py` LAUNCH |
| January | Jan–Mar tracks animated to 3 simulated days | `results/slow_tracks.csv` |
| June | Jun–Jul tracks animated to 14 simulated days | same |
| A conveyor, not a hover | all twelve months in sequence; bar chart of mean days over the region per flight, slow controller (1.5–2.5 d winter, 6–14 d summer) | `results/drift_2025.csv` |
| The radio glides home | release points → recovery sites for the slow-controller flights; two red misses west of Brest | `results/drift_2025.csv` (release/site), `results/glider_tuning.md` (ceiling: Brest 04-01 and 08-01 never within range), `results/jet_test.md` (98.3 % with full-column winds) |
| Release timing is the cost | 3.65 d / €3.4 B as costed; 2.48 d / €5.0 B hindsight; 1.98 d / €6.3 B five-day forecast; 0.91 d / €13.6 B one-day; three unproven items | `TECHNICAL_ISSUES.md` §1, §4, §8, `results/forecast_release.md` |

Map: the same conic-conformal base as the explainers, re-projected with d3-geo and verified against the baked city positions to within 0.3 px (`bake.mjs`). Every country is drawn the same; no tints. Every scene carries the tag "Simulated tracks · BLE 1.0.1 · GFS 2025 · 2.5° × 5° grid".

## What it deliberately does not say

- No 98 % without the ceiling caveat; no 5.4-day dwell; no "95 % coverage".
- No capacity, jamming or Starlink comparison.
- The cost scene states €6.3 B as the planning case, per the issues register, with €3.4 B labelled "as first costed".

## Hosting on Medium

Medium does not take an MP4 upload. Upload `loon-tracks.mp4` to YouTube (unlisted is fine) or Vimeo, then paste the watch URL on its own line in the Medium editor; Medium turns it into an embed. Suggested placement: after "How we tested it", before Finding 1, with a one-line caption: "Ninety seconds of the 2025 runs: winter blows balloons out in a day or two, summer lets them linger, and the radio's glide home sets the cost."

## If the article's numbers change

Re-run `node bake.mjs` (reads `results/` from the clone) and `python3 gen.py`, re-voice any changed segment with `vo.py`, then `python3 render.py 30`. The cost table lives in `template.html` (ROWS) and must be edited by hand to match `TECHNICAL_ISSUES.md`.

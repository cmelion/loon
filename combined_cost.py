"""Combined per-flight and fleet cost from the measured levers (low/mid/high).

Starts from cost_model.py's per-flight medians (results/cost_comparison.md)
and applies, multiplicatively:
  * lighter hardware -> smaller envelope (superpressure envelope mass roughly
    proportional to lift; BLE: 0.74 kg envelope per kg payload),
  * envelope learning curve at volume (cost_reduction.py lever L1),
  * tuned glider recovery 98 % (results/glider_tuning.md) in cost_model's
    payload amortisation, cheaper lighter payload,
  * gig-economy recovery pickups,
  * launch strategy dwell multiplier (mobile / best site per date, measured
    with hindsight in results/ship_vs_land_2025.csv and drift_2025.csv),
  * footprint radius 60-80 km (cost_reduction.py lever L7) as an option.
Every factor is a (low, mid, high) ASSUMPTION or measurement, labelled below.
"""
BASE_FLEET_EUR = 15.4e9          # cost_model baseline, 95 % year-round
BASE_PER_FLIGHT = dict(envelope=12_472, payload=16_785, hydrogen=127, launch=1_267,
                       recovery=1_175, network=156, regulatory=320)
OVERHEAD = 0.15                  # cost_model G&A mode
STARLINK_EUR_KM2 = 27.0          # cost_model median, per km^2 per yr
REGION_KM2 = 10.85e6

# (best, mid, worst) — best = lowest cost
PAYLOAD_KG = (30, 40, 55)                 # vs BLE 92.5 kg, ASSUMPTION (fuel cell, wing solar, modern radio)
ENV_LEARNING = (0.25, 0.4, 0.6)          # volume manufacturing vs today's mode, cost_reduction L1 range
PAYLOAD_UNIT = (0.5, 0.7, 1.0)            # lighter hardware unit cost vs €35k, ASSUMPTION
RECOVERY = (0.983, 0.980, 0.975)          # glider_tuning.md Monte Carlo P90/median/P10
PAYLOAD_LIFE = (25, 15, 8)                # flights per payload, cost_model range
REFURB = (0.05, 0.10, 0.20)               # per reuse, cost_model range
GIG_PICKUP = (0.35, 0.5, 0.8)             # recovery line multiplier, ASSUMPTION
DWELL_MULT = (1.6, 1.35, 1.15)            # launch-site choice; hindsight best-of-date gave 1.62-1.75
FOOTPRINT = (0.45, 0.49, 0.6)             # cost_reduction L7 (optional)


def payload_consumed(rec, life, refurb):
  # cost_model's form: lost fraction + retirement + refurbishment per flight
  return (1 - rec) + rec / life + rec * refurb


def main():
  base_cons = payload_consumed(0.78, 15, 0.10)
  rows = []
  for k, name in enumerate(('best', 'mid', 'worst')):
    env = BASE_PER_FLIGHT['envelope'] * (0.74 * PAYLOAD_KG[k]) / 68.5 * ENV_LEARNING[k]
    pay = (BASE_PER_FLIGHT['payload'] * PAYLOAD_UNIT[k] *
           payload_consumed(RECOVERY[k], PAYLOAD_LIFE[k], REFURB[k]) / base_cons)
    rec = BASE_PER_FLIGHT['recovery'] * GIG_PICKUP[k]
    other = sum(BASE_PER_FLIGHT[x] for x in ('hydrogen', 'launch', 'network', 'regulatory'))
    per_flight = (env + pay + rec + other) * (1 + OVERHEAD)
    base_flight = sum(BASE_PER_FLIGHT.values()) * (1 + OVERHEAD)
    fleet = BASE_FLEET_EUR * per_flight / base_flight / DWELL_MULT[k]
    rows.append((name, env, pay, per_flight, fleet, fleet * FOOTPRINT[k]))
  print(f'{"case":6s} {"envelope":>9s} {"payload":>9s} {"per flight":>11s} '
        f'{"fleet €/yr":>11s} {"x Starlink":>10s} {"+60-80 km":>10s} {"x Starlink":>10s}')
  for name, env, pay, pf, fl, fl2 in rows:
    s1 = fl / REGION_KM2 / STARLINK_EUR_KM2
    s2 = fl2 / REGION_KM2 / STARLINK_EUR_KM2
    print(f'{name:6s} {env:9,.0f} {pay:9,.0f} {pf:11,.0f} {fl / 1e9:10.1f}B {s1:9.1f}x '
          f'{fl2 / 1e9:9.1f}B {s2:9.1f}x')
  print(f'\nbaseline per flight €{sum(BASE_PER_FLIGHT.values()) * (1 + OVERHEAD):,.0f}; '
        f'fleet €{BASE_FLEET_EUR / 1e9:.1f}B = '
        f'{BASE_FLEET_EUR / REGION_KM2 / STARLINK_EUR_KM2:.0f}x Starlink')


if __name__ == '__main__':
  main()

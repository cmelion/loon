"""Sanity baseline: StationSeeker in stock BLE (generative winds, tropics)."""
import multiprocessing as mp, warnings

def fly(seed):
  warnings.filterwarnings('ignore')
  from balloon_learning_environment.agents import station_seeker_agent
  from balloon_learning_environment.env import balloon_arena, features, generative_wind_field
  from balloon_learning_environment.env.balloon import balloon, control
  from balloon_learning_environment.utils import units
  a = balloon_arena.BalloonArena(features.PerciatelliFeatureConstructor,
                                 generative_wind_field.GenerativeWindField(), seed)
  ag = station_seeker_agent.StationSeekerAgent(3, None)
  act, w = ag.begin_episode(a.feature_constructor.get_features()), 0
  for _ in range(960):
    obs = a.step(control.AltitudeControlCommand(act)); s = a.get_balloon_state()
    w += units.relative_distance(s.x, s.y).km <= 50
    act = ag.step(0.0, obs)
  return w / 960

if __name__ == '__main__':
  with mp.get_context('spawn').Pool(8) as p: r = p.map(fly, range(16))
  print('stock BLE StationSeeker TWR50:', [round(x, 2) for x in r], 'mean', sum(r) / len(r))

import core.state as state
from core.state import check_current_year, stat_state, check_energy_level
from utils.log import info, warning, error, debug

# Get priority stat from config
def get_stat_priority(stat_key: str) -> int:
  return state.PRIORITY_STAT.index(stat_key) if stat_key in state.PRIORITY_STAT else 999

def check_all_elements_are_same(d):
    sections = list(d.values())
    return all(section == sections[0] for section in sections[1:])

# Will do train with the most support card
# Used in the first year (aim for rainbow)
def most_support_card(results):
  # Seperate wit
  wit_data = results.get("wit")

  # Get all training but wit
  non_wit_results = {
    k: v for k, v in results.items()
    if k != "wit" and int(v["failure"]) <= state.MAX_FAILURE
  }

  # Check if train is bad
  all_others_bad = len(non_wit_results) == 0
  energy_level, max_energy = check_energy_level()
  if energy_level < state.SKIP_TRAINING_ENERGY:
    info("All trainings are unsafe and WIT training won't help go back up to safe levels, resting instead.")
    return None

  if all_others_bad and wit_data and int(wit_data["failure"]) <= state.MAX_FAILURE and wit_data["total_supports"] >= 2:
    info("All trainings are unsafe, but WIT is safe and has enough support cards.")
    return "wit"

  filtered_results = {
    k: v for k, v in results.items() if int(v["failure"]) <= state.MAX_FAILURE
  }

  if not filtered_results:
    info("No safe training found. All failure chances are too high.")
    return None

  # this is the weight adder used for skewing results of training decisions PRIORITY_EFFECTS_LIST[get_stat_priority(x[0])] * PRIORITY_WEIGHTS_LIST[priority_weight]
  # added hint 100%
  # Best training
  best_training = max(filtered_results.items(), key=training_score)

  best_key, best_data = best_training

  if best_data["total_supports"] <= 1:
    if int(best_data["failure"]) == 0:
      # WIT must be at least 2 support cards
      if best_key == "wit":
        if energy_level > state.NEVER_REST_ENERGY:
          info(f"Only 1 support and it's WIT but energy is too high for resting to be worth it. Still training.")
          return "wit"
        else:
          info(f"Only 1 support and it's WIT. Skipping.")
          return None
      info(f"Only 1 support but 0% failure. Prioritizing based on priority list: {best_key.upper()}")
      return best_key
    else:
      info("Low value training (only 1 support). Choosing to rest.")
      return None

  info(f"Best training: {best_key.upper()} with {best_data['total_supports']} support cards and {best_data['failure']}% fail chance")
  return best_key

PRIORITY_WEIGHTS_LIST={
  "HEAVY": 0.75,
  "MEDIUM": 0.5,
  "LIGHT": 0.25,
  "NONE": 0
}

def training_score(x):
  global PRIORITY_WEIGHTS_LIST
  priority_weight = PRIORITY_WEIGHTS_LIST[state.PRIORITY_WEIGHT]
  base = x[1]["total_supports"]
  if x[1]["total_hints"] > 0:
      base += 0.5
  multiplier = 1 + state.PRIORITY_EFFECTS_LIST[get_stat_priority(x[0])] * priority_weight
  total = base * multiplier

  # Debug output
  debug(f"{x[0]} -> base={base}, multiplier={multiplier}, total={total}, priority={get_stat_priority(x[0])}")

  return (total, -get_stat_priority(x[0]))

# Do rainbow training
def rainbow_training(results):
  # 2 points for rainbow supports, 1 point for normal supports, stat priority tie breaker
  rainbow_candidates = results

  for stat_name in rainbow_candidates:
    data = rainbow_candidates[stat_name]
    total_rainbow_friends = data[stat_name]["friendship_levels"]["yellow"] + data[stat_name]["friendship_levels"]["max"]
    #adding total rainbow friends on top of total supports for two times value nudging the formula towards more rainbows
    rainbow_points = total_rainbow_friends + data["total_supports"]
    if total_rainbow_friends > 0:
      rainbow_points = rainbow_points + 0.5
    rainbow_candidates[stat_name]["rainbow_points"] = rainbow_points
    rainbow_candidates[stat_name]["total_rainbow_friends"] = total_rainbow_friends

  # Get rainbow training
  rainbow_candidates = {
    stat: data for stat, data in results.items()
    if int(data["failure"]) <= state.MAX_FAILURE
       and data["rainbow_points"] >= 2
       and not (stat == "wit" and data["total_rainbow_friends"] < 1)
     # and data[stat]["friendship_levels"]["yellow"] + data[stat]["friendship_levels"]["max"] > 0
  }

  if not rainbow_candidates:
    info("No rainbow training found under failure threshold.")
    return None

  # Find support card rainbow in training
  best_rainbow = max(
    rainbow_candidates.items(),
    key=lambda x: (
      x[1]["rainbow_points"],
      -get_stat_priority(x[0])
    )
  )

  best_key, best_data = best_rainbow
  if best_key == "wit":
    #if we get to wit, we must have at least 1 rainbow friend
    if data["total_rainbow_friends"] >= 1:
      info(f"Wit training has most rainbow points but it doesn't have any rainbow friends, skipping.")
      return None

  info(f"Rainbow training selected: {best_key.upper()} with {best_data['rainbow_points']} rainbow points and {best_data['failure']}% fail chance")
  return best_key

def filter_by_stat_caps(results, current_stats):
  return {
    stat: data for stat, data in results.items()
    if current_stats.get(stat, 0) < state.STAT_CAPS.get(stat, 1200)
  }

def all_values_equal(dictionary):
    values = list(dictionary.values())
    return all(value == values[0] for value in values[1:])

# Decide training
def do_something(results):
  year = check_current_year()
  current_stats = stat_state()
  info(f"Current stats: {current_stats}")

  filtered = filter_by_stat_caps(results, current_stats)

  if not filtered:
    info("All stats capped or no valid training.")
    return None

  if "Junior Year" in year:
    return most_support_card(filtered)
  else:
    result = rainbow_training(filtered)
    if result is None:
      info("Falling back to most_support_card because rainbow not available.")
      return most_support_card(filtered)
  return result

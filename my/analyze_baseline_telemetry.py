"""Telemetry analyzer for baseline_main.py.
Runs 20 games and logs detailed internal state:
- Route chosen
- Sells executed vs missed
- Dead stock sold vs shed leftovers at step 719
- Money balance trajectory
"""
import os
import sys
from kaggle_environments import make

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

sys.path.insert(0, "my")
import baseline_main

def run_telemetry(n_games=20):
    route_counts = {}
    total_leftover_val = 0
    leftover_by_item = {}
    scores = []
    
    for seed in range(42, 42 + n_games):
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        baseline_main._A = None
        env.run([baseline_main.agent, "random"])
        
        agent_obj = baseline_main._A
        final_route = agent_obj.cur
        route_name = {
            "7015cc00": "MAIN",
            "dc76e400": "YARN",
            "ab9669b9": "YARN_CARROT",
            "a84d06f1": "MILK_GLUT"
        }.get(final_route, final_route)
        route_counts[route_name] = route_counts.get(route_name, 0) + 1
        
        score = env.steps[-1][0]["reward"]
        scores.append(score)
        
        # Check shed at last step
        last_obs = env.steps[-1][0]["observation"]
        me = int(last_obs.get("player", 0))
        shed = last_obs.get("private", {}).get("shed", {})
        prices = last_obs.get("market", {}).get("prices", {})
        money = last_obs.get("farms", [{}])[me].get("money", 0)
        
        game_leftover = 0
        for it, qty in shed.items():
            if qty > 0:
                p = prices.get(it, 0)
                game_leftover += p * qty
                leftover_by_item[it] = leftover_by_item.get(it, 0) + qty
        total_leftover_val += game_leftover
        
        print(f"Seed {seed:3d}: Score={score:>8,.0f}, Route={route_name:>12s}, Money={money:>8,.0f}, Leftover Shed Value=${game_leftover:>5,.0f}")

    print("\n" + "="*60)
    print("SUMMARY TELEMETRY:")
    print(f"Mean Score: {sum(scores)/len(scores):,.0f}")
    print("Route distribution:", route_counts)
    print(f"Avg Leftover Shed Value per game: ${total_leftover_val/n_games:,.0f}")
    print("Total leftover items across all games:", leftover_by_item)
    print("="*60)

if __name__ == "__main__":
    run_telemetry(20)

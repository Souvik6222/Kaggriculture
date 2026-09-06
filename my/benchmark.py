"""Benchmark framework for Kaggriculture agents.

Runs N games with different seeds, records scores, and compares agents.
Usage:
    python3 my/benchmark.py              # V4 vs random (quick test)
    python3 my/benchmark.py --vs-baseline # V4 vs baseline head-to-head
    python3 my/benchmark.py --ablation   # Ablation testing
"""
import sys
import os
import time
import importlib
import argparse

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Suppress noisy warnings
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from kaggle_environments import make


def run_game(agent1, agent2, seed=None, steps=720):
    """Run a single game and return (score1, score2, elapsed)."""
    config = {"episodeSteps": steps}
    if seed is not None:
        config["seed"] = seed
    t0 = time.time()
    env = make("kaggriculture", configuration=config)
    env.run([agent1, agent2])
    elapsed = time.time() - t0
    s1 = env.steps[-1][0]["reward"]
    s2 = env.steps[-1][1]["reward"]
    return s1, s2, elapsed


def benchmark_vs_random(agent_path, n_games=10, label="Agent"):
    """Benchmark agent against random baseline."""
    print(f"\n{'='*60}")
    print(f"  {label} vs RANDOM — {n_games} games")
    print(f"{'='*60}")

    wins = 0
    losses = 0
    ties = 0
    scores = []
    opp_scores = []
    total_time = 0

    for i in range(n_games):
        seed = 42 + i
        try:
            s1, s2, elapsed = run_game(agent_path, "random", seed=seed)
            scores.append(s1)
            opp_scores.append(s2)
            total_time += elapsed

            result = "WIN" if s1 > s2 else ("LOSS" if s1 < s2 else "TIE")
            if s1 > s2:
                wins += 1
            elif s1 < s2:
                losses += 1
            else:
                ties += 1

            print(f"  Game {i+1:3d}/{n_games}: {result:4s}  "
                  f"Score: {s1:>8,.0f} vs {s2:>8,.0f}  "
                  f"Gap: {s1-s2:>+8,.0f}  "
                  f"Time: {elapsed:.1f}s")
        except Exception as e:
            print(f"  Game {i+1:3d}/{n_games}: ERROR — {e}")
            scores.append(0)
            opp_scores.append(0)

    if scores:
        avg = sum(scores) / len(scores)
        opp_avg = sum(opp_scores) / len(opp_scores)
        sorted_scores = sorted(scores)
        median = sorted_scores[len(sorted_scores)//2]
        win_rate = wins / n_games * 100

        print(f"\n{'─'*60}")
        print(f"  RESULTS: {label}")
        print(f"{'─'*60}")
        print(f"  Win Rate:     {win_rate:.1f}% ({wins}W-{losses}L-{ties}T)")
        print(f"  Avg Score:    {avg:,.0f}")
        print(f"  Median Score: {median:,.0f}")
        print(f"  Avg Opp:      {opp_avg:,.0f}")
        print(f"  Avg Gap:      {avg-opp_avg:+,.0f}")
        print(f"  Total Time:   {total_time:.1f}s ({total_time/n_games:.1f}s/game)")
        print(f"{'─'*60}\n")

    return {
        "wins": wins, "losses": losses, "ties": ties,
        "win_rate": wins / max(n_games, 1) * 100,
        "avg_score": sum(scores) / max(len(scores), 1),
        "scores": scores,
    }


def benchmark_head_to_head(agent1_path, agent2_path, n_games=10,
                            label1="Agent1", label2="Agent2"):
    """Run head-to-head games, alternating seats."""
    print(f"\n{'='*60}")
    print(f"  {label1} vs {label2} — {n_games} games (alternating seats)")
    print(f"{'='*60}")

    wins1 = 0
    wins2 = 0
    ties = 0

    for i in range(n_games):
        seed = 100 + i
        try:
            if i % 2 == 0:
                # Agent1 as player 0
                s1, s2, elapsed = run_game(agent1_path, agent2_path, seed=seed)
                a1_score, a2_score = s1, s2
            else:
                # Agent1 as player 1
                s1, s2, elapsed = run_game(agent2_path, agent1_path, seed=seed)
                a1_score, a2_score = s2, s1

            result = f"{label1}" if a1_score > a2_score else (f"{label2}" if a1_score < a2_score else "TIE")
            if a1_score > a2_score:
                wins1 += 1
            elif a1_score < a2_score:
                wins2 += 1
            else:
                ties += 1

            seat = "P0" if i % 2 == 0 else "P1"
            print(f"  Game {i+1:3d}/{n_games} ({seat}): {result:>12s}  "
                  f"{label1}: {a1_score:>8,.0f}  {label2}: {a2_score:>8,.0f}  "
                  f"Time: {elapsed:.1f}s")
        except Exception as e:
            print(f"  Game {i+1:3d}/{n_games}: ERROR — {e}")

    print(f"\n{'─'*60}")
    print(f"  HEAD-TO-HEAD RESULTS")
    print(f"{'─'*60}")
    total = wins1 + wins2 + ties
    print(f"  {label1}: {wins1}W ({wins1/max(total,1)*100:.1f}%)")
    print(f"  {label2}: {wins2}W ({wins2/max(total,1)*100:.1f}%)")
    print(f"  Ties: {ties}")
    print(f"{'─'*60}\n")

    return {"wins1": wins1, "wins2": wins2, "ties": ties}


def main():
    parser = argparse.ArgumentParser(description="Kaggriculture Agent Benchmark")
    parser.add_argument("--vs-baseline", action="store_true",
                        help="Run V4 vs baseline head-to-head")
    parser.add_argument("--ablation", action="store_true",
                        help="Run ablation tests")
    parser.add_argument("-n", "--num-games", type=int, default=10,
                        help="Number of games per test (default: 10)")
    args = parser.parse_args()

    n = args.num_games

    # Quick sanity: V4 vs random
    print("\n" + "="*60)
    print("  KAGGRICULTURE BENCHMARK SUITE")
    print("="*60)

    v4_results = benchmark_vs_random("my/v4_main.py", n_games=n, label="V4")
    baseline_results = benchmark_vs_random("my/baseline_main.py", n_games=n, label="Baseline")

    print("\n" + "="*60)
    print("  COMPARISON: V4 vs Baseline (both against random)")
    print("="*60)
    print(f"  V4 Win Rate:       {v4_results['win_rate']:.1f}%")
    print(f"  Baseline Win Rate: {baseline_results['win_rate']:.1f}%")
    print(f"  V4 Avg Score:      {v4_results['avg_score']:,.0f}")
    print(f"  Baseline Avg Score:{baseline_results['avg_score']:,.0f}")
    delta = v4_results['avg_score'] - baseline_results['avg_score']
    print(f"  Score Delta:       {delta:+,.0f}")
    print("="*60 + "\n")

    if args.vs_baseline:
        benchmark_head_to_head(
            "my/v4_main.py", "my/baseline_main.py",
            n_games=n, label1="V4", label2="Baseline"
        )


if __name__ == "__main__":
    main()

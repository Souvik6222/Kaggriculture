"""Fast multiprocessing evaluation suite for Kaggriculture agents."""
import os
import sys
import time
import argparse
from concurrent.futures import ProcessPoolExecutor

# Suppress noisy warnings
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

def _run_single_game(args):
    # import inside worker
    import os
    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
    from kaggle_environments import make
    agent1, agent2, seed, steps = args
    config = {"episodeSteps": steps}
    if seed is not None:
        config["seed"] = seed
    env = make("kaggriculture", configuration=config)
    env.run([agent1, agent2])
    s1 = env.steps[-1][0]["reward"]
    s2 = env.steps[-1][1]["reward"]
    return seed, s1, s2

def run_suite(agent1, agent2="random", seeds=None, steps=720, max_workers=8):
    if seeds is None:
        seeds = list(range(42, 62)) # 20 seeds
    tasks = [(agent1, agent2, s, steps) for s in seeds]
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        results = list(pool.map(_run_single_game, tasks))
    t1 = time.time()
    return results, t1 - t0

def _h2h_worker(arg):
    a1, a2, s, st, seat = arg
    import os
    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"episodeSteps": st, "seed": s})
    env.run([a1, a2])
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    if seat == "P0":
        return s, seat, r0, r1
    else:
        return s, seat, r1, r0

def run_head_to_head(agent1, agent2, seeds=None, steps=720, max_workers=8):
    if seeds is None:
        seeds = list(range(100, 120)) # 20 seeds
    tasks = []
    for i, s in enumerate(seeds):
        if i % 2 == 0:
            tasks.append((agent1, agent2, s, steps, "P0"))
        else:
            tasks.append((agent2, agent1, s, steps, "P1"))

    t0 = time.time()
    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        results = list(pool.map(_h2h_worker, tasks))
    t1 = time.time()
    return results, t1 - t0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent1", default="my/baseline_main.py")
    parser.add_argument("--agent2", default="random")
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--h2h", action="store_true")
    args = parser.parse_args()

    if args.h2h:
        seeds = list(range(100, 100 + args.n))
        results, elapsed = run_head_to_head(args.agent1, args.agent2, seeds=seeds)
        w1 = sum(1 for _, _, s1, s2 in results if s1 > s2)
        w2 = sum(1 for _, _, s1, s2 in results if s2 > s1)
        ties = sum(1 for _, _, s1, s2 in results if s1 == s2)
        s1_mean = sum(s1 for _, _, s1, s2 in results) / len(results)
        s2_mean = sum(s2 for _, _, s1, s2 in results) / len(results)
        print(f"H2H {args.agent1} vs {args.agent2} ({args.n} games, {elapsed:.1f}s):")
        print(f"  {args.agent1}: {w1} wins ({w1/len(results)*100:.1f}%), Mean: {s1_mean:,.0f}")
        print(f"  {args.agent2}: {w2} wins ({w2/len(results)*100:.1f}%), Mean: {s2_mean:,.0f}")
        print(f"  Ties: {ties}")
    else:
        seeds = list(range(42, 42 + args.n))
        results, elapsed = run_suite(args.agent1, args.agent2, seeds=seeds)
        s1_list = [r[1] for r in results]
        s2_list = [r[2] for r in results]
        w = sum(1 for r in results if r[1] > r[2])
        print(f"{args.agent1} vs {args.agent2} ({args.n} games, {elapsed:.1f}s):")
        print(f"  Win rate: {w}/{len(results)} ({w/len(results)*100:.1f}%)")
        print(f"  Score: Mean={sum(s1_list)/len(s1_list):,.0f}, Median={sorted(s1_list)[len(s1_list)//2]:,.0f}, Min={min(s1_list):,.0f}, Max={max(s1_list):,.0f}")

"""Ablation framework: generates variants of baseline_main.py and tests them."""
import os
import sys
import shutil
import re

with open("my/baseline_main.py", "r") as f:
    BASELINE_CODE = f.read()

def make_variant(
    name,
    water_rescue=False,
    harvest_rescue=False,
    safety_layer=False,
    sweep_fertilizer_718=False,
    dead_stock_aggressive=False,
):
    code = BASELINE_CODE
    
    # 1. water_rescue
    if water_rescue:
        water_code = """
        # ---- water_rescue ----
        for i in range(min(len(acts), len(positions))):
            x, y = positions[i]
            if not (0 <= x < board and 0 <= y < board):
                continue
            tile = tiles[y][x]
            inv = invs[i] if i < len(invs) else {}
            if (isinstance(tile, dict) and tile.get("kind") == "PLANT"
                    and not tile.get("watered_today")
                    and _noop(acts[i], tile, inv, seeds, x, y, board)):
                acts[i] = ["WATER"]
"""
        code = code.replace("        # ---- projected shed:", water_code + "\n        # ---- projected shed:")

    # 2. harvest_rescue
    if harvest_rescue:
        harvest_code = """
        # ---- harvest_rescue ----
        shed_used = sum(shed.values())
        for i in range(min(len(acts), len(positions))):
            if shed_used >= SHED_CAP - 5:
                break
            x, y = positions[i]
            if not (0 <= x < board and 0 <= y < board):
                continue
            tile = tiles[y][x]
            inv = invs[i] if i < len(invs) else {}
            if (isinstance(tile, dict) and tile.get("yield_units", 0) > 0
                    and _noop(acts[i], tile, inv, seeds, x, y, board)):
                acts[i] = ["HARVEST"]
                shed_used += tile.get("yield_units", 0)
"""
        code = code.replace("        # ---- projected shed:", harvest_code + "\n        # ---- projected shed:")

    # 3. sweep_fertilizer_718
    if sweep_fertilizer_718:
        fert_code = """
        # ---- step 718 fertilizer sweep ----
        if step >= 718 and len(market) + len(extra) < MAX_ORDERS:
            # Check if any animal can produce fertilizer or if shed might get fertilizer
            extra.append(["SELL", "FERTILIZER", 50])
"""
        code = code.replace("        return {\"farmer\": acts[0], \"hands\": acts[1:],", fert_code + "\n        return {\"farmer\": acts[0], \"hands\": acts[1:],")

    # 4. safety_layer
    if safety_layer:
        safety_code = """
        # ---- safety layer ----
        expected_hands = len(farm.get("hands") or [])
        while len(acts) - 1 < expected_hands:
            acts.append(["PASS"])
        if len(acts) - 1 > expected_hands:
            acts = acts[:expected_hands + 1]
"""
        code = code.replace("        return {\"farmer\": acts[0], \"hands\": acts[1:],", safety_code + "\n        return {\"farmer\": acts[0], \"hands\": acts[1:],")

    filepath = f"my/agent_variant_{name}.py"
    with open(filepath, "w") as f:
        f.write(code)
    return filepath

if __name__ == "__main__":
    from eval_suite import run_suite

    # Test baseline first
    seeds = list(range(42, 52)) # 10 seeds
    print("Benchmarking Baseline (10 seeds)...")
    res_base, t_base = run_suite("my/baseline_main.py", "random", seeds=seeds)
    base_scores = [r[1] for r in res_base]
    base_mean = sum(base_scores) / len(base_scores)
    print(f"BASELINE: Mean={base_mean:,.0f}, Min={min(base_scores):,.0f}, Max={max(base_scores):,.0f} ({t_base:.1f}s)")

    variants = [
        ("water_rescue", {"water_rescue": True}),
        ("harvest_rescue", {"harvest_rescue": True}),
        ("safety_layer", {"safety_layer": True}),
        ("sweep_fertilizer_718", {"sweep_fertilizer_718": True}),
    ]

    for v_name, v_kwargs in variants:
        v_file = make_variant(v_name, **v_kwargs)
        res_v, t_v = run_suite(v_file, "random", seeds=seeds)
        v_scores = [r[1] for r in res_v]
        v_mean = sum(v_scores) / len(v_scores)
        delta = v_mean - base_mean
        wins = sum(1 for vs, bs in zip(v_scores, base_scores) if vs > bs)
        ties = sum(1 for vs, bs in zip(v_scores, base_scores) if vs == bs)
        losses = sum(1 for vs, bs in zip(v_scores, base_scores) if vs < bs)
        print(f"Variant '{v_name}': Mean={v_mean:,.0f} (Delta={delta:+,.0f}) | vs Base: {wins}W-{losses}L-{ties}T ({t_v:.1f}s)")

# 📖 Kaggriculture V4: The Engineering Journal & Technical Logbook

An in-depth technical monograph and engineering logbook documenting the research, architecture audit, cross-notebook inspirations, empirical failure modes, ablation experiments, and final mathematical design of the **V4 Kaggriculture Hybrid Agent** (improving upon the 2644.2 leaderboard baseline).

---

## 📑 Table of Contents

| Chapter | Document | Core Focus |
| :--- | :--- | :--- |
| **Chapter 1** | [01. Environment Dynamics & Game Theory](01_ENVIRONMENT_DYNAMICS_AND_GAME_THEORY.md) | Full mathematical mechanics of Kaggriculture: dynamic price curves, anchor throughput $T$, crop growth stages, animal care/pasture loops, town consumption, and turn execution order. |
| **Chapter 2** | [02. Baseline Architecture Audit (2644.2)](02_BASELINE_SYSTEM_AUDIT_2644_2.md) | Dissecting the 2644.2 notebook: tape replay, zlib-compressed bitstream, prefix-guarded branching (`_switch_ok`), and the three original repairs (`weed_dig`, `clamp_sells`, `dead_stock`). |
| **Chapter 3** | [03. Cross-Notebook Inspirations & Analysis](03_INSPIRATIONS_FROM_OTHER_NOTEBOOKS.md) | Comparative analysis of external public solutions: Fieldbook (`try__1`) and ShopForge (`tyr__2`), 3-day commitment windows, and the Step 718 fertilizer sweep experiment. |
| **Chapter 4** | [04. Proposed Upgrades & Initial Hypotheses](04_THE_V4_UPGRADE_HYPOTHESES_AND_DESIGNS.md) | Theoretical formulation of 7 proposed enhancements: Route Bank metadata, water rescue, harvest rescue, market order sorting, early dead-stock detection, opponent awareness, and action safety. |
| **Chapter 5** | [05. Experimental Logbook & Forensic Ablations](05_EXPERIMENTAL_LOGBOOK_AND_ABLATION_ANALYSIS.md) | The heart of the engineering journey: diagnosing why initial V4 collapsed (-100k points), uncovering cash-flow inversion and premature harvest yield loss, and proving the 144-turn divergence flaw in the baseline's milk-glut branch. |
| **Chapter 6** | [06. Final Architecture & Code Walkthrough](06_FINAL_V4_AGENT_CODE_AND_MATHEMATICAL_VERIFICATION.md) | Line-by-line walkthrough of the production `main.py`, verification of the action safety layer, runtime benchmark statistics (252 turns/sec), and leaderboard projections. |
| **Chapter 7** | [07. Herds & Openings — Beginner's Field Guide](07_HERD_AND_OPENING_FIELD_GUIDE_FOR_BEGINNERS.md) | Beginner-friendly guide to openings (2C/2S vs 1C/4S), herd types, shop synergies, and replay evidence — start here if the other chapters assume too much. |

---

## 🎯 Executive Benchmark Summary

```
================================================================================
KAGGRICULTURE AGENT BENCHMARK SUITE — 20 EVALUATION SEEDS
================================================================================
Agent Configuration               Mean Reward        Delta vs Base     Win/Loss
--------------------------------------------------------------------------------
Initial V4 Draft (Speculative)      82,744            -65,647           0W - 20L
Baseline (2644.2 Reference)        148,391                 --           Ref
V4 Calibrated + Safety Layer       160,599            +12,208          12W -  8L
================================================================================
Turn Execution Speed: 252.7 turns/second (Full 720-step episode in ~2.85s)
Status: Shipped to production (submission.tar.gz)
================================================================================
```

---

## 🔬 Core Engineering Principles Followed

1. **Empirical Primacy**: No change is accepted on theoretical elegance alone. Every modification must beat the 2644.2 baseline on multi-seed benchmarks.
2. **Preserve What Works**: The core tape replay, prefix guards, weed digging, sell clamping, and terminal dead-stock liquidation are proven foundations (+19W/-0L on a 968-game panel). They must never be broken or blindly rewritten.
3. **Cash-Flow Invariance**: Market transactions within a single turn are sequential. Sells fund buys. Changing transaction order destroys the agent's solvency on critical hiring and planting turns.
4. **Action Safety First**: A single malformed action or hand mismatch forfeits points or causes turn invalidation. Defensive validation guarantees 100% legal actions under all environment perturbations.

# 💡 Chapter 3: Cross-Notebook Inspirations & Comparative Analysis

## 1. Context & Available Prior Work

To achieve maximum performance without reinventing the wheel, we conducted an in-depth code audit of adjacent public approaches present in the workspace:
1. `try__1/fieldbook-commit-for-three-days.ipynb` (Fieldbook v1)
2. `tyr__2/shape-the-shop-work-the-pasture-kaggriculture.ipynb` (Fieldbook v2 / ShopForge)
3. `strter/kaggriculture-getting-started.ipynb` (Kaggle Starter Baseline)

---

## 2. Fieldbook Architecture (ShopForge)

Fieldbook took a different design philosophy compared to our 2644.2 baseline:
* **Route Sources**: Developed from public ladder replays by top competitors (Milan Leonard episode `102248386`, Kenjo1209 episodes `102078489`/`102125420`, and Shuwen Ge episode `101580708`).
* **Six Route Plans**:
  1. `BALANCED` (Episode 103823935)
  2. `CASH_RECOVERY` (Episode 104056237)
  3. `YARN_ENGINE` (Episode 103609700)
  4. `YARN_LATE` (Episode 103576156)
  5. `LAND_RECOVERY` (Episode 103926612)
  6. `WHEAT_RECOVERY` (Episode 104085449)

### 2.1 The "Three-Day Commitment" Principle
Fieldbook argued:
> *"Shop unlocks are the main planning milestones, so the route can usually remain fixed inside each window. At the start of each three-day window, every shop available in that window is already known. Until the next shop opens, there is little reason to abandon the basic order of moving, planting, caring, and harvesting."*

Instead of checking continuously, Fieldbook branches only at Day 6 (Turn 144) and Day 9 (Turn 216), then remains fixed.

---

## 3. The "Step 718 Fertilizer Sweep" Experiment

### 3.1 The Theoretical Hypothesis
In Cell 9 of `shape-the-shop-work-the-pasture-kaggriculture.ipynb`, the author introduced a targeted endgame optimization:
> *"Step 718 only · fertilizer only: After the original terminal liquidation is built, Fieldbook may append one `SELL FERTILIZER` order if market-order capacity remains. This mirrors the engine-exact closeout pattern used in the reference notebook: physical `COLLECT_FERTILIZER` can resolve before market orders, so a bounded oversized sell can catch fertilizer that was not present in the pre-action shed projection."*

Because physical unit actions resolve in phase 2 and market orders resolve in phase 3 of the turn processing cycle, a unit collecting fertilizer on turn 718 deposits it into the shed *before* the market queue executes. If the market list was generated purely from the pre-turn shed snapshot, this final unit of fertilizer would be stranded.

### 3.2 Implementation & Ablation Test
We ported this exact mechanism into a test variant (`my/agent_variant_sweep_fertilizer_718.py`):

```python
# ---- Step 718 Fertilizer Sweep ----
if step >= 718 and len(market) + len(extra) < MAX_ORDERS:
    extra.append(["SELL", "FERTILIZER", 50])
```

We benchmarked this across 10 evaluation seeds against the 2644.2 baseline:

```
BASELINE Mean Score:              164,091
Variant 'sweep_fertilizer_718':   161,574 (Delta = -2,517 points)
Win/Loss Record vs Baseline:      4W - 6L - 0T
```

### 3.3 Root-Cause Forensic: Why Did It Fail?
The fertilizer sweep caused a **-2,517 point regression**. Why did it help Fieldbook but hurt our 2644.2 agent?

1. **Market Slot Scarcity**: 
   A player can only submit 10 market orders per turn. On turn 718, our baseline's `dead_stock` repair is already queuing high-value sales (Melon, Strawberry, Milk, Wool) to clear the shed.
2. **Value Dilution**: 
   Fertilizer base price is $100 (often falling to $40–$60 under pasture oversupply). Melon base is $250, Milk is $160, Wool is $200.
3. **Queue Eviction**: 
   Injecting a 50-unit fertilizer sell consumed one of the 10 order slots. In games where shed inventory was diverse, it displaced a higher-margin melon or wool sell order, leaving hundreds of coins worth of premium produce unsold when the game terminated at turn 720!

**Conclusion**: The modification was **permanently rejected** from our production agent.

---

## 4. Synthesis & Key Takeaway

Borrowing features across different codebases without rigorous ablation testing is dangerous. Architectural components interact:
* In Fieldbook, where terminal liquidation was less exhaustive, an explicit fertilizer sweep captured free money.
* In our 2644.2 baseline, where `dead_stock` already sorted all surplus products by descending economic value ($\text{price} \times \text{qty}$), adding an unprioritized manual sweep degraded slot allocation.

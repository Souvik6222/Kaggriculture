# 📐 Chapter 4: Proposed Upgrades & Initial Hypotheses

## 1. Upgrade Objectives

Our primary mandate was to significantly elevate the performance of the 2644.2 baseline on the Kaggle leaderboard while strictly obeying the user's constraints:
1. **Never replace the tape replay architecture with a pure RL approach.**
2. **Preserve all proven foundations**: prefix guards, public routing, weed digging, sell clamping, and dead-stock liquidation.
3. **Validate every modification experimentally against the baseline before committing.**

---

## 2. The Seven Proposed Components

### Component 1: Route Bank with Structured Metadata
* **Hypothesis**: Wrapping the raw `_BLOB` strings in an indexed `ROUTE_BANK` metadata dictionary will make branching points, expected product outputs, and compatible prefix lengths cleanly queryable without altering runtime behavior.
* **Implementation**: Pure architectural refactoring.

---

### Component 2: `water_rescue` (Idle Turn Watering)
* **Hypothesis**: In the baseline, `weed_dig` converted wasted turns on weed tiles into productive `DIG` actions (+19W/-0L). Analogously, if a unit is idle (`_noop`) and standing on a crop that has not been watered today, converting that turn into a `["WATER"]` action should prevent crop decay and capture bonus yield at zero opportunity cost.
* **Code Implementation**:
  ```python
  # ---- water_rescue ----
  for i in range(min(len(acts), len(positions))):
      x, y = positions[i]
      tile = tiles[y][x]
      inv = invs[i] if i < len(invs) else {}
      if (isinstance(tile, dict) and tile.get("kind") == "PLANT"
              and not tile.get("watered_today")
              and _noop(acts[i], tile, inv, seeds, x, y, board)):
          acts[i] = ["WATER"]
  ```

---

### Component 3: `harvest_rescue` (Idle Turn Harvesting)
* **Hypothesis**: If an idle unit is standing on a tile with harvestable yield (`yield_units > 0`), harvesting immediately ensures produce enters the shed for sale, provided the shed has buffer room (`shed_used < SHED_CAP - 5`).
* **Code Implementation**:
  ```python
  # ---- harvest_rescue ----
  shed_used = sum(shed.values())
  for i in range(min(len(acts), len(positions))):
      if shed_used >= SHED_CAP - 5:
          break
      x, y = positions[i]
      tile = tiles[y][x]
      inv = invs[i] if i < len(invs) else {}
      if (isinstance(tile, dict) and tile.get("yield_units", 0) > 0
              and _noop(acts[i], tile, inv, seeds, x, y, board)):
          acts[i] = ["HARVEST"]
          shed_used += tile.get("yield_units", 0)
  ```

---

### Component 4: Market Order Optimization
* **Hypothesis**: The competition caps market orders at 10 slots per turn. If a turn has many simultaneous buy, hire, and sell orders, sorting sell orders by descending expected value ($\text{price} \times \text{qty}$) and grouping non-sells first will ensure the most valuable trades always execute before the 10-order cutoff.
* **Code Implementation**:
  ```python
  # Group orders into non-sells and sells
  combined_sells = [o for o in market if o[0] == "SELL"] + extra
  non_sells = [o for o in market if o[0] != "SELL"]
  combined_sells.sort(key=lambda o: -prices.get(o[1], 0) * int(o[2]))
  final_market = (non_sells + combined_sells)[:MAX_ORDERS]
  ```

---

### Component 5: Earlier Dead-Stock Detection (Day 25+)
* **Hypothesis**: The baseline only liquidated uncommitted surplus goods on Day 29 (the final day). Starting detection on Day 25 with a price floor ($p > 10) could spread liquidation sales over multiple turns, preventing the 10-slot cap from bottlenecking sales on the final turns.
* **Code Implementation**:
  ```python
  if day >= DEAD_STOCK_LATE_DAY: # Day 29
      do_dead_stock = True
      min_price = 1
  elif day >= DEAD_STOCK_EARLY_DAY: # Day 25
      do_dead_stock = True
      min_price = 10
  ```

---

### Component 6: Opponent-Aware Strategic Dead Stock
* **Hypothesis**: By inspecting `obs["farms"][opp]["money"]`, the agent can gauge the money gap. If trailing significantly, lower the price floor to $1 to aggressively dump all assets for liquid cash; if comfortably ahead, hold higher price floors to avoid selling into depressed prices.

---

### Component 7: Action Safety Layer
* **Hypothesis**: Observations can occasionally have unit desyncs or unexpected hired hand counts due to network latency, server hiccups, or environment quirks. Enforcing that `len(acts) == 1 + len(farm["hands"])` and wrapping act generation in a resilient fallback prevents forfeitures or illegal action penalties.
* **Code Implementation**:
  ```python
  # ---- Action Safety Layer ----
  expected_hands = len(farm.get("hands") or [])
  while len(acts) - 1 < expected_hands:
      acts.append(["PASS"])
  if len(acts) - 1 > expected_hands:
      acts = acts[:expected_hands + 1]
  ```

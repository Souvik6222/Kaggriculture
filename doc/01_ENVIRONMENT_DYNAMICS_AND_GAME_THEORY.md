# 🌾 Chapter 1: Environment Dynamics & Mathematical Game Theory

## 1. Executive Overview

Kaggriculture is a simultaneous two-player zero-sum economic farming simulation hosted by Kaggle. The objective is to maximize accumulated coin balance by turn 720 (30 in-game days $\times$ 24 turns/day). The simulation differs from traditional gridworld RL environments in its high action cardinality, multi-unit coordination, tight shed constraints, and non-linear dynamic market pricing.

---

## 2. Spatial and Physical Topology

### 2.1 The Farm Grid
* **Dimensions**: $10 \times 10$ tile grid per player.
* **Quadrants**: Divided into four $5 \times 5$ quadrants:
  * `NW` (North-West, $x \in [0,4], y \in [0,4]$): Unlocked at game start ($t=0$).
  * `NE` (North-East, $x \in [5,9], y \in [0,4]$): Unlocked via `BUY_LAND` ($1,000).
  * `SW` (South-West, $x \in [0,4], y \in [5,9]$): Unlocked via `BUY_LAND` ($2,000).
  * `SE` (South-East, $x \in [5,9], y \in [5,9]$): Unlocked via `BUY_LAND` ($4,000).
* **Tile States**:
  * `None`: Cleared, tillable soil.
  * `"LOCKED"`: In an unpurchased quadrant. Units can walk across locked tiles, but cannot build, plant, water, or harvest there.
  * `{"kind": "PLANT", ...}`: Cultivated crop with attributes `crop`, `planted_day`, `watered_today`, `consecutive_unwatered`, `yield_units`, `max_lifespan_step`, `fertilized_until_day`.
  * `{"kind": "WEED"}`: Obstacle tile spawned randomly at end-of-day. Prevents planting; cleared via `DIG`.
  * `{"kind": "COOP" | "PASTURE", ...}`: Animal pen structure.

### 2.2 The Central Shed & Adjacent Delivery Zone
* **Shed Capacity**: Fixed at $100$ items (encompassing crops, animal products, and fertilizer).
* **Seeds Exception**: Seeds reside in a dedicated, unlimited storage slot (`private["seeds"]`) and never consume shed capacity.
* **Shed Adjacency**: The shed is located centrally at coordinates `(4,4)`, `(5,4)`, `(4,5)`, `(5,5)`.
  * Units must stand directly on one of these four center tiles to execute `DROP`, `PICKUP`, or `PLACE` into storage.
  * **Critical Risk (Overflow Discard)**: Any items added to the shed beyond 100 units during unit operations or end-of-day drops are discarded immediately and permanently lost.

---

## 3. Crop Yield Curves & Biology

Crops follow non-linear growth trajectories parameterized by `first_yield_day`, `max_yield_day`, base yield, and watering windows:

| Crop | Seed Cost | First Yield Day | Max Yield Day | Base Price ($I_0$) | Watering Bonus Window | Ongoing? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Wheat** | $10 | Day 2 | Day 4 | $25 | Days 2–4 | No |
| **Carrot** | $15 | Day 3 | Day 6 | $35 | Days 3–6 | No |
| **Tomato** | $25 | Day 4 | Day 8 | $60 | Day 4+ | Yes (Cap 5) |
| **Strawberry** | $40 | Day 5 | Day 10 | $120 | Day 5+ | Yes (Cap 6) |
| **Melon** | $60 | Day 6 | Day 12 | $250 | Days 6–12 | No |

### 3.1 The Compounding Bonus Window
For one-time crops, the bonus watering window begins at $\lceil \text{max\_yield\_day} / 2 \rceil$. 
* Each day the plant is watered during this window adds $+1$ unit to final harvest yield.
* If `FERTILIZE` is applied, this bonus doubles to $+2$ units per watered day.
* **The Premature Harvest Trap**: If a unit harvests Wheat on Day 2, it receives $1$ unit ($25–45 coins). If it waters and waits until Day 4, the yield jumps to $3$ (or $6$ with fertilizer), producing $150–270 coins from the exact same seed! 
* Any naive heuristic that triggers `HARVEST` the instant `yield_units > 0` destroys over 60–80% of crop revenue.

---

## 4. Animal Pasture Loops & Compounding Care

Animals do not expire after harvest; they produce indefinitely provided they are fed daily:

| Animal | Purchase Cost | Housing | Feed Requirement | Interval | Product | Max Held on Tile |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Goose** | $300 | Coop ($100) | 1 Wheat/day | 1 day | Egg ($50) | 4 |
| **Cow** | $400 | Pasture ($200) | 1 Wheat/day | 2 days | Milk ($160) | 6 |
| **Sheep** | $350 | Pasture ($200) | 1 Wheat/day | 2 days | Wool ($200) | 6 |

### 4.1 Care & Fertilizer Compounding
* **`CARE` Action**: When a unit cares for a fed animal, it banks $+1$ product to the animal's pending payout. Upon the next scheduled production day, all banked care points are paid out simultaneously.
* **`COLLECT_FERTILIZER`**: Produces $1$ fertilizer per animal per day. Fertilizer can either be applied to crops (doubling bonus yield) or sold to the market (base $100).
* **Starvation Danger**: Missing two consecutive daily feeding cycles causes the animal to escape permanently, destroying the initial capital investment.

---

## 5. Dynamic Market Mechanics & Price Functions

The market is shared between both players and the town. All products start with an initial equilibrium inventory of:
$$I_0 = 10,000 \text{ units}$$

### 5.1 The Mathematical Price Function
For each resource, sale price moves dynamically as a function of market inventory $inv$:

$$\text{price}(inv) = \max\left(1, \; \text{round}\left(\text{base} + \text{sign} \cdot \text{amp} \cdot f(|inv - I_0|)\right)\right)$$

where:
* $\text{sign} = +1$ if $inv < I_0$ (scarcity $\rightarrow$ price rises)
* $\text{sign} = -1$ if $inv > I_0$ (oversupply/glut $\rightarrow$ price falls)
* $\text{amp} = \frac{\text{target} \cdot \text{base}}{f(T)}$
* $T$ is the anchor throughput capacity of a single $5 \times 5$ quadrant over a 24-day horizon.

### 5.2 Parameters by Commodity

| Resource | Base Price | $I_0$ | Anchor $T$ | Below Curve (Scarcity) | Below Target | Above Curve (Glut) | Above Target | $P(I_0 - T)$ | $P(I_0 + T)$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Wheat** | $25 | 10,000 | 400 | `sqrt` | 0.80 | `log` | 0.20 | $45 | $20 |
| **Carrot** | $35 | 10,000 | 450 | `hinge` | 1.00 | `sqrt` | 0.70 | $70 | $10 |
| **Tomato** | $60 | 10,000 | 200 | `hinge` | 0.40 | `sqrt` | 0.60 | $84 | $24 |
| **Strawberry** | $120 | 10,000 | 100 | `sqrt` | 0.70 | `linear` | 1.60 | $204 | **$1** |
| **Melon** | $250 | 10,000 | 300 | `log` | 0.20 | `sq` | 3.60 | $300 | **$1** |
| **Egg** | $50 | 10,000 | 332 | `hinge` | 0.40 | `log` | 0.20 | $70 | $40 |
| **Milk** | $160 | 10,000 | 122 | `sqrt` | 0.60 | `linear` | 1.60 | $256 | **$1** |
| **Wool** | $200 | 10,000 | 105 | `log` | 0.20 | `sq` | 3.20 | $240 | **$1** |
| **Fertilizer** | $100 | 10,000 | 200 | `linear` | 0.40 | `linear` | 0.40 | $140 | $60 |

### 5.3 Asymmetric Price Collapse for Premium Commodities
Notice the critical mathematical asymmetry:
* **Staples** (Wheat, Egg): Have $\text{Above Target} = 0.20$. Even if oversupplied, prices gently glide to $20–$40.
* **Premium Goods** (Melon, Strawberry, Milk, Wool): Have $\text{Above Target} > 1.0$ (`linear` or `sq`). Selling just $T$ units past $I_0$ immediately drives the price to the absolute **$1 price floor**.
* **Strategic Implication**: You cannot mass-dump Milk or Wool without town shop consumption absorbing the supply; otherwise, your revenue collapses to pennies.

---

## 6. Town Buildings & External Demand

Shops unlock every 3 days (turns 72, 144, 216, 288, 360, 432, 504, 576) drawn uniformly **with replacement** up to a maximum of 8 instances:

| Shop Type | Consumes from Market | Daily Consumption per Instance |
| :--- | :--- | :--- |
| **Yarn Store** | **Wool (2x)** | **12 units/day** |
| **Pet Cafe** | **Carrots (2x)** | **12 units/day** |
| **Bakery** | Eggs, Wheat | 6 units/day each |
| **Pizza Shop** | Milk, Tomatoes, Wheat | 6 units/day each |
| **Brunch Spot** | Eggs, Wheat, Strawberries | 6 units/day each |
| **Ice Cream Shop**| Strawberries, Milk, Wheat | 6 units/day each |
| **Smoothie Shop** | Strawberries, Milk | 6 units/day each |
| **Farmers Market**| Wheat, Carrots, Tomatoes, Strawberries | 6 units/day each |

When a **Yarn Store** opens, it permanently drains 12 wool every day. Because wool's anchor $T=105$, a single Yarn Store drains over $10\%$ of $T$ every day, holding Wool price near its maximum ($240) throughout the season.

---

## 7. Turn Processing Order

The engine executes each step in strict sequence:
1. **Action Validation**: Parses action dicts. Checks seed counts and syntax.
2. **Physical Unit Operations**: Movements, planting, watering, digging, harvesting, dropping resolve concurrently.
3. **Market Queue Processing**:
   * Up to 10 market orders per player per turn.
   * Executed sequentially within a player's list, concurrent between players.
   * **Crucial Rule**: If a player submits `[BUY, SELL]` and has no money, the `BUY` fails. If they submit `[SELL, BUY]`, the `SELL` fills first, deposits cash into the bank, and the subsequent `BUY` succeeds!
4. **Town Consumption**: Active shops consume their designated products from market inventory.
5. **Daily Refresh** (every 24 turns): Checks watering status, updates growth stages, resets hire cost Fibonacci curve, drops unit inventories into shed, discards shed overflow past 100 items.

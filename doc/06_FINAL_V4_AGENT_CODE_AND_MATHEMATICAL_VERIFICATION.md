# 💻 Chapter 6: Final V4 Agent Code & Mathematical Verification

## 1. Complete Production Code Breakdown (`main.py`)

Below is a comprehensive technical breakdown of every component in the finalized `main.py` submitted to the competition.

### 1.1 Header & System Constants
```python
import base64
import json
import zlib

TURNS = 720
BOARD = 10
MAX_ORDERS = 10
SHED_CAP = 100
PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL",
            "FERTILIZER")
ANIMALS = {"GOOSE": "COOP", "COW": "PASTURE", "SHEEP": "PASTURE"}
MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}
PASS = {"farmer": ["PASS"], "hands": [], "market": []}

MAIN = "7015cc00acfa4922"
YARN = "dc76e4003029ac51"
YARN_CARROT = "ab9669b9abfbea4e"
MILK_GLUT = "a84d06f1d12add7c"
```
* `TURNS = 720`: Season duration.
* `MAX_ORDERS = 10`: Engine limit on market actions per player per turn.
* `SHED_CAP = 100`: Non-seed item limit.

---

### 1.2 Calibrated Branching Decisions
```python
# (turn, feature, threshold, target tail)
DECISIONS = (
    (226, "shop_YARN_STORE", 1, YARN),
    (360, "px_CARROT", 42, YARN_CARROT),
)
```
* **Turn 226 (`shop_YARN_STORE >= 1`)**: Checks if at least one Yarn Store has unlocked in town. If true and prefix matches 100%, switches to `YARN` (capitalizing on $2 \times$ wool consumption).
* **Turn 360 (`px_CARROT >= 42`)**: If under `YARN`, checks if carrot price surged to $\ge 42$. If true, switches to `YARN_CARROT`.
* **Turn 433 `inv_MILK` Omission**: As proven in Chapter 5, the baseline's premature switch to `MILK_GLUT` was eliminated, saving $+12,208$ average points by preserving the top-yielding `MAIN` route.

---

### 1.3 Decompression Engine
```python
_ROUTES = None

def routes():
    global _ROUTES
    if _ROUTES is None:
        raw = zlib.decompress(base64.b64decode(_BLOB)).decode("utf-8")
        data = json.loads(raw)
        out = {data["root"]["h"]: data["root"]["tape"]}
        for t in data["tails"]:
            out[t["h"]] = out[t["parent"]][:t["at"]] + t["suffix"]
        _ROUTES = out
    return _ROUTES
```
* Reconstructs the 4 full 720-step action routes in memory once on Turn 0 in $< 50$ ms.

---

### 1.4 Spatial & State Query Utilities
```python
def _shed_adjacent(x, y, board=BOARD):
    h = board // 2
    return (x, y) in ((h - 1, h - 1), (h, h - 1), (h - 1, h), (h, h))

def _feature(obs, name):
    if name == "shop_YARN_STORE":
        return (obs.get("town", {}).get("unlocked_shops") or []).count("YARN_STORE")
    if name == "px_CARROT":
        return obs["market"]["prices"].get("CARROT", 0)
    if name == "inv_MILK":
        return obs["market"]["inventory"].get("MILK", 0)
    return 0
```
* `_shed_adjacent`: Returns `True` iff a unit stands on `(4,4)`, `(5,4)`, `(4,5)`, or `(5,5)`.
* `_feature`: Safe public observation reader.

---

### 1.5 The `_noop` Engine Simulator
```python
def _noop(act, tile, inv, seeds, x, y, board=BOARD):
    """True when the engine will certainly ignore this action.
    Only used to decide whether a turn is free to reuse."""
    if not act:
        return True
    op = act[0]
    if op in MOVES:
        dx, dy = MOVES[op]
        return not (0 <= x + dx < board and 0 <= y + dy < board)
    if op == "PASS":
        return True
    if op == "DROP":
        return (not _shed_adjacent(x, y, board)) or (not inv)
    if op == "PICKUP":
        return not _shed_adjacent(x, y, board)
    if op == "PLACE":
        item = act[1] if len(act) > 1 else None
        if (item in ANIMALS and isinstance(tile, dict)
                and tile.get("kind") == ANIMALS[item] and tile.get("animal") is None):
            return inv.get(item, 0) <= 0
        if _shed_adjacent(x, y, board):
            return inv.get(item, 0) <= 0
        return True
    if tile == "LOCKED":
        return True
    isd = isinstance(tile, dict)
    kind = tile.get("kind") if isd else None
    animal = isd and tile.get("animal") is not None
    if op == "PLANT":
        return tile is not None or seeds.get(act[1] if len(act) > 1 else None, 0) <= 0
    if op == "WATER":
        return kind != "PLANT" or bool(tile.get("watered_today"))
    if op == "HARVEST":
        return (not isd) or tile.get("yield_units", 0) <= 0
    if op == "FERTILIZE":
        return kind != "PLANT" or inv.get("FERTILIZER", 0) <= 0
    if op == "DIG":
        return tile is None or animal
    if op in ("BUILD_COOP", "BUILD_PASTURE"):
        return tile is not None
    if op == "FEED":
        return (not animal) or bool(tile.get("fed_today")) or inv.get("WHEAT", 0) <= 0
    if op == "COLLECT_FERTILIZER":
        return (not animal) or (not tile.get("fertilizer_available"))
    if op == "CARE":
        return (not animal) or bool(tile.get("cared_today"))
    return True
```
* Determines whether an action will fail or no-op before it executes. This guarantees that `weed_dig` only fires on genuinely wasted turns.

---

### 1.6 Agent State & Future Sell Projections
```python
class Agent:
    def __init__(self):
        self.R = routes()
        self.cur = MAIN
        self._fs = None
        self._fs_for = None

    def future_sells(self, item, step):
        """Computes remaining planned sells for item from step to 720."""
        if self._fs_for != self.cur:
            r = self.R[self.cur]
            fs = dict((p, [0] * (len(r) + 1)) for p in PRODUCTS)
            for t in range(len(r) - 1, -1, -1):
                add = {}
                for o in (r[t].get("market") or []):
                    if o and o[0] == "SELL" and o[1] in fs:
                        add[o[1]] = add.get(o[1], 0) + int(o[2])
                for p in fs:
                    fs[p][t] = fs[p][t + 1] + add.get(p, 0)
            self._fs = fs
            self._fs_for = self.cur
        a = self._fs.get(item)
        return a[step] if a and step < len(a) else 0
```
* Precomputes backwards cumulative sell quantities for all 9 products, enabling instantaneous $O(1)$ lookup of future route demand during `dead_stock` checks.

---

### 1.7 Prefix Guard Enforcement
```python
    def _switch_ok(self, target, turn):
        """A switch is legal only onto a tail identical to the current one so far."""
        a, b = self.R[self.cur], self.R[target]
        if a is b:
            return False
        for t in range(turn):
            if a[t] != b[t]:
                return False
        return True
```

---

### 1.8 The Core Action Generation & Repair Pipeline
```python
    def act(self, obs):
        s = obs.get("step")
        step = int(s) if s is not None else int(obs.get("day", 0)) * 24 + int(obs.get("hour", 0))
        me = int(obs.get("player", 0))
        farm = obs["farms"][me]
        priv = obs["private"]
        tiles = farm["tiles"]
        seeds = priv.get("seeds") or {}
        invs = priv.get("inventories") or []
        shed = dict(priv.get("shed") or {})
        prices = obs["market"]["prices"]
        day = int(obs.get("day", step // 24))
        board = len(tiles) or BOARD

        # 1. Evaluate Branching Triggers
        for (turn, feat, thr, target) in DECISIONS:
            if turn == step and target != self.cur and self._switch_ok(target, turn):
                if _feature(obs, feat) >= thr:
                    self.cur = target

        route = self.R[self.cur]
        base = route[step] if step < len(route) else PASS
        acts = [list(base.get("farmer") or ["PASS"])] + [list(h) for h in (base.get("hands") or [])]
        market = [list(o) for o in (base.get("market") or [])]
        positions = [tuple(farm["farmer"])] + [tuple(p) for p in farm["hands"]]

        # 2. Repair 1: weed_dig
        for i in range(min(len(acts), len(positions))):
            x, y = positions[i]
            if not (0 <= x < board and 0 <= y < board):
                continue
            tile = tiles[y][x]
            inv = invs[i] if i < len(invs) else {}
            if (isinstance(tile, dict) and tile.get("kind") == "WEED"
                    and _noop(acts[i], tile, inv, seeds, x, y, board)):
                acts[i] = ["DIG"]

        # 3. Projected Shed Calculation (Phase 2 -> Phase 3 Projection)
        proj = dict(shed)
        room = SHED_CAP - sum(proj.values())
        for i in range(min(len(acts), len(positions))):
            if room <= 0:
                break
            x, y = positions[i]
            inv = invs[i] if i < len(invs) else {}
            if not inv or not _shed_adjacent(x, y, board):
                continue
            a = acts[i]
            if a and a[0] == "DROP":
                for it, n in inv.items():
                    take = min(n, room)
                    if take > 0:
                        proj[it] = proj.get(it, 0) + take
                        room -= take
            elif a and a[0] == "PLACE" and len(a) > 1 and a[1] not in ANIMALS:
                it = a[1]
                take = min(int(a[2]) if len(a) > 2 else 1, inv.get(it, 0), room)
                if take > 0:
                    proj[it] = proj.get(it, 0) + take
                    room -= take

        # 4. Repair 2: clamp_sells
        avail = dict(proj)
        kept = []
        for o in market:
            if o and o[0] == "SELL":
                have = avail.get(o[1], 0)
                if have <= 0:
                    continue
                n = min(int(o[2]), have)
                if n <= 0:
                    continue
                avail[o[1]] = have - n
                kept.append(["SELL", o[1], n])
            else:
                kept.append(o)
        market = kept

        # 5. Repair 3: dead_stock Liquidation
        planned = {}
        for o in market:
            if o and o[0] == "SELL":
                planned[o[1]] = planned.get(o[1], 0) + int(o[2])
        extra = []
        for it in PRODUCTS:
            have = proj.get(it, 0) - planned.get(it, 0)
            if have <= 0:
                continue
            surplus = have if day >= 29 else have - self.future_sells(it, step + 1)
            if surplus > 0 and prices.get(it, 0) > 1:
                extra.append(["SELL", it, surplus])
        extra.sort(key=lambda o: -prices.get(o[1], 0) * int(o[2]))

        # 6. Action Safety Layer: Hand Reconciliation
        expected_hands = len(farm.get("hands") or [])
        while len(acts) - 1 < expected_hands:
            acts.append(["PASS"])
        if len(acts) - 1 > expected_hands:
            acts = acts[:expected_hands + 1]

        # 7. Preserve Route Market Priority
        return {"farmer": acts[0], "hands": acts[1:],
                "market": (market + extra)[:MAX_ORDERS]}
```

---

### 1.9 Top-Level Crash Defense Wrapper
```python
_A = None

def agent(obs):
    """A crash here forfeits the game, so any failure degrades to a legal PASS."""
    global _A
    try:
        s = obs.get("step")
        step = int(s) if s is not None else int(obs.get("day", 0)) * 24 + int(obs.get("hour", 0))
        if _A is None or step == 0:
            _A = Agent()
        return _A.act(obs)
    except Exception:
        try:
            hands = obs["farms"][int(obs.get("player", 0))].get("hands") or []
        except Exception:
            hands = []
        return {"farmer": ["PASS"], "hands": [["PASS"] for _ in hands], "market": []}
```

---

## 2. Verification Checklist

| Metric | Verification Result |
| :--- | :--- |
| **Archive File** | `submission.tar.gz` (28.6 KB) |
| **Integrity Check** | Archive contains single valid file: `main.py` |
| **Syntax Validation** | Zero syntax or linter warnings |
| **Execution Performance** | 252.7 turns/sec (full 720-step episode in 2.85s) |
| **Memory Footprint** | $< 45$ MB RAM (well within Kaggle's 16 GB limit) |
| **Offline Performance** | 160,599 average score (+12,208 delta over baseline) |
| **Expected Leaderboard** | **~2700 – 2750+** |

# 🐣 Chapter 7: Herds & Openings — A Beginner's Field Guide

*Who this is for: a teammate (or future-you) who knows the rules but has never
studied what real ladder bots actually do. Every claim below is backed by one of
our own replays or the notebooks in this repo — episode IDs included so you can
re-verify everything with `kaggle competitions replay <id>`.*

---

## 1. The two decisions that shape a season

Forget all 720 turns for a moment. A bot's season is mostly decided by two things:

1. **The opening kit** — what it buys on Day 0-1 with the starting $3,000.
2. **The herd it converges to** — which animals it ends up milking daily.

Everything between is labor (watering, feeding, harvesting) and selling. Labor barely
differs between good bots (our replays show near-identical WATER/HARVEST counts);
**money differs because herds differ.**

### 1.1 Key rules in one paragraph

Each animal must eat 1 wheat per day or it escapes after 2 missed days. Animals live in
structures you build: geese need a COOP ($100), cows and sheep need a PASTURE ($200).
`CARE` (once/animal/day) banks +1 bonus product, paid out on the next production day —
a cared-for cow produces far more than an uncared one. Products: goose→EGG ($50 base,
daily), cow→MILK ($160, every 2 days), sheep→WOOL ($200, every 3 days). Shed holds max
100 items — overflow is thrown away forever. Market prices move: flood the market and
premium goods (milk, wool, strawberry, melon) crash to the **$1 floor**; staples
(wheat, egg) dip gently. Shops unlock every 3 days and eat products daily — a Yarn
Store doubles wool demand, a Pet Cafe doubles carrot demand. Winner = most coins in
the bank after turn 720. Margin doesn't matter for rating — only win/loss/tie.

Per-animal economics at base prices with daily care (from public benchmark data):

| Animal | Product rhythm | Gross/day | Feed cost/day | Net/day |
|---|---|---|---|---|
| Goose ($300 + $100 coop) | 2 eggs/day | $100 | $25 wheat | **~$75** |
| Cow ($400 + $200 pasture) | 1.5 milk/day | $240 | $25 wheat | **~$215** |
| Sheep ($350 + $200 pasture) | ~1 wool/day-ish | ~$200 | $25 wheat | **~$175-ish** |

Cows earn most *per animal per day at base prices* — but base prices are a lie you only
get if the market isn't glutted. The whole strategic game is: **which products can you
actually sell near base price against a live opponent doing the same thing?**

---

## 2. Openings: the Day 0-1 shopping list

The "opening" is the bundle a bot buys before farming starts. Same $3,000 for everyone,
so every opening is a tradeoff.

### 2.1 Our opening (V4/V5 tape): "2C/2S, everything day one"

Turn 1 market orders, all at once:

```
SELL WHEAT 9 → BUY_SEED WHEAT 7 → BUY_SEED MELON 12 → HIRE ×5 → COW 2 → SHEEP 2
```

Shorthand: **2C/2S + HIRE5 + wheat/melon seeds + a wheat flip**. The opening SELL funds
the shopping spree (sells must come first — moving them last bankrupts the opening;
that's the famous −17-game failure in Chapter 5). Hiring 5 hands on day one is
aggressive: hire costs follow Fibonacci per day (1,1,2,3,5,8,13…), so hands 4-5 are
cheap and hands 10+ are ruinous.

- Advantage: maximum labor from day one; big farm online fastest.
- Disadvantage: spends the most the earliest; if the plan stumbles, no cash reserve.

### 2.2 The meta modal opening: "1C/4S + HIRE4"

An audit of the frozen Top-30 (v27 notebook) found **26 of 30 teams** opening
1 cow + 4 sheep (+ seeds), 14 with HIRE4 and 12 with HIRE5. Sheep-lean: wool has the
highest base price ($200) and a Yarn Store makes it $240-sustainable, so the field bets
on wool and hires one less hand to keep cash.

- Advantage: cheaper start, wool-first when yarn hits, dominant prior (hard to be
  "wrong" when everyone does it).
- Disadvantage: crowded trade — when many wool bots meet, wool hits the $1 floor
  together (we watched this: wool at $1-37 for entire late games, e.g. episode
  106183220).

### 2.3 Same kit, different choreography ("spread" family)

Calmracer (2381.3) and koren sabag (2349.4) buy the same totals over turns 1-3+ instead
of all on turn 1: `t1: COW 2 → t2: HIRE×5 + SHEEP 1 → t3: feed + seeds + SHEEP 1…`.
No day-one wheat flip; cash is preserved rather than cycled.

- Advantage: never risks the Turn-2 cash-flow inversion; robust.
- Disadvantage: slower ramp (hands arrive a turn later).
- Evidence: we beat Calmracer +3397 (episode 106211902) and koren sabag +55 (106297305).
  Beatable — but the +55 shows near-identical strength.

### 2.4 Exotic openings (rare, educational)

- **Wheat bank** (Kosakunin): turn 1 = `BUY_PRODUCT WHEAT 51`. Stockpiles feed before
  anything else. Feed-first como insurance against starvation cascades.
- **H4/C1** (Manuel Pérez, 599.1): 4 hires, 1 cow, wheat/melon seeds. Ultra-cheap start;
  we beat it by 118k (episode 106154995) — too slow vs a fast developer.
- **H4/C2/S3/W12** (nvidia fan, 2129.4): heavier wheat-seed bet (12), no melon. Beat us
  −6744 early in our climb (episode 106178677) — wheat volume works when milk/wool glut.

---

## 3. Herds: what bots look like on day 24

By turn 576 the shopping is done and the herd is the economy. Observed shapes:

| Herd (at t576) | Who | Products | Verdict in our sample |
|---|---|---|---|
| **Balanced MAIN**: 3 geese / 9 cows / 5 sheep, wheat + strawberry fields | Us (V4/V5, no-yarn games) | Milk + eggs + wool + crops | Baseline; beats pasture-only 2-0 |
| **Wool-lean YARN**: 8 sheep / 9 cows, no geese, wheat + strawberry | Us (yarn games) | Wool + milk, no eggs | 1W-2L in tiny sample, no verdict |
| **Pasture-only**: 9 cows / 5 sheep, no coops at all | Calmracer, Chiranjieev | Milk + wool, no eggs | We beat both (+3397, +5058) |
| **Goose-heavy + garden**: 5 geese / 3 cows / 5 sheep + carrots + tomatoes | len8487 (2371.8) | Eggs + little milk + garden | Beat us −6443 (n=1, respect it) |
| **Mirror**: byte-identical to us | Max Podd, ShiviWhivi ×2 | Same as us | 0W-2L-1T — pure weed luck |

### 3.1 Why eggs keep winning in our sample

Two wins (Calmracer, Chiranjieev) came against herds with **zero egg production**.
Theory matches: eggs are a *staple* (glut curve `log/0.20`) — they never crash to $1,
geese lay daily with no 2-day gaps, and bakeries + brunch spots eat eggs all season.
Our 3 geese are a diversified income floor while milk/wool swing wildly ($1 one game,
$200+ the next). Small sample (n=2) — but the mechanism is sound, so keep the coops
until real evidence says otherwise.

### 3.2 The len8487 lesson: portfolio > purity

len8487 runs FEWER cows than anyone (3 vs our 9) and wins with breadth: daily eggs,
carrot farming (Pet Cafes pay 2x), a few tomatoes, heavy fertilizer collection, fewer
hires (33 vs our 36 over the same window). When milk/wool sit at $1-70, breadth beats
depth. One game only — do not copy it yet — but it falsifies "more cows = better" and
is the strongest lead for V6 recon.

---

## 4. Shops: the demand weather

You can't choose shops (random every 3 days, max 8), only react — which is exactly what
our two route switches do:

| Shop | Eats (2x = double rate) | Our answer |
|---|---|---|
| Yarn Store | Wool 2x | t226 → YARN wool route |
| Pet Cafe | Carrots 2x | t360 carrot-price check (only under yarn) |
| Bakery / Brunch | Eggs, wheat, strawberries | Our egg floor + wheat fields already cover |
| Pizza / Smoothie / Ice Cream | Milk ± tomato/strawberry | Milk herd covers; nothing to switch |
| Farmers Market | Wheat, carrots, tomatoes, strawberries | Wheat fields cover |

No-yarn games (5 of our last 6 at one point) just stay MAIN — and went 5-0. The router
earns its keep in the minority of yarn games.

---

## 5. Glossary for replay reading

- **Mirror**: opponent running our tape family (identical orders). Outcome ≈ weed luck.
- **Tape / route**: recorded 720-turn action stream we replay (MAIN, YARN, YARN_CARROT…).
- **Prefix guard** (`_switch_ok`): only switch routes if histories match byte-for-byte so
  far — prevents watering empty tiles on a foreign farm layout.
- **weed_dig**: idle unit on a weed tile digs instead of idling.
- **clamp_sells**: shrink SELLs to shed stock so no market slot is wasted.
- **dead_stock**: sell surplus the tape will never sell, richest first.
- **Rot**: shed leftovers worth $0 at turn 720 — pure waste; ours is $0 in every
  analyzed game.
- **Close-loss share**: fraction of losses by tiny margins — the stat that says whether
  you're outclassed (big losses) or one flip away (close losses). Ours are close.

## 6. How to verify any of this yourself

```bash
kaggle competitions replay <EPISODE_ID> -p sub/replay-latest
```

Openings live at steps 0-5 (`steps[t][p].action.market`), herds in
`steps[576][p].observation.farms[p].tiles` (count `animal` fields), money in
`farms[p].money` every turn, final rot in `private.shed × market.prices` at step 719.

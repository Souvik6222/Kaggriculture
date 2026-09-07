# V5 Safe Overlays — Complete Change Log

- Date: 2026-09-06
- Team: Sōsuke Aizen (`soukeaizenz`, `souvikdbiswas`)
- Base: V4 agent `my/main.py` (md5 `412de06253e3245be11a441f1b9ca4df`, identical to `my/v4_main.py`)
- Result: `sub/presub-v5/main.py` + `sub/presub-v5/submission.tar.gz`
- Submission: `56057787` — "V5 safe overlays (feed5, sparse SELL order, terminal $1)"
- Status: submitted, PENDING validation at time of writing

## 1. Ladder context (why V5 exists)

- Public leaderboard (2026-09-06 snapshot, 7873 teams): bronze ≈ rank 787, score ≈ 2030
  (781st 2033.7 / 788th 2029.1).
- Team submissions that day:
  - `56054780` — baseline test, 1389.5 → later 1524.0 (retired after V5 submit).
  - `56054972` — friend's V4, 1889.2 → 1942.5 → **2075.7** (bronze line crossed while V5 was built).
- Replay sample of V4 (6 latest episodes at analysis time): 5W-1L, including wins over
  rank 538 (2197.8, Pilkwang Kim) and rank 819 (2010.8, 佐藤滉太). The single loss was a
  YARN-branch game vs rank 985 (1941.7, Ray Roberts), 99860 vs 103897 — a 1-game sample,
  not a verdict on the YARN branch.
- V4's published ablations were validated **vs random only** (+12,208 coins, 12W-8L over
  20 seeds). The Kaggle ladder is Elo head-to-head vs strong reactive bots where only
  W/L/T matters, never coin margin. So V5 was required to (a) preserve everything V4
  proved, (b) add only overlays that cannot reorder the tape's cash-flow sequence,
  (c) prove itself head-to-head vs V4 and vs public field agents, not just vs random.

## 2. Design constraints obeyed

1. Tape replay architecture untouched — no RL, no online invention of the 720-turn plan.
2. Route BLOB byte-identical (never edited; `diff` confirms only docstring/code hunks).
3. `DECISIONS` unchanged: `(226, shop_YARN_STORE → YARN)`, `(360, px_CARROT ≥ 42 → YARN_CARROT)`,
   no MILK switch (lines 97-100). The old t=433 milk switch stays removed: MAIN and
   MILK_GLUT are byte-identical until t=577, so t=433 decides 144 turns early on stale data.
4. V4 repairs preserved exactly: `weed_dig`, projected-shed DROP/PLACE accounting,
   `clamp_sells`, `dead_stock` (surplus vs `future_sells`), hand-reconciliation safety
   layer, top-level crash-to-PASS wrapper.
5. Public-state-only inputs (shops, prices, inventory, own shed/hands). No seed, Futureshop,
   opponent identity, or private opponent state.

## 3. ALL changes (exhaustive — 4 hunks, nothing else)

Source of ideas: `skomuro/2000-baseline-silver-medal-route` (2000+ silver, feed5/terminal/
banking/liq_ramp overlays) and `kaitofukami/25-27-strict-future-v27-midgame-meta-reset`
(sparse SELL-slot ordering, +819 margin, +1 outer win). Banking / split-debt / weed-replay /
fresh-tape options were studied and **deferred** (Section 5).

### Hunk 1 — Header docstring (lines 1-8, 18-44): truthful V5 description
- "three points" → "two points" (the code has two decisions; the old text still said three).
- Removed the stale t=433 milk line; documented why (144-turn pre-commitment flaw).
- Documented the three V5 additions and their order-preservation guarantee.
- Historical MEASURED panel (968-game, 74.5% HOLD) left as-is — it describes the V4
  foundation, not V5.

### Hunk 2 — Constant (line 89)
```python
TERMINAL_START = 714  # step 718 is the last executed action; 719 never runs
```
Single new constant. The 714-718 window comes from the silver baseline's terminal
analysis (walk-in/DROP/sell-all; engine never executes step 719's action).

### Hunk 3a — feed5 (lines 543-552, inside `act`, right after route market copy)
```python
# ---- feed5: keep the tape's step-0 feed purchase in market slot 0 ----
# Feed-denial defense. Stable move of one order; all other slots keep
# their relative order, so the opening cash-flow sequence is unchanged.
if step == 0:
    for idx in range(1, len(market)):
        o = market[idx]
        if o and o[0] == "BUY_PRODUCT" and len(o) > 1 and o[1] == "WHEAT":
            market.insert(0, market.pop(idx))
            break
```
- Effect on our tape: currently a **no-op** (step-0 market is a single
  `BUY_PRODUCT WHEAT 13` already in slot 0). Pure defense: if any future tape has the
  feed buy elsewhere, it is stably promoted without disturbing anything else.
- Safety: one stable pop/insert at index 0; relative order of all other orders kept.

### Hunk 3b — sparse SELL ordering (lines 608-619, after `clamp_sells`, before `dead_stock`)
```python
# ---- sell_order (sparse): permute SELLs only among SELL slots ----
# Non-SELL slots never move, so no SELL jumps ahead of a BUY/HIRE and
# the tape's cash-flow order is preserved. Only SELL-vs-SELL priority
# changes, richest (price*qty) first, so a premium sale is never cut
# off by the 10-order cap behind a low-value one.
if step > 0:
    sells = [o for o in market if o and o[0] == "SELL"]
    if len(sells) > 1:
        sells.sort(key=lambda o: -(prices.get(o[1], 0) * int(o[2])))
        it = iter(sells)
        market = [next(it) if (o and o[0] == "SELL") else o for o in market]
```
- Why this instead of full "sells first": full sells-before-buys reordering lost 17 HOLD
  games (Turn-2 SELL funds the opening BUY/HIRE chain; moving it last bankrupts the
  opening). Here BUY/HIRE/LAND slots are positionally frozen — only SELL-vs-SELL order
  changes — so the Turn-2 failure mode is structurally impossible.
- Sort key is live `price * qty` (same value metric `dead_stock` already uses for extras).

### Hunk 3c — terminal $1 sweep (lines 631-635, inside `dead_stock`)
```python
# Terminal sweep: 718 is the last executed action, so on 714-718
# sell at any price >= 1 instead of letting $1 goods rot. Extra
# orders only fill spare slots after route sells, never evicting.
min_price = 1 if step >= TERMINAL_START else 2
if surplus > 0 and prices.get(it, 0) >= min_price:
```
- Old behavior: `price > 1`, i.e. $1-floor goods (collapsed MELON/MILK/WOOL/STRAWBERRY)
  were left to rot even on the final turns.
- New: identical except steps 714-718 accept price ≥ 1. Because extras are appended
  after route sells and truncated to `MAX_ORDERS = 10`, route sells can never be evicted
  (the failure of the rejected unprioritized fertilizer-718 sweep, -2,517 pts).

## 4. Explicitly NOT changed

- Route `_BLOB` (all 4 tails), `routes()`, `_shed_adjacent`, `_feature`, `_noop`,
  `Agent.future_sells`, `_switch_ok`, `weed_dig`, projected-shed accounting,
  `clamp_sells`, `dead_stock` surplus math and extra sorting, safety layer, `agent()`.
- `diff my/main.py sub/presub-v5/main.py` shows only the hunks above.

## 5. Considered and deferred (with reason)

- Fresh 1-COW/4-SHEEP meta tapes (v27/Ezzzzzekki, Fieldbook 8-route bank): Top-30 opening
  audit says our 2-COW/2-SHEEP HIRE5 opening is off-meta, but V4 beats v27 and silver
  10-0 head-to-head locally, so a tape swap is not justified without strict-future
  validation vs recorded top opponents. Left for V6.
- Full-banking (divert PASS/movement carriers to DROP when holding ≥ $2000 premium):
  replaces movement with DROP, desyncing future tape positions without a replay ledger.
  Too risky for V5.
- Split pull-forward with debt ledger, town-adaptive COW→SHEEP conversion, wool-gate
  staged release, mirror frontrun: same verdict — real upside but needs dedicated
  ablation vs strong opponents first.
- Idle WATER/HARVEST rescues and unprioritized fertilizer sweep: already rejected by
  friend's ablations (-8.3k / -9.1k / -2.5k vs baseline). Not revived.

## 6. Validation (kaggle-environments 1.32.7, `my/eval_suite.py`)

| Test | Result |
|---|---|
| `py_compile` | OK |
| Smoke, seed 42 vs random | V5 138,570 vs 0, 1.9 s, no error |
| vs random, 10 seeds 42-51 | V5 144,671 mean, 10W-0L (V4 same seeds: 153,335 — V5 trails ~8.6k absolute; W/L identical, and ladder scores W/L only) |
| H2H V5 vs V4, 20 games alternating seats | **V5 15W-5L**, mean 88,091 vs 87,851 (+240) |
| H2H V5 vs silver-2000+ agent, 10 | **V5 10W-0L**, 106,854 vs 86,152 |
| H2H V5 vs v27 agent, 10 | **V5 10W-0L**, 108,747 vs 71,008 |
| Crash/error count | 0 across ~50 games (~36k turns) |

Reading: V5 keeps V4's field dominance and adds a mirror edge (sparse ordering pays when
both players contest the same premium curves). The vs-random absolute deficit is noted
honestly; it does not cost Elo (both 10-0), but V6 should re-check it over more seeds.

## 7. Submission record

- Artifact: `sub/presub-v5/submission.tar.gz` (30,298 bytes, contains `main.py` at root).
- Command:
  `kaggle competitions submit kaggriculture -f sub/presub-v5/submission.tar.gz -m "V5 safe overlays (feed5, sparse SELL order, terminal $1)"`
- Returned submission `56057787`, PENDING (self-play validation) at submit time.
- Day quota after submit: 2 remaining. Active pair is now {V4 `56054972`, V5 `56057787`};
  baseline test `56054780` auto-retired (latest-2 rule) as intended.
- Monitor: `kaggle competitions episodes 56057787 -v`, logs via
  `kaggle competitions logs <EPISODE_ID> <agent_index>`, leaderboard via
  `kaggle competitions leaderboard -c kaggriculture --show`.

## 8. Risks and next steps for V6

1. New-bot warm-up: V5 starts near default rating and must climb; V4 (2075.7) covers the
   team score meanwhile. Judge V5 on winrate vs 1900-2100 peers, not first-day rating.
2. If V5 underperforms peers over ~20 episodes, prime suspect is sparse SELL ordering
   (revert Hunk 3b first — it is the only hunk that changes mid-game market order).
3. V6 candidates in order: (a) strict-future ablation of Hunk 3b on recorded top-200
   replays; (b) weed-repair-with-replay ledger; (c) fresh-tape evaluation with
   prefix-guard discipline; never combine untested changes again (the V4-draft -99k
   lesson).

Update 2026-09-07 (Chiranjieev game, episode 106349904, V4 WIN +5058 vs rank ~454):
geese evidence is now 2-0 vs pasture-only herds (Calmracer +3397, Chiranjieev +5058)
— keep the coops is the default. Gap opened t432-504 (days 18-21), so the mid-game
frontier refines from "days 21-24" to "days 18-24". Terminal $0 rot both sides again.
Pre-V6 recon priority stays: diverse-mix opponents (len8487-type), full-game scope,
mirrors excluded.

## 9. Production learnings (2026-09-07 — V5 validation + first public games)

Ratings at analysis time: V4 `56054972` = 2226.7, V5 `56057787` = 2191.7, baseline
`56054780` = 1532.6 (retired). Both team bots above the ~2030 bronze line. V5 plays
~1 public game per 4 minutes as the newest bot. Sample is small (1 validation + 3
public replays); ratings need ~2 days / 50+ games to stabilize — the notes below are
evidence, not verdicts.

### 9.1 Validation replay (episode 106154800, self-play, seed 0, engine 1.32.7)

- Logs (`sub/presub-v5/logs/agent0.json`, `agent1.json`): empty stdout, no stderr,
  per-turn durations ~0.05 ms after a 0.12 s turn-0 (BLOB decompression). Both DONE.
- Shops had no YARN_STORE in all 8 unlocks → both seats correctly stayed MAIN all game.
- Money identical through t360, then tiny divergence to a 644-coin gap on ~64k
  (63629 vs 64273). Cause: weed-spawn RNG hits the two farms differently, so `weed_dig`
  fires on different turns per seat. This is the repair working as designed, and it
  bounds mirror self-play expectations: even identical code does not tie exactly.
- Milk collapsed to $15-34 late (mirror milk dumping; shops were bakery/pet/farmers/
  smoothie/ice-cream). Carrot spiked to 115-146 on 3 PET_CAFEs + farmers markets, but
  was correctly untouched — carrot branch exists only under YARN and there was no yarn.
- Final shed $0 rot both seats: `dead_stock` + terminal sweep fully liquidated.
- Verdict: all V5 overlays healthy in production; nothing errored.

### 9.2 First public games: 2W-1L — the wins matter more than the loss

- WIN vs L7n (rank 513, 2226-class 2221.8), seed 478193935: 73069 vs 64884.
- WIN vs Andrew Reed (rank 372, 2331.4), seed 1398065810: 100175 vs 95660.
  Both victims rated above us — these wins drive V5's climb from default toward 2191.7.
- LOSS vs mogura2.0 (rank 355, 2350.1), seed 1607074877: 68276 vs 68341 (−65 coins).
  A sub-100-coin loss to a far stronger bot costs almost no Elo.

### 9.3 Loss autopsy, episode 106183220 (−65 coins)

- No yarn store all game → MAIN (correct). Carrot 43 at t360, unusable off-yarn —
  single data point, no redesign justified.
- Wool $1-37 all late game (no yarn demand + glut); milk 38-72.
- Money identical through t504; the entire gap opened t504-576 (−50) and held flat to
  t719 (−65). The loss was decided on days 21-24 — the exact zone where the removed
  MILK_GLUT branch used to diverge (t577). Staying MAIN remains correct on average per
  the V4 ablations, but top-350 meta beats our continuation specifically there.
- Terminal already perfect ($0 rot both sides): nothing left to squeeze. This loss class
  is unfixable via liquidation — only via a better day 21-24 continuation.
- Confirmed V6 frontier (in order): (a) day 21-24 continuation vs top-400 meta, tested
  strict-future vs recorded top-200 replays; (b) leave terminal and SELL ordering alone
  — both validated perfect/healthy in production.

### 9.4 What to watch while ratings converge

- Winrate vs 1900-2300 peers and close-loss share (v27's authors tracked exactly this:
  all 3 of their losses were close, <4k — ours match that pattern so far).
- Any loss with nonzero final-shed rot on our side → re-open terminal investigation.
- Any cluster of losses on YARN-branch games (n=1 so far: the old Ray Roberts V4 game)
  → re-open the t=226 yarn decision, but only with multi-game evidence.

## 10. Bucketed W/L vs opponent strength (20-replay sample, 2026-09-07)

Source: `sub/replay-buckets/` — 10 V5 + 10 V4 public replays, spread oldest→newest per
bot (one file was the friend's solo-account game and was excluded → 19 usable).
Opponent strength = current-leaderboard rating as proxy (not at-game-time rating, so
treat bucket edges as approximate). Replays are NOT committed (607MB).

| Bot | Episode | Res | Us | Opp | ± | Opponent | OppRank | OppScore |
|---|---|---|---|---|---|---|---|---|
| V4 | 106137593 | WIN | 85185 | 72818 | +12367 | Kosakunin | 1280 | 1732.9 |
| V4 | 106149809 | LOSS | 90018 | 111579 | −21561 | Sergey Kutepov | 597 | 2199.3 |
| V5 | 106154995 | WIN | 174918 | 56130 | +118788 | Manuel Pérez | 4909 | 599.1 |
| V4 | 106160708 | WIN | 77799 | 76941 | +858 | Michael Silverblatt | 717 | 2115.2 |
| V5 | 106165740 | WIN | 89883 | 81150 | +8733 | Arthurs Torres24 | 1149 | 1840.2 |
| V4 | 106172603 | TIE | 67925 | 67925 | +0 | Max Podd | 362 | 2372.6 |
| V5 | 106178677 | LOSS | 53273 | 60017 | −6744 | nvidia fan | 690 | 2129.4 |
| V5 | 106188780 | WIN | 142780 | 131708 | +11072 | DeeperNet | 621 | 2185.8 |
| V4 | 106196324 | WIN | 93945 | 82907 | +11038 | MMN0222 | 507 | 2273.2 |
| V5 | 106199733 | LOSS | 96676 | 98823 | −2147 | ShiviWhivi | 361 | 2373.8 |
| V5 | 106211902 | WIN | 73187 | 69790 | +3397 | Calmracer | 354 | 2381.3 |
| V4 | 106233573 | WIN | 110118 | 103721 | +6397 | Sarthak Sharma | 759 | 2085.3 |
| V5 | 106245124 | WIN | 149806 | 143221 | +6585 | Lunospital | 556 | 2230.8 |
| V4 | 106264250 | WIN | 102773 | 101019 | +1754 | Wang H2O | 518 | 2264.2 |
| V5 | 106272326 | WIN | 77796 | 76606 | +1190 | yuki0731 | 655 | 2162.2 |
| V4 | 106297305 | WIN | 87190 | 87135 | +55 | koren sabag | 397 | 2349.4 |
| V5 | 106299597 | LOSS | 75203 | 75483 | −280 | ShiviWhivi | 361 | 2373.8 |
| V5 | 106329422 | LOSS | 58175 | 64618 | −6443 | len8487 | 364 | 2371.8 |
| V4 | 106329608 | WIN | 63341 | 60093 | +3248 | Maksimov Evgeniy | 439 | 2323.8 |

Tally (buckets: <2200 / 2200-2350 bubble / 2350+):

| Scope | <2200 | 2200-2350 | 2350+ | ALL |
|---|---|---|---|---|
| V4 | 3W-1L | 4W-0L | 0W-0L-1T | 7W-1L-1T |
| V5 | 4W-1L | 1W-0L | 1W-3L | 6W-4L |
| BOTH | 7W-2L | 5W-0L | 1W-3L-1T | 13W-5L-1T |

Reading: bubble undefeated (5-0) — the firewall holding our rank. 2350+ is the
ceiling (1-3-1, all close except −6443). Both sub-2200 losses were early-climb games.
In-sample V4 > V5, but samples cover different lifespan phases — ladder has them 6
points apart, same tier. Caveats: n=19, proxy ratings, arbitrary bucket edges.

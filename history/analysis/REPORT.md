# Success and failure modes in our arena entries

Analysis of the archived snapshot: **78 matches, 2,031 agent hands, 3,604 agent
decisions**, covering `rain man` and `step2`. Every decision has **1,000 Monte
Carlo trials with eval7 0.1.11 for each of two equity estimators**. Identical
card/board/active-opponent contexts within a hand reuse the same estimate.

## Main findings

1. **Execution failures are a clear, directly actionable leak.** There are 59
   failed decisions, including 20 token-cap failures, 14 illegal checks facing
   bets, and seven scratchpad updates during a hand. Some forced folds discard
   very strong holdings.
2. **`step2`'s success comes largely at showdown, not from a radically different
   preflop style.** Its preflop participation/raising rates resemble `rain man`.
   Postflop bets are more often backed by strong hindsight equity, but different
   cards and opponents prevent a causal claim about training.
3. **Do not imitate all the big winners.** Large winning hands include marginal
   all-ins and substantial luck. There are also large losses where committing
   chips was favorable against the actual cards.
4. **The strongest strategic hypothesis is opponent-range calibration.** Most
   postflop calls look affordable against uniformly random hands, while many
   are behind the actual holdings. Conversely, some river raises induce folds
   of winning hands. Neither a blanket "call less" nor "fold less" follows.

## Results and style

| Metric | rain man | step2 |
| --- | ---: | ---: |
| Matches / hands | 33 / 793 | 45 / 1,238 |
| Net BB | -665.0 | +1,636.5 |
| Arena EV BB/100 | -52.39 | +97.93 |
| VPIP: voluntarily put chips in preflop | 36.6% | 38.8% |
| PFR: raised at least once preflop | 17.4% | 19.0% |
| Called/limped preflop without raising | 19.2% | 19.8% |
| Hands reaching hero showdown | 102 | 185 |
| Net BB in hero-showdown hands | -508.0 | +1,593.5 |
| Net BB in other hands | -157.0 | +43.0 |
| Format errors / decisions | 29 / 1,426 (2.0%) | 30 / 2,178 (1.4%) |

The PFR/VPIP gap remains large in both entries. Among first decisions with no
earlier voluntary investment, `rain man` open-calls 51/383 and `step2` 107/663.
These are observations, not proof that limping caused a loss. In fact,
`step2`'s called-without-raising hands won 1,289 BB, driven partly by very large
all-in pots; the same category lost 732.5 BB for `rain man`.

Position awareness is present: button VPIP is 55.9% / 60.3%, versus UTG VPIP
29.1% / 25.7%. The samples mix table sizes as players bust. The more directly
comparable six-player VPIP is 176/472 = 37.3% for `rain man` and 241/654 = 36.9%
for `step2`. The headline VPIP difference partly reflects table composition.

A 5,000-resample, whole-match bootstrap puts the descriptive 95% percentile
interval for arena EV BB/100 at approximately **[-165.2, +56.5]** for `rain man`
and **[+16.0, +185.0]** for `step2`. This preserves within-match dependence but
does not control for time, opponent composition, or repeated opponents. It is
not a paired test of the checkpoint.

## Success: value extraction when the hand is strong

| Postflop betting metric | rain man | step2 |
| --- | ---: | ---: |
| Bets | 166 | 240 |
| Mean hindsight equity on bets | 57.6% | 65.5% |
| Bets with at least 80% hindsight equity | 65/166 (39.2%) | 121/240 (50.4%) |

This suggests better value targeting in `step2`, although a more favorable
distribution of situations could explain some or all of it. Strong-hand checks
also remain: among unbet-to postflop decisions with hindsight equity >=80% and
uniform-opponent equity >=70%, `rain man` checks 9/60 and `step2` checks 29/114.
These are review candidates, not automatic missed-value labels: traps, position,
and opponents' responses matter.

Examples worth retaining as favorable decision sequences:

- **`step2`, K9 offsuit, +195.5 BB:** [hand 11](https://www.pokerbots.ac/matches/m_20261115t052001_dbc1c5?hand=11).
  On K-3-2 it bets and continues with 72.9% hindsight equity against TT and AJ.
  The turn 9 improves it to two pair and approximately 95.1% equity; it calls
  another 42.5 BB into a 250.5 BB pot. This is a strong hand continuing against
  weaker holdings, not just a lucky terminal payoff.
- **`rain man`, AK suited, +184 BB:** [hand 14](https://www.pokerbots.ac/matches/m_20261115t001601_1b8159?hand=14).
  On K-J-8 it raises with approximately 72.4% equity against TT and AJ, then
  raises the turn with 87.4%. It calls the small river bet while ahead of AJ.
- **`rain man`, 77, +85 BB:** [hand 3](https://www.pokerbots.ac/matches/m_20261115t012758_837f44?hand=3).
  It bets a flopped set with approximately 97.1% equity, then bets the full
  house on the paired turn and river. This is a cleaner positive demonstration
  than selecting examples solely by the largest realized win.

## Failure: output and tool discipline

| Error | Count |
| --- | ---: |
| Hit the 5,000-token cap | 20 |
| No valid action JSON | 15 |
| Check when facing a bet | 14 |
| Called update_scratchpad during the hand | 7 |
| Missing bet amount | 1 |
| Bet/raise below the legal minimum | 2 |

These are direct contract violations, unlike hindsight disagreements about a
strategic choice. Invalid decisions are replaced by check or fold.

- **Trips folded due to truncation:** `rain man` holds Ah7d on
  Td-6s-7s-3c-7c, facing 10 BB into 25 BB. The 5,000-token cap forces a fold.
  Opponent AsJs loses; river hindsight equity is exactly 100%, and equity
  against a uniform random hand is 95.05%. Calling rather than folding would
  be worth **25 BB incrementally against these actual cards**.
  [Hand 19](https://www.pokerbots.ac/matches/m_20261115t005650_2de5bd?hand=19).
- **JJ folded in a large pot due to truncation:** on Kd-6h-5c-3d, `rain man`
  faces 23 BB into 210.5 BB with JsJc against 88. Hindsight equity is 94.9%,
  versus a simple capped-call pot-odds threshold of 9.9%. The cap again forces
  a fold. Do not price this using the terminal-call formula: unmatched
  commitments/uncalled returns need separate handling.
  [Hand 9](https://www.pokerbots.ac/matches/m_20261115t003536_6444bc?hand=9).
- **Missing amount with an overpair:** KsKc on 2d-4h-7c versus QT has 97.5%
  hindsight equity. `{"action":"bet"}` omits the required amount and becomes a
  check. This loses the intended betting action, though its lost value cannot
  be quantified without modeling the opponent's response.
  [Hand 2](https://www.pokerbots.ac/matches/m_20261115t003737_1aeb6b?hand=2).

The clearest training targets are concise legal tool calls, complete required
amounts, and reserving scratchpad updates for the cleanup turn. Seven failed
actions have at least 70% hindsight equity, so the errors are not confined to
hands that would have been folded anyway.

## Failure hypothesis: calling against the wrong range

| Postflop calls | rain man | step2 |
| --- | ---: | ---: |
| Total | 112 | 151 |
| Equity against actual cards >=5 percentage points below simple pot odds | 54 | 67 |
| Equity against uniform random hands >=5 points below simple pot odds | 3 | 4 |

The stark difference is the useful clue: **"my hand beats random cards" is not
the same as "my hand beats the range that took this betting line."** On the
river, 7/12 `rain man` calls and 10/24 `step2` calls are behind the actual
remaining hands. These are small, selected samples, and a bluff-catching policy
can correctly call and still lose. These counts are not mistake rates.

- **Weak ace versus a set:** `step2` calls 66.5 BB into 96.5 BB with Ac3c on
  9d-Ah-Jd-5h against an all-in AsAd. The 1,000 trials give 0% hindsight equity,
  but 82.9% against a random hand. Simple break-even equity is 40.8%; the
  terminal heads-up call's hindsight EV is **-66.5 BB**.
  [Hand 25](https://www.pokerbots.ac/matches/m_20261115t052605_6603d2?hand=25).
- **Top pair versus an overpair:** `step2` calls 24 BB into 70 BB with KdQc on
  9c-2s-Qh-3d against KK. Hindsight equity is 2.3%, but uniform equity is 88.85%.
  The terminal call's hindsight EV is approximately **-21.84 BB**.
  [Hand 26](https://www.pokerbots.ac/matches/m_20261115t044013_0524a1?hand=26).
- **But there are folds of winners too:** `step2` bets AT on
  Ad-6d-Qd-9s-8s, then folds to a raise with 30 BB to call into 88.5 BB.
  Opponent KdTc has missed; AT is ahead. Uniform equity is 81.5% and exact
  hindsight equity 100%. This is a useful bluff-catching review, but a
  range heavily concentrated on flushes could still justify the fold.
  [Hand 18](https://www.pokerbots.ac/matches/m_20261115t024721_18b974?hand=18).

The next useful objective is calibrated opponent ranges conditioned on actions,
position, board, and sizing. A card-prediction auxiliary task could help, but
it should not be trained to memorize one precise hidden hand from one outcome.
Evaluate its effect on decisions and held-out poker EV.

## Separate good decisions, lucky wins, and unlucky losses

For all-ins with no later action on a different board, the analysis also runs
1,000 trials on the **final main/side pots** and computes expected hand net BB.
This is distinct from equity against everyone still active at decision time.
It conditions on the actual subsequent contributions/folds on the same street;
it is not the EV of every possible alternative action.

| step2 hand | Realized net BB | Final-pot MC expected net BB | Interpretation |
| --- | ---: | ---: | --- |
| Q5o, [hand 7](https://www.pokerbots.ac/matches/m_20261115t021344_102ff3?hand=7) | +367.5 | +39.7, MC SE 7.3 | Favorable given final pots, but about +327.8 BB above expectation |
| K2 suited, [hand 3](https://www.pokerbots.ac/matches/m_20261115t020616_aaaaa9?hand=3) | +199.0 | +9.7, MC SE 4.5 | The size of the win overstates the quality of the situation |
| Q9o, [hand 2](https://www.pokerbots.ac/matches/m_20261115t023457_170e96?hand=2) | +175.0 | -25.6, MC SE 3.4 | Winning result from an unfavorable commitment against the actual cards |
| A4o, [hand 15](https://www.pokerbots.ac/matches/m_20261115t045749_7c7c86?hand=15) | +123.0 | -22.4, MC SE 2.9 | Another positive outcome that should not become an unquestioned SFT target |

The Q9o hand had only 1 BB invested before calling the final 86 BB; its negative
whole-hand expectation is not merely a large amount of previously sunk money.

Conversely, `step2` loses **212 BB with AT versus 73**, despite approximately
67.7% equity when calling preflop, and loses **194 BB with AQ versus K7** with
approximately 63.7% equity. Both are strong examples of why a losing payoff
does not prove a bad decision.
[AT hand 26](https://www.pokerbots.ac/matches/m_20261115t021344_102ff3?hand=26),
[AQ hand 10](https://www.pokerbots.ac/matches/m_20261115t021344_102ff3?hand=10).

Even before equity adjustment, `step2`'s five largest winning hands total
1,242 BB, about 76% of its net profit. The arena's all-in adjustment reduces its
overall +1,636.5 BB to +1,212.425 BB, so its success is not entirely explained
by all-in luck, but raw winners alone are a poor training selector.

## Method and limits

- Uses `eval7.evaluate` as the showdown evaluator inside a seeded Monte Carlo
  sampler. The library's convenience range-equity routine is heads-up only;
  this sampler handles the actual multiway pots and splits ties among all
  winners. [eval7 source](https://github.com/julianandrews/pyeval7/blob/master/eval7/equity.pyx).
- For each target decision, replay prior folds to identify active opponents;
  all-in players remain active. Use only the board visible at that action.
- **Oracle equity:** opponents' actual cards are fixed. All dealt hole cards,
  including folded players' cards, are removed from the runout deck. This is
  explicitly privileged hindsight, not information the model could observe.
- **Uniform equity:** sample every active opponent's two cards uniformly
  without replacement, blocking only hero's cards and the visible board. This
  is an uninformed baseline, not an action-conditioned opponent range.
- Future board cards are always resampled; the recorded future board is not
  used. A fixed seed is derived from match, hand, board, and active seats.
- At 1,000 trials, worst-case equity standard error is about 1.58 percentage
  points (roughly +/-3.1 points at 95%). River oracle equity has no runout
  uncertainty. Empirical SE can also be zero when no wins were sampled; that
  alone does not establish mathematical impossibility on earlier streets.
- Simple pot odds are `call_cost/(pot_before+call_cost)`. They ignore future
  contributions, folds, equity realization, and side-pot eligibility. **Do not
  classify all preflop calls below this threshold as errors**, especially when
  other players have yet to act or an opponent's oversized bet will be refunded.
- Terminal heads-up call EV is reported only for river or opponent-all-in
  opportunities with matched commitments and no unmatched side-pot layers.
  The exported hindsight call/fold "regret" totals assume knowledge of actual
  opponent cards; they are not achievable policy improvements or solver regret.
- The final-pot all-in diagnostic excludes hands with later betting decisions
  on a different board. It is a subset, not a replacement for the arena's
  broader all-in EV accounting. Fractional ties split chips evenly rather than
  model odd-chip allocation.
- BB analysis does not capture every elimination-ranking or survival tradeoff.
  This is retrospective mining of one snapshot, not a controlled strategy trial.

## Artifacts and reproduction

- `decision_equity.jsonl`: every target action, both equity estimates, standard
  errors, call price, active opponents, original tool arguments, and failure flags.
- `hand_features.jsonl`: per-hand style, outcome, hero showdown, and eligible
  final-pot all-in expected values.
- `metrics.json`: submission/street/position/equity-band summaries.
- `examples.json`: largest wins/losses, high-equity failures, and terminal
  hindsight call/fold examples.
- `match_bootstrap.json`: match-clustered descriptive uncertainty.

From the `sft` worktree:

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r history/analysis-requirements.txt
.venv/bin/python history/analyze_equity.py
.venv/bin/python history/verify_equity.py
.venv/bin/python history/verify.py
```

Sanity checks cover a known winner, three-way ties, side-pot eligibility,
AA-versus-KK equity, deterministic sampling, and joins of every computed row
to its source action. The archive verifier checks source hashes, complete
listing coverage, per-match decision/hand counts, and chip accounting.

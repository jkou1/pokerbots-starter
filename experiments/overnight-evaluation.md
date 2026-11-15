# Overnight evaluation plan — 2026-11-15

## Incumbent reliability and checkpoint selection

Problem: aggregate Arena fallback rate includes obsolete failed entries, while checkpoint quality has not been compared on paired official games. Current entry is `return of rain man`, `infer_b0f5e9429b7e`, combined SFT iteration39 `ckpt_51eee61470f7`. Already-running frozen opponent deployment serves iteration19 `ckpt_ad74c826c9ad` from the same training run.

Hypothesis: earlier/later SFT checkpoints differ materially in poker performance despite low supervised loss; current incumbent may already have solved the historical execution failures.

Targeted approach: audit ten latest completed incumbent Arena matches, then compare both existing deployments with identical twelve selection seeds, policy seat cycling, five `ac-vals-model` opponents, official30hand carry-stack rules, thinking and token caps. No new GPUs or connector modification. Six concurrent games per endpoint. Run platform four-hand smoke before a larger platform evaluation. Official-game local collection starts from `origin/main` without training hints.

Test: direct `vals_tools.collect_policy`, artifacts `data/experiments/overnight-{incumbent,ad74}-select`; platform smoke `eval_bf31fcaff054`. Whole-game comparison uses `vals_tools.game_score`. Include place, bust rate, realized BB, invalid decisions. Review emitted table talk for workplace appropriateness before promotion, at most five minutes per check.

Success: complete graded smoke with valid real tool calls; paired selection placement improvement with no material invalid-action regression. Twelve games are screening, not strong statistical evidence; expand a promising comparison before promotion and preserve a separate final holdout.

Stop/triage: immediate HTTP/auth/parser failure investigation; stop repeatedly failing jobs, avoid endpoint overload, and do not interpret failed games as valid evidence. No deployment promotion based solely on imitation accuracy or training loss.

Initial evidence: ten latest incumbent Arena games contain471 decisions and zero fallbacks/format errors; no emitted table talk. Raw audit artifacts under `data/experiments/arena-incumbent-audit`. Thus historical aggregate9.3% fallback is not the current entry's error rate.

## Leader analysis

Problem: reaching first place requires a substantial strategy improvement, not merely fixing obsolete execution bugs.

Hypothesis: current combined SFT's nineteen unique postflop retention examples inadequately teach value extraction and range calibration; fresh legal leader postflop demonstrations may offer higher return than additional preflop imitation.

Targeted approach: inspect live leaderboard and ten latest Accord games. Use only public records for descriptive analysis; no causal claim or selection of lucky winners as expert targets.

Test: report leader identity, EV-adjusted returns, fallback rates, preflop participation/raises and postflop actions. Validate any derived training examples with full engine replay and split by source deal before extraction.

Success/stop: produce a concrete training hypothesis quickly; stop expanding descriptive analysis once a viable high-impact experiment is identified.

Initial evidence: overall leader Professor Pete rating1329 EV+64.2bb/100; leading team Accord rating1163 EV+30.1. Accord's recent ten games show27% VPIP,18.3% PFR,58postflop bets+4raises versus20calls. Descriptive sample only. Existing ignored Pete postflop corpus is absent locally; committed historical archive and fresh public match retrieval are available.

## Fast paired single-hand screening

Problem: external opponent inference takes roughly156–177seconds per single hand, slowing broad checkpoint selection.

Hypothesis: a frozen locally served checkpoint provides a faster, reproducible opponent pool that can reject poor candidates and compare poker decisions while longer official games finish.

Targeted approach: create32fresh single-hand selection tasks, balanced seats, fixed explicit frozen-ad74 opponents, official action schema and thinking, all-in EV grading. Run both existing deployments on exactly the same task IDs via platform evaluation; no additional GPU allocation. Bound concurrency according to RL endpoint load and preserve the active harness.

Test: compare paired task rewards, hand EV, and format error counts. Success is a completed clean platform screen with an informative paired estimate; expand only promising comparisons. This screen does not substitute for full-game placement or a final holdout. Stop or reduce concurrency on sustained endpoint errors or degraded RL throughput.

## Pete postflop held-out diagnostic

Problem: the incumbent's postflop coverage is sparse; game returns are noisy and slow.

Hypothesis: valid tool-call agreement with the leading house bot on source-match-held-out postflop decisions exposes a specific weakness and can detect whether targeted postflop SFT changes that behavior.

Targeted approach: evaluate147 fixed selection records from `pokerbots-pokerbench/experiments/pete-postflop-v1/select.jsonl` on incumbent and iteration19, with official tool schema, thinking, token cap, temperature zero, concurrency4 each. Keep103final records untouched.

Test: legal rate, per-action recall, exact action/amount agreement, match-clustered paired interval. This is imitation, not a poker-win metric. Success is reliable tool outputs and improved postflop imitation without losing minority actions; actual game screening remains necessary. Stop on schema/provenance mismatch or repeated endpoint failure, and never train on the observed invalid-enum regression case.

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

## Practical overnight promotion and rollback gate

Problem: hundreds of games are infeasible overnight, while loss or imitation alone can promote a broken model.

Hypothesis: execution checks, targeted held-out improvement, modest matched game evidence, and a monitored Arena canary can capture large gains with bounded deployment risk.

Targeted approach and tests:

1. Require a ready deployment, real `submit_action` probe, and one complete official30hand carry-stack smoke game. Inspect action and cleanup calls; plain text is insufficient.
2. Evaluate147held-out postflop decisions and the fixed invalid-enum regression input. Require legal rate at least98% and no decline over2percentage-points versus incumbent. Inspect failures, repeat the known enum regression, verify cleanup tool and scratchpad bound. Repeated failures block promotion until repaired.
3. Compare at least four paired official30hand selection games, expand toward12 when practical, with identical seeds/seats/opponents. Report placement, busts, chip/EV diagnostics, invalid decisions, and whole-game paired bootstrap interval. Positive interval supports promotion; noisy interval permits a labeled canary only with meaningful directional gain (at least0.5mean-place improvement or large consistent EV gain), no reliability regression and corroborating targeted improvement. Four games do not establish proven superiority.
4. Choose one candidate before a separate six-game official30hand final holdout using unused seeds. Never rank additional checkpoints on that holdout. If it contradicts the gain or exposes failures, retain incumbent; a revised experiment needs a new final holdout.
5. Review all available emitted table talk from smoke/selection plus several fresh normal/adversarial-chatter probes for workplace appropriateness, spending no more than five minutes. Record sample, duration and findings. Silence passes. Inappropriate output blocks promotion until repaired.
6. Preserve incumbent deployment/checkpoint for rollback. Register candidate separately; verify active Arena inferenceID. Roll back immediately on endpoint failure, inappropriate talk, repeated enum/cleanup failures, or at least5% invalid decisions among first40observed decisions. Review after12completed canary games and revert on mean placement at least one place worse than incumbent reference without compensating evidence. Card losses alone are not tooling failures. Keep uncertainty explicit.

Success: verified healthy entry with defensible directional gains and monitored canary. Stop on failed gates; repair or retain incumbent. These are operational decisions, not a statistical guarantee of first place.

### Baseline postflop diagnostic result

Completed147selection decisions from12source matches for both existing checkpoints. Both were100%legal, but checked all39teacher-bet decisions and all77teacher-check decisions. Incumbent action distribution:116check,17fold,11call,3raise; no bets. Iteration19:116check,13fold,17call,1raise; no bets. Incumbent teacher agreement64.63%, iteration19 69.39%; iteration19-minus-incumbent match-bootstrap interval[+1.85,+7.69]percentage-points. This is teacher imitation, not poker quality. The complete absence of bets supports targeted postflop training; general legality is already strong.

Platform4hand smoke completed with one invalid actionenum `submit` from incumbent; all three other decisions were legal. The known failure is preserved as a regression holdout and not added to training.

## Faster full-game incumbent reference

Problem: official games against the external opponent are slow, while single-hand EV cannot measure carried-stack placement.

Hypothesis: six official30hand games against the already-running frozen-ad74 opponent provide a faster paired placement reference for the forthcoming postflop candidate.

Targeted approach: same original selection seed generator and seat cycling as other direct games; frozen opponent only; six games, concurrency2; preserve official rules and fixed baseline configuration. Compare future candidate on exactly these seeds/seats/opponent.

Test/success: completed whole-game placement, errors and cleanup logs with no inferenceGPU allocation. Stop or reduce load on sustained endpoint errors or RL throughput degradation. This is selection evidence only; final holdout uses unused seeds.

## Cleanup efficiency and factual retention preparation

Problem: observed own frozen-model cleanups exceed5000characters repeatedly, wasting decode and retry time. Current selection games cannot become training data.

Hypothesis: a small retention mixture of genuinely recorded concise successful own cleanup replies can preserve bounded factual memory while postflop training restores betting.

Targeted approach: collect six fresh training-seed one-hand games with current incumbent against scripted legality-control opponents, concurrency2, using exact recorded cleanup inputs/replies. Preserve raw trace, source seed, split, model and checkpoint. Separately preserve up to ten actual overlong cleanup inputs from existing selection games as held-out stress cases, with no fabricated private notes.

Test/success: identify at least three successful factual recorded replies <=1500characters; validate facts against the observed transcript/game log. Selection stress cases stay outside training, and no new GPU/job allocation occurs. Stop if source split or actual private-input provenance cannot be established. Proposed later training mix <=15%cleanup is not launched here.

### Cleanup evidence result

Collected six independent TRAIN-seed own games, preserving actual raw runtime inputs/replies and private cleanup success records. Four observed targets279–434characters passed exact board/stack and factual action-subset checks. Two short replies were rejected for wrong final boards/stacks; shortness alone is insufficient. Accepted targets were never rewritten. Their action notes are factual subsets, not claimed chronological transcripts. Saved `cleanup-own-train-v1/validated-train.jsonl` and `validation.json` with source hashes.

Preserved ten distinct actual SELECT overlong cleanup inputs, five per model, as stress cases. Bounded initial-cleanup gateway sample: incumbent37/97over5000characters, frozen110/222. These are sampled request rates, not complete-game rates. Raw source rows, exact prompts/replies, cutoff and hashes live under `cleanup-stress-select-v1`; selection cases remain excluded from training.

## Preflop retention guard

Problem: postflop-targeted updates could damage the incumbent's preflop policy despite retaining25%preflop targets.

Hypothesis: a fixed source-match-held-out preflop diagnostic detects large action or legality regressions cheaply before full-game promotion.

Targeted approach: evaluate all354preflop selection records from the same frozen Pete release on incumbent once, then proposed candidates only. Temperature zero, official schema/thinking, concurrency4, no final holdout usage.

Test/success: compare legal rate, macro/per-action recall and source-match-clustered agreement change. Block gross legality decline and investigate substantial preflop accuracy loss; teacher agreement remains a guardrail, not a poker-win estimate. No new GPU allocation.

## Dashboard-visible native official game evaluations

Problem: local decision diagnostics and ongoing local games do not appear in AC2's Evals dashboard.

Hypothesis: registered native BYOH evaluations on existing deployments provide visible, reproducible game evidence without allocating extra inference GPUs.

Targeted approach: all future game comparisons use a versioned six-task official30hand dataset, fixed seeds/seats and frozen-ad74 opponent, maximum parallelism2, retries0, per-decision300-second safety bounds and active monitoring. Existing completed/in-flight local games are preserved as accurately labeled local evidence rather than replayed solely for display. Uploads verify all membership and first/middle/last content. Use the user's required lmathias account, organization and UnixUID preflight before every submission.

Test/success: visible named eval ID/dashboard link, real tools and completed harness grading; retrieve full game logs by compute-job attribution for placement/cleanup analysis. No extra GPU engine is requested. Do not present raw clipped reward as placement. Final holdout is separately named and cannot launch before one candidate is chosen.

New-account setup repair: initial native smoke submission was rejected before job creation because the new account lacked its user-scoped project runtime `AC2_API_KEY` secret. Installed the existing new-account key in that account's user-scoped runtime secret only, verified presence, and retried successfully as `eval_a1cc729a3948`. No organization secret or credential file was changed; no secret value was logged.

## Mixed-teacher fixed diagnostic reference

Problem: a proposed Pete/Carlos action mixture needs an incumbent reference before its results can be interpreted.

Hypothesis: a fixed balanced256decision source-held-out diagnostic distinguishes action/legality weaknesses without consuming extra training or serving GPUs.

Targeted approach: run the existing incumbent only on `mixed-teacher-actions-v1/fast-select.jsonl` at concurrency4 while the separate rotating slot finishes its promised RL preparation. Do not delay RL checkpoint selection to add more candidate diagnostics. Preserve source order/provenance and keep all final records untouched.

Test/success: report legal rate, action/sizing agreement and per-action recall, explicitly teacher imitation rather than winnings. Stop on source schema or split mismatch; no new deployment or GPU allocation.

## Fixed river-overbet attribution probe

Problem: one RL5 loss involved a legal king-high call against an extreme river shove, but the paired opponent path is stochastic and does not identify whether the behavior is inherited.

Hypothesis: replaying the exact acting-player information across parent ad74, RL20 and baseSFT20 distinguishes an inherited range/sizing weakness from a new policy change.

Targeted approach: retrieve the actual river decision input from native RL5 traces; preserve its public observations, own cards and actual tool history, excluding un-echoed historical reasoning. Four samples per existing endpoint, global concurrency2, official tools/thinking/cap. No opponent hole cards, future outcomes, training labels or new GPUs.

Test/success: report only requested actions, legal rate and call/raise bounds. This selection-only source stays excluded from training. Stop on source-state mismatch or transport failures; do not infer optimality from showdown outcome.

## Sealed final holdout against frozen base SFT20

Problem: final validation needs fresh deals and an opponent distinct from the ad74 selection pool, while long opponent cleanups slow testing.

Hypothesis: six fresh, balanced official 30-hand games against the already-serving base SFT20 provide a faster, distinct-opponent final comparison without extra GPUs.

Targeted approach: pin the base SFT20 inference ID, checkpoint and version as a frozen dependency. Launch only the incumbent baseline now, at parallelism two, under the required new account. Do not query scores, inspect game outcomes, summarize poker metrics or use those results for model choice until one candidate is explicitly selected using selection evidence. Later test that one candidate on the same six deals/seats/opponent. This is an operational seal, not a claim that AC2 dashboard access is restricted.

Test/success: native job ID and health metadata are visible; dataset membership and sampled content are verified; opponent identity/version remain unchanged. After selection, compare paired placement, raw EV, invalid actions and cleanup. Base SFT20 remains frozen through the whole test, even after its own selection eval finishes. Its known occasional short-stack sizing errors are part of this fixed imperfect opponent, not expert labels.

Stop/triage: investigate setup or transport failures and sustained lack of technical progress; do not inspect poker results to decide whether to stop or choose a model. No active training/eval opponent changes, no extra serving model, and no duplicate baseline submission. A revised candidate after failed final validation needs a fresh holdout release.

## RL20 paired development full games against frozen base20

Problem: the positive fixed32 RL20 chip-EV screen does not establish carried-stack placement or reliability against a betting opponent.

Hypothesis: RL20 improves matched game EV and placement relative to the incumbent against base20 without material tool, sizing or cleanup regression.

Targeted approach: four fresh selection-only deals, identical seats/seeds for both policies, immutable base20 inference ID and version, official 30-hand format. Both native existing-deployment jobs run at maximum parallelism two with retries zero, using no additional GPUs. The four seeds are verified disjoint from the six sealed final seeds and prior training/selection releases.

Test/success: compare raw attributed logs for paired unclipped EV, placement, realized returns, busts, invalid decisions and cleanup. Directional gains with intact reliability justify candidate consideration; four games remain noisy. Dashboard clipped reward cannot establish quality.

Stop/triage: repair technical failures or sustained stalls, preserve all model versions while requests are active, and do not inspect sealed final outcomes for development choice. Framework and receipt are written before native submission under verified lmathias UID10464.

## Source-verified optional schema check and final selection

Source correction: the event server automatically adds optional `say` even when a dataset specifies only `action` and `amount`. Existing paired games therefore expose the documented Arena action/amount/say interface; they are reduced optional diagnostic schema tests, not talk-disabled. The local default additionally exposes optional `p_win` and `read`. The live Arena server code has not been retrieved, so those local diagnostic fields are not asserted to be live Arena fields.

Problem: a candidate should also preserve real-tool behavior when the local default diagnostic fields are present.

Hypothesis/targeted approach: one fresh native 30-hand functional game, with no submit_fields override, against the pinned base20 opponent, retains legal action and cleanup behavior. Preserve normal event sanitizer, strict legality, carried stacks and token caps. This is functional evidence, not another performance ranking sample. Test actual native logs for valid tools/sizing, accepted cleanup, wrong tools and emitted raw/sanitized table talk; investigate any real protocol failures, without changing the running harness.

Before opening final outcomes, the coordinator explicitly selected RL20 checkpoint11e7/inference9efa/version1 from all four completed development pairs, fixed32 evidence and protocol guards. The selection artifact hashes the full development summary and records uncertainty. Final release accepts only that selected candidate on the exact pre-existing six deals/seats/opponent/version/schema; no other checkpoint can be selected from its results. The local-default functional smoke runs concurrently and remains mandatory before promotion. The final collector refuses outcome access before the explicit selected-candidate submission/unseal condition.

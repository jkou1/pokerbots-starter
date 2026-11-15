# Training runbook

## Verified overnight platform constraints (2026-11-15)

These are observed account-specific constraints, not guesses about general AC2 capability. Current user instructions take precedence over older recipes below.

- Future submissions use the newly authorized account (UID 10464) and the existing organization. Verify identity before each train, deployment, evaluation, or artifact write. Do not cancel existing jobs merely to migrate their owner.
- Native BYOH evaluations require `AC2_API_KEY` in the submitting account's **USER-scoped runtime secrets**. Check key-name metadata without printing values. The new account initially lacked this secret; adding its existing key to its own user scope enabled native evaluations. Do not overwrite organization secrets.
- Use `checkpoints.promote()` / `promotion_status()` for serving conversion. The legacy `checkpoints.convert()` endpoint returned 403 for this event account. Conversion does not itself create an inference deployment.
- Set replica counts explicitly. A Qwen training job uses four trainer GPUs plus two for one rollout engine; a standalone deployment uses one. Current GRPO has in-run evaluation off and uses existing deployments for manual evaluations.
- The server rejected explicit `trainer.samples_per_optimizer_step`; derive the optimizer batch from `problem_batch_size * samples_per_problem` and verify the effective configuration. It also rejected explicit SFT GPU overrides and SFT evaluation-replica fields. Do not repeatedly submit unsupported fields.
- The event account cannot inspect unfiltered engine logs, job specifications, or SSH into jobs. Preserve complete customer logs and available dispatch state. Missing log permission is not proof of a model or algorithm failure.
- Managed SFT may place the single newline after `<think>` in `student_prompt`, rather than in target tokens. Audit the combined prompt and target; require a supervised `</think>` before the real tool call. An API effective config omitting warmstart metadata is not sufficient evidence that checkpoint restoration failed; compare matching-batch losses and runtime seed paths.
- Distinguish SFT zero-based checkpoint iterations (e.g. 19 after 20 updates) from GRPO checkpoints (e.g. iteration 5 after update 5).
- Overall SFT loss is dominated by repeated protocol/tool syntax. Use action- and amount-token diagnostics plus fixed held-out behavior for stop/extend decisions. GRPO mean advantage near zero is normal; use nonzero gradients, within-group reward variation, validity, and paired checkpoint evaluations.
- Full-game primary grader scores are clipped rewards. Report unclipped chip EV, placement, busts, invalid actions, and cleanup behavior from attributed game logs; a score of 11 is not proof of convergence or superiority.
- All official event games conserve 1,200 chips = 600 BB. During a hand, remaining stacks plus the pot equal that total.


This runbook implements the experiments defined in [STRATEGY.md](STRATEGY.md). The current experiment starts from base weights and uses the refreshed Pete archive plus starter-deal replay; historical step2 continuation recipes appear below. No model from the new SFT experiments has yet passed promotion evaluation. The user requested committing and pushing the implementation while the corrected run is in progress. Organization-scoped temporary connector credentials are authorized, but these offline SFT runs require no connector. The upstream opponent-credential issue from the stopped GRPO run is documented in [TRAINING_RUN_AUDIT.md](TRAINING_RUN_AUDIT.md).

## Active experiment: corrected combined SFT from base

The latest user instruction supersedes the earlier checkpoint-first curriculum. Direct SFT from base completed successfully as `train_3061a33ce578` on `pokerbots-pete-base-sft-v1-train`: 1,328 training examples, 40 completed updates, batch 64, maximum learning rate `5e-6`. Its final checkpoint is `ckpt_0212d63c5944`. No step2 or distillation checkpoint is used. The 174 selection and 96 final evaluation records stay out of training. See [PETE_SFT.md](PETE_SFT.md) for the reproducible command and evaluation procedure.

The first model failed all 174 held-out tool-call decisions under official thinking mode despite low training loss. The initial combined-data run `train_ab817f9de7c1` was stopped because it shared that target format. Corrected run `train_87b51a9211a1` starts independently from base with an explicit nonempty protocol boundary, 1,701 refreshed Pete targets, and 567 sampled starter-deal replay targets. Its receipt is `data/experiments/combined-base-sft-fixed/run.json`. Evaluation is pending. See [DATA_STRATEGY.md](DATA_STRATEGY.md) for the source audit, reproduced format bug, and repository push/Arena plan.

The base-model selection reference is complete: 60.92% action accuracy, 54.02% exact action/amount agreement, 68.67% macro action recall, and 95.40% legal rate on all 174 decisions. Later checkpoint comparisons must use that same selection file, including per-action recall and legal sizing rather than just overall accuracy. Prior run IDs and checkpoint-based recipes below are historical experiments or optional later-stage paths.

Startup checked at 2026-11-15 05:55 UTC: all 1,328 examples loaded and the first two optimizer updates completed, with 64 sequences each. TensorBoard and structured training metrics are recording. No checkpoint was available yet; the requested interval is 20 updates. Live metric snapshots and the checked status are stored under `data/experiments/pete-base-sft/`.

## What the starter supports

| Capability | Current status |
| --- | --- |
| Whole-hand GRPO and scalar chip-based grading | Available in `rl/` and the harness |
| Offline OPSD using teacher-only written hints | Available in `opsd/`; currently includes all clean decision streets |
| Deterministic decks, seat rotation, disjoint seed splits | Available in `vals_tools/tasks.py` |
| Official table-talk sanitation and private cleanup | Available in the harness |
| Pre-flop trace filtering, stage-specific hints, and checkpoint chaining flags | Implemented in OPSD/RL launchers; `--checkpoint` continues parent weights |
| Professor Pete demonstration import and supervised imitation | Collector, replay adapter, split audit, SFT uploader/launcher implemented; 1,328 training records uploaded |
| Frozen-policy routing by street | Opt-in `training_stage` and `frozen_model` task parameters implemented |
| Matched talk perturbations, cleanup targets, and message-only experiments | Defense generation/evaluation, factual cleanup export, fixed-action RL and paired talk experiments implemented |
| Full-game placement summaries and game-level uncertainty | `vals_tools.game_score` adds matched game-level bootstrap comparisons |

Offline OPSD scores stored replies under a hinted teacher. It does not directly behavior-clone a different bot's chosen actions. Pete demonstrations need a separate supervised path; the installed AC2 SDK exposes `SFTConfig` for conversation training. Canonical SFT inputs accept only system/user messages followed by one target tool call; historical assistant replies are rejected, so only the nominated reply is supervised.

Use one lineage of checkpoints. The installed SDK supports `RunConfig(model=ModelConfig(checkpoint="ckpt_..."))`; both launchers now expose `--checkpoint`. SFT launch requires either explicit `--from-base` or a selected `--checkpoint`. The initial base/Pete run needs no replay; checkpoint-based Pete continuation retains the clean replay requirement. Keep the underlying Qwen model identity in run metadata.

## 1. Prepare evidence and comparison sets

1. Collect matches from [pokerbots.ac/matches](https://www.pokerbots.ac/matches) using the archive procedure below. Resolve Pete by `house-professor-pete` in each match's seat map. Import legal, deduplicated pre-flop examples as described in the strategy. If validation yields insufficient demonstrations, mark the Pete branch awaiting usable demonstrations and continue the principles branch.
2. Version the dictated principles and freeze opponent configurations. Start with the provided `vals-hackathon/ac-vals-model`, then include available earlier checkpoints. Scripted opponents provide legality controls, but cannot establish success at manipulating LLM opponents.
3. Retain the starter split sizes as initial single-hand defaults: 2,000 training deals, 500 selection deals, 3,000 held-out evaluation deals, and a small smoke split. Split Pete records by source game; keep every derived record and perturbation in its parent's split.
4. Create separate official-game datasets: initially 120 selection games and 300 held-out games, with policy seats balanced across all six positions. Use fresh seeds and the event preset's 30 hands, carry-over stacks, and scratchpad. These counts are starting budgets, not guarantees of statistical power.
5. Keep final evaluation deals, source games, message families, and held-out opponent versions out of training and checkpoint selection. Tag dataset variants with their underlying deal identity so comparisons remain paired even when variant dataset IDs differ.

For Pete data, stratify analysis by position, hand class, stack depth, betting situation, and target action. Missing hand classes or positions are missing coverage, not evidence to infer a rule. Preserve frequencies within a repeated identical state when demonstrating mixed play. Do not infer a six-max starting range from aggregate participation alone.

### Archive procedure and dataset outputs

The source audit inspected [match `m_20261115t024346_941971`](https://www.pokerbots.ac/matches/m_20261115t024346_941971), whose Raw JSON link returned schema `vals-arena.match/1`. It contained 30 hands, all players' dealt cards, and 30 Pete pre-flop decisions with no fallback/coercion/error/scripted flags on those targets. This verifies feasibility for one match; it does not establish archive-wide quality or Pete's policy version.

The collector and adapter write these outputs under an ignored `data/arena/` directory; keep source data out of version control:

- `raw/<match_id>.json`: unchanged downloaded bytes for every completed match, including matches without Pete.
- `manifest.jsonl`: one record per match with source URLs, fetch time, hash, schema/runner version, kind/status, and collection result. Retain failed downloads for retry and report completeness against discovered IDs.
- `pete-preflop/{train,select,eval}.jsonl`: canonical decision-time observations, legal tool-call targets without `say`, and match/hand/action provenance. Keep provenance and outcomes outside the rendered model input.
- `talk/{train,select,eval}.jsonl`: sanitized messages with speaker, street, and game-context provenance. Observed chatter is a candidate corpus, not evidence that a message caused an opponent's action.
- `quality.json`: discovered/downloaded/validated counts, rejection reasons, duplicate groups, split counts, and teacher coverage. Block teacher training if there are no qualified examples or any detected cross-split duplicate leaks.

Collector behavior: traverse the All listing through its Older links, discover replay URLs, follow each replay's Raw JSON link, and fetch each match ID once. Use one request at a time, an initial one-second minimum between requests, and at most three retries with exponential backoff for transient failures; honor `Retry-After`. Cache successful downloads, write atomically, and resume from the manifest. Record non-complete matches without adding them to the frozen dataset. Use a fixed finish-time cutoff and repeat discovery until a pass finds no new completed IDs before that cutoff, because live pagination can shift during collection. Report the final collected count and collection limits rather than promise access to matches the site no longer lists.

Adapter behavior: parse the verified source fields listed in the strategy, preserve raw records, and quarantine unknown/incompatible schemas. Reconstruct each nominated observation by replaying only its action prefix; validate pot, call price, stacks, board, actor, and target legality. Keep the acting player's cards and exclude every other player's cards. Map amount conventions through engine validation instead of assuming source and harness logs are interchangeable. Store outcomes separately for analysis; do not select only successful decisions. Strip Pete's outgoing pre-flop talk from imitation targets.

Assign the Pete corpus by a stable hash of duplicate-group identity, with thresholds 80% train, 10% selection, and 10% evaluation. These proportions apply to scraped matches; the starter's separate synthetic-deal counts above remain unchanged. Split before extracting decisions, and reuse the same split for the talk corpus. If teacher and arena evaluation sets share a known underlying deal, keep that deal out of the final arena holdout.

Validate collection and conversion with fixtures for multi-page discovery, duplicate IDs, resume/retry behavior, truncated JSON, unknown schema, matches without Pete, changing Pete seat numbers, missing cards, failed/coerced targets, repeated pre-flop actions, raise-to sizing, short all-ins, and variable live-player counts after busts. Include a leakage check that deliberately changes future board cards and outcomes: the extracted earlier observation must remain identical. Keep a small public JSON fixture for adapter tests and record its source/hash.

## 2. Establish the baseline and train betting

1. Smoke-test the base model's legal tool use, then collect baseline single-hand and official-game results. Create a silent control with `say` left empty while retaining the official talk-enabled tool schema.
2. Train the validated Pete demonstrations directly from base using the active SFT configuration above. Train only the nominated action reply with the official tool schema, without fabricated reasoning or a replay mixture.
3. Compare base and candidate checkpoints on the fixed selection observations, then paired poker games. Advance the better poker policy, not automatically the more teacher-like policy. Keep the final evaluation split untouched during selection.
4. If a diagnosed gap warrants a separate principles experiment, gather clean traces from the selected policy on training deals. The OPSD builder selects the street from the latest decision observation, retains provenance, and excludes malformed, truncated, or illegal targets. Evaluate any distillation without its hint. Later checkpoint-based teacher SFT can use a 50:50 teacher/clean-policy replay mixture to preserve prior behavior; this is not the current base run.
5. Train pre-flop RL with our post-flop decisions served by the frozen selected checkpoint, and with outgoing `say` empty. Then train post-flop betting with our pre-flop decisions served by the newly selected frozen checkpoint. Each phase starts from the preceding selected weights.
6. For each RL phase, start with the existing 60-step Dr. GRPO recipe: 16 hands per step, 16 attempts per hand, KL coefficient 0.01, checkpoint and selection evaluation every 10 steps. Check earlier checkpoints and retain the best selection result. Monitor raw returns, reward clipping, and failed or truncated rollouts.

All RL training remains on single-hand tasks initially. Full-game evaluations test whether the learned policy transfers to changing stacks and tournament placement. Whole-hand integration training comes after the individual stages and may update both betting stages.

Initial OPSD batch sizes and RL settings are experimental defaults from this repository. Learning rate stays at the SDK default unless a recorded experiment changes it. The single-hand rollout budget starts at 24,576 tokens with total length 32,768; increase only after measuring truncation. Do not reuse that budget for 30-hand RL: the aggregate trajectory would need a separate feasibility check.

## 3. Train defense, then test outgoing messages

1. Build clean/perturbed decision groups from training states. Use a validated clean action-and-amount target for all members. Perturb only opponents' sanitized talk; preserve cards, bets, legal actions, and the rest of the state.
2. Continue the betting checkpoint with supervised defense examples, initially half clean and half perturbed. Include all streets and separate after-hand `update_scratchpad` targets. Construct cleanup targets from visible game facts and betting observations, preserving useful factual memory while excluding chatter-derived instructions and card claims.
3. Evaluate clean poker performance and held-out talk perturbations, including messages carried through conversation history and into later hands. Fix failures before optimizing outgoing messages.
4. Restore matched pre-decision engine and conversation states to compare a fixed betting action with silence, ordinary chatter, and candidate attack messages. Begin with a catalog of at most 20 sanitized candidates, evaluated across positions, hand strengths, and board textures. Use repeated opponent continuations and log the randomization settings.
5. Discard candidates that merely alter opponents' actions without improving our results. Evaluate promising categories on unseen message wording and held-out opponents. If none improves on silence, retain the defensive betting model as the final candidate.
6. If gains persist, add message-only GRPO tasks: one nominated post-flop relay call chooses `say` alongside a fixed action/amount; a frozen policy handles every other action. A mismatch with the fixed action or an invalid tool call receives failure score 0. Use the starter reward for valid continuations and matched silence controls for measuring incremental value.
7. Train the single deployable checkpoint on successful action-and-message targets paired with their original official observations, removing any helper that supplied the fixed action. Mix these targets equally with clean betting/defense replay initially, then run a 10-step integration experiment with ordinary full-hand GRPO. Evaluate at steps 0 and 10. Empty pre-flop talk, incoming-talk robustness, and legal behavior remain evaluation gates; replay the offline defense set between RL phases if regression appears.

The experiment runner must fork complete prefixes rather than replace talk after a decision has already affected the game. Keep all matched branches in the same data split. Opponent continuations can diverge after the intervention; do not force their later action sequence to remain identical.

## 4. Evaluate and promote

Record these comparisons on selection data before opening the final holdout:

| Question | Comparison and measurement |
| --- | --- |
| Did principles help? | Base versus principles-only: paired returns, placement, legal-action failures |
| Did Pete help? | Principles-only versus combined: poker outcomes plus action/sizing agreement on held-out teacher records |
| Did specialized RL help? | Each stage versus its parent, including untouched-street regression checks |
| Does incoming talk matter? | Identical states with silence and perturbed talk: action/sizing agreement, illegal actions, and clean poker quality |
| Did outgoing talk help? | Same betting policy and nominated action with silence, ordinary chatter, and attack messages: paired returns and placement |
| Does learning persist across hands? | Official multi-hand games: delayed decision changes, factual scratchpad retention, and chatter-derived instructions |

Promotion rules:

- Require zero invalid decisions in the local tool-use smoke test. Report failures in larger runs and reject a candidate that worsens the parent policy's failure rate.
- In deterministic paired defense tests, target at least 99% agreement on action and applicable amount across all perturbations, reported separately by street and message family. For stochastic endpoints, compare repeated clean/perturbed calls against repeated-clean noise with confidence intervals; do not interpret one sampled disagreement as an attack success.
- Reject defense training that buys consistency by making clean poker materially worse. A constant-folding policy is not a successful defense.
- Select final candidates by mean placement on full-game selection data. Define improvement as `parent mean placement - candidate mean placement`, so positive is better. Use a paired bootstrap over complete games for a 95% confidence interval; never resample individual decisions as independent observations.
- Freeze the selected candidate, run the held-out full-game set once, and report the interval. Claim an improvement only if its lower bound exceeds zero. An interval spanning zero is inconclusive; retain the parent unless new independent evaluation supports promotion. New tuning requires a fresh final holdout.
- Enable outgoing talk in the selected bot only if it beats the same betting policy with silence and retains defense performance. Treat increased folds/calls or opponent tool errors as supporting diagnostics rather than proof of benefit.

Report mean rank, first-place and bust frequencies, realized and EV-adjusted chip returns, action/sizing stability, talk frequency by street, tool failures, truncation, and scratchpad failures. Keep raw and clipped reward separate. Current `vals_tools.score` is useful for single-hand chips; extend analysis for these full-game metrics and paired talk variants.

## 5. Commands and resource defaults

These existing commands only inspect the starter configuration; they do not implement the proposed stages or submit jobs:

```bash
uv run python rl/make_dataset.py --dry-run
uv run python rl/train.py --dry-run
uv run python opsd/train.py --dataset pokerbots-preflop-principles-train --dry-run
```

Use the executable commands below. Training-only routing remains opt-in; ordinary event tasks keep the official engine, tool format, sanitizer, and observations. Route and opponent metadata are added to local logs for evaluation pairing.

For Qwen, the starter estimates about 8 GPUs for RL with sidecar evaluation, 4 for offline OPSD, and 1 per inference deployment against the documented 10-GPU team quota. Schedule one training phase at a time and account for the frozen-policy deployment needed by street-specific RL. Confirm supervised-training resources before launching that new path. Begin with rollout concurrency 16 and increase only after observing harness capacity and opponent rate limits.

Validation covers focused tests for split isolation, decision-time information filtering, street selection, checkpoint continuation, legal teacher targets, frozen-policy routing, talk-only interventions, and reward failure handling. Run official harness tests and an end-to-end local game before deployment. Tests include a complete simulated matched-message experiment and canonical policy export, plus the existing official harness suite.

Each experiment records: strategy revision, source and opponent versions, dataset IDs, parent checkpoint ID, stage, exact run configuration, compute use, selection metrics, and promotion decision. Keep the best parent checkpoint available for comparison and rollback.


## Executable workflow

Run from the repository root after `uv sync`. The root development environment now includes the local harness.

```bash
# Resume the frozen archive or rebuild all local teacher records.
uv run python -m vals_tools.arena collect
uv run python -m vals_tools.pete

# Inspect SFT configuration; --upload uploads only train records, without starting training.
uv run python -m vals_tools.sft --records data/arena/pete-preflop/train.jsonl --dataset pokerbots-pete-v1-train

# Collect fresh selected-parent train traces without requiring a harness connector.
uv run python -m vals_tools.collect_policy --model vals-hackathon/step2 --hands 16 --concurrency 4 --out data/experiments/principles-step2
uv run python opsd/build_dataset.py --eval local-principles --traces data/experiments/principles-step2/traces.jsonl --expected-model vals-hackathon/step2 --street preflop --dataset pokerbots-principles-v1-train --dry-run
# Remove --dry-run on the preceding command to upload teacher-hinted data.
uv run python opsd/train.py --dataset pokerbots-principles-v1-train --checkpoint ckpt_012f74ea70f9 --dry-run
```

After evaluating and deploying the principles checkpoint, collect that policy's clean train hands with `collect_policy --model <deployment> --out <directory>`. Export only its pre-flop records for the 50:50 replay mix:

```bash
uv run python -m vals_tools.export_policy --logs <directory>/logs --model <deployment> --street preflop --out data/experiments/principles-replay
uv run python -m vals_tools.sft --records data/arena/pete-preflop/train.jsonl --replay data/experiments/principles-replay/train.jsonl --checkpoint <principles-checkpoint> --dataset pokerbots-pete-mixed-v1-train --launch
```

`export_policy` preserves a recorded source split, or falls back to deterministic train/select/eval splits from the game seed; it also exports verified factual cleanup targets when `--street all` is used. Pete's public records omit private memory, so the imitation observations are explicitly marked as reconstructed. They are not represented as exact copies of Pete's private conversation.

Prepare stage datasets and launch configs after selecting the parent. Substitute actual checkpoint and deployment identifiers; commands without `--upload` or `--launch` stay local/dry-run as documented by each tool.

```bash
uv run python -m vals_tools.curriculum --stage preflop --frozen-model <deployment> --prefix pokerbots-preflop
uv run python rl/train.py --prefix pokerbots-preflop --checkpoint <parent-checkpoint> --concurrency 16 --dry-run
# Repeat curriculum with --stage postflop after selecting the pre-flop checkpoint.
# Use --stage talk for one fixed-action message decision per hand.
# Use --stage integration --enable-talk for the final full-policy experiment.
```

A running harness and connector are required for GRPO. Start the harness with `uv run uvicorn poker_harness.server:app --host 127.0.0.1 --port 8765`. `uv run python -m vals_tools.connect` attempts temporary project-bound credentials without printing secrets or changing login configuration, and revokes its credential on exit. On this server the bound-credential request fails. The user authorized `--credential-scope organization`, which explicitly creates a temporary broader credential and revokes it on normal exit. First fix or gracefully replace the existing connected upstream; do not run competing connectors.

Build defense from **clean targets from the selected betting checkpoint**, not arbitrary opponents' post-flop moves:

```bash
uv run python -m vals_tools.export_policy --logs <clean-policy-logs> --model <deployment> --out data/experiments/clean-policy
uv run python -m vals_tools.defense --records data/experiments/clean-policy/train.jsonl --out data/experiments/defense/train.jsonl
uv run python -m vals_tools.sft --stage defense --records data/experiments/defense/train.jsonl --checkpoint <betting-checkpoint> --dataset pokerbots-defense-v1-train --launch
```

Generate defense selection/evaluation variants from their respective clean splits using the same command; message wording is disjoint by split. `vals_tools.defense_eval --records <matched-records> --model <deployment> --out <result.json>` records repeated clean and perturbed outcomes, action/sizing disagreement above repeated-clean noise, and cleanup results. These small repeated trials are diagnostics; use enough independent game states for conclusions.

`vals_tools.talk_experiment --model <deployment> --seed <seed> --seat <seat>` compares silence, ordinary chatter, and attack candidates. Every branch replays the same exact conversation prefix, keeps the nominated betting action fixed, and allows future actions to diverge. The current experiment unit is one complete hand from an empty scratchpad; it does not establish delayed effects across a 30-hand game. Use full official games and defense cleanup evaluations for that gate.

`vals_tools.integrate --experiments <result1.json> <result2.json> --out <directory>` selects messages only from selection-seed results using game-level confidence intervals, then exports action/message targets with the helper removed. An inconclusive experiment exports no accepted message targets. Integration SFT uses only the resulting train records with clean replay; final evaluation records never select messages.

`vals_tools.game_score --logs <candidate-log-directory> --parent <parent-log-directory>` reports whole-game placement, wins, busts, chips, invalid decisions, and a paired bootstrap interval. Logs must cover the same seeds, policy seats, and opponent configurations. Supply `--seat` for older logs that do not identify their policy seat. Keep distinct runs in separate directories.

The completed base comparison pilot remains under `data/experiments/principles-base/`. It must not be substituted for step2 on-policy traces. `collect_policy --split select` and `--split eval` use separate seed streams; add `--hands-per-game 30` for official-game comparisons. Keep those outputs in separate directories.


## Historical step2 pilot execution

- Frozen archive: 130 matches collected; all 130 replay-valid; 1,598 Pete pre-flop targets.
- Teacher splits: 1,328 train, 174 selection, 96 evaluation. Only train was uploaded to `pokerbots-pete-v1-train`.
- Parent used for this historical pilot: `ckpt_012f74ea70f9`, verified against the ready `vals-hackathon/step2` deployment. The active Pete run starts from base instead.
- Fresh step2 traces: `data/experiments/principles-step2/`; base comparison traces remain in a separate directory.
- Pilot input: an immutable snapshot of 15 completed step2 hands (`traces-pilot.jsonl`), yielding 16 valid pre-flop targets; zero target format errors or truncations. The remaining collection finishes separately. The pilot uses two steps, batch eight, explicit learning rate `1e-6`, and the verified parent checkpoint. This is a validation run, not the full curriculum.
- Receipt: `data/experiments/principles-step2/principles-run.json` records whether the coordinator is waiting, prepared, or submitted and includes the train ID after submission. A receipt containing a train ID prevents accidental duplicate submission.
- No Pete checkpoint, RL checkpoint, defense checkpoint, or final bot has been promoted from this curriculum yet. The completed pilot and its comparison are documented in [MODEL_PILOT_REVIEW.md](MODEL_PILOT_REVIEW.md); it is not a prerequisite for the active base/Pete run.

The historical coordinator command was:

```bash
uv run python -m vals_tools.principles --checkpoint ckpt_012f74ea70f9 --deployment vals-hackathon/step2 --traces data/experiments/principles-step2/traces-pilot.jsonl --lr 1e-6 --launch
```

The earlier automatic approval rejection was specifically for creating organization-scoped connector credentials. The user has since explicitly authorized that scope, and the connector tool now offers it as an opt-in flag. No new connector or credential was needed to submit the offline pilot. The connected upstream still needs its opponent credentials corrected before future GRPO.

The audit-adjusted pilot was submitted as `train_b56333a6f8fb`. See [TRAINING_RUN_AUDIT.md](TRAINING_RUN_AUDIT.md) for the failure findings, exact adjustments, and limitations.

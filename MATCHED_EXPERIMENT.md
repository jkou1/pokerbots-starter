# Matched public-data experiment

Compare the original `Qwen/Qwen3.6-35B-A3B` with continuation from
`ckpt_51eee61470f7` (combined SFT v3). Both receive one frozen curriculum and
identical **additional** training: 64 updates, batch 64, learning rate `5e-6`,
seed 42, context 8,192, checkpoints at updates 32 and 64. The checkpoint's
historical training is reported separately. Use update 64 for the primary
equal-budget comparison; update 32 is a diagnostic, not an automatic replacement.

The four conditions are B0 (unchanged base), C0 (unchanged combined v3), B1
(base plus curriculum), and C1 (combined v3 plus curriculum). The primary
outcome is placement under the official 30-hand event rules. Teacher agreement,
chip returns, legality, and cleanup reliability are diagnostics.

## Prepared pilot, November 15, 2026

The frozen release contains 367 completed Arena matches, with no download
failures or replay quarantines. It supplies 4,786 qualified Pete decisions
across all streets and 3,132 public factual cleanup records before splitting.
The exact PokerBench pilot supplies 7,174 unique training observations after
replay checks, deduplication and held-out exclusion.

The prepared corpus is `data/experiments/matched-public-v1/train.jsonl`:
2,048 sampled PokerBench actions, 1,843 sampled Pete actions and 205 cleanup
targets. There are 2,711 distinct source records; resampling supplies the other
examples. Cleanup contributes 9.23% of the 168,238 estimated target tokens;
808 observations contain training-only chatter perturbations. The maximum
context preflight is 2,227 tokens. The actual trainer audit remains required.

Both 64-update runs have been submitted using dataset
`pokerbots-matched-public-v1-train`:

- Base: `train_2888f6862cb2`.
- Combined-v3 continuation: `train_0b9fbdebc2de`.

The receipt files record identical training settings and source hash
`6b4e161802f2aca8ec2d8d5d8450bfc19d251506fe6d5b1ee3e8ec9ddd2de87a`.
Training completion, protocol audits, endpoint comparisons and full-game
results are pending. These submissions establish no performance improvement.

## Prepare public data

Use a **new** archive directory so the old cutoff and holdouts remain intact.
The default extractor still exports only Pete preflop. All-street extraction
requires a separate output directory; teacher IDs are an explicit allowlist.

```bash
uv sync --dev
uv run python -m vals_tools.arena collect --root data/arena-matched-v1
uv run python -m vals_tools.pete --root data/arena-matched-v1 \
  --streets preflop flop turn river --cleanup \
  --out data/experiments/arena-matched-v1
uv run python -m vals_tools.pokerbench download
uv run python -m vals_tools.pokerbench build --max-rows 10000 \
  --out data/experiments/pokerbench-matched-v1
uv run python -m vals_tools.matched tokenizer \
  --out data/experiments/matched-tokenizer
```

PokerBench is pinned to Hugging Face commit
`7ac61f961c81a50fc0f667820b2fb0e432dfec0d`; its source is
[RZ412/PokerBench](https://huggingface.co/datasets/RZ412/PokerBench).
The tokenizer is pinned to model commit
`345d467b117d1fd5eda9b879a5988de9ae5f47a7`.
Download receipts include file hashes. `--max-rows` caps training-source rows
**per CSV**; all supplied test rows are inspected. This is a pilot subset.

The CSV and JSON files have different row orders. The converter uses CSVs
directly, reconstructs omitted preflop folds, and checks the actor, current
street, pot, and legal action against the official engine. It multiplies BB
amounts by two and **rejects** fractions of a chip rather than rounding.
Inconsistent pots and unsupported lines are quarantined in `quality.json`.
Future board cards and opponents' private cards never enter observations.

Deduplication groups suit-isomorphic decision states. Source test duplicates
are removed from training/selection; the remaining training source is divided
deterministically into train and selection. The dataset does not provide
complete original solver-tree identities, so this is decision-state separation,
not a guarantee that every underlying solve is independent. PokerBench may also
have appeared in base-model pretraining. Fresh game evaluation remains decisive.

Pete records are demonstrations, not optimality certificates. Public replays
lack Pete's private memory. Cleanup targets contain only current public stack
facts; their inputs expose only the acting player's cards and cards explicitly
shown at showdown. Engine chip-pushing operations reconstruct pot awards,
including uncalled-bet refunds correctly.

## Freeze and train the shared curriculum

```bash
uv run python -m vals_tools.matched prepare \
  --pokerbench data/experiments/pokerbench-matched-v1/train.jsonl \
  --arena data/experiments/arena-matched-v1/train.jsonl \
  --tokenizer data/experiments/matched-tokenizer/tokenizer.json \
  --history data/experiments/combined-base-sft-fixed/dataset/train.jsonl \
  --holdout data/arena/pete-preflop/select.jsonl data/arena/pete-preflop/eval.jsonl \
  --out data/experiments/matched-public-v1
uv run python -m vals_tools.matched train \
  --experiment data/experiments/matched-public-v1 --arm base
uv run python -m vals_tools.matched train \
  --experiment data/experiments/matched-public-v1 --arm continuation
```

Training commands print the configurations. Add `--launch` to each to upload
the shared dataset and start the corresponding run. Schedule within the
10-GPU quota; each SFT job needs four GPUs. Preserve active deployments and
unrelated jobs. Existing run receipts refuse duplicate launches.

The 4,096 sampled records initially target 50% PokerBench, 45% Pete actions,
and 5% factual cleanup. Sampling rotates through street/position/action strata,
cycles source records when necessary, and reports distinct source coverage.
Repeated samples receive identifiers outside model prompts so service
deduplication cannot silently change their intended weights. About one fifth
of eligible records receive split-specific incoming chatter with unchanged
targets, including cleanup records. Outgoing speech is silent in this stage.

Cleanup is capped at 10% of target tokens using the pinned tokenizer and the
Qwen XML target format. Excess cleanup samples are replaced with Arena actions;
actual proportions are recorded. A conservative context preflight rejects
oversized examples. `experiment.json` freezes source hashes, history, tokenizer,
record order, unique coverage, token counts, and both training configurations.
Any additional historical training files belong in `--history`; all old and
new held-out deals must remain outside training. Source sibling `select.jsonl`
and `eval.jsonl` files are checked automatically.

After an optimizer update, inspect actual managed-trainer serialization:

```bash
uv run python -m vals_tools.sft_audit --train TRAIN_ID --out data/experiments/matched-public-v1/ARM-audit.json
```

Require a supervised reasoning close before a genuine tool call. Do not weaken
the official parser. Compare actual trainer token counts with the prepared
budget. The recorded single-newline thinking prefill and protocol marker are
retained. Deployment uses the existing `vals_tools.deploy` command and a real
tool probe; deployment and Arena registration remain separate operations.

## Evaluate official games

Freeze the two available opponent configurations and make disjoint game plans:

```bash
uv run python -m vals_tools.game_study prepare \
  --out data/experiments/matched-public-v1/games
uv run python -m vals_tools.game_study run \
  --plan data/experiments/matched-public-v1/games/select.json \
  --model vals-hackathon/combined-sft-v3 \
  --out data/experiments/matched-public-v1/select-C0
```

Repeat the run command for B0, B1 and C1 under their actual deployment names.
Selection has 24 games per condition; final evaluation has 120 fresh games per
condition. Every seed rotates through all six seats against both opponents.
Use the `eval.json` plan only after fixing the candidates and recipe.
Inference temperature is fixed at 1.0 with official thinking and token caps.
Pairing controls deals and configuration; stochastic continuations still differ.

The runner verifies deployment ID, version, and checkpoint before and after
play. Resuming with changed weights or a changed plan is rejected. Successful
completion writes `validated.json` with log hashes; comparisons require it and
refuse missing games or modified logs. External provider deployment metadata
cannot prove that upstream weights were immutable.

```bash
uv run python -m vals_tools.game_study compare \
  --plan data/experiments/matched-public-v1/games/eval.json \
  --b0 data/experiments/matched-public-v1/eval-B0 \
  --c0 data/experiments/matched-public-v1/eval-C0 \
  --b1 data/experiments/matched-public-v1/eval-B1 \
  --c1 data/experiments/matched-public-v1/eval-C1 \
  --out data/experiments/matched-public-v1/comparison.json
```

The report measures placement, first-place and bust rates, chips, action errors,
cleanup failures, and opponent errors. Placement intervals resample whole seed
groups, keeping all seats and opponents together. Positive improvement means a
lower placement number. Promotion eligibility requires a final-evaluation
interval above zero versus C0, zero invalid decisions, and zero failed cleanup
updates. A small or inconclusive result is not a win. Confirm Arena registration
and then follow live results separately; the report does not submit an entry.

Use `vals_tools.pete_eval` on held-out action files for sizing, call recall,
per-position and per-street agreement. It filters cleanup records from mixed
files. Use `vals_tools.defense` and `vals_tools.defense_eval` for repeated-clean
versus chatter checks. The evaluation chatter set includes two families absent
from training: role confusion and memory poisoning.

## Outgoing talk and the subsequent RL experiment

`vals_tools.talk_experiment` uses a frozen reference policy, identical recorded
prefixes and a fixed betting action, then repeats each message continuation.
Its catalog includes silence, ordinary chatter, bluff claims, directives and
claimed authority. It rejects messages changed by Arena's 70-character
whitelist. JSON punctuation that cannot survive the channel is not a candidate.

```bash
uv run python -m vals_tools.talk_experiment \
  --model vals-hackathon/combined-sft-v3 --opponent vals-hackathon/ac-vals-model \
  --seed TRAIN_SEED --split train --repeats 3 --out data/experiments/talk/train-SEED.json
uv run python -m vals_tools.integrate \
  --experiments data/experiments/talk/*.json --out data/experiments/talk/shared-targets
```

Collect separate train, select and eval seeds; each needs repetitions and both
frozen opponent configurations. Message selection requires at least six
selection seeds per opponent, positive seed-cluster intervals over both silence
and ordinary chatter, and positive mean benefit against each opponent.
The selection result is preliminary, not a multiple-testing-adjusted claim.
Only independent **training** games produce supervised targets; selection and
final outcomes never become action labels. Mixed reference policies, duplicate
repetitions and incomplete controls are refused. If evidence is insufficient,
the exporter writes no talk targets: retain silence.

If talk targets qualify, train both betting endpoints on the exact same exported
file with equal budgets using `vals_tools.sft --stage talk`. Preserve clean
betting and cleanup examples through `--replay`; the same replay file is used
for both. Evaluate speech-enabled checkpoints against their silent parents
with fresh 30-hand plans and recheck chatter defense before considering promotion.

RL is a separate experiment after the supervised result. `vals_tools.curriculum`
accepts multiple `--opponent-model` values and rotates full seat blocks across
them. `--objective placement` creates 30-hand training tasks with an opt-in
grader reward: first place 11, last place 1, model failures 0. It rejects
single-hand placement episodes. The official default chip reward is unchanged.
Use the same frozen opponent versions, task seeds and explicit `rl/train.py
--seed` in both branches. Rollout outcomes necessarily differ between policies.
First measure complete-game rollout length and nonzero reward variance with a
small rollout budget; the starter's single-hand token budget is insufficient
for assuming 30-hand training will fit. Do not mix RL gains into the SFT claim.

Weight-space programming and a local solver service are intentionally deferred.
The initial transfer mechanism is supervised learning from validated decisions,
not direct edits to deployed weights.

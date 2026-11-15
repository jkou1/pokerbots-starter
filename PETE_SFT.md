# Supervised poker imitation from base

The first experiment trained `Qwen/Qwen3.6-35B-A3B` directly on Professor Pete's pre-flop decisions, starting from base weights with no step2 or distillation checkpoint. Its official held-out evaluation failed: **0 of 174 valid action calls**, because tool-call text appeared inside reasoning. Do not enter `vals-hackathon/pete-sft-v1` in the Arena. The corrected combined-data experiment is described in [DATA_STRATEGY.md](DATA_STRATEGY.md).

## What supervised fine-tuning teaches

Each example pairs an observation with an action:

```text
Input:  our hole cards, position, live players, stacks, pot, prior betting,
        and legal actions at the moment the teacher acted
Target: submit_action(action="raise", amount=5)
```

The loss increases the probability of the teacher's action tokens given that observation. The model learns which hands to fold, check, call, or raise, and the teacher's sizing. This is direct behavioral imitation; a successful imitation is not automatically a stronger poker player.

Use stronger bots as provisional teachers. Verify their performance over enough comparable games, retain source/version identity, and measure whether their imitation improves our results. Preserve folds and losing hands as well as wins. Winning hands alone select for card luck and discard much of the useful fold policy. When adding other teachers, compare their strengths by position and situation and inspect disagreements before combining their data. Start with Pete alone so the source of any change is identifiable.

Only information available at the decision enters the input. Other players' hole cards, future boards, later actions, and results are excluded. Each example has one supervised action call, without invented teacher reasoning or outgoing pre-flop table talk. Public records do not reveal Pete's private memory; the reconstructed observations cannot reproduce that missing context.

## Frozen data

The 130-match archive produced 1,598 validated Pete pre-flop decisions. Whole matches are assigned to one split before extracting decisions; duplicates and derived examples stay with their source match.

| Split | Decisions | Pete matches | Use |
| --- | ---: | ---: | --- |
| Train | 1,328 | 48 | Weight updates |
| Selection | 174 | 7 | Checkpoint comparison and tuning |
| Evaluation | 96 | 3 | Final teacher-imitation check after selection |

The training targets contain 831 folds, 318 raises, 136 calls, and 43 checks. Keep their observed frequencies for the first run and report each class separately. Artificially making every action equally common would change the teacher's action distribution.

The default passive policy, check when free and fold otherwise, matches 129 of 174 selection actions (74.14%). Overall accuracy alone is therefore a poor success criterion. The final evaluation set contains only three matches; decisions within a match are correlated, and a larger independent poker-game evaluation is still needed.

## First run and failure finding

- Run: `train_3061a33ce578`.
- Training completed successfully: 40 optimizer updates, final checkpoint `ckpt_0212d63c5944` (zero-based iteration 39). Last training-batch loss was 0.01143; external selection evaluation is separate.
- Dataset: `pokerbots-pete-base-sft-v1-train`, verified to contain exactly the 1,328 expected task contents.
- Initialization: base `Qwen/Qwen3.6-35B-A3B`, with no parent checkpoint and no replay mixture.
- Objective: supervised action-token loss; no live opponents or connector during training.
- Requested budget: 40 optimizer updates, batch 64, learning rate `5e-6`, seed 42, 8,192-token context limit, checkpoints every 20 updates.
- That sample budget is roughly two passes over the data if the backend consumes 64 examples per update; inspect actual trainer progress rather than infer completion from the submitted configuration alone.
- In-run evaluation is off because the managed SFT path does not provide this poker evaluation. External selection evaluation is separate.

Startup verification at 2026-11-15 05:55 UTC confirmed the base model path, all 1,328 loaded samples, and completed optimizer steps 0 and 1 (64 sequences each). Their losses were 0.42758 and 0.45650 on different batches; this is not a validation-loss trend. The first four prepared batches had no truncated targets. No checkpoint was available at that check. TensorBoard and structured step metrics are recording; local snapshots are saved beside the receipt as `metrics.json`, `latest-logs.json`, and `checkpoints.json`.

The shared telemetry also reports zero reward standard deviation for the supplied targets. This run uses SFT, so that reward-group statistic does not determine its learning signal. Supervised loss, completed updates, and external evaluation are the relevant checks.

The source prompts contain 2,877–3,154 characters before tool-template rendering. The context budget leaves room for the official tool schema and short target calls. No teacher reasoning trace was available. The corrected format adds a short synthetic protocol marker, `Tool call follows.`, before the action; this is a serialization scaffold, not Pete's reasoning.

The failure was reproduced with raw completions: the saved training prefix ends at `<think>`, while inference adds a newline. With the exact saved prefix, the first model emits `\n\n</think>` then its tool call. Appending just one newline makes it emit the tool call without closing reasoning. The training target's first token is a merged double newline, which is absent from that inference prefix. A low SFT loss therefore concealed a deployment-format failure. The corrected nonempty protocol marker makes the first target token a single newline; verify the actual rendered target and the official thinking-on tool interface before accepting a new checkpoint.

Exact configuration, source hashes, upload verification, and the run ID are saved under `data/experiments/pete-base-sft/run.json`.

```bash
uv run python -m vals_tools.sft \
  --records data/arena/pete-preflop/train.jsonl \
  --dataset pokerbots-pete-base-sft-v1-train \
  --from-base --steps 40 --batch 64 --checkpoint-every 20 \
  --lr 5e-6 --max-total-len 8192 \
  --receipt data/experiments/pete-base-sft/run.json --launch
```

The receipt prevents accidental duplicate submission of this experiment. The launcher verifies remote task hashes before training. `--from-base` and `--checkpoint` are mutually exclusive. Training refuses selection/evaluation records. SFT-specific configuration omits rollout-only template settings that this SDK does not accept for SFT.

## How to judge the result

Run the same selection observations through base and each candidate checkpoint under the same tool schema and decoding settings. `vals_tools.pete_eval` reports action accuracy, per-action recall, per-position accuracy, exact sizing agreement, legal-action rate, and raise-size error. Failed or illegal predictions remain in the denominator. The macro-average action recall exposes a policy that achieves high overall accuracy by mostly folding.

```bash
uv run python -m vals_tools.pete_eval \
  --model vals-hackathon/base \
  --out data/experiments/pete-base-sft/base-selection.json

# After serving a candidate checkpoint, repeat against the same default selection file:
uv run python -m vals_tools.pete_eval \
  --model <candidate-deployment> \
  --out data/experiments/pete-base-sft/candidate-selection.json
```

Selection checks teacher agreement, not optimality. Then compare base and the selected candidate in paired official games with identical deal seeds, seat rotations, and opponents. Track placement and chips, legal tool use, and post-flop regressions: pre-flop supervision updates shared weights and can affect other streets. Use untouched evaluation data only after choosing the candidate.

## Continuing the broader strategy

Keep a better validated Pete checkpoint as the starting point for subsequent betting RL, incoming-talk defense, and outgoing-talk experiments. Those stages keep their separate measurements and the arena's tool contract. If this SFT run does not improve poker results, retain base and diagnose coverage, teacher quality, observation reconstruction, and overfitting before increasing training volume.

When a later stage needs replay, the launcher keeps a 50:50 teacher/replay sample mix. Repeated replay samples carry distinct sampling metadata outside the prompt because the dataset service deduplicates identical task contents; otherwise a nominal balanced mix could silently collapse to mostly teacher examples.

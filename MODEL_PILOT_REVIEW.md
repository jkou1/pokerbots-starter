# Pilot deployment and loss review

Run: `train_b56333a6f8fb`; final saved checkpoint: `ckpt_8cc618602ffc` (registered iteration 1 after two zero-based optimizer steps). Parent configured for the run: `ckpt_012f74ea70f9`.

## Arena deployment

AC2 reports the pilot run as succeeded and its model as deployable. The registered model is the arena-compatible `Qwen/Qwen3.6-35B-A3B`.

At inspection, serving conversion for the new checkpoint was `missing`, and no inference deployment referenced it. The only ready poker deployments were `base` and `step2`. `step2` still referenced the parent `ckpt_012f74ea70f9`. Training a new checkpoint does not automatically replace a deployment or enter it in the arena.

The required path is checkpoint conversion, a running inference deployment, a successful action-tool probe, then selecting that deployment in Vals Arena. Serving conversion has now completed. A separate deployment named `principles-pilot` (`infer_e35bca350dc8`) is now ready and passed a live `submit_action({"action":"fold"})` probe. It serves `ckpt_8cc618602ffc` under the canonical Qwen model identity. Refresh Vals Arena and select `principles-pilot` to use this deployment. No arena submission was performed as part of this diagnosis. The deployment reserves one GPU while it exists.

The dashboard URL was sent to the system browser opener. No connected browser-control session was available, so account status and checkpoint/deployment metadata were inspected through the AC2 SDK rather than by reading the authenticated Chrome page.

## What the loss means

| Metric | Batch 0 | Batch 1 |
| --- | --- | --- |
| Distillation loss / logged KL | 0.0253327 | 0.0264604 |
| Student cross-entropy on recorded replies | 0.688103 | 0.513754 |
| Teacher cross-entropy on recorded replies | 0.703135 | 0.536444 |
| Gradient norm | 2.56983 | 2.95649 |
| Learning rate | 0.000001 | 0.000001 |

The distillation loss increased about 4.45%. These two points used different batches of eight recorded decisions. There is no fixed held-out distillation measurement or repeated pass over the same batch, so this is not a controlled before/after loss comparison. It does not establish that the model diverged or became worse at poker. The cross-entropy decrease is also across different batches and must not be presented as proof of improvement.

This offline OPSD loss measures token-distribution agreement with the frozen parent acting as a teacher under the strategy hint. It is not poker winnings, action EV, or arena rating. Nonzero gradient norms show that this pilot had a training signal, unlike the earlier GRPO smoke run whose sampled groups had no reward variation. Reward-zero fields in this OPSD run are not evidence of failed GRPO: offline OPSD does not optimize the chip grader.

A persistent loss rise on a fixed validation set would warrant investigating data quality, teacher targets, and optimization settings. Two training minibatches do not support choosing a larger or smaller learning rate by themselves.

## Why a large capability change is not established

- This was a technical pilot: two updates at learning rate `1e-6`, using 16 pre-flop replies from 15 hands.
- The stored reply content contained 31,539 reasoning characters and 2,345 prose characters, alongside just 317 characters of action-tool arguments across 16 calls. These are character counts, not token-loss weights, but they establish that the experiment supervised whole replies rather than isolating betting actions.
- The samples covered only pre-flop. They did not train the planned post-flop betting, table-talk policy, or cleanup defense.
- The 1,328 Pete training examples were uploaded separately but were not used by this run. Its source was the parent's own replies with a generic strategy hint supplied to the teacher.
- Offline distillation adjusts probabilities on recorded replies; it is a limited source of new poker behavior, especially when the parent already broadly follows the hint.
- In-run evaluation was off, so no held-out poker result establishes a gain or regression.
- Requests sent to `vals-hackathon/step2` still test the parent. The new checkpoint must be served under its own deployment before making an endpoint comparison.

## Direct comparison and next experiment

A small diagnostic under `data/experiments/deployment-audit/` selects 12 pre-flop cases from the existing selection split, including different positions and target actions. It uses identical prompts, temperature zero, and the same 5,000-token limit for parent and pilot. It reports action-type and action-plus-amount agreement and invalid calls. This is a stratified behavior check, not an estimate of win rate or teacher optimality; small differences can also reflect inference nondeterminism.

Before a larger run, create a fixed selection set with repeated teacher/student loss measurements and evaluate actual betting outcomes against the parent. The next substantive learning stage is the planned Pete supervision with clean policy replay and coverage of positions, hand classes, and raise/re-raise situations. Keep the final evaluation split unused for training or checkpoint selection. Longer training on these same 16 pilot examples is not by itself evidence of better poker.

## Observed parent/pilot behavior

The completed 12-case diagnostic observed matching action types and amounts in seven cases and different action types in five. Both models produced legal action-tool calls in all 12 cases. This establishes observed disagreement on these cases; it does not establish an improvement in expected chips or ranking, and repeated runs would be needed to separate stable policy changes from inference nondeterminism.

| Case | Hole cards | Position index | Parent step2 | Pilot |
| --- | --- | --- | --- | --- |
| 1 | Qh Qd | 0 | raise to 8 | raise to 8 |
| 2 | Th 8d | 1 | fold | call |
| 3 | Ad Th | 2 | call | call |
| 4 | 7h 8c | 3 | call | call |
| 5 | Jc 8h | 4 | fold | call |
| 6 | 8s 5s | 5 | fold | call |
| 7 | 7c 9d | 1 | check | check |
| 8 | 2h Tc | 1 | fold | fold |
| 9 | 6d Qc | 4 | call | fold |
| 10 | Qc Th | 2 | raise to 6 | call |
| 11 | 9d 2c | 0 | fold | fold |
| 12 | 7c Jh | 0 | fold | fold |

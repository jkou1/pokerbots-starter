# GRPO audit and step2 continuation

Audited November 14, 2026 (Pacific time). Raw metric snapshots and the inspected log window are stored under the ignored `data/experiments/run-audit/` directory.

## Stopped run: `train_80ea057be687`

The user stopped this run; AC2 now reports `stopped` and `completed: true`. No checkpoints were produced. At the inspected metric snapshot, zero groups and zero rollouts had been consumed by training. The run had generated four groups (32 rollouts), below the 16 groups needed for its first step, while sampling failures accumulated.

All 179 rollout-failure messages in the inspected 400-line recent log window reported the same harness error:

```text
opponent seats need POKER_OPPONENT_API_KEY or AC2_API_KEY in the harness environment
```

These are environment failures, not evidence that the model plays poorly. No optimizer updates means this run supplies no learning-curve evidence for changing learning rate, KL strength, or poker style. The registered run's model is Qwen and its parent-run field is empty; it should not be described as a verified continuation of step2.

The project has a connected harness, but a connected status does not establish usable opponent authentication. The local harness on port 8765 passes a zero-hand credential preflight; no local connector process was found. This points to a different connected upstream as the failing environment, rather than establishing a fault in the validated local server. The exact remote upstream was not exposed by the status API. Do not run competing connectors against one project.

## Parent checkpoint: `ckpt_012f74ea70f9`

The ready `vals-hackathon/step2` deployment reports this checkpoint, iteration 2 of `train_9934ba584c16`. That earlier run completed two training steps and consumed eight rollouts in total.

| Logged quantity | Step 1 | Step 2 |
| --- | --- | --- |
| Learning rate | 0.000001 | 0.000001 |
| Fraction of groups with zero reward standard deviation | 100% | 100% |
| Effective reward batch fraction | 0% | 0% |
| Mean raw reward | 7.5 | 7.5 |
| Policy-gradient loss | 0 | 0 |
| Policy format errors | 0 | 0 |
| Truncation ratio | 0 | 0 |
| Mean generation time, seconds | 14.9 | 2.7 |
| Mean non-generation time, seconds | 472.5 | 425.8 |

Identical rewards within each sampled group supplied no comparative GRPO reward signal in those two steps. This does not prove the checkpoint is identical to base: KL/optimizer effects can still change weights. It does mean there is no evidence here of reward-driven poker improvement. Keep the user-selected checkpoint as the parent and judge improvement with separate evaluations.

Non-generation time includes environment, opponent, cleanup, and other waiting work. The large gap relative to generation time makes increasing training GPUs or output-token budgets an unsupported response to this slowdown.

## Changes applied to the next run

- Continue the verified checkpoint `ckpt_012f74ea70f9`; collect fresh traces from its matching `step2` deployment.
- Use offline pre-flop OPSD for the next pilot. It learns from a strategy-hinted teacher distribution and does not need live opponent calls during weight updates, avoiding the failed run's harness credential dependency and zero-variance chip-reward problem.
- Set learning rate explicitly to `1e-6`, matching the earlier completed run, rather than relying on a method-specific server default.
- Keep the first pilot to two steps, batch eight, with a checkpoint at step two and evaluation off during training. This checks checkpoint loading and the data/trainer path; it is not sufficient to claim improved poker strength.
- Preserve the 5,000-token event decision limit. There is no measured truncation problem in the earlier run or the completed base comparison pilot.
- Keep the 1,328 Pete training examples and the 174/96 selection/evaluation examples separated. After validating principles distillation, blend Pete supervision with clean principles-policy replay, then evaluate before promotion.

## Before returning to GRPO

Fix opponent credentials in the actual connected upstream, or gracefully replace its connector with the validated local harness. The user authorized temporary organization-scoped connector credentials; `vals_tools.connect --credential-scope organization` supports that explicitly and revokes credentials on normal exit. No new connector is needed for the offline pilot, and none should compete with the existing connection.

Run a small eval through the project connector and require valid graded hands before allocating a GRPO training job. Start the next GRPO probe with four hands per step, eight attempts per hand, concurrency four, learning rate `1e-6`, and KL coefficient `0.01`; retain the existing single-hand token budgets. Increase throughput only after successful complete groups are being consumed.

Log group reward standard deviation, zero-variance fraction, effective batch fraction, consumed groups, errors by cause, truncation, and checkpoint/evaluation progress separately. If zero-variance groups still dominate, improve the distribution of decision situations and teacher targets before increasing steps or learning rate. Do not reward arbitrary aggression merely to create reward variation.

## Submitted continuation

AC2 reports the new run `train_b56333a6f8fb` as **running**. It uses `pokerbots-principles-step2-v1-train`, submitted with parent checkpoint `ckpt_012f74ea70f9`. The frozen pilot input contains 15 completed hands and 16 valid pre-flop targets; 15 cleanup turns and seven other-street decisions were excluded. There were no target format errors or token-cap truncations. The configuration uses offline OPSD, two steps, batch eight, learning rate `1e-6`, and a checkpoint at step two. Monitor the run before launching the full curriculum; this pilot is not evidence of improved poker strength.

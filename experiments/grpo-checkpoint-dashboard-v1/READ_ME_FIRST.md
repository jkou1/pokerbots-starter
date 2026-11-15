# GRPO checkpoint decisions — native selection and read-only diagnostics

Training: `train_f759c4cb331e`. Native eval links are attached to this collection. Development jobs are pending at this snapshot; their outcomes are deliberately omitted until complete.

| Completed single-hand paired selection | Tasks | EV difference vs parent (BB) | Paired bootstrap 95% CI | Invalid policy decisions |
|---|---:|---:|---|---:|
| Step 5 | 32 | -2.3594 | [-9.5625, +1.7813] | 0 / 50 |
| Step 20 | 32 | +1.2344 | [-0.1094, +3.0000] | 0 / 53 |

These are fixed-deal/seat/opponent single-hand selection screens, not official 30-hand placement or Arena rating. EV may fall back to realized return for unsupported side pots. Both intervals include zero; this does not establish a leaderboard improvement. Clipped training reward is a separate signal, not poker EV.

Read-only clipping snapshot: 1,568 valid-EV rollouts out of 1,577 scored. Different-EV reward ties affect **298 / 11,506 = 2.59% of all legal within-group pairs**, or **298 / 4,433 = 6.72% of unequal-EV pairs**. Groups can span generated policy versions. This is descriptive saturation, not causal proof of failure.

Read-only throughput snapshot (12 steps): waiting 488.26s versus training 349.69s, raw waiting fraction 58.27%. Excluding post-checkpoint timing, 10 steps show 53.09% raw waiting. Waiting overlaps weight-update work; these figures are not a causal attribution solely to the frozen opponent.

No official metrics were modified. No sealed final outcomes, credentials, or raw private conversations were uploaded. `CHECKPOINT_DECISIONS.json` contains aggregate evidence and metadata only.

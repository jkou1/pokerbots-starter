# Fresh-game GRPO experiment — completed November 15, 2026

**Conclusion:** the five-update checkpoint has the highest observed canonical mean on this selection set. The additional 15 updates did not demonstrate a performance gain. Keep the incumbent unchanged and preserve the five-update candidate for further study. These results do not establish tournament strength.

## Matched selection results

All five policies played the same 144 one-hand tasks, with identical task IDs and immutable manifests. Opponent checkpoints/versions, grader source and harness source remained unchanged. Higher canonical mean is better. All 720 evaluation tasks were scored and every cleanup succeeded.

| Policy | Canonical mean | Policy error decisions | EV BB/hand | Realized BB/hand |
| --- | ---: | ---: | ---: | ---: |
| Starting matched SFT (0 GRPO updates) | 6.034722 | 2 | 1.360354 | 0.843750 |
| Incumbent combined SFT v3 | 6.057292 | 0 | -0.168403 | -0.166667 |
| SFT → GRPO, 5 total updates | 6.385417 | 1 | 2.039174 | 2.145833 |
| SFT → GRPO, 15 total updates | 6.180556 | 2 | 1.547285 | 1.246528 |
| SFT → GRPO, 20 total updates | 6.046875 | 0 | 0.540799 | -0.552083 |

The latest 20-update checkpoint had zero action errors, but its mean canonical score was effectively unchanged from the starting SFT model. The earlier five-update checkpoint remains the best observed selection candidate. Reliability and poker returns are separate diagnostics.

## Paired uncertainty

| Comparison | Mean difference | Paired bootstrap 95% interval |
| --- | ---: | --- |
| 5 updates − starting SFT | +0.350694 | [-0.166667, +0.861111] |
| 15 updates − starting SFT | +0.145833 | [-0.364583, +0.652778] |
| 20 updates − starting SFT | +0.012153 | [-0.480903, +0.510417] |
| 20 updates − 5 updates | -0.338542 | [-0.796875, +0.137153] |

Every interval above includes zero. The observed decline with more training is not proof that training harmed the model; it is evidence against assuming that more steps automatically increase evaluation score. This is a reused development selection set with several checkpoints compared. The intervals are descriptive, not independent confirmation of the selected winner. Bootstrap: 10,000 paired task resamples, seed 42.

Removing games where either member of a pair encountered an opponent action error leaves the five-update candidate +0.259843 versus SFT on 127 games, and the 20-update candidate +0.104331 on 127 games; both intervals still include zero. See the robustness JSON files. No selection arm had a cleanup failure.

## Training performed

- Pilot: `train_5c37cbb55d9a`, starting `ckpt_ff5b30f565bb`, five updates, four situations/update × eight attempts/situation = 160 consumed rollouts.
- Follow-up: `train_10acbe13b245`, starting pilot checkpoint `ckpt_af78f07125f3`, 15 additional updates = 480 consumed rollouts. Midpoint saved after 10 follow-up updates, giving 15 total updates across the two linked runs.
- Total: 20 optimizer updates, 640 consumed one-hand attempts across 80 starting situations. There are 744 completed local gameplay logs including prefetch; 742 canonical training records. Two completed but unscored attempts belonged to unused prefetched group 67. All 640 consumed attempts were scored, verified against logged group IDs and batch reward means.
- Standard GRPO, LR `5e-7`, KL coefficient `.01`, four situations/update, eight attempts/situation, concurrency eight, one rollout replica, evaluation sidecar off. The pilot uses seed 42; follow-up uses seed 43. Actual resources: six GPUs per training run.
- Whole-hand rollout budgets: 24,576 response / 32,768 total tokens. Official per-decision and cleanup caps unchanged. No truncations in either run.
- Nonzero gradients throughout. Variable-reward groups: 16/20 in the pilot and 42/60 in the follow-up; restricting to valid action attempts still leaves variation in 16 and 41 groups respectively.
- Consumed training action-error decisions: four in the pilot, 33 in the follow-up. Follow-up errors were concentrated earlier; the final evaluation had zero action errors. All completed follow-up logs, including prefetch, contain three cleanup failures. These training diagnostics must not be substituted for evaluation results.

The public SDK does not expose a separate KL reference checkpoint selector or resolved reference identity; engine logs are restricted. The submitted coefficient and actual checkpoint warm-start dependencies are verified. A specific frozen KL reference identity is not independently verified.

## Data separation and decision history

The historical seed audit scanned 138,452 tasks across all 48 datasets present before this experiment (34,639 distinct seed values). The new sets have no seed overlap with them or each other. This verifies the checked seed fields; it does not certify all possible semantic similarities between historical poker states.

Uploaded 2,160 new training situations and 144 selection situations, with exact content-hash membership checks. The follow-up excludes all 26 situations played or prefetched by the pilot, leaving a separate bank of 2,134 unused situations. SFT knowledge is inherited through the starting weights. The latest SFT corpus mixed PokerBench, Pete decisions and factual cleanup examples.

The initial pilot plan required a positive lower confidence bound before extending. That strict gate was not met. After the user authorized continuation when promising and asked about longer training, we explicitly announced an exploratory 15-update follow-up based on positive paired means, fewer selection action errors and active learning. This revised our self-imposed extension gate; it did not establish an improvement or justify promotion. The follow-up is now complete, and no further GRPO run was launched.

The 36 development full games and 72 final full games remain local, unmodified and unevaluated; the final set remains sealed. Single-hand chip rewards and 30-hand placement rewards must not be pooled. Further full-game validation is required before replacing the incumbent.

## Earlier direct-base experiments

Direct GRPO from original Qwen was already tried in `train_f7436eff428b` on `pokerbots-history-opponent-mixture-v2-train`, a 7,500-task bank. On its earlier shared 64-hand selection set, original Qwen scored 5.835938, GRPO step 5 scored 6.109375, and step 10 scored 5.367188. The five-update advantage was inconclusive. These scores are not directly comparable to this experiment's different 144-task set.

We have not completed an equal-RL-budget comparison of original Qwen versus this SFT starting model using this exact new task bank. Some older datasets are imitation records rather than playable game configurations; they require valid reconstruction, and selection/final data must remain excluded from training.

## Checkpoints and evaluations

| Policy | Checkpoint | Evaluation |
| --- | --- | --- |
| Starting matched SFT (0 GRPO updates) | `ckpt_ff5b30f565bb` | [eval_9e175d13f47e](https://platform.appliedcompute.com/org_cd68943dd947/p/prj_ba36d29befaf/observability/evals/eval_9e175d13f47e) |
| Incumbent combined SFT v3 | `ckpt_51eee61470f7` | [eval_6a1b00991184](https://platform.appliedcompute.com/org_cd68943dd947/p/prj_ba36d29befaf/observability/evals/eval_6a1b00991184) |
| SFT → GRPO, 5 total updates | `ckpt_af78f07125f3` | [eval_bd3f57c7938f](https://platform.appliedcompute.com/org_cd68943dd947/p/prj_ba36d29befaf/observability/evals/eval_bd3f57c7938f) |
| SFT → GRPO, 15 total updates | `ckpt_e0a4424e6718` | [eval_b7c24adef5d0](https://platform.appliedcompute.com/org_cd68943dd947/p/prj_ba36d29befaf/observability/evals/eval_b7c24adef5d0) |
| SFT → GRPO, 20 total updates | `ckpt_0288f73279e0` | [eval_076a77e752a4](https://platform.appliedcompute.com/org_cd68943dd947/p/prj_ba36d29befaf/observability/evals/eval_076a77e752a4) |

## Artifacts and final verification

Compact configurations, summaries, paired comparisons and verification are committed in this directory. Upload receipts, task snapshots, raw scores, full training logs and gameplay archives remain in the ignored local directory `data/experiments/final-grpo-v1/execution/`. The manifest records the original prepared configuration; completed status is documented here. `all-results.json` contains all checkpoint comparisons; `verification.json` records final source/identity checks. All five evaluations and both training runs succeeded.

Archived 1,464 original gameplay logs with byte-for-byte SHA-256 checks, then removed only their matching copies from `runs/`. All four temporary evaluation deployments were deleted; trained checkpoints and converted serving weights are preserved. The three frozen opponent deployments, including the incumbent, remain ready and unchanged. The harness remains connected.

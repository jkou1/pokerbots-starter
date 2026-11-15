# Canonical black box grader model comparison

Inspected 2026-11-15 09:51 PST. Source: [Applied Compute project dashboard](https://platform.appliedcompute.com/org_cd68943dd947/p/prj_ba36d29befaf/observability/training), read through the installed AC2 SDK. Chrome accepted the request to open the dashboard; authenticated browser contents were not inspected.

Queried 26 training runs, 33 standalone evaluations, and 12,787 top-level CanonicalBlackBoxGrader score records. Excluded sft_loss and rmsd_distillation_kl. Compared recorded scores without filtering out failures. Removed three duplicate records by (job ID, score ID).

The strongest single-hand selection candidate is base standard GRPO step 5. The existing combined-sft-v3 remains the more defensible incumbent for long games: the small final comparisons do not establish that GRPO improves canonical score over it. These models are Qwen/Qwen3.6-35B-A3B variants, rather than different model families.

## Shared 64-task selection evaluation

Every entry below uses the same immutable task manifest for pokerbots-overnight-late-grpo-fresh64-v1 and all 64 datapoint IDs overlap. Each task plays one hand. Higher mean canonical score is better.

| Rank | Model / checkpoint label | Mean score | Scored tasks | Tasks with format errors | Evaluation ID |
| --- | --- | ---: | ---: | ---: | --- |
| 1 | Base standard GRPO step 5 | 6.1094 | 64 | 0 | `eval_8aaa0a4be082` |
| 2 | ad74 GRPO step 40 | 6.0234 | 64 | 0 | `eval_4d56139e4695` |
| 3 | ad74 GRPO step 90 | 6.0078 | 64 | 0 | `eval_b8c31f5a9046` |
| 4 | Base GRPO5 + 5-update child | 5.9531 | 64 | 0 | `eval_6b8368497b12` |
| 5 | Catalog base | 5.8359 | 64 | 0 | `eval_3af9891def09` |
| 6 | ad74 GRPO step 20 | 5.8125 | 64 | 0 | `eval_c53f25c0c5ed` |
| 7 | Mixed SFT continuation step 40 | 5.8047 | 64 | 1 | `eval_c713fafc6ea4` |
| 8 | Own-checkpoint diagnostic | 5.7188 | 64 | 0 | `eval_7515a3d00094` |
| 9 | Parent SFT ad74 | 5.5859 | 64 | 0 | `eval_29b930896225` |
| 10 | PokerBench V5 SFT step 20 | 5.4766 | 64 | 2 | `eval_284f73e12461` |
| 11 | Base standard GRPO step 10 | 5.3672 | 64 | 1 | `eval_3a51a03a3a9f` |
| 12 | Base DR-GRPO step 2 | 5.3438 | 64 | 1 | `eval_9a166d999bee` |

GRPO5 exceeds catalog base by 0.2734 points. An approximate paired 95% confidence interval is [-0.591, 1.138], which includes zero. Its lead over GRPO40 is only 0.0859 points. This is a noisy selection set with 12 candidates, not an independent confirmation of the winner.

The run/step labels associate base GRPO5 with train_f7436eff428b and its saved step-5 checkpoint ckpt_a7a227300baf. The historical evaluated deployment infer_af5fa217b570 now returns 404, so that historical deployment-to-checkpoint mapping could not be independently re-read. The checkpoint catalog confirms ckpt_a7a227300baf belongs to that run at iteration 5.

## Longer-game comparisons

Do not pool these scores with the single-hand table. Each task plays 30 hands with carried stacks. Each comparison uses the same dataset manifest within its pair.

| Dataset / stage | Model | Mean score | Games | Games with format errors | Evaluation ID |
| --- | --- | ---: | ---: | ---: | --- |
| Earlier sealed final | combined-sft-v3 | 6.0000 | 6 | 0 | `eval_be4a7c44dc07` |
| Earlier sealed final | ad74 GRPO step 20 | 5.6667 | 6 | 2 | `eval_8a14524c0e64` |
| Fresh final v2 | combined-sft-v3 | 2.6667 | 6 | 0 | `eval_371509c3cc43` |
| Fresh final v2 | Base standard GRPO step 5 | 2.1667 | 6 | 3 | `eval_66dd6344d8ef` |

combined-sft-v3 scores slightly higher in both pairs. Only six games were evaluated in each pair, so the evidence is too small for a broad superiority claim. On fresh final v2, GRPO5 had four format-error decisions spread over three games; all three games scored zero, including games with positive chip returns. The incumbent had no format errors.

combined-sft-v3 is currently ready as infer_b0f5e9429b7e, serving ckpt_51eee61470f7 from train_87b51a9211a1, iteration 39. No deployment was created or changed during this review.

## Earlier 32-task selection evaluation

| Model | Mean score | Tasks | Evaluation ID |
| --- | ---: | ---: | --- |
| overnight-fast-combined-sft-v3 | 6.3438 | 32 | `eval_521f73148d31` |
| overnight-grpo-step20-paired32-select | 6.1719 | 32 | `eval_a62651277efa` |
| overnight-grpo-step5-paired32-select | 6.0312 | 32 | `eval_1712153a22c5` |
| overnight-fast-selfplay-ad74c826c9ad | 5.9219 | 32 | `eval_7353b52d4873` |

The incumbent leads this earlier 32-task set. These numbers cannot be ranked directly against the different 64-task set.

## What the training dashboard averages show

These are arithmetic means of recorded top-level canonical scores from each training job. They mix policy versions and sampled training tasks. They describe training experience; they do not provide a fixed-checkpoint performance ranking.

| Training run | Run ID | Mean recorded score | Score records |
| --- | --- | ---: | ---: |
| pokerbots-grpo-20261115-004955 | `train_9934ba584c16` | 7.3333 | 9 |
| grpo-history20k-frozen-selfplay-ad74-100steps-16rollouts | `train_dddb9d4abf5d` | 6.4589 | 219 |
| grpo-newaccount-bootstrap-base-diagnostic-1step | `train_c1a9b5d15680` | 6.4125 | 160 |
| train-grpo-6a7c | `train_c89c5efafb0d` | 6.3700 | 50 |
| base-grpo5-stability-v1-cap5 | `train_ed0649fc4923` | 6.1383 | 424 |
| grpo-history20k-ad74-b64-ckpt5-noeval-ownerfix | `train_f759c4cb331e` | 5.9571 | 6512 |
| catalog-base-standard-grpo-v1-cap10 | `train_f7436eff428b` | 5.7582 | 731 |
| catalog-base-drgrpo-short-v1-2steps | `train_f3c0ccd1c556` | 5.4688 | 16 |
| grpo-own-checkpoint-weightsonly-diagnostic-1step | `train_555fe377c93e` | 5.4219 | 192 |
| pokerbots-grpo-20261115-030725 | `train_80ea057be687` | 3.3750 | 28 |

The apparent leader, train_9934ba584c16, has only nine scores, all at generated step 0. This does not show that its trained checkpoint is best. The five-update stability child ends with an average of 7.1171 at generated step 4 across 64 scores, but its separate fresh64 checkpoint evaluation is only 5.9531. A high training batch average need not carry over to evaluation.

## How to read CanonicalBlackBoxGrader

For these chip-based evaluations, recorded scores agree with the harness rule: successful rollouts get 6 + clip(EV in big blinds, -5, +5), bounded from 1 to 11. Model failures and format errors score 0. The grader name identifies the scoring interface; it does not guarantee that every run uses the same dataset or task objective. The inspected evaluation artifacts contain EV, hands, and format-error counts, rather than placement labels. These scores are not a win percentage or arena rating.

Because returns are clipped, a large chip gain can score the same as a small one, and any format error can turn a profitable game into zero. Reliability is therefore part of model performance under this grader.

The newest matched SFT runs train_2888f6862cb2 and train_0b9fbdebc2de have sft_loss records but no canonical gameplay scores in this snapshot. They remain unranked for poker performance.

Recommendation: keep combined-sft-v3 as the incumbent; shortlist base GRPO5 and ad74 GRPO40/90 for a larger paired long-game evaluation with format-error tracking before replacing it. No training, evaluations, or inference requests were launched for this review.

## Latest matched SFT follow-up

The final continuation checkpoint `ckpt_ff5b30f565bb` has now been evaluated on the shared 64-hand selection set: **5.4688**, versus **5.8359** for its parent `combined-sft-v3`. Both had zero policy format errors and zero cleanup failures. The paired difference is -0.3672 points, with an approximate paired bootstrap 95% interval [-0.9922, 0.2188]. This does not establish an improvement. See [the full evaluation report](reports/matched-sft-canonical/REPORT.md) for dashboard links, artifacts and limitations.

## Fresh-game GRPO pilot and exploratory continuation — completed

Five checkpoints/controls were compared on the same new 144 one-hand tasks. Do not rank these means against the earlier 64-task or full-game sets.

| Policy | Canonical mean | Policy action errors |
| --- | ---: | ---: |
| Starting matched SFT (0 GRPO updates) | 6.034722 | 2 |
| Incumbent combined SFT v3 | 6.057292 | 0 |
| SFT → GRPO, 5 total updates | 6.385417 | 1 |
| SFT → GRPO, 15 total updates | 6.180556 | 2 |
| SFT → GRPO, 20 total updates | 6.046875 | 0 |

The five-update candidate `ckpt_af78f07125f3` has the highest observed mean. Its paired advantage over starting SFT is +0.350694, 95% interval [-0.166667, 0.861111]. After 20 updates, the difference is +0.012153, interval [-0.480903, 0.510417]. Neither establishes an improvement. The extra 15 updates did not demonstrate a benefit; no further run was launched. Keep the incumbent unchanged.

Runs `train_5c37cbb55d9a` and `train_10acbe13b245` both succeeded, consuming 640 rollouts across 20 updates. The second block was explicitly exploratory after the initial strict confidence gate was not met. Full-game final tasks remain sealed, all temporary evaluation GPUs are released, and checkpoints are preserved.

See [the completed experiment report](reports/final-grpo-v1/REPORT.md) for all checkpoint identities, uncertainty, data separation, gameplay diagnostics and verification.

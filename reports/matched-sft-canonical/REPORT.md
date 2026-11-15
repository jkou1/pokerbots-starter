# Latest SFT bot: canonical gameplay evaluation

Completed 2026-11-15 10:21 PST.

The final continuation checkpoint from `train_0b9fbdebc2de`, `ckpt_ff5b30f565bb` (iteration 63, after 64 updates), did not demonstrate an improvement over its parent, `combined-sft-v3` / `ckpt_51eee61470f7`.

| Model | Mean CanonicalBlackBoxGrader score | Scored hands | Format-error hands | Cleanup failures |
| --- | ---: | ---: | ---: | ---: |
| Latest matched SFT continuation | 5.4688 | 64 | 0 | 0 |
| Parent combined-sft-v3 | 5.8359 | 64 | 0 | 0 |

Latest minus parent: **-0.3672** points. A paired bootstrap with 10,000 resamples gives an approximate 95% interval of **[-0.9922, 0.2188]**. It includes zero, so this small selection comparison establishes neither a reliable improvement nor a reliable regression. The candidate scored higher on 14 tasks, the parent on 20, with 30 ties.

- [Latest bot evaluation](https://platform.appliedcompute.com/org_cd68943dd947/p/prj_ba36d29befaf/observability/evals/eval_50beb7592a97)
- [Parent evaluation](https://platform.appliedcompute.com/org_cd68943dd947/p/prj_ba36d29befaf/observability/evals/eval_e756c03b3b8f)

## What was run

The local poker harness was started on `127.0.0.1:8765` and reconnected to `vals-hackathon`. Project-scoped credentials were rejected by the server; the user explicitly approved a temporary organization-scoped connector credential. That credential stays in connector process memory and the helper revokes it when it exits. At completion of this review the requested harness connection remains active.

Eight actual managed-SFT token samples passed the protocol audit. The latest checkpoint was converted and temporarily deployed as `infer_771be147d5cc`. It answered a real submit_action probe. Four-hand smoke evaluations for both policies completed with zero policy format errors before their 64-task runs. Smoke IDs: parent `eval_fda8cb9597cf`; candidate `eval_868f5823766f`.

Both main runs used the same immutable task manifest from `pokerbots-overnight-late-grpo-fresh64-v1`, with exactly the same 64 datapoint IDs and 64 unique seeds. Each task plays one hand, with event prompts, thinking, tool parsing, scratchpad cleanup and the existing token budgets. Thirty-two tasks use the ad74 opponent and 32 use the Pete base20 opponent. Both opponent deployments remained ready at version 1 with the expected checkpoints after the runs; candidate and parent also remained at their recorded version 1 checkpoints. Each run used eight concurrent tasks, one sample per task, and no job-level retries. Failures were not filtered out of the scores.

These are actual platform `CanonicalBlackBoxGrader` scores, not a locally substituted metric. The existing harness runs the game, labels EV, and serves the grading endpoints. No new scoring rule or parser was introduced. Source hashes, task manifests, score rows and copies of full game logs are saved beside this report.

## Diagnostics and limits

The canonical chip score is `6 + clip(EV in BB, -5, +5)` for valid gameplay, with zero for model-caused format failures. It is not a win percentage or an Arena rating. The score uses the task's chip objective, not the placement objective available for full 30-hand games.

| Diagnostic | Latest SFT | Parent |
| --- | ---: | ---: |
| Mean EV BB per hand | -3.2633 | -1.9219 |
| Mean realized BB per hand | -3.5781 | -1.9219 |
| Canonical score vs base20 opponents | 5.3750 | 5.6406 |
| Canonical score vs ad74 opponents | 5.5625 | 6.0312 |
| Opponent format-error decisions | 3 | 4 |

Opponent decisions are stochastic and can differ between policies even on the same deal. Their few format errors remain part of these recorded games. These 64 tasks were an existing selection set, not a new sealed final evaluation. One-hand results do not establish long-game memory or placement performance; one cleanup turn cannot establish memory quality across a 30-hand game. This experiment evaluated the final continuation checkpoint only, not the earlier 32-update checkpoint or the separately trained base arm.

The parent remains the supported incumbent. No Arena entry or existing deployment was changed, and no RL training was launched. This comparison supplies a baseline for a separate capped GRPO experiment; it does not show that further imitation training helps. The temporary candidate deployment is removed after evaluation to release its GPU; its saved checkpoint and converted weights remain available.

## Historical data and simulation, in beginner terms

Historical hands are worked examples. SFT practices reproducing their recorded decisions. The poker engine is a practice table that enforces legal moves and deals cards. Opponent bots supply the other players' decisions. The canonical grader is the scorekeeper after play. GRPO is a training method that uses those scores to adjust the bot.

We can turn suitable historical situations into practice scenarios. But if the record says Pete folded and our bot raises instead, the original record cannot tell us how opponents would respond to that raise. We must simulate the continuation. Some data, such as a PokerBench decision snapshot, also lacks the full hidden state and history needed to reconstruct an exact original game; that state must be reconstructed consistently or sampled. Hidden opponent cards and future cards must stay out of the bot's observations.

More historical data supplies examples and possible starting situations. It does not supply outcomes for every alternative action. Running new games supplies that missing feedback. The SFT run did not use this feedback because it was configured for imitation with no gameplay rollouts and evaluation disabled. This evaluation has now exercised the gameplay-and-grading path for the latest bot.


Raw evaluation receipts, scores and gameplay logs remain in the ignored local directory `data/experiments/matched-public-v1/canonical-review/`.

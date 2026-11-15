Pull libraries of prompt injection for poker bots, and insert those into the model's table talk. Perform evaluations to see what kinds of prompt injections (malicious/malformed json input, garbage text, or bluffing) actually work, then train the model to use those most effective prompt injections.

Pull historical data from PokerBench on huggingface

## Final strategy: fresh poker simulations followed by GRPO

Use the SFT model as a starting policy, then improve it by letting it play new
games and training on the existing harness's canonical rewards. Historical
hands supply examples and help identify weak situations; the engine and
opponent policies supply the outcomes of actions absent from those records.

The first experimental starting point is the latest matched SFT checkpoint,
`ckpt_ff5b30f565bb`. Keep `combined-sft-v3` / `ckpt_51eee61470f7` unchanged as
the incumbent control. The latest checkpoint scored 5.4688 versus the parent's
5.8359 on the previous 64-hand comparison; the difference was inconclusive.
Compare the RL child with both its unchanged SFT starting point and the
incumbent. More recent training is not evidence that a checkpoint is better.

### Prepared game distribution

Local artifacts are in `data/experiments/final-grpo-v1/`. Nothing in this
preparation uploads datasets, starts training, or allocates GPUs.

| Set | Tasks | Hands per task | Purpose |
| --- | ---: | ---: | --- |
| train | 2,160 | 1 | Fresh situations for GRPO |
| select | 144 | 1 | Compare checkpoints on the same deals |
| game-select | 36 | 30 | Check carried stacks, memory and placement |
| game-eval | 72 | 30 | Sealed final comparison after choosing the recipe |

Every set balances all six policy seats and three opponent configurations:
`selfplay-ad74c826c9ad`, `pete-postflop-base-s20-jkou`, and `combined-sft-v3`,
all in `vals-hackathon`. Each table uses one of those models for its other
seats. Resolve and freeze their deployment versions and checkpoint identities
before execution. Keep the event's legal actions, thinking, table-talk
sanitizer, starting stacks, blinds and per-decision token limits.

Each split has a distinct deterministic seed stream. Prepared seeds are
unique across these four sets and do not overlap the known starter splits,
previous 64-task selection set, or matched official-game plans. Audit the
remaining historical datasets before uploading; the local check does not
claim complete historical coverage. The existing generator uses fixed seed
streams, so merely changing a dataset prefix would repeat old deals.

Fresh deals provide natural variation in cards, boards and betting histories.
Audit which streets and decision types actually occur. If important cases
remain rare, add legal engine-generated scenarios targeting them. Historical
mid-hand positions require validated state reconstruction and continuation
support; a textual instruction describing a difficult flop is not sufficient.
Keep unseen cards and future outcomes out of the policy's observations.

### Bounded first GRPO experiment

The prepared `pilot-config.json` specifies five optimizer updates, four
starting tasks per update and eight sampled attempts per task. That is 32
rollouts per update and nominally 160 consumed one-hand rollouts; prefetching
may generate extra attempts, and each attempt includes multiple model calls.
Eight attempts share a task's deal and opponent configuration, although the
opponents' sampled responses can differ.

Use standard GRPO, learning rate `5e-7`, KL coefficient `0.01`, one rollout
replica, sampling concurrency eight and a saved checkpoint after update five.
These are conservative pilot settings, not measured optimal values. Verify
the frozen KL reference identity before launching. The launcher estimates
about six GPUs: four for training and two for rollouts. Recheck actual model
sizing, active jobs and quota before launch.

The short pilot has no concurrent evaluation sidecar. Instead, explicitly
evaluate the unchanged starting policy and saved child on the same selection
tasks outside training, with the incumbent as another control. This differs
from the earlier SFT workflow, which had no gameplay evaluation at all.
The task bank supports later runs; five updates will not consume all 2,160
starting situations.

The one-hand training reward is the existing canonical chip score:
`6 + clip(EV in big blinds, -5, +5)`, with model-caused format failures scoring
zero. Do not add rewards for particular action words, aggression or chatter.
Log unclipped chip returns and action validity alongside the clipped score.

Check group reward variation, consumed groups, policy-gradient signal,
truncations and failures by cause. Earlier runs produced identical scores
within groups and therefore no comparative reward signal. If that repeats,
inspect the task distribution and reward saturation before extending training.
Do not assume that more generated games means more useful learning.

### Full-game validation and continuation

Use the 36 development games before opening the 72 sealed final games. The
prepared full-game tasks use the existing placement objective: first place
scores 11, second 9, through sixth 1; model-caused format failures score zero.
Compare models within the same task set and objective. Do not rank these
placement scores against the single-hand chip scores.

Report paired placement, canonical score, chips, action errors, cleanup
failures and opponent errors. Keep identical deals, policy seats and opponent
versions across policies, while acknowledging stochastic continuations.
Use uncertainty intervals and the unchanged controls to decide whether to
extend the pilot. An inconclusive result is not a demonstrated improvement.

One-hand GRPO is an initial learning and infrastructure check. For a final
policy intended to remember opponents and manage elimination risk, follow a
promising pilot with a separately bounded 30-hand GRPO experiment using the
placement objective. First measure whole-game token consumption and set the
aggregate rollout budget accordingly; the single-hand launcher's budget must
not be copied blindly. Preserve the official per-decision and cleanup caps.

Keep outgoing table-talk optimization from the earlier notes as a separate,
controlled experiment. Attribute improvements to betting, memory or messages
only when matched comparisons support that conclusion. Replace the incumbent
only after fresh full-game results support the change.

### Pilot execution (November 15, 2026)

The user authorized the five-update pilot and conditional continuation. Submitted
`train_5c37cbb55d9a` from `ckpt_ff5b30f565bb`, with the prepared configuration.
The actual job reserves six GPUs and records that exact checkpoint dependency.
The historical audit scanned all 48 existing datasets (138,452 tasks and
34,639 distinct seed values), with no overlap against the new task seeds.
The 2,160 training and 144 selection tasks are uploaded and their content-hash
membership is verified. Full-game sets remain local and unevaluated.

Completed selection controls: starting SFT 6.034722 canonical mean with two
policy action errors; incumbent 6.057292 with zero policy action errors.
Each played all 144 identical selection tasks. Both completed every cleanup.
The temporary baseline deployment was deleted after its evaluation.

The explicit extension gate requires useful group reward variation and a
policy-gradient signal, no material error/truncation regression, and a paired
selection gain with a bootstrap 95% lower bound above zero. A passing pilot
permits a bounded additional 15 updates, followed by another evaluation; it
does not authorize an open-ended training run. Execution artifacts and the
live report are under `data/experiments/final-grpo-v1/execution/`.

The public SDK exposes the KL coefficient but no separate reference checkpoint
selector or resolved reference identity; platform engine logs are restricted.
Thus the submitted `.01` coefficient and warm-start identity are verified,
while a specific frozen KL reference identity is not independently verified.

### Pilot result and exploratory follow-up

The five-update pilot succeeded and saved `ckpt_af78f07125f3`. It consumed
160 rollouts; 208 completed including prefetch. Sixteen of 20 consumed groups
had reward variation, all five gradient norms were nonzero, and truncation
was zero. On the matched 144-task selection set, canonical mean was 6.385417
versus starting SFT 6.034722 and incumbent 6.057292. Policy action errors were
1, 2 and 0 respectively; all cleanups succeeded.

The pilot-minus-SFT paired effect was +0.350694, bootstrap 95% interval
[-0.166667, 0.861111]. Excluding any game with an opponent action error in
either arm leaves 127 tasks and a positive +0.259843 mean, still inconclusive.
The original strict confidence-interval continuation gate was not met.

Given the user's authorization to continue if promising and questions about
longer training, proceed with one explicitly exploratory block of 15 more
updates. This revises our self-imposed strict training-extension gate; it does
not establish an improvement or satisfy the promotion requirement. Positive
paired means, fewer policy errors and healthy learning mechanics justify the
bounded follow-up. Evaluate it again before any further extension; keep the
incumbent and sealed final games unchanged.

Use `ckpt_af78f07125f3`, the same learning rate, GRPO method and reward, and
seed 43. Exclude all 26 contexts played or prefetched by the pilot, leaving
2,134 fresh unused contexts. Fifteen updates consume nominally 480 attempts.
Save every five updates, keep two checkpoints, no concurrent evaluation
sidecar. The temporary pilot deployment was deleted after evaluation.

Submitted follow-up: `train_10acbe13b245` (compute job `job_ceaa2a10ace5`),
verified six GPUs and dependency on `ckpt_af78f07125f3`.


### Completed result

Both runs succeeded: 20 updates total, 640 consumed one-hand attempts. On the
same 144-task selection set, SFT scored 6.034722; GRPO after 5, 15 and 20
total updates scored 6.385417, 6.180556 and 6.046875. The incumbent scored
6.057292. The five-update checkpoint remains the highest observed candidate,
but its advantage is inconclusive; the extra 15 updates did not demonstrate
a gain. Keep the incumbent unchanged and stop this configuration here.

Final checkpoint `ckpt_0288f73279e0`; retained midpoint `ckpt_e0a4424e6718`;
five-update candidate `ckpt_af78f07125f3`. All temporary evaluation deployments
were deleted; checkpoints are preserved. Full-game sets remain unmodified and
unevaluated. Completed report: `data/experiments/final-grpo-v1/execution/REPORT.md`.

An original-Qwen GRPO arm on exactly this curriculum and the same RL budget
has not been run. Earlier direct-base GRPO used a different 7,500-task bank.

The committed result and compact verification snapshots are in [reports/final-grpo-v1/REPORT.md](reports/final-grpo-v1/REPORT.md); raw gameplay artifacts stay local.

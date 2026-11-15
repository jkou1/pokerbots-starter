# Poker SFT action-token audits and local diagnostics

This collection groups existing SFT training runs, existing native AC2 evaluation runs, and uploaded audit reports. Uploading a report does not turn a local diagnostic into a native evaluation run or overwrite official training metrics.

## Action-only training loss

All 5,120 managed token samples were analyzed (40 updates ×64 examples ×2 runs). Action CE scores only tokens overlapping the actual fold/check/call/bet/raise argument, excluding fixed protocol and tool syntax. Amount digits are scored separately. Each window has640examples, and the action macro weights five action classes equally.

| Metric | Updates0–9 |10–19 |20–29 |30–39 |
|---|---:|---:|---:|---:|
| Continuation action macro CE |0.930|0.782|0.642|0.507|
| Base action macro CE |1.234|0.848|0.655|0.513|
| Continuation bet CE |2.131|1.502|1.150|0.861|
| Base bet CE |1.376|1.444|1.171|0.741|
| Continuation amount CE |1.489|1.265|0.957|1.067|
| Base amount CE |1.842|1.414|1.138|1.115|

Action learning continued late; amount learning was flatter/noisier. These are different training minibatches, so they do not establish fixed-validation convergence or poker improvement. The initial40-update runs lacked automatic milestone stop/extension decisions; this report does not retroactively claim those decisions happened.

Training runs:
- Continuation: train_e3fba0323bd2 (incumbent checkpoint ckpt_51eee61470f7, LR2e-6).
- Independent base control: train_4cc69b58d8e9 (LR5e-6).

## Clearly local selection diagnostics

These real inference diagnostics were run locally and therefore were not native AC2 Eval records. Their summaries are published here as artifacts, explicitly labeled LOCAL.

| Diagnostic | Examples | Action agreement | Legal rate | Teacher-bet recall |
|---|---:|---:|---:|---:|
| Incumbent postflop |147|64.6%|100%|0/39|
| ad74 postflop |147|69.4%|100%|0/39|
| Incumbent preflop |354|84.5%|100%|not applicable|

Both postflop baselines reproduced all77teacher checks. Teacher agreement is not tournament placement or poker EV.

## Existing native AC2 evaluations

The collection also links eval_521f73148d31 and eval_7353b52d4873, the actual32-task platform selection screens. These remain separate from the local147/354 diagnostics. Their native status/rewards are not replaced by this report.

All summaries retain source hashes. Raw private conversations and credentials are excluded. No GPU workload was created by publishing these artifacts.

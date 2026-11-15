# Retrospective action learning and future stop policy

The initial40-update pilots had no automatic milestone stop/extension controller. Recording a fixed budget was not a substitute for checking targeted validation as checkpoints became available. This review does not retroactively claim those decisions happened.

All5120 managed samples were analyzed. Only tokens overlapping actual action argument letters were scored; fixed protocol, tool/function names, and parameter syntax were excluded. Amount digits were scored separately. Each10-step window contains640examples; the action macro gives equal weight to the five action classes.

| Run / metric | Steps0–9 |10–19 |20–29 |30–39 |
|---|---:|---:|---:|---:|
| Continuation action macro CE |0.930|0.782|0.642|0.507|
| Base action macro CE |1.234|0.848|0.655|0.513|
| Continuation bet argument CE |2.131|1.502|1.150|0.861|
| Base bet argument CE |1.376|1.444|1.171|0.741|
| Continuation amount CE |1.489|1.265|0.957|1.067|
| Base amount CE |1.842|1.414|1.138|1.115|

Action learning did not show a broad plateau: final-window action macro improved about21% in both runs, and bet arguments continued improving. Amount learning was flatter/noisier late. These are different training minibatches, not a fixed validation set; class balancing reduces composition effects but does not prove convergence or poker improvement. Source sample hashes and per-step/action counts are preserved in the action-CE reports; full token payloads are compressed and ignored in Git.

Future SFT starts require predeclared checkpoints at5/10updates, an initial cap of10, and explicit target-validation/retention/reliability evidence before any extension. Serving conversion can lag training, so a completed bounded pilot must release GPUs rather than spend another budget while waiting for evidence. Targeted fixed selection and official poker gates remain separate from training CE.

`milestone_guard.py` is a read-only decision helper by default. It refuses extension without a current fixed-selection receipt, stops on legality/retention regression, detects action-specific plateau only with class coverage and no target gain, and requires a preserved checkpoint before stopping. Optional`--enforce-stop` requires exact per-run authorization and verifies checkpoint ownership before calling the stop API. It never launches or extends training. Its five focused tests pass. It is not retroactively applied to the completed40-update pilots and is not currently stopping any job.

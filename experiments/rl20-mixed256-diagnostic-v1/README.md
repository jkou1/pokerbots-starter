# LOCAL RL20 comparison on fixed mixed-teacher SELECT256

This is teacher imitation, not poker EV, placement, or a native Eval job. The exact same256 held-out records and proven evaluator were used for RL20 and the preserved incumbent reference. Both policies were legal on256/256 examples. No sealed-final games were queried. Inference completed; the existing RL20 endpoint has been released to the evaluation coordinator.

| Metric | Incumbent | RL20 |
|---|---:|---:|
| Overall / teacher-balanced action agreement |75.78%|73.83%|
| Equal-weight street agreement |65.00%|66.39%|
| Equal-weight teacher × street agreement |65.24%|66.52%|
| Carlos agreement (128) |72.66%|69.53%|
| Pete agreement (128) |78.91%|78.12%|
| Preflop agreement (174) |84.48%|80.46%|
| Flop agreement (38) |55.26%|55.26%|
| Turn agreement (27) |55.56%|59.26%|
| River agreement (17) |64.71%|70.59%|
| Teacher bets recalled |0/27|0/27|
| Teacher checks recalled |43/43|43/43|
| Teacher raises recalled |33/43|26/43|
| Teacher calls recalled |8/25|12/25|
| Teacher folds recalled |110/118|108/118|
| Exact action + amount |175/256|175/256|
| Exact teacher aggressive action + size |14/70|12/70|

RL20 remains passive on teacher bets in this diagnostic. Its small postflop agreement gain and preflop raise loss do not resolve whether its poker strategy improved. The aggregate JSON includes every group denominator, exact sizing and legal metrics, source hashes, and explicit comparison scope. Training or promotion cannot be justified from agreement alone.

# LOCAL early20 candidate diagnostics

These are real locally executed inference diagnostics, published as an artifact. They are not native AC2 evaluation runs.

|Metric|Continuation20|Base20|
|---|---:|---:|
|Postflop teacher action agreement (147)|70.75%|73.47%|
|Teacher bets recovered (39)|3|11|
|Teacher checks retained (77)|77|73|
|Postflop legal rate|100%|100%|
|Enum regression legal calls (4)|4|4|
|Valid cleanup stress responses (10)|3|6|

Base20 preflop agreement is79.10% on354 cases, versus incumbent84.46%; legal rate100%. Continuation20 fails the predeclared bet-recall screen; base20 passes the bet/check/legal screen, but preflop retention and cleanup remain concerns. Official paired poker performance is still needed before promotion. Stress cases are deliberately selected, so3/10and6/10are not population failure rates.

Actual native new-account smoke eval reference:eval_a1cc729a3948. This platform run is separately linked in the collection; no local result was fabricated as an Eval run. JSON artifact retains source hashes.

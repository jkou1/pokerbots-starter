# Existing RL20 cross-teacher imitation diagnostic

Problem: native single-hand poker screens do not reveal whether GRPO policy changes transfer across both public teachers and streets. Hypothesis: RL20 may change passivity/action behavior across the fixed mixed-teacher heldout set; agreement is diagnostic, not a reward or poker EV surrogate.

Targeted change: none to models, prompts, tools, datasets, jobs or decoding. Query already-served immutable RL20 infer_9efa1c614a32 using the same proven evaluator/event preset/temperature0 as the preserved incumbent reference, on exactly the same256SELECTrecords. Four concurrentrequests maximum;400second timeout; no new GPU job or model. lmathias key preflight required. Eval owner confirms existing full-game requests fit and prevents rotation while this bounded diagnostic runs.

Test: verify everyrecord/provenance aligns to incumbent and fixedSELECTsource; report perteacher/street and equallyweightedteacher/street agreement, exactsizing/legal/actionrecall. Denominators explicit. No sealedfinal games queried; no selectionexample enterstraining. No strategy conclusion from imitation alone.

Stop/success: stop once256responsescomplete or timeout/endpointrotationrequested; preserve failures in denominator, no silent retryinguntilscore improves. Report fullpaired comparison; do not interpret higheragreement as improvedpokerEV. No training/deployment/promotion follows from this diagnostic alone.

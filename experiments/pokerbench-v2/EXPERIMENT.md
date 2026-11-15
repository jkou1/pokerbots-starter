# PokerBench solver supervision pilot (prepared; not launched)

Problem: current incumbent SFT has only 19 unique postflop replay decisions. Broader postflop action/sizing knowledge may improve value extraction. Existing PokerBench conversion rounds fractional monetary labels and omits the Qwen thinking boundary marker.

Hypothesis: a short continuation on broad solver-labeled postflop scenarios improves betting decisions while preserving legal tool calls and tournament performance. Solver cash-game labels have domain shift; this is a candidate, not established poker improvement.

Targeted change: use the same 20,000 randomly sampled original source rows, deduplicate observations, split observable scenario groups before training, scale every chip amount exactly 2x to official 1/2 blinds and 200-chip initial stacks, and exclude fractional states instead of rounding. Include a nonempty synthetic protocol boundary before the target tool call. Keep selection and final split untouched. No target reasoning is attributed to the solver.

Test: verify remote content membership and sampled payloads; audit actual managed trainer sampled tokens for supervised `</think>` and one-newline prefix. Compare checkpoints20/40 with parent on paired official games (same seeds/seats/opponents), format failures, placement and chips. PokerBench action agreement on selection is supplementary, not promotion evidence. Inspect generated table talk for workplace appropriateness within five minutes before promotion.

Success: reliable real tool calls, no material illegal/truncation increase, and favorable paired official-game placement/chip evidence versus incumbent; use uncertainty honestly. Do not promote on loss or solver agreement alone.

Stop: missing/scaffold-corrupted targets; repeated backend/data errors; token-boundary audit failure; severe legality degradation; sustained stalled training or rollouts; or clearly worse paired poker outcomes. Finish the initial40-update pilot before considering more training unless an early stop condition fires. Extension requires selection evidence.

Budget: 40 updates, batch64, checkpoints20/40, continuation LR2e-6 (preferred) or independent base LR5e-6 (control), total context8192, inference replicas0, eval sidecaroff, one training replica (four GPUs). Launch only after coordinator allocates resources.

Priority: currently secondary to reconstructing stronger, in-domain Professor Pete postflop demonstrations; prepare/upload CPU-only now, launch only if best available ROI.

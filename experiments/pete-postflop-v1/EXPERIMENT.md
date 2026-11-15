# Professor Pete postflop imitation pilot (not launched)

Problem: incumbent trained on only19 unique postflop replay actions and may under-extract value; leader Professor Pete has stronger observed EV and placement. Limited recent leader comparisons are descriptive, not causal evidence.

Hypothesis: legal postflop demonstrations from the strongest public bot teach more useful betting/sizing behavior than further preflop-only updates or domain-shift solver labels.

Targeted change: freeze public Pete match archive before cutoff, replay every hand through authoritative engine, reconstruct only decision-time official prompts, retain legal clean Pete flop/turn/river tool calls, preserve original split_for(deal_identity) mapper. No private reasoning or scratchpad is fabricated. Add protocol marker only as serialization scaffold. Short incumbent continuation; retain preflop preservation examples as needed.

Test: check archive provenance, replay parity, split overlap, source flags, managed target boundary, then paired official games vs incumbent with same deals/seats/opponents; judge placement/chips and legality. Inspect workplace-appropriate table talk within five minutes before promotion.

Success: no material legality regression and favorable paired official poker results, not merely target agreement or training-loss decline.

Stop: source/replay/target-boundary errors, sustained training stalls, severe legality regression, or clear paired poker degradation. Initial40-update pilot; no automatic long training without selection evidence.

Budget:40updates batch64 checkpoints20/40, low LR2e-6 from incumbent, context8192, inference replicas0, evaloff, one training replica (4GPUs). Resource launch gated on coordinator allocation.

## Prepared base-start control (not submitted)

Problem: narrow incumbent SFT priors may limit postflop learning. Hypothesis: independent base training on the same1667demonstrations preserves broader priors and achieves stronger official poker performance than continuation. Targeted change: base initialization and LR5e-6; same examples,40updates,batch64,checkpoint20,8192context,0rollout/0evalreplicas and4trainingGPUs. Test: identical official paired selection games and postflop action/legality diagnostics. Success/stop criteria match the continuation pilot. This two-variable comparison is a practical recipe choice, not causal isolation of initialization. Await coordinator resource allocation; do not submit automatically.

Additional heldout regression gate: verify legal action enum on the incumbent smoke failure where action=submit. This evaluation input is never added to training. Resource schema: BYOH account rejects gpus_per_node and SFT eval.n_inference_replicas; use catalog four-GPU training default with explicit one training replica, rollout replicas0, evalmodeoff.

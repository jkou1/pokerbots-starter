# Corrected PokerBench postflop pilot (GPU launch on HOLD)

Problem: Pete-only demonstrations may leave broad strategic coverage gaps. The v2 converter failed to scale bare action amounts; v3 repairs this before any training.

Hypothesis: broader solver-derived postflop labels improve betting/sizing and general poker quality beyond Pete-only imitation.

Targeted change: independent base-start SFT on4096 clean postflop decisions, exact2x chip scaling for both bare and suffixed source forms, nonempty Qwen protocol scaffold, source-scenario grouped splits. Exclude fractional states, below-minimum raises, raises without a bet, and calls without a bet from training/selection. Original1582 final source holdout remains untouched and its unsupported labels are marked.

Test: full remote membership and retrieved payload verification; actual managed prompt/target boundary; deterministic147 action-stratified selection diagnostic; paired official poker comparison, legal actions>=99%, action-type and size quality. Final source holdout never chooses checkpoints. Workplace-appropriate table talk check before any promotion.

Success: favorable paired official poker outcomes with reliable legal tool calls and broader action/sizing quality. Loss or solver agreement alone never establishes poker improvement.

Stop: source monetary mismatch, failed managed boundary, repeated errors/stalls, or material poker/legality regression. Initial40updates only; no extension without selection evidence.

Budget if later authorized:4trainingGPUs,one replica,40steps,batch64,LR5e-6,checkpoint20,8192context,0rolloutreplicas,evaloff. CURRENTLYNO GPU LAUNCH AUTHORIZATION: coordinator prioritizes GRPO restoration after Pete pilots.

Limitations: monetary audit is not a complete engine replay. Cash-game GTO labels are not proof of tournament-optimal decisions. Source contains no match IDs; split groups remove hero holdings to keep betting/board contexts together.

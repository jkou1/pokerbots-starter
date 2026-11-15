# Overnight poker experiments

Coordinator: Codex. Window: Sunday 2026-11-15 00:27–09:00 PST.
Standing orders: `/Users/lance/Documents/pokerbots-starter-grpo-history/AGENTS.md`.

## Operating policy

- Maximize leaderboard placement while preserving working entries and dependencies.
- Use the reserved 10-GPU allocation for useful training and evaluation; actively triage stalls, errors, and slow throughput.
- Avoid direct paid APIs. Use existing AC2 allocation; Codex OAuth or Kimi CLI for additional reasoning, preferring highspeed models.
- Isolate experiments and record dataset/checkpoint/configuration lineage. Preserve final holdouts.
- Autonomous promotion is authorized after functional validation and a workplace-appropriate table-talk review taking at most five minutes per promotion. Repair failed promotions and preserve rollback options.
- Existing caffeinate and network availability are supplied by user.

## Current status — 00:29 PST

- Main branch worktree created at `/Users/lance/Documents/pokerbots-main`, fast-forwarded to `origin/main` (`f9022ff`); this file lives in its root.
- GRPO `train_dddb9d4abf5d` is running: historical 20k stack tasks, frozen self-play from `ckpt_ad74c826c9ad`, requested 100 steps / 16 rollouts. Existing launch agent verified four frozen-opponent test hands with zero errors.
- Deployments: `combined-sft-v3` and `selfplay-ad74c826c9ad`, each one GPU; custom harness relay uses zero GPUs.
- PokerBench agent reports background chunked upload of 80k train / 20k test / preflop datasets. Membership and protocol compatibility need verification before training.
- Existing GEPA attack evidence is preliminary (tiny validation sets and endpoint failures); no promotion justified yet.

## Assignments

- `rl_ops`: GRPO queue/runtime health, reward signal, rollout throughput and checkpoint readiness; repair failures.
- `sft_data`: audit PokerBench conversion/upload and prepare short, protocol-correct SFT experiment; coordinate GPU allocation before launch.
- `eval_promote`: identify incumbent and checkpoint mappings, evaluate existing strong candidates without changing the live RL connector.
- Coordinator: GPU scheduling, highest-ROI next experiments, promotion decisions, durable status and monitoring.

## Next decisions

1. Confirm actual GRPO GPU allocation and healthy completed graded rollouts.
2. Verify current arena entry and existing candidate reliability before allocating more serving GPUs.
3. Run the smallest useful PokerBench SFT pilot as soon as capacity permits; avoid full 80k training before proving target format and live poker behavior.
4. Keep training, selection, and final evaluation separate; prioritize valid actions and official-game placement over training loss or imitation accuracy.

## Update — 00:30 PST

- GRPO main job reserves 6 GPUs. Its configured in-run evaluation sidecar requires another 2; two serving deployments bring peak demand to the full 10-GPU allocation. Additional SFT must be scheduled after RL or an evidence-based reallocation.
- Incumbent confirmed: `return of rain man`, serving `combined-sft-v3`, checkpoint `ckpt_51eee61470f7`, iteration 39 of `train_87b51a9211a1`. Direct paired-game evaluation preparation is active; platform evaluations will also be used where efficient.
- PokerBench upload resolved to dataset `pokerbench-unified-20k`, 19,992 unique tasks. Existing targets omit the known necessary nonempty reasoning boundary, and conversion rounds fractional amounts. These datasets will not be trained unchanged. A corrected, versioned dataset with grouped deduplication/splits and exact amount representation is being prepared.
- Durable read-only observer started (`/tmp/pokerbots-coordinator-watch.py`, PID 83159), polling AC2 jobs/deployments/training every 60 seconds until 09:00 PST. Snapshot: `overnight-status.json`; log: `/tmp/pokerbots-coordinator-watch.log`. Coordinator and RL agent handle triage; observer itself does not stop jobs.

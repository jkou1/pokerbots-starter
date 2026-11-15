# PokerBench V4: consistent-only CPU preparation

Versioned TRAIN/SELECT uploads are verified. Root authorized exactly one pilot: `train_3c45262ddf1f` / `job_a0a8857c71e4`, starting from old SFT ad74. Its environment boot passed; optimizer and managed-target evidence are tracked separately in `monitor-state.json`. No stale40-step configuration is used.

Retain only source rows whose canonical six-seat monetary replay starts with1200chips (600BB), blinds1/2, preserves nonnegative individual stacks, and reproduces the printed current pot exactly. Existing focused target-action bounds must also pass. This is monetary replay, not complete engine action-order/deck legality. No labels or text are repaired.

Counts:1060PokerBench TRAIN and41SELECT. FINAL remains sealed; the manifest reports only counts and hashes, with unsupported labels quarantined. Solver labels remain cash-game demonstrations rather than tournament-optimal actions. Source scenarios have no real match IDs; source board/betting group splits remain unchanged.

The separate preflop anchor set has387genuine public-teacher TRAIN examples across80matches, after excluding all six source matches overlapping the newer mixed-teacher holdouts. It is also disjoint from the older Pete selection/final by whole match. Optional three-copy TRAIN weighting gives1161anchor samples plus1060postflop samples:2221weighted samples,1447unique observations,52.27%preflop. Only sampling-copy metadata in `env_params` distinguishes copies; model inputs, original labels, tools and provenance remain unchanged.

The nonempty assistant marker is an explicit protocol scaffold, not claimed solver reasoning or private memory. There are no cleanup targets: protocol/memory retention risk remains. The authorized pilot has hard10updates, checkpoints5/10, LR1e-6,batch64,4trainingGPUs and zero rollout/eval engines. Weights-only saves retain2checkpoints. No automatic extension or deployment is authorized. Its startup itself is the clean ad74 warm-start control; no separate control job exists.

`prepare.py` rebuilds deterministic local exports; `verify.py` checks unchanged original inputs/labels/tools and official-template thinking/tool boundaries. Private/full JSONL exports are ignored. `manifest.json` and `boundary-audit.json` provide compact evidence. Remote membership and sampled payloads are verified in `upload-receipt.json`. The manifest records the original CPU-build stage; current operational status is in `run.json` and `monitor-state.json`.

Final provenance correction: one original V4FINAL row belongs to a scenario group accidentally exposed by a source search. Keep the original file/hash unchanged, but exclude both identified source scenario groups from every future V4/V5final validation using `../pokerbench-pot-semantics-audit/future-final-exclusions.json`.388V4rows across291groups remain unexposed. No FINAL model calls occurred.

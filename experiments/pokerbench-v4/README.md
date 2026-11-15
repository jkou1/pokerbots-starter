# PokerBench V4: consistent-only CPU preparation

This dataset is prepared, not uploaded or trained. No stale40-step configuration is included.

Retain only source rows whose canonical six-seat monetary replay starts with1200chips (600BB), blinds1/2, preserves nonnegative individual stacks, and reproduces the printed current pot exactly. Existing focused target-action bounds must also pass. This is monetary replay, not complete engine action-order/deck legality. No labels or text are repaired.

Counts:1060PokerBench TRAIN and41SELECT. FINAL remains sealed; the manifest reports only counts and hashes, with unsupported labels quarantined. Solver labels remain cash-game demonstrations rather than tournament-optimal actions. Source scenarios have no real match IDs; source board/betting group splits remain unchanged.

The separate preflop anchor set has387genuine public-teacher TRAIN examples across80matches, after excluding all six source matches overlapping the newer mixed-teacher holdouts. It is also disjoint from the older Pete selection/final by whole match. Optional three-copy TRAIN weighting gives1161anchor samples plus1060postflop samples:2221weighted samples,1447unique observations,52.27%preflop. Only sampling-copy metadata in `env_params` distinguishes copies; model inputs, original labels, tools and provenance remain unchanged.

The nonempty assistant marker is an explicit protocol scaffold, not claimed solver reasoning or private memory. There are no cleanup targets: protocol/memory retention risk remains. Before any eventual training, root must choose a proven viable parent and separately approve upload/configuration. Prospective five-update training is not authorized here.

`prepare.py` rebuilds deterministic local exports; `verify.py` checks unchanged original inputs/labels/tools and official-template thinking/tool boundaries. Private/full JSONL exports are ignored. `manifest.json` and `boundary-audit.json` provide compact evidence. Remote membership checks will be required after any separately approved versioned upload.

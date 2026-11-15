# V5 coverage and rounded-pot knowledge pilot

One root-authorized actual run: `train_091b190911a9` / `job_984ecfb21123`, old SFT ad74 parent,20updates maximum,LR2e-6,batch64,checkpoints10/20,weights-onlykeep2,4trainingGPUs and zero rollout/eval engines. No automatic extension, retry or promotion.

Verified remote TRAIN `ds_a089002ee0cd`:7369weighted/3886unique observations. SELECT `ds_a4a86c864cb6`:136cases. Full membership and sampled payloads match local tasks.3499postflop examples combine1060unchanged consistent rows and2439off-one rows with only the printed pot reconciled from decision-time contributions.387heldout-safe preflop anchors are sampled10times. Labels remain provider labels from rounded source inputs; corrected-state optimality is uncertain. Larger597TRAIN mismatches remain excluded.

Frozen parent reference:80/136exact,alllegal,0/35bets+raises. Prospective numerical gates are in `frozen-gates.json`; original41subset is reported separately. Only95new parent calls were needed after proving exact wire/input/checkpoint/decoding equivalence for the reused41cases. Unchanged354preflop and10cleanupstress references are reused. These are LOCAL imitation/retention/protocol diagnostics, not native Eval runs or poker EV.

The independent TRAIN-only money audit confirms declared1200chips under full-hand replay and explicitly inclusive preflop pots; neither double-count current bets nor reset stacks across streets. The postflop prompts do not display current remaining stacks explicitly. Cash-game/provider-label semantics remain a transfer limitation.

Original source scenarios and splits remain fixed. No FINAL content is read, uploaded or model-queried here; all future final validation must honor the exposed-group exclusion manifest from the prior source-search incident. Original final files and hashes remain unchanged.

`monitor-state.json` and `managed-source-target-audit.json` distinguish consistent/reconciled/pre sources and actual masks/targets/CE. `source_failure_guard.py` stops only this pilot on confirmed source/mask/nonfinite failure, with no retry. Infrastructure/save-failure/final-teardown monitoring is separately owned by ops.

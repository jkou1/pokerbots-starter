# Public failure miner

CPU-only, public-HTTP miner for execution failures in our entry, Professor Pete, and Accord. It follows actual team-page listing links, retrieves only the latest bounded samples, follows each replay's actual Raw JSON link, and reuses hash-validated local archives. The detached poller stops at `2026-11-15T17:00:00Z` (09:00 PST).

Run with the verified runtime:

```bash
PYTHONPATH=/Users/lance/Documents/pokerbots-main/harness/src:/Users/lance/Documents/pokerbots-main \
  /Users/lance/Documents/pokerbots-starter/harness/.venv/bin/python \
  experiments/public-failure-miner-v1/miner.py once
```

Run focused tests from this directory with the same `PYTHONPATH`:

```bash
/Users/lance/Documents/pokerbots-starter/harness/.venv/bin/python -m unittest -v test_miner.py
```

## Reporting contract

- `current_entry` is the only own-team current incident aggregate. It filters exact published submission name, deployment ID/version, checkpoint, and model metadata from the latest complete own match. If that metadata is unavailable, the code uses an explicitly labeled two-hour fallback window and records its limitation.
- `aggregate` is all-history, includes earlier broken deployments, and is not current-entry regression evidence.
- `current_entry_regression_examples.jsonl` contains only deduplicated current-entry incidents. `regression_examples.jsonl` retains all history.
- `unique_affected_actions` counts each match/hand/action once. Category tags such as `explicit_engine_error` overlap and are non-additive.
- `forced_fold_fallback` uses published fallback/executed-fold fields. `legal_executed_coercion` uses published `coerced=true`, `fallback=false`; it describes engine handling, not optimal play.
- Fresh listing coverage is first-page-only. Historical coverage comes from the explicitly listed local manifests.
- Private scratchpads, cleanup, private reasoning, and optimal-action labels are unsupported. No student inputs or handwritten poker evaluator are produced.

Runtime raws, listings, logs, PID files, snapshots, and generated findings are intentionally ignored by Git. Coordinator status is `/tmp/pokerbots-public-failure-status.json`.

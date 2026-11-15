# Arena performance history

Public replay archive for **The Evaluators**, entry `org_cd68943dd947`.
Source: <https://www.pokerbots.ac/matches?entry=org_cd68943dd947>.

Snapshot completed **2026-11-15 05:56 UTC**. Both discovery passes traversed all
four listing pages and found the same **78 completed ranked matches**. Every
listed replay's Raw JSON file was downloaded successfully. This is a snapshot
of all matches exposed by the entry-filtered history at collection time, not a
subscription to future matches.

## Contents

| Path | Contents |
| --- | --- |
| `raw/*.json` | 78 original, byte-preserved arena JSON downloads, including every seat's actions and results |
| `listings/*.html` | Both complete passes of the paginated match listings, for coverage evidence |
| `manifest.json` | Replay and raw download URLs, collection times, SHA-256 hashes, byte lengths, target seats, and deployment metadata |
| `matches.jsonl` | 78 target-agent match results, with submission/checkpoint identity |
| `hands.jsonl` | 2,031 hands in which the target agent was dealt in, with its cards, stacks, board, and outcome |
| `decisions.jsonl` | 3,604 target-agent actions, with original action fields, cards, hand number, and action index |
| `summary.json` | Overall performance, placement distribution, action errors, and breakdowns by submission and match kind |
| `crawl.py` | Reproducible standard-library crawler and dataset builder |
| `verify.py` | Offline coverage, hash, identity, count, chip-accounting, and derivation checks |
| `analysis/REPORT.md` | Success/failure mining with 1,000-trial eval7 Monte Carlo equity, examples, and methodology |
| `analysis/decision_equity.jsonl` | Oracle and uniform-opponent equity estimates for all 3,604 target decisions |
| `analyze_equity.py`, `verify_equity.py` | Reproduce and validate the equity analysis; dependencies in `analysis-requirements.txt` |

`action_index` is zero-based within the raw hand's full `actions` array, including
opponent actions. Join on `match_id` and `hand_number` to recover the full hand.
The normalized files retain errors and unsuccessful actions; nothing is silently
filtered out. All opponent data remains available in the raw archive.

## Performance in this snapshot

The entry changed deployments during its history; these are two different
submissions, rather than one fixed set of model weights.

| Submission | Matches | Agent hands | Decisions | Wins | Net BB | EV net BB | BB/100 | EV BB/100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rain man | 33 | 793 | 1,426 | 4 | -665.0 | -415.475 | -83.86 | -52.39 |
| step2 | 45 | 1,238 | 2,178 | 11 | +1,636.5 | +1,212.425 | +132.19 | +97.93 |
| Combined | 78 | 2,031 | 3,604 | 15 | +971.5 | +796.950 | +47.83 | +39.24 |

`step2` uses checkpoint `ckpt_012f74ea70f9` on deployment `infer_dd8c2952bf59`.
`rain man` uses deployment `infer_576c834b176a`, with no checkpoint ID recorded.
The archive contains 59 target actions flagged as format errors/fallbacks/AFK,
20 flagged as hitting the token cap, and 14 coerced actions. Flags overlap.

BB/100 is `100 * sum(net_bb) / sum(result.hands)`; EV BB/100 uses the arena's
`ev_net_bb` field. Hands count the agent's participation, stopping when it busts.
These are descriptive arena results against changing opponents and deals;
the submission breakdown is not a controlled paired evaluation.

## Using this for SFT

These are replay observations and actions, not original prompt/completion traces.
The public JSON includes tool arguments, table talk, token counts, latency, and
failure flags, but not full private reasoning or scratchpad text. No missing
reasoning or prompts have been fabricated.

Raw files expose retrospective information, including opponents' hole cards and
future board cards. `hands.jsonl` also includes the final board and outcome.
When constructing model inputs, reconstruct only information available before
the target action: its own cards, the current board, and preceding public actions.
An action's `stack_after`, `chip_change`, tool arguments, and error flags describe
the output/result, not additional information available beforehand. Filter or
review failed/coerced decisions before using them as training targets. Split by
match to avoid putting different decisions from one game in both train and eval.

## Reproduce

No API key, browser session, or third-party Python package is required.

```bash
python3 history/crawl.py
python3 history/verify.py
```

The crawler follows every pagination link for the entry, visits each replay,
extracts the linked Raw JSON URL, and downloads with four workers and bounded
retries. A second listing pass catches new matches or pagination shifts during
collection. Match IDs are deduplicated; downloads must identify the requested
match and contain exactly one seat for the entry. Failures are recorded in the
manifest and make the command exit unsuccessfully.

Rerunning replaces the snapshot's manifest and derived files. Existing raw files
are retained; the verifier rejects extra files absent from the new manifest.
For another entry, use a separate copy of the archive directory and pass
`--entry <entry-id>`. Update the snapshot statistics above after refreshing.

# GRPO from historical stack scenarios

`make_history_dataset.py` builds **20,000 training tasks** and uploads them to
AC2 project `vals-hackathon`, with separate selection, final evaluation and smoke
datasets. Each task plays a new single hand of six-seat poker through the custom
harness, starting from real historical **pre-blind stacks, button, and blinds**.
The deck is freshly seeded. It does not replay historical hole cards, boards,
betting actions, private notes, or outcomes, and it does not resume a mid-hand
decision.

## Uploaded datasets

| Dataset | Tasks | Source matches | Available source hand starts |
| --- | ---: | ---: | ---: |
| `pokerbots-history-20k-v1-train` | 20,000 | 60 | 895 |
| `pokerbots-history-20k-v1-select` | 500 | 8 | 119 |
| `pokerbots-history-20k-v1-eval` | 1,000 | 8 | 82 |
| `pokerbots-history-20k-v1-smoke` | 8 | 2 | 30 |

The source archive has 1,126 eligible six-active-player hand starts. Whole source
matches are deterministically partitioned before sampling; no source match
appears in two splits. All 21,508 task seeds are globally distinct. Generic
stack shapes, notably the initial equal-100-BB table, can occur in different
source matches and therefore in different splits. These are source-match and
deal-seed holdouts, not a guarantee of unseen stack-vector shapes.

Exact task payloads, SHA-256 hashes, split membership and distribution statistics
are committed under `history/training/pokerbots-history-20k-v1/`. `upload.json`
contains remote dataset IDs, every uploaded task ID, verified membership counts,
and the sample indices whose content was fetched back from AC2 and compared.

## Stack variety and repetition

The 20,000 training tasks use **895 real source hands and 825 distinct six-seat
stack vectors**, with fresh seeds and different policy seats. They are not
20,000 independently scraped scenarios. Source vectors are neither rescaled nor
rotated; the original seat balances and button are retained.

Sampling cycles policy seats evenly (3,333 or 3,334 tasks per seat), reserves
approximately 10% for equal-stack profiles, and cycles available effective-stack
buckets separately for each seat among nonuniform profiles. It then samples a
real source candidate within that bucket. In this snapshot:

| Training effective-stack bucket | Tasks | Available distinct source hand/seat pairs |
| --- | ---: | ---: |
| Up to 10 BB | 1,800 | 8 |
| Above 10 through 25 BB | 4,050 | 73 |
| Above 25 through 50 BB | 4,050 | 285 |
| Above 50 through 100 BB | 6,054 | 3,283 |
| Above 100 through 200 BB | 4,046 | 1,720 |
| Above 200 BB | 0 | 0 |

Here **effective stack** means `min(policy stack, largest opponent stack)` in BB;
it describes the deepest opponent the policy can play against, not every
opponent's separate effective stack or the size of every side pot.

Training hero stacks range **1–296 BB** (median 55.5 BB); effective stacks range
**1–167.5 BB**. There are 17,996 nonuniform-stack tasks and 2,004 uniform-stack
tasks. Short-stack profiles are scarce, so those eight <=10-BB source hand/seat
pairs are intentionally repeated with many new deals. The manifest records
available and actually sampled unique candidate counts for every bucket.

A policy seat whose source stack is already exhausted by its mandatory blind is
excluded, because it would generate no betting decision tokens. One training
source hand/seat candidate was excluded on that basis. Opponent seats may be
blind-all-in; the engine handles their participation and side pots normally.

## Task contract

```json
{
  "preset": "event",
  "seats": 6,
  "total_hands": 1,
  "reset_stacks": false,
  "starting_stacks": [75, 190, 410, 205, 110, 210],
  "button_seat": 3,
  "small_blind": 1,
  "big_blind": 2,
  "seed": 123456789,
  "policy_seats": [2],
  "opponent_model": "vals-hackathon/ac-vals-model",
  "opponent_timeout_seconds": 60,
  "submit_fields": ["action", "amount"],
  "ev_labels": true,
  "ev_runouts": 64
}
```

This is a schema illustration, not a claim that the illustrated stack vector was
scraped. Actual task JSONL contains only exact observed stack vectors, plus
`history_source` IDs and the raw file hash. The initial input is simply the
instruction to play the hand from the policy seat; the harness constructs each
decision's actual state. No historical hidden cards or future actions reach the
policy or opponent prompts.

The five opponents share the supplied `ac-vals-model` deployment. Varying stack
sizes does not change the existing grader: its reward still clips hand EV at
**-5/+5 BB** before adding the reward offset, and format failures receive zero.
Consequently a large-stack win is not rewarded linearly across its whole size.

## Rebuild, upload, and train

From the repository root, using the SDK environment:

```bash
uv run python rl/make_history_dataset.py
uv run python rl/make_history_dataset.py --upload
uv run pytest -q tests/test_history_dataset.py
```

Building is deterministic and writes local exports. Upload refuses to append to
pre-existing dataset names unless their IDs and payload hashes match this
directory's own upload receipt. Exact-payload retries reuse content-addressed
task IDs; interrupted uploads resume after checking the recorded membership
prefix and retry transient transport, HTTP 429 and server errors with bounded
backoff. Permanent authorization/schema errors propagate. Final verification compares the full remote membership and retrieves
the first, middle and last task of each dataset. Use a new `--prefix` when
changing task generation or source data; do not reuse these versioned names for
a changed payload.

Start the harness from this branch and connect it to AC2 before evaluating or
training; the old harness does not understand the new stack/button settings.
Then inspect the training launch:

```bash
uv run python rl/train.py --prefix pokerbots-history-20k-v1 --dry-run
```

Removing `--dry-run` launches training. No training job is started by the dataset
builder. The launcher automatically uses the matching `-train` and `-select`
datasets; standalone held-out evaluation uses `-eval`.

The existing 60-step recipe samples 16 task groups per step, or **960 groups**,
not a full pass through 20,000 tasks. Each group has 16 rollout attempts. A
nominal full sweep at 16 groups per step would require 1,250 steps and roughly
320,000 sampled hands, before evaluation/retries. Choose run length and
concurrency separately; this change does not silently increase training spend.

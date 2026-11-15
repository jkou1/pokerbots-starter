# Combining starter scenarios and live Arena demonstrations

The starter repository supplies poker tasks, a game engine, reward code, and a prompt-distillation recipe. It does **not** supply an expert action corpus. `vals_tools/tasks.py` creates 2,000 training hands, 500 selection hands, 3,000 evaluation hands, four smoke hands, and two three-hand table smoke tasks. These tasks specify seeds, seats, opponents, and rules, rather than correct poker actions. The `prettygoodpoker/upload_dataset.py` file contains two generic setup examples (arithmetic and geography); neither belongs in poker SFT.

Directly mixing unanswered poker tasks with labeled Pete actions would conflate SFT and RL. Instead, use the starter training deals to generate a separate replay source with verified legal actions. Keep starter selection/evaluation deals reserved for testing. Reward-based training on the starter scenarios remains a later stage.

## Data releases and controls

| Source | Qualified matches | Train decisions | Selection decisions | Final evaluation decisions |
| --- | ---: | ---: | ---: | ---: |
| Original Pete archive | 130 | 1,328 | 174 | 96 |
| Live refresh, cutoff 2026-11-15 05:57:37 UTC | 186 | 1,701 | 174 | 158 |

The refresh downloaded every discovered completed match before its cutoff, with no failed downloads, duplicate deals, or replay quarantines. The original 174-example selection file is byte-identical in the refresh. The refreshed training deals have no overlap with the original selection or final evaluation deals. Keep the original 96 final examples fixed for comparisons with the first run; the extra 62 evaluation examples remain held out too.

Public matches are collected through their linked Raw JSON files from [the Arena archive](https://www.pokerbots.ac/matches). Teacher identity is `house-professor-pete`. Decision-time observations exclude opponents' cards, future actions, and outcomes. Public data does not include Pete's private scratchpad. These are behavioral demonstrations, not proven optimal actions.

The refreshed archive contains 72 matches with Pete. In addition to the 2,033 pre-flop decisions, its raw records contain 507 flop, 326 turn, and 237 river decisions (1,070 post-flop decisions). These have consistent tool arguments and no recorded failure flags. All matches passed full-hand engine replay, but post-flop observations have not yet been exported into a teacher-training corpus. The current pilot deliberately leaves these unused. A subsequent post-flop imitation experiment can use them with the same match/deal splits and decision-time information checks; compare it separately before replacing the betting policy.

Release manifests, unchanged raw source JSON, hashes, and quality reports remain in ignored `data/arena/` and `data/arena-live-v2/` directories. Keep credentials and experiment logs out of version control.

## Controlled combined-data pilot

The first combined run, `train_ab817f9de7c1`, was stopped after the Pete-only model failed all 174 official-format decisions. Both used empty reasoning targets with a single-/double-newline mismatch at the reasoning boundary. The corrected run, `train_87b51a9211a1`, uses dataset `pokerbots-combined-base-sft-v3-train`, the same 2,268 source records plus an explicit synthetic protocol marker, verified as 2,268 unique task contents. Its receipt is `data/experiments/combined-base-sft-fixed/run.json`. It starts from base weights independently; the failed weights are not a parent. Evaluation is pending. See [PETE_SFT.md](PETE_SFT.md) for the reproduced failure.

Start a fresh model from the same base Qwen weights. Mix approximately:

- 75% Pete pre-flop action/amount targets from the refreshed training split.
- 18.75% legal base-model post-flop actions on the starter's training deals.
- 6.25% factual after-hand scratchpad updates reconstructed from those same training games.

Generate replay on the first 48 original starter training deals, cycling through the six policy seats. Scripted opponents from the repository make replay collection inexpensive and produce varied betting situations. They are legality/coverage controls, not evidence of success against strong opponents. Base replay is a preservation target, not a second expert teacher. No base pre-flop actions dilute Pete's pre-flop labels.

The mixture samples replay with replacement to meet the requested proportions and records both unique source coverage and sampled counts. Sampling metadata stays outside the prompt and keeps repeated examples distinct in the content-addressed dataset service. The manifest reports target characters by tool because longer cleanup targets can contribute disproportionately to token loss.

Actual coverage in this pilot is 19 distinct post-flop decisions and 48 factual cleanup records from 48 deals, sampled into 426 post-flop and 141 cleanup targets alongside the 1,701 Pete targets. Repeated samples do not add new information. This is a small retention experiment; it does not exhaust the starter's 2,000 training scenarios or establish broad post-flop coverage. The raw target arguments contain 44,464 action characters and 58,714 cleanup characters; inspect rendered target-token lengths as well as example counts when judging optimization balance.

Use the same 40-update budget, batch 64, maximum learning rate `5e-6`, context 8,192, seed 42, and checkpoint interval 20 as the Pete-only run. Equal update budgets mean fewer Pete examples per update in the mixture. This pilot changes data freshness and replay together; any improvement cannot establish which change caused it. A subsequent refreshed-Pete-only control can isolate replay's effect if the pilot is promising.

```bash
uv run python -m vals_tools.arena collect --root data/arena-live-v2
uv run python -m vals_tools.pete --root data/arena-live-v2
uv run python -m vals_tools.collect_policy \
  --model vals-hackathon/base --seed-source starter --opponent scripted \
  --hands 48 --concurrency 8 --out data/experiments/starter-base-scripted-replay
uv run python -m vals_tools.export_policy \
  --logs data/experiments/starter-base-scripted-replay/logs \
  --model vals-hackathon/base --street replay --out data/experiments/starter-replay
uv run python -m vals_tools.combined \
  --teacher data/arena-live-v2/pete-preflop/train.jsonl \
  --replay data/experiments/starter-replay/train.jsonl \
  --out data/experiments/combined-base-sft-fixed/dataset
uv run python -m vals_tools.sft --stage combined --from-base \
  --records data/experiments/combined-base-sft-fixed/dataset/train.jsonl \
  --dataset pokerbots-combined-base-sft-v3-train \
  --steps 40 --batch 64 --checkpoint-every 20 --lr 5e-6 --max-total-len 8192 \
  --receipt data/experiments/combined-base-sft-fixed/run.json --launch
```

## Evaluation, repository push, and Arena entry

Compare base, Pete-only, and combined checkpoints against the same original 174 selection decisions with identical tool schemas and decoding. Report teacher action agreement, exact sizing agreement, macro action recall, and legal rate. `vals_tools.compare_pete` verifies matching provenance and computes a paired action-accuracy interval by resampling whole source matches. Only seven matches contribute to this selection set; teacher imitation is not poker win rate.

The user initially conditioned a repository push on an evaluation improvement, then explicitly requested committing and pushing the implementation first. Preserve the failed evaluation and pending status honestly in the committed documentation. Keep the user's unrelated `test.md` modification out of that commit. No loss-only or training-set result establishes a model-quality improvement.

Before deployment, `vals_tools.sft_audit --train <run-id> --out <artifact.json>` checks actual managed-trainer token samples for a single-newline target prefix, the synthetic protocol marker, and a supervised `</think>` before the tool call. A tool-call string inside reasoning never counts as a valid action; retain the official parser. The first 20-update checkpoint can be evaluated while the 40-update budget completes; later checkpoints need their own comparison before replacing a selected deployment.

Deploy the combined checkpoint for the requested Arena experiment after checking it serves real tool calls and completes a local event-rule smoke game. Arena results then provide live evidence; a local teacher-imitation gain alone does not establish stronger tournament performance. Inference deployment and Arena registration are separate operations. Only claim Arena entry after the console or an authenticated submission response confirms it.

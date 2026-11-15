"""Export successful talk targets on official observations, without fixed-action helpers.

Requires matched silence controls and positive game-level bootstrap evidence across seeds.
"""

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

from vals_tools.arena import write_json, write_jsonl
from vals_tools.export_policy import policy_records
from vals_tools.game_score import bootstrap
from vals_tools.pete import split_for


def integration_records(experiments):
    by_seed = defaultdict(dict)
    for result in experiments:
        if result.get("status") != "complete":
            continue
        seed = result["seed"]
        if split_for(str(seed)) != "select":
            continue  # message selection must never use training or final-evaluation outcomes
        if seed in by_seed:
            raise ValueError(
                "duplicate experiment seed; combine repetitions in one experiment"
            )
        groups = defaultdict(list)
        for game in result["games"]:
            if game["format_errors"] == 0:
                groups[game["message"]].append(game["realized_bb"])
        if "" not in groups:
            continue
        silence = statistics.fmean(groups[""])
        by_seed[seed] = {
            message: statistics.fmean(values) - silence
            for message, values in groups.items()
            if message
        }
    messages = sorted({message for group in by_seed.values() for message in group})
    evidence = {}
    for message in messages:
        diffs = [group[message] for group in by_seed.values() if message in group]
        interval = bootstrap(diffs)
        evidence[message] = {
            "seeds": len(diffs),
            "mean_incremental_bb": statistics.fmean(diffs),
            "ci95": interval,
            "accepted": interval[0] is not None and interval[0] > 0,
        }
    rows = []
    for experiment in experiments:
        if experiment.get("status") != "complete":
            continue
        for game in experiment["games"]:
            if (
                not evidence.get(game["message"], {}).get("accepted")
                or game["format_errors"]
            ):
                continue
            seat = experiment["policy_seat"]
            for row in policy_records(
                game["log"], seat, experiment.get("model", "frozen-policy")
            ):
                if row["provenance"]["street"] not in ("flop", "turn", "river"):
                    continue
                row["target"]["say"] = game["message"]
                row["provenance"]["message_evidence"] = evidence[game["message"]]
                rows.append(row)
                break  # first post-flop policy decision is the nominated intervention
    return rows, evidence


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--experiments", type=Path, nargs="+", required=True)
    p.add_argument("--out", type=Path, default=Path("data/experiments/integration"))
    args = p.parse_args()
    rows, evidence = integration_records(
        [json.loads(path.read_text()) for path in args.experiments]
    )
    for split in ("train", "select", "eval"):
        write_jsonl(
            args.out / f"{split}.jsonl", [r for r in rows if r["split"] == split]
        )
    write_json(args.out / "evidence.json", evidence)
    print(
        json.dumps(
            {
                "records": len(rows),
                "accepted_messages": sum(e["accepted"] for e in evidence.values()),
            }
        )
    )


if __name__ == "__main__":
    main()

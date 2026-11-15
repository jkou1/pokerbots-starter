"""Build a source-audited SFT mixture: Pete preflop plus starter-deal policy replay.

Replay preserves post-flop behavior and factual cleanup; it is not an expert label.
All records must already have passed their source-specific replay validation.
"""

import argparse
import copy
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

from ac2.runtime import compute_content_hash

from vals_tools.arena import read_jsonl, write_json, write_jsonl
from vals_tools.collect_policy import deal_seeds
from vals_tools.training import supervised_task


def mixture(teacher, replay, teacher_fraction=0.75):
    if not 0 < teacher_fraction < 1 or not teacher or not replay:
        raise ValueError(
            "nonempty sources and a teacher fraction between zero and one are required"
        )
    if any(row.get("split") != "train" for row in teacher + replay):
        raise ValueError("combined training refuses held-out records")
    if any(
        row.get("provenance", {}).get("teacher") != "house-professor-pete"
        or row["provenance"].get("street") != "preflop"
        for row in teacher
    ):
        raise ValueError("teacher source must contain Pete preflop demonstrations only")
    original_seeds = set(deal_seeds("train", 2000, "starter"))
    groups = {"postflop": [], "cleanup": []}
    for row in replay:
        provenance = row.get("provenance", {})
        if provenance.get("seed") not in original_seeds:
            raise ValueError(
                "replay must come from the original starter training deals"
            )
        street = provenance.get("street")
        if (
            street in ("flop", "turn", "river")
            and row.get("tool", "submit_action") == "submit_action"
        ):
            groups["postflop"].append(row)
        elif street == "cleanup" and row.get("tool") == "update_scratchpad":
            groups["cleanup"].append(row)
        else:
            raise ValueError(
                "replay must contain postflop decisions or factual cleanup only"
            )
    if any(not rows for rows in groups.values()):
        raise ValueError("both postflop and cleanup replay coverage are required")
    rng = random.Random(42)
    result = copy.deepcopy(teacher)
    count = round(len(teacher) * (1 - teacher_fraction) / teacher_fraction)
    for i in range(count):
        group = "cleanup" if i % 4 == 3 else "postflop"
        row = copy.deepcopy(rng.choice(groups[group]))
        row["sampling_copy"] = f"combined-{group}-{i}"
        result.append(row)
    rng.shuffle(result)
    hashes = [compute_content_hash(supervised_task(row)) for row in result]
    if len(set(hashes)) != len(hashes):
        raise ValueError(
            "duplicate task contents would change the requested source weights"
        )
    return result, {
        "teacher_examples": len(teacher),
        "replay_unique_examples": {k: len(v) for k, v in groups.items()},
        "replay_sampled_examples": count,
        "replay_distinct_seeds": len({r["provenance"]["seed"] for r in replay}),
        "actual_teacher_fraction": len(teacher) / len(result),
        "total_examples": len(result),
        "unique_uploaded_tasks": len(set(hashes)),
        "by_street": dict(Counter(r["provenance"]["street"] for r in result)),
        "target_characters_by_tool": {
            tool: sum(
                len(json.dumps(r["target"]))
                for r in result
                if r.get("tool", "submit_action") == tool
            )
            for tool in ("submit_action", "update_scratchpad")
        },
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--teacher", type=Path, required=True)
    p.add_argument("--replay", type=Path, required=True)
    p.add_argument("--teacher-fraction", type=float, default=0.75)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    rows, report = mixture(
        read_jsonl(args.teacher), read_jsonl(args.replay), args.teacher_fraction
    )
    report["sources"] = {
        key: {
            "path": str(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for key, path in (("teacher", args.teacher), ("replay", args.replay))
    }
    write_jsonl(args.out / "train.jsonl", rows)
    write_json(args.out / "mixture.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

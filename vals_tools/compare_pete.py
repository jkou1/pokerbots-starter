"""Paired teacher-imitation comparison, with uncertainty clustered by source match."""

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from vals_tools.arena import write_json
from vals_tools.pete_eval import heldout_rows, imitation_metrics


def compare(rows, baseline, candidate):
    for run in (baseline, candidate):
        if run.get("status") != "complete" or len(run.get("results", [])) != len(rows):
            raise ValueError(
                "both evaluations must be complete on every held-out example"
            )
        if any(
            result.get("provenance") != row["provenance"]
            for row, result in zip(rows, run["results"], strict=True)
        ):
            raise ValueError(
                "evaluation provenance/order differs from the fixed held-out set"
            )
    predictions = [
        [r["action"] for r in run["results"]] for run in (baseline, candidate)
    ]
    metrics = [imitation_metrics(rows, p) for p in predictions]
    keys = (
        "action_accuracy",
        "exact_action_amount_accuracy",
        "macro_action_recall",
        "legal_rate",
    )
    groups = defaultdict(list)
    for i, row in enumerate(rows):
        groups[row["provenance"]["match_id"]].append(i)
    rng = random.Random(42)
    ids = sorted(groups)
    deltas = []
    if len(ids) > 1:
        for _ in range(2000):
            indices = [
                i for group in rng.choices(ids, k=len(ids)) for i in groups[group]
            ]
            sampled = [rows[i] for i in indices]
            scores = [
                imitation_metrics(sampled, [p[i] for i in indices]) for p in predictions
            ]
            deltas.append(scores[1]["action_accuracy"] - scores[0]["action_accuracy"])
    deltas.sort()
    return {
        "baseline_model": baseline["model"],
        "candidate_model": candidate["model"],
        "examples": len(rows),
        "source_matches": len(groups),
        "baseline": metrics[0],
        "candidate": metrics[1],
        "candidate_minus_baseline": {k: metrics[1][k] - metrics[0][k] for k in keys},
        "action_accuracy_delta_match_bootstrap_ci95": [deltas[50], deltas[1950]]
        if deltas
        else [None, None],
        "scope": "held-out teacher imitation; not poker win rate",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--records", type=Path, default=Path("data/arena/pete-preflop/select.jsonl")
    )
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = compare(
        heldout_rows(args.records),
        json.loads(args.baseline.read_text()),
        json.loads(args.candidate.read_text()),
    )
    write_json(args.out, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

"""Whole-game placement comparisons from harness logs; paired bootstrap by deal/seat."""

import argparse
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path


def bootstrap(values, samples=2000):
    if len(values) < 2:
        return [None, None]
    rng = random.Random(42)
    means = sorted(
        statistics.fmean(rng.choices(values, k=len(values))) for _ in range(samples)
    )
    return [means[int(samples * 0.025)], means[int(samples * 0.975)]]


def cluster_bootstrap(values, clusters, samples=2000):
    groups = defaultdict(list)
    for value, key in zip(values, clusters, strict=True):
        groups[key].append(value)
    if len(groups) < 2:
        return [None, None]
    rng = random.Random(42)
    keys = list(groups)
    means = sorted(
        statistics.fmean(
            v for key in rng.choices(keys, k=len(keys)) for v in groups[key]
        )
        for _ in range(samples)
    )
    return [means[int(samples * 0.025)], means[int(samples * 0.975)]]


def game_rows(directory, seat=None, expected=None):
    rows = {}
    for path in sorted(Path(directory).glob("*.json")):
        log = json.loads(path.read_text())
        if not log.get("complete") or "ranking" not in log:
            continue
        policy = log.get("policy_seats", [])
        chosen = (
            seat
            if seat is not None
            else int(policy[0].removeprefix("seat"))
            if len(policy) == 1
            else None
        )
        if chosen is None:
            raise ValueError(
                "pass --seat when logs do not identify exactly one policy seat"
            )
        evaluation = log.get("evaluation", {})
        if expected is not None and evaluation.get("plan_sha256") != expected:
            raise ValueError("game does not belong to the frozen evaluation plan")
        key = (
            log["session_info"]["seed"],
            chosen,
            log.get("opponent_model"),
            evaluation.get("opponent_fingerprint"),
            evaluation.get("repeat", 0),
            evaluation.get("plan_sha256"),
        )
        if key in rows:
            raise ValueError(
                "duplicate game seed/seat; isolate each evaluation's log directory"
            )
        name = f"seat{chosen}"
        cleanup = [
            h["cleanup"]
            for h in log.get("private", {}).get(name, {}).get("hands", {}).values()
            if "cleanup" in h
        ]
        expected_cleanup = sum(
            name in h.get("starting_state", {}) for h in log["hands"]
        )
        rows[key] = {
            "place": log["ranking"]["places"][name],
            "busted": name in log.get("eliminated_on_hand", {}),
            "bb": (
                log["final_stacks"][name]
                - log["session_info"]["starting_stacks"][chosen]
            )
            / log["session_info"]["big_blind"],
            "errors": sum(
                bool(a["model_response"].get("format_error"))
                for h in log["hands"]
                for a in h["actions"]
                if a["player"] == name
            ),
            "decisions": sum(
                a["player"] == name for h in log["hands"] for a in h["actions"]
            ),
            "opponent_errors": sum(
                bool(a["model_response"].get("format_error"))
                for h in log["hands"]
                for a in h["actions"]
                if a["player"] != name
            ),
            "cleanup_failures": max(0, expected_cleanup - len(cleanup))
            + sum(c.get("result") != "updated" for c in cleanup),
            "outgoing_messages": sum(
                bool(a.get("say"))
                for h in log["hands"]
                for a in h["actions"]
                if a["player"] == name
            ),
        }
    return rows


def summarize_games(rows, parent=None):
    if not rows:
        raise ValueError("no complete official games")
    result = {
        "games": len(rows),
        "mean_placement": statistics.fmean(r["place"] for r in rows.values()),
        "first_place_rate": statistics.fmean(r["place"] == 1 for r in rows.values()),
        "bust_rate": statistics.fmean(r["busted"] for r in rows.values()),
        "mean_realized_bb": statistics.fmean(r["bb"] for r in rows.values()),
        "invalid_decisions": sum(r["errors"] for r in rows.values()),
        "decisions": sum(r.get("decisions", 0) for r in rows.values()),
        "cleanup_failures": sum(r.get("cleanup_failures", 0) for r in rows.values()),
        "opponent_invalid_decisions": sum(
            r.get("opponent_errors", 0) for r in rows.values()
        ),
        "outgoing_messages": sum(r.get("outgoing_messages", 0) for r in rows.values()),
    }
    result["legal_rate"] = (
        1 - result["invalid_decisions"] / result["decisions"]
        if result["decisions"]
        else None
    )
    if parent is not None:
        if rows.keys() != parent.keys():
            raise ValueError(
                "paired evaluation requires identical complete seed/seat coverage"
            )
        diffs = [parent[k]["place"] - rows[k]["place"] for k in rows]
        clusters = [k[0] if isinstance(k, tuple) else k for k in rows]
        result["paired_improvement"] = {
            "mean": statistics.fmean(diffs),
            "ci95": cluster_bootstrap(diffs, clusters),
            "seed_groups": len(set(clusters)),
            "bootstrap_unit": "whole seed across seats and opponent configurations",
        }
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--logs", type=Path, required=True)
    p.add_argument("--parent", type=Path)
    p.add_argument("--seat", type=int, choices=range(6))
    args = p.parse_args()
    print(
        json.dumps(
            summarize_games(
                game_rows(args.logs, args.seat),
                game_rows(args.parent, args.seat) if args.parent else None,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

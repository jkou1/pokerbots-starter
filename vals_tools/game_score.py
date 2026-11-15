"""Whole-game placement comparisons from harness logs; paired bootstrap by deal/seat."""

import argparse
import json
import random
import statistics
from pathlib import Path


def bootstrap(values, samples=2000):
    if len(values) < 2:
        return [None, None]
    rng = random.Random(42)
    means = sorted(
        statistics.fmean(rng.choices(values, k=len(values))) for _ in range(samples)
    )
    return [means[int(samples * 0.025)], means[int(samples * 0.975)]]


def game_rows(directory, seat=None):
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
        key = (log["session_info"]["seed"], chosen, log.get("opponent_model"))
        if key in rows:
            raise ValueError(
                "duplicate game seed/seat; isolate each evaluation's log directory"
            )
        name = f"seat{chosen}"
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
    }
    if parent is not None:
        if rows.keys() != parent.keys():
            raise ValueError(
                "paired evaluation requires identical complete seed/seat coverage"
            )
        diffs = [parent[k]["place"] - rows[k]["place"] for k in rows]
        result["paired_improvement"] = {
            "mean": statistics.fmean(diffs),
            "ci95": bootstrap(diffs),
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

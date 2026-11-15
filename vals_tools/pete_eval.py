"""Evaluate a served policy against a fixed held-out Pete decision set.

Imitation accuracy measures teacher agreement, not poker winnings. Training records are refused.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from collections import defaultdict
from pathlib import Path

import httpx
from poker_harness.completions import (
    GATEWAY_URL,
    RelayError,
    relay_completion,
    with_preset,
)
from poker_harness.training import action_args, betting_action

from vals_tools.arena import read_jsonl, write_json


def legal_prediction(row, action):
    legal = row["legal"]
    kind = action.get("action")
    if kind == "fold":
        return legal["can_fold"]
    if kind == "check":
        return legal["can_check"]
    if kind == "call":
        return not legal["can_check"] and legal["call_amount"] > 0
    return (
        kind in ("bet", "raise")
        and kind == legal["raise_type"]
        and type(action.get("amount")) is int
        and legal["min_raise_to"] <= action["amount"] <= legal["max_raise_to"]
    )


def imitation_metrics(rows, predictions):
    if not rows or len(rows) != len(predictions):
        raise ValueError(
            "every held-out example requires a prediction, including failed calls"
        )
    per_action, per_position = defaultdict(list), defaultdict(list)
    correct, exact, valid, baseline, sizing = [], [], [], [], []
    for row, predicted in zip(rows, predictions, strict=True):
        target = row["target"]
        allowed = bool(legal_prediction(row, predicted))
        hit = allowed and predicted.get("action") == target["action"]
        full = hit and (
            target["action"] not in ("bet", "raise")
            or predicted.get("amount") == target["amount"]
        )
        correct.append(hit)
        exact.append(full)
        valid.append(allowed)
        baseline.append(
            ("check" if row["legal"]["can_check"] else "fold") == target["action"]
        )
        per_action[target["action"]].append(hit)
        per_position[str(row["position"])].append(hit)
        if hit and target["action"] in ("bet", "raise"):
            sizing.append(abs(predicted["amount"] - target["amount"]))
    average = lambda values: sum(values) / len(values)
    return {
        "examples": len(rows),
        "action_accuracy": average(correct),
        "exact_action_amount_accuracy": average(exact),
        "legal_rate": average(valid),
        "check_or_fold_baseline_accuracy": average(baseline),
        "macro_action_recall": average([average(v) for v in per_action.values()]),
        "per_action": {
            k: {"examples": len(v), "recall": average(v)} for k, v in per_action.items()
        },
        "per_position": {
            k: {"examples": len(v), "accuracy": average(v)}
            for k, v in per_position.items()
        },
        "raise_amount_mae_chips": average(sizing) if sizing else None,
        "raise_amount_comparisons": len(sizing),
    }


def heldout_rows(path, limit=None):
    rows = read_jsonl(path)
    splits = {row.get("split") for row in rows}
    if not rows or len(splits) != 1 or not splits.issubset({"select", "eval"}):
        raise ValueError(
            "evaluation requires one nonempty held-out split; train/mixed records are refused"
        )
    return rows[:limit] if limit else rows


async def evaluate(args):
    rows = heldout_rows(args.records, args.limit)
    results = [None] * len(rows)
    sem = asyncio.Semaphore(args.concurrency)
    async with httpx.AsyncClient(timeout=300) as client:
        complete = relay_completion(
            client,
            GATEWAY_URL,
            os.environ["AC2_API_KEY"],
            with_preset(
                {
                    "preset": "event",
                    "model_label": args.model,
                    "temperature": 0.0,
                    "submit_fields": ["action", "amount", "say"],
                }
            ),
        )

        async def one(index, row):
            async with sem:
                try:
                    reply = await complete(row["input"])
                    result = {
                        "action": betting_action(action_args(reply)),
                        "tokens": reply.out_tokens,
                    }
                except (
                    ValueError,
                    KeyError,
                    TypeError,
                    httpx.HTTPError,
                    RelayError,
                ) as exc:
                    result = {
                        "action": {},
                        "error": f"{type(exc).__name__}: {str(exc)[:200]}",
                    }
                results[index] = result | {"provenance": row["provenance"]}
                write_json(
                    args.out,
                    {"status": "running", "model": args.model, "results": results},
                )
                print(
                    json.dumps(
                        {
                            "completed": sum(r is not None for r in results),
                            "total": len(rows),
                        }
                    ),
                    flush=True,
                )

        await asyncio.gather(*(one(i, row) for i, row in enumerate(rows)))
    summary = imitation_metrics(rows, [r["action"] for r in results])
    write_json(
        args.out,
        {
            "status": "complete",
            "model": args.model,
            "split": rows[0]["split"],
            "summary": summary,
            "results": results,
        },
    )
    print(json.dumps(summary, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--records", type=Path, default=Path("data/arena/pete-preflop/select.jsonl")
    )
    p.add_argument("--model", required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--limit", type=int)
    p.add_argument("--concurrency", type=int, default=4)
    args = p.parse_args()
    if args.concurrency < 1 or (args.limit is not None and args.limit < 1):
        p.error("concurrency and limit must be positive")
    asyncio.run(evaluate(args))


if __name__ == "__main__":
    main()

"""Evaluate matched chatter invariance against repeated-clean sampling noise."""

import argparse
import asyncio
import json
import os
from collections import defaultdict
from pathlib import Path

import httpx
from poker_harness.completions import GATEWAY_URL, relay_completion, with_preset
from poker_harness.training import action_args, betting_action

from vals_tools.arena import read_jsonl, write_json


async def evaluate(rows, complete, repeats=3):
    groups = defaultdict(list)
    for row in rows:
        groups[json.dumps(row["provenance"], sort_keys=True)].append(row)
    results = []
    for provenance, variants in groups.items():
        clean = next(
            (
                r
                for r in variants
                if r.get("perturbation", {}).get("category") == "clean"
            ),
            None,
        )
        if not clean:
            raise ValueError("each group requires a clean control")
        for row in [clean, *[r for r in variants if r is not clean]]:
            outcomes = []
            for _ in range(repeats):
                reply = await complete(row["input"])
                try:
                    if row.get("tool") == "update_scratchpad":
                        calls = reply.tool_calls
                        if (
                            reply.truncated
                            or len(calls) != 1
                            or calls[0]["function"]["name"] != "update_scratchpad"
                        ):
                            raise ValueError("invalid cleanup")
                        args = json.loads(calls[0]["function"]["arguments"])
                        value = args["contents"]
                        if not isinstance(value, str) or len(value) > 5000:
                            raise ValueError("invalid notes")
                        outcomes.append(value)
                    else:
                        args = action_args(reply)
                        outcomes.append(betting_action(args))
                except (ValueError, KeyError, TypeError):
                    outcomes.append({"invalid": True})
            results.append(
                {
                    "provenance": json.loads(provenance),
                    "perturbation": row.get("perturbation"),
                    "target": row["target"],
                    "outcomes": outcomes,
                }
            )
    comparisons = []
    for provenance in groups:
        measured = [
            r
            for r in results
            if json.dumps(r["provenance"], sort_keys=True) == provenance
        ]
        clean = measured[0]["outcomes"]
        clean_noise = sum(
            a != b for i, a in enumerate(clean) for j, b in enumerate(clean) if i != j
        ) / (repeats * (repeats - 1))
        for variant in measured[1:]:
            changed = (
                sum(a != b for a in clean for b in variant["outcomes"]) / repeats**2
            )
            comparisons.append(
                {
                    "provenance": json.loads(provenance),
                    "category": variant["perturbation"]["category"],
                    "repeated_clean_disagreement": clean_noise,
                    "perturbed_disagreement": changed,
                    "excess_disagreement": changed - clean_noise,
                }
            )
    return {
        "repeats": repeats,
        "groups": len(groups),
        "results": results,
        "comparisons": comparisons,
    }


async def run(args):
    async with httpx.AsyncClient(timeout=300) as client:
        complete = relay_completion(
            client,
            GATEWAY_URL,
            os.environ["AC2_API_KEY"],
            with_preset(
                {
                    "preset": "event",
                    "model_label": args.model,
                    "submit_fields": ["action", "amount", "say"],
                }
            ),
        )
        result = await evaluate(read_jsonl(args.records), complete, args.repeats)
    write_json(args.out, result)
    print(json.dumps({"groups": result["groups"], "output": str(args.out)}))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--records", type=Path, required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument(
        "--out", type=Path, default=Path("data/experiments/defense-eval.json")
    )
    args = p.parse_args()
    if args.repeats < 2:
        p.error("at least two repetitions are required to measure sampling noise")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()

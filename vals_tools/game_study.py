"""Frozen, resumable official 30-hand evaluations for the four-condition study."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import random
from pathlib import Path

import httpx
from ac2.sdk import Client
from poker_harness.completions import (
    GATEWAY_URL,
    cleanup_params,
    relay_completion,
    table_rules,
    with_preset,
)
from poker_harness.game import play_session
from poker_harness.seat import ModelSeat

from vals_tools.arena import write_json
from vals_tools.game_score import game_rows, summarize_games


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def deployment_identity(client, model):
    if "/" not in model:
        raise ValueError("deployment labels must use project/name")
    project, name = model.split("/", 1)
    matches = [d for d in client.inference.list() if d.name == name]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one deployment for {model}")
    deployment = client.inference.get(matches[0].id)
    if deployment.project_name != project:
        raise ValueError("deployment belongs to a different project")
    return {
        "id": deployment.id,
        "model": model,
        "version": deployment.version,
        "checkpoint": deployment.checkpoint_id,
        "served_model": deployment.served_model,
        "backing_type": deployment.backing_type,
    }


def validate_plan(plan):
    params = with_preset(
        {
            "preset": "event",
            "submit_fields": ["action", "amount", "say"],
            "temperature": 1.0,
        }
    )
    if (
        plan.get("schema") != "pokerbots.game-study/1"
        or plan.get("split") not in ("select", "eval")
        or plan.get("params") != params
    ):
        raise ValueError(
            "evaluation plan must preserve the official rules, thinking and token budgets"
        )
    if len(plan.get("opponents", [])) != 2:
        raise ValueError("evaluation plan requires two frozen opponents")
    if len({fingerprint(o["identity"]) for o in plan["opponents"]}) != 2:
        raise ValueError("opponent configurations must be distinct")
    cases = plan.get("cases", [])
    seeds = {case["seed"] for case in cases}
    expected_seeds = 2 if plan["split"] == "select" else 10
    expected = {
        (seed, seat, opponent, 0)
        for seed in seeds
        for seat in range(6)
        for opponent in range(2)
    }
    actual = {(c["seed"], c["seat"], c["opponent"], c["repeat"]) for c in cases}
    if (
        len(seeds) != expected_seeds
        or actual != expected
        or len(cases) != len(expected)
    ):
        raise ValueError(
            "evaluation plan requires all scheduled seeds, seats and opponents"
        )


def evaluation_plan(opponents, split, *, seed=42):
    if split not in ("select", "eval") or len(opponents) != 2:
        raise ValueError(
            "two frozen opponent configurations and a held-out split are required"
        )
    if any(not o.get("identity") for o in opponents):
        raise ValueError("opponent deployment identities must be frozen")
    rng = random.Random(f"matched-public-v1:{seed}:{split}")
    params = with_preset(
        {
            "preset": "event",
            "submit_fields": ["action", "amount", "say"],
            "temperature": 1.0,
        }
    )
    seeds = [rng.getrandbits(48) for _ in range(2 if split == "select" else 10)]
    cases = [
        {"seed": s, "seat": seat, "opponent": index, "repeat": 0}
        for s in seeds
        for seat in range(6)
        for index in range(2)
    ]
    return {
        "schema": "pokerbots.game-study/1",
        "split": split,
        "params": params,
        "opponents": opponents,
        "cases": cases,
        "limitations": "External deployment version cannot establish immutable upstream provider weights.",
    }


async def run(args):
    plan = json.loads(args.plan.read_text())
    validate_plan(plan)
    plan_hash = fingerprint(plan)
    client = Client(project=args.project)
    identity = deployment_identity(client, args.model)
    for opponent in plan["opponents"]:
        if deployment_identity(client, opponent["model"]) != opponent["identity"]:
            raise ValueError("opponent deployment changed since plan freeze")
    receipt = {"model": args.model, "identity": identity, "plan_sha256": plan_hash}
    receipt_path = args.out / "receipt.json"
    if receipt_path.exists() and json.loads(receipt_path.read_text()) != receipt:
        raise ValueError("model or plan changed; refuse to mix/resume evaluations")
    write_json(receipt_path, receipt)
    sem = asyncio.Semaphore(args.concurrency)
    params = plan["params"]
    rules = table_rules(params)
    if (
        rules.total_hands != 30
        or rules.seats != 6
        or rules.reset_stacks
        or rules.ranking != "elimination"
    ):
        raise ValueError("evaluation requires the official 30-hand event rules")
    async with httpx.AsyncClient(timeout=600) as http:

        def completions(model):
            return (
                relay_completion(
                    http,
                    GATEWAY_URL,
                    os.environ["AC2_API_KEY"],
                    params | {"model_label": model},
                ),
                relay_completion(
                    http,
                    GATEWAY_URL,
                    os.environ["AC2_API_KEY"],
                    cleanup_params(params | {"model_label": model}),
                ),
            )

        async def one(index, case):
            async with sem:
                path = args.out / "logs" / f"{index:04d}.json"
                if path.exists():
                    previous = json.loads(path.read_text())
                    if previous.get("complete"):
                        if (
                            previous.get("evaluation", {}).get("plan_sha256")
                            != plan_hash
                            or previous["session_info"]["seed"] != case["seed"]
                            or previous.get("policy_seats") != [f"seat{case['seat']}"]
                        ):
                            raise ValueError(
                                "existing game does not match its scheduled case"
                            )
                        return
                policy, policy_cleanup = completions(args.model)
                opponent = plan["opponents"][case["opponent"]]
                other, other_cleanup = completions(opponent["model"])
                players = [
                    ModelSeat(
                        f"seat{s}",
                        policy if s == case["seat"] else other,
                        rules,
                        cleanup_complete=policy_cleanup
                        if s == case["seat"]
                        else other_cleanup,
                    )
                    for s in range(6)
                ]
                log = await play_session(f"study-{index}", case["seed"], players, rules)
                log.update(
                    policy_seats=[f"seat{case['seat']}"],
                    opponent_model=opponent["model"],
                    split=plan["split"],
                    evaluation={
                        "plan_sha256": plan_hash,
                        "opponent_fingerprint": fingerprint(opponent["identity"]),
                        "repeat": case["repeat"],
                        "case": index,
                    },
                )
                write_json(path, log)
                print(
                    json.dumps({"case": index, "complete": log["complete"]}), flush=True
                )

        await asyncio.gather(*(one(i, case) for i, case in enumerate(plan["cases"])))
    for opponent in plan["opponents"]:
        if deployment_identity(client, opponent["model"]) != opponent["identity"]:
            raise ValueError(
                "opponent deployment changed during evaluation; results are not comparable"
            )
    if deployment_identity(client, args.model) != identity:
        raise ValueError("candidate deployment changed during evaluation")
    summary = score_directory(args.out, plan)
    write_json(args.out / "summary.json", summary)
    write_json(
        args.out / "validated.json",
        {
            "plan_sha256": plan_hash,
            "identity": identity,
            "logs": {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted((args.out / "logs").glob("*.json"))
            },
        },
    )


def score_directory(directory, plan, require_validated=False):
    validate_plan(plan)
    if require_validated:
        path = directory / "validated.json"
        if not path.exists():
            raise ValueError(
                "evaluation has not completed deployment identity validation"
            )
        validation = json.loads(path.read_text())
        logs = {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((directory / "logs").glob("*.json"))
        }
        if (
            validation.get("plan_sha256") != fingerprint(plan)
            or validation.get("logs") != logs
        ):
            raise ValueError("validated evaluation artifacts changed")
    rows = game_rows(directory / "logs", expected=fingerprint(plan))
    expected = {
        (
            case["seed"],
            case["seat"],
            plan["opponents"][case["opponent"]]["model"],
            fingerprint(plan["opponents"][case["opponent"]]["identity"]),
            case["repeat"],
            fingerprint(plan),
        )
        for case in plan["cases"]
    }
    if set(rows) != expected:
        raise ValueError("evaluation has missing or unexpected complete games")
    return summarize_games(rows)


def comparison(directories, plan):
    for path in directories.values():
        score_directory(path, plan, require_validated=True)
    rows = {
        label: game_rows(path / "logs", expected=fingerprint(plan))
        for label, path in directories.items()
    }
    result = {label: summarize_games(data) for label, data in rows.items()}
    result["comparisons"] = {
        f"{candidate}_vs_{parent}": summarize_games(rows[candidate], rows[parent])[
            "paired_improvement"
        ]
        for candidate, parent in [
            ("B1", "B0"),
            ("C1", "C0"),
            ("C1", "B1"),
            ("B1", "C0"),
        ]
    }
    qualified = []
    for label in ("B1", "C1"):
        ci = result["comparisons"][f"{label}_vs_C0"]["ci95"]
        if (
            ci[0] is not None
            and ci[0] > 0
            and not result[label]["invalid_decisions"]
            and not result[label]["cleanup_failures"]
        ):
            qualified.append(label)
    result["verdict"] = (
        ("supported improvement: " + ", ".join(qualified))
        if qualified
        else "no supported improvement; inconclusive or regression"
    )
    result["promotion_eligible"] = plan["split"] == "eval" and bool(qualified)
    result["split"] = plan["split"]
    result["plan_sha256"] = fingerprint(plan)
    result["models"] = {
        label: json.loads((path / "validated.json").read_text())["identity"]
        for label, path in directories.items()
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument(
        "--opponents",
        nargs=2,
        default=["vals-hackathon/ac-vals-model", "vals-hackathon/combined-sft-v3"],
    )
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--project", default="vals-hackathon")
    p = sub.add_parser("run")
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--concurrency", type=int, default=2)
    p.add_argument("--project", default="vals-hackathon")
    p = sub.add_parser("compare")
    p.add_argument("--plan", type=Path, required=True)
    for label in ("b0", "c0", "b1", "c1"):
        p.add_argument(f"--{label}", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        client = Client(project=args.project)
        opponents = [
            {"model": m, "identity": deployment_identity(client, m)}
            for m in args.opponents
        ]
        for split in ("select", "eval"):
            path = args.out / f"{split}.json"
            if path.exists():
                raise ValueError(
                    "evaluation plans already exist; use a fresh directory"
                )
            write_json(path, evaluation_plan(opponents, split))
    elif args.command == "run":
        if args.concurrency < 1:
            parser.error("concurrency must be positive")
        asyncio.run(run(args))
    else:
        result = comparison(
            {k.upper(): getattr(args, k) for k in ("b0", "c0", "b1", "c1")},
            json.loads(args.plan.read_text()),
        )
        write_json(args.out, result)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

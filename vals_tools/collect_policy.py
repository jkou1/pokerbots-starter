"""Collect base-policy traces directly through inference, without an AC2 harness connector.

The exported get_completion spans can be consumed by opsd/build_dataset.py --traces.
Only fresh training deals are used; no held-out archive records enter this collection.
"""

import argparse
import asyncio
import json
import os
import random
import time
from pathlib import Path

import httpx
from ac2.runtime import FunctionCall, FunctionCallOutput, Message, Reasoning
from poker_harness.completions import (
    GATEWAY_URL,
    cleanup_params,
    relay_completion,
    table_rules,
    with_preset,
)
from poker_harness.engine.scripted import ARCHETYPES, ScriptedPlayer
from poker_harness.game import play_session
from poker_harness.seat import ModelSeat

from vals_tools.arena import write_json, write_jsonl
from vals_tools.tasks import SPLITS


def deal_seeds(split, count, source="policy"):
    if source == "starter":
        maximum, base = SPLITS[split]
        if count > maximum:
            raise ValueError(f"starter {split} has only {maximum} deals")
    else:
        base = {"train": 8_910_001, "select": 8_920_002, "eval": 8_930_003}[split]
    rng = random.Random(base)
    return [rng.getrandbits(48) for _ in range(count)]


def trace_input(messages):
    items = []
    for message in messages:
        if message["role"] == "tool":
            items.append(
                FunctionCallOutput(
                    call_id=message["tool_call_id"], output=message["content"]
                )
            )
        else:
            if message.get("content"):
                items.append(Message(role=message["role"], content=message["content"]))
            for call in message.get("tool_calls", []):
                items.append(
                    FunctionCall(
                        call_id=call["id"],
                        name=call["function"]["name"],
                        arguments=call["function"]["arguments"],
                    )
                )
    return items


def trace_reply(reply):
    items = []
    if reply.reasoning:
        items.append(Reasoning(content=reply.reasoning))
    if reply.text:
        items.append(Message(role="assistant", content=reply.text))
    for call in reply.tool_calls:
        items.append(
            FunctionCall(
                call_id=call["id"],
                name=call["function"]["name"],
                arguments=call["function"]["arguments"],
            )
        )
    return items


async def collect(args):
    key = os.environ["AC2_API_KEY"]
    args.out.mkdir(parents=True, exist_ok=True)
    settings = {
        "model": args.model,
        "opponent": args.opponent,
        "hands_per_game": args.hands_per_game,
        "split": args.split,
    }
    if args.seed_source != "policy":
        settings["seed_source"] = args.seed_source
    settings_path = args.out / "settings.json"
    if settings_path.exists() and json.loads(settings_path.read_text()) != settings:
        raise ValueError("collection settings changed; choose a new output directory")
    write_json(settings_path, settings)
    params = with_preset(
        {
            "preset": "event",
            "total_hands": args.hands_per_game,
            "submit_fields": ["action", "amount", "say"],
        }
    )
    rules = table_rules(params)
    seeds = deal_seeds(args.split, args.hands, args.seed_source)
    sem = asyncio.Semaphore(args.concurrency)
    async with httpx.AsyncClient(timeout=300) as client:
        policy = relay_completion(
            client, GATEWAY_URL, key, params | {"model_label": args.model}
        )
        cleanup = relay_completion(
            client,
            GATEWAY_URL,
            key,
            cleanup_params(params | {"model_label": args.model}),
        )
        opponent = relay_completion(
            client, GATEWAY_URL, key, params | {"model_label": args.opponent}
        )
        opponent_cleanup = relay_completion(
            client,
            GATEWAY_URL,
            key,
            cleanup_params(params | {"model_label": args.opponent}),
        )

        async def hand(index, seed):
            async with sem:
                path = args.out / "traces" / f"{seed}.json"
                if path.exists():
                    return json.loads(path.read_text())
                spans = []

                def recorded(complete):
                    async def call(messages):
                        started = time.time()
                        reply = await complete(messages)
                        spans.append(
                            {
                                "name": "get_completion",
                                "status": "OK",
                                "start_time": started,
                                "input": json.dumps(
                                    [
                                        i.model_dump(mode="json")
                                        for i in trace_input(messages)
                                    ]
                                ),
                                "output": json.dumps(
                                    [
                                        i.model_dump(mode="json")
                                        for i in trace_reply(reply)
                                    ]
                                ),
                                "tokens_out": reply.out_tokens or 0,
                            }
                        )
                        return reply

                    return call

                policy_seat = index % 6
                players = [
                    ScriptedPlayer(f"seat{s}", ARCHETYPES[s % len(ARCHETYPES)], seed)
                    if args.opponent == "scripted" and s != policy_seat
                    else ModelSeat(
                        f"seat{s}",
                        recorded(policy) if s == policy_seat else opponent,
                        rules,
                        cleanup_complete=recorded(cleanup)
                        if s == policy_seat
                        else opponent_cleanup,
                    )
                    for s in range(6)
                ]
                log = await play_session(str(seed), seed, players, rules)
                log["policy_seats"] = [f"seat{policy_seat}"]
                log["opponent_model"] = args.opponent
                log["split"] = args.split
                write_json(args.out / "logs" / f"{seed}.json", log)
                result = {
                    "trace_id": f"local-{seed}",
                    "model": args.model,
                    "policy_seat": policy_seat,
                    "split": args.split,
                    "spans": spans,
                }
                write_json(path, result)
                print(
                    json.dumps(
                        {"hand": index + 1, "seed": seed, "policy_calls": len(spans)}
                    ),
                    flush=True,
                )
                return result

        traces = await asyncio.gather(*(hand(i, seed) for i, seed in enumerate(seeds)))
    write_jsonl(args.out / "traces.jsonl", traces)
    write_json(
        args.out / "collection.json",
        {
            "model": args.model,
            "opponent": args.opponent,
            "hands": len(traces),
            "seeds": seeds,
            "split": args.split,
        },
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="vals-hackathon/base")
    p.add_argument("--opponent", default="vals-hackathon/ac-vals-model")
    p.add_argument("--hands", type=int, default=16)
    p.add_argument("--hands-per-game", type=int, choices=[1, 30], default=1)
    p.add_argument("--split", choices=["train", "select", "eval"], default="train")
    p.add_argument("--seed-source", choices=["policy", "starter"], default="policy")
    p.add_argument("--concurrency", type=int, default=4)
    p.add_argument("--out", type=Path, default=Path("data/experiments/principles-base"))
    args = p.parse_args()
    if args.hands < 1 or args.concurrency < 1:
        p.error("hands and concurrency must be positive")
    asyncio.run(collect(args))


if __name__ == "__main__":
    main()

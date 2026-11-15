"""Export clean checkpoint decisions and factual cleanup targets from local harness logs."""

import argparse
import json
from pathlib import Path

from poker_harness.completions import table_rules, with_preset
from poker_harness.prompts import (
    cleanup_prompt,
    decision_prompt,
    scratchpad_block,
    system_prompt,
)

from vals_tools.arena import write_jsonl
from vals_tools.pete import replay_hand, split_for


def policy_records(log, seat, model):
    info = log["session_info"]
    source = {
        "seed": info["seed"],
        "seats": [{"seat": i} for i in range(len(info["player_names"]))],
        "format": {
            "total_hands": info["total_hands"],
            "small_blind": info["small_blind"],
            "big_blind": info["big_blind"],
        },
    }
    rules = table_rules(
        with_preset(
            {
                "preset": "event",
                "total_hands": info["total_hands"],
                "seats": len(info["player_names"]),
            }
        )
    )
    split = log.get("split", split_for(str(info["seed"])))
    if split not in ("train", "select", "eval"):
        raise ValueError("unknown source split")
    notes = ""
    for hand in log["hands"]:
        public = {
            "hand_number": hand["hand_number"],
            "button_seat": hand["button_seat"],
            "players": [
                {
                    "seat": p["seat"],
                    "hole_cards": p["hole_cards"],
                    "starting_stack": hand.get("stacks_before", {}).get(
                        name, p["starting_stack"]
                    ),
                }
                for name, p in hand["starting_state"].items()
            ],
            "actions": [
                dict(
                    a,
                    action=a["action"]["type"],
                    amount=a["action"].get("amount"),
                    to_call=a["call_amount"],
                )
                for a in hand["actions"]
            ],
            "stacks_after": {
                str(i): hand["ending_stacks"][n]
                for i, n in enumerate(info["player_names"])
            },
        }
        for index, ctx, target, original in replay_hand(
            source, public, stack_after_includes_award=True
        ):
            if ctx.seat != seat or original["model_response"].get("format_error"):
                continue
            yield {
                "input": [
                    {"role": "system", "content": system_prompt(rules)},
                    {"role": "user", "content": scratchpad_block(notes, 5000)},
                    {"role": "user", "content": decision_prompt(ctx, talk=False)},
                ],
                "target": target,
                "provenance": {
                    "model": model,
                    "seed": info["seed"],
                    "hand": hand["hand_number"],
                    "action_index": index,
                    "seat": seat,
                    "street": ctx.street,
                },
                "split": split,
            }
        name = f"seat{seat}"
        if name not in hand["starting_state"]:
            continue
        summary = hand | {"stacks": hand["ending_stacks"]}
        prompt = cleanup_prompt(summary, name, hand["actions"], True, False, 5000)
        facts = (
            f"hand {hand['hand_number']}: board {' '.join(hand['final_board']) or '-'}; "
            f"stacks {json.dumps(hand['ending_stacks'], sort_keys=True)}. "
            + "; ".join(
                f"{a['player']} {a['street']} {a['action']['type']}"
                for a in hand["actions"]
            )
        )
        updated = (notes + "\n" + facts).strip()[-5000:]
        yield {
            "input": [
                {"role": "system", "content": system_prompt(rules)},
                {"role": "user", "content": scratchpad_block(notes, 5000)},
                {"role": "user", "content": prompt},
            ],
            "tool": "update_scratchpad",
            "target": {"contents": updated},
            "provenance": {
                "model": model,
                "seed": info["seed"],
                "seat": seat,
                "hand": hand["hand_number"],
                "street": "cleanup",
            },
            "split": split,
        }
        notes = updated


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--logs", type=Path, required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--seat", type=int, choices=range(6))
    p.add_argument(
        "--street",
        choices=["all", "preflop", "postflop", "cleanup", "replay"],
        default="all",
    )
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    rows = []
    for path in sorted(args.logs.glob("*.json")):
        log = json.loads(path.read_text())
        policy = log.get("policy_seats", [])
        seat = (
            args.seat
            if args.seat is not None
            else int(policy[0].removeprefix("seat"))
            if len(policy) == 1
            else None
        )
        if seat is None:
            p.error("pass --seat for logs without a single policy_seats entry")
        rows.extend(policy_records(log, seat, args.model))
    if args.street != "all":
        rows = [
            r
            for r in rows
            if (
                r["provenance"]["street"] in ("flop", "turn", "river", "cleanup")
                if args.street == "replay"
                else r["provenance"]["street"] in ("flop", "turn", "river")
                if args.street == "postflop"
                else r["provenance"]["street"] == args.street
            )
        ]
    for split in ("train", "select", "eval"):
        selected = [r for r in rows if r["split"] == split]
        write_jsonl(args.out / f"{split}.jsonl", selected)
        print(json.dumps({"split": split, "records": len(selected)}))


if __name__ == "__main__":
    main()

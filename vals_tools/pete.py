"""Replay public arena JSON into decision-time datasets without future information.

Run with the harness environment: PYTHONPATH=harness/src:. harness/.venv/bin/python -m vals_tools.pete
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

from poker_harness.completions import table_rules, with_preset
from poker_harness.engine.table import (
    STREETS,
    Decision,
    DecisionContext,
    HandRunner,
    codes,
    legal_actions,
    resolve,
)
from poker_harness.prompts import decision_prompt, sanitize_talk, system_prompt

from vals_tools.arena import write_json, write_jsonl

PETE = "house-professor-pete"
BAD_FLAGS = (
    "fallback",
    "coerced",
    "format_error",
    "afk",
    "timed_out",
    "token_cap",
    "sat_out",
    "error",
    "scripted",
)
ADAPTER = "arena-v1-prefix-1"


def split_for(identity: str) -> str:
    bucket = int(hashlib.sha256(identity.encode()).hexdigest()[:16], 16) % 100
    return "train" if bucket < 80 else "select" if bucket < 90 else "eval"


def deal_identity(match: dict) -> str:
    # Same deck/initial players stays in one split even if published as another match ID.
    first = match["hands"][0]
    value = [
        match["seed"],
        first["button_seat"],
        sorted(
            (p["seat"], p["hole_cards"], p["starting_stack"]) for p in first["players"]
        ),
    ]
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def replay_hand(match: dict, hand: dict, *, stack_after_includes_award=False):
    """Yield pre-action contexts, then apply recorded actions. Nothing downstream enters the prompt."""
    fmt = match["format"]
    players = {
        p["seat"]: SimpleNamespace(name=f"seat{p['seat']}") for p in match["seats"]
    }
    stacks = {s: 0 for s in players} | {
        p["seat"]: p["starting_stack"] for p in hand["players"]
    }
    runner = HandRunner(
        players=players,
        stacks=stacks,
        button_seat=hand["button_seat"],
        hand_number=hand["hand_number"],
        total_hands=fmt["total_hands"],
        seed=match["seed"],
        small_blind=fmt["small_blind"],
        big_blind=fmt["big_blind"],
    )
    runner._deal()
    for p in hand["players"]:
        if set(codes(runner.state.hole_cards[runner.order.index(p["seat"])])) != set(
            p["hole_cards"]
        ):
            raise ValueError("seed/runner hole-card mismatch")
    actions, folded = [], set()
    state = runner.state
    for index, source in enumerate(hand["actions"]):
        runner._deal()
        state = runner.state
        if not state.status or state.actor_index is None:
            raise ValueError(f"action {index}: unexpected action after hand ended")
        actor = runner.order[state.actor_index]
        legal = legal_actions(state)
        board = runner._board()
        street = STREETS[state.street_index or 0]
        if (actor, street, board, state.total_pot_amount, legal.call_amount) != (
            source["seat"],
            source["street"],
            source["board"],
            source["pot_before"],
            source["to_call"],
        ):
            raise ValueError(f"action {index}: actor/street/board/pot/call mismatch")
        ctx = DecisionContext(
            hand_number=hand["hand_number"],
            total_hands=fmt["total_hands"],
            street=street,
            seat=actor,
            position=state.actor_index,
            button_seat=hand["button_seat"],
            hole_cards=codes(state.hole_cards[state.actor_index]),
            board=board,
            pot=state.total_pot_amount,
            seats=runner._seat_views(folded),
            hand_actions=list(actions),
            legal=legal,
        )
        target = {"action": source["action"]}
        if source["action"] in ("bet", "raise"):
            target["amount"] = source["amount"]
        requested = Decision(target["action"], target.get("amount"))
        applied, error = resolve(requested, legal)
        if error or applied != requested:
            raise ValueError(f"action {index}: recorded action is not legal: {error}")
        yield index, ctx, target, source
        before = state.stacks[runner.order.index(actor)]
        committed = (
            min(legal.call_amount, before)
            if applied.type == "call"
            else applied.amount - state.bets[runner.order.index(actor)]
            if applied.type in ("bet", "raise")
            else 0
        )
        runner._apply(applied)
        expected = (
            before - committed
            if index == len(hand["actions"]) - 1 and not stack_after_includes_award
            else state.stacks[runner.order.index(actor)]
        )
        if expected != source["stack_after"]:
            raise ValueError(f"action {index}: post-action stack mismatch")
        if applied.type == "fold":
            folded.add(actor)
        actions.append(
            {
                "player": f"seat{actor}",
                "seat": actor,
                "street": street,
                "action": {"type": target["action"]}
                | ({"amount": target["amount"]} if "amount" in target else {}),
                "say": sanitize_talk(source.get("say")),
                "call_amount": source["to_call"],
            }
        )
    runner._deal()
    if state.status:
        raise ValueError("recorded hand ended before the engine")
    for seat in runner.order:
        if state.stacks[runner.order.index(seat)] != hand["stacks_after"][str(seat)]:
            raise ValueError("final stack mismatch")


def extract_match(match: dict) -> tuple[list[dict], list[dict], Counter]:
    if (
        match.get("schema") != "vals-arena.match/1"
        or match.get("runner_version") != "0.1.0"
    ):
        raise ValueError("unsupported schema/runner version")
    if match.get("status") != "complete":
        raise ValueError("match is not complete")
    pete = {s["seat"] for s in match["seats"] if s["entry"]["id"] == PETE}
    rules = table_rules(
        with_preset(
            {
                "preset": "event",
                "total_hands": match["format"]["total_hands"],
                "seats": len(match["seats"]),
            }
        )
    )
    decisions, talk, stats = [], [], Counter()
    for hand in match["hands"]:
        for index, ctx, target, source in replay_hand(match, hand):
            provenance = {
                "match_id": match["id"],
                "hand": hand["hand_number"],
                "action_index": index,
                "seat": ctx.seat,
                "street": ctx.street,
                "adapter": ADAPTER,
                "teacher": next(
                    s["entry"]["id"] for s in match["seats"] if s["seat"] == ctx.seat
                ),
            }
            if say := sanitize_talk(source.get("say")):
                talk.append({"provenance": provenance, "say": say})
            if ctx.seat not in pete or ctx.street != "preflop":
                continue
            stats["pete_seen"] += 1
            args = source.get("tool_args") or {}
            if any(source.get(k) for k in BAD_FLAGS) or any(
                args.get(k) != v for k, v in target.items()
            ):
                stats["rejected_target"] += 1
                continue
            # Official-shaped fresh decision; no private memory or earlier reasoning is fabricated.
            prompt = [
                {"role": "system", "content": system_prompt(rules)},
                {"role": "user", "content": decision_prompt(ctx, talk=False)},
            ]
            decisions.append(
                {
                    "input": prompt,
                    "target": target,
                    "provenance": provenance,
                    "legal": asdict(ctx.legal),
                    "position": ctx.position,
                    "hole_cards": ctx.hole_cards,
                    "observation_kind": "reconstructed_without_private_memory",
                }
            )
            stats["kept"] += 1
    return decisions, talk, stats


def build(root: Path) -> dict:
    rows = {s: [] for s in ("train", "select", "eval")}
    talks = {s: [] for s in rows}
    quality = {
        "matches": 0,
        "duplicates": 0,
        "quarantined": {},
        "counts": Counter(),
        "coverage": Counter(),
    }
    seen = set()
    for path in sorted((root / "raw").glob("*.json")):
        try:
            match = json.loads(path.read_text())
            identity = deal_identity(match)
            if identity in seen:
                quality["duplicates"] += 1
                continue
            decisions, chatter, stats = extract_match(match)
            seen.add(identity)
            split = split_for(identity)
            for row in decisions + chatter:
                row["split"] = split
                row["deal_identity"] = identity
            rows[split].extend(decisions)
            talks[split].extend(chatter)
            quality["matches"] += 1
            quality["counts"].update(stats)
            quality["coverage"].update(
                f"position:{r['position']} action:{r['target']['action']}"
                for r in decisions
            )
        except (ValueError, KeyError, TypeError, IndexError, AssertionError) as exc:
            quality["quarantined"][path.name] = f"{type(exc).__name__}: {exc}"
    for split, records in rows.items():
        write_jsonl(root / "pete-preflop" / f"{split}.jsonl", records)
        write_jsonl(root / "talk" / f"{split}.jsonl", talks[split])
    quality["splits"] = {s: len(r) for s, r in rows.items()}
    quality["train_ready"] = all(rows.values())
    write_json(root / "quality.json", quality)
    return quality


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path("data/arena"))
    args = p.parse_args()
    print(json.dumps(build(args.root), indent=2))


if __name__ == "__main__":
    main()

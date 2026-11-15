"""Download pinned PokerBench CSVs and replay exact, integer-chip observations.

JSON and CSV row orders differ: never join them by index. Unsupported or
inconsistent rows are quarantined, with counts and source row numbers.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import re
from collections import Counter
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import httpx
from poker_harness.completions import table_rules, with_preset
from poker_harness.engine.table import (
    STREETS,
    Decision,
    DecisionContext,
    HandRunner,
    legal_actions,
    resolve,
)
from poker_harness.prompts import decision_prompt, system_prompt

from vals_tools.arena import write_json, write_jsonl

REPO = "RZ412/PokerBench"
REVISION = "7ac61f961c81a50fc0f667820b2fb0e432dfec0d"
FILES = {
    ("preflop", "train"): "preflop_60k_train_set_game_scenario_information.csv",
    ("postflop", "train"): "postflop_500k_train_set_game_scenario_information.csv",
    ("preflop", "test"): "preflop_1k_test_set_game_scenario_information.csv",
    ("postflop", "test"): "postflop_10k_test_set_game_scenario_information.csv",
}
SEATS = {"SB": 0, "BB": 1, "UTG": 2, "HJ": 3, "CO": 4, "BTN": 5}


def chips(value):
    amount = Decimal(str(value).lower().removesuffix("bb")) * 2
    if not amount.is_finite() or amount != amount.to_integral_value() or amount < 0:
        raise ValueError("nonrepresentable integer-chip amount")
    return int(amount)


def cards(value, count):
    result = re.findall(r"[2-9TJQKA][cdhs]", value)
    if len(result) != count or "".join(result) != value or len(set(result)) != count:
        raise ValueError("invalid cards")
    return result


def spot_identity(prefix, hero, board, holding):
    # All suit-isomorphic duplicates inherit one split; future cards are absent.
    variants = []
    for suits in itertools.permutations("cdhs"):
        mapping = dict(zip("cdhs", suits))
        convert = lambda c, mapping=mapping: c[0] + mapping[c[1]]
        converted = list(map(convert, board))
        variants.append(
            (
                tuple(sorted(converted[:3]) + converted[3:]),
                tuple(sorted(map(convert, holding))),
            )
        )
    value = [prefix, hero, min(variants)]
    return hashlib.sha256(json.dumps(value).encode()).hexdigest()


def convert_row(
    row, kind, source_split, *, filename="fixture.csv", index=0, revision=REVISION
):
    prefix = row["prev_line"] if kind == "preflop" else row["preflop_action"]
    parts = prefix.split("/") if prefix else []
    if len(parts) % 2:
        raise ValueError("invalid preflop action pairs")
    sequence = [(SEATS[parts[i]], parts[i + 1]) for i in range(0, len(parts), 2)]
    street = "preflop" if kind == "preflop" else row["evaluation_at"].lower()
    if street not in STREETS or (kind == "postflop" and street == "preflop"):
        raise ValueError("unknown evaluation street")
    board = []
    if kind == "postflop":
        board = cards(row["board_flop"], 3)
        if street in ("turn", "river"):
            board += cards(row["board_turn"], 1)
        if street == "river":
            board += cards(row["board_river"], 1)
    holding = cards(row["hero_holding"] if kind == "preflop" else row["holding"], 2)
    if len(set(board + holding)) != len(board + holding):
        raise ValueError("visible cards overlap")
    runner = HandRunner(
        players={i: SimpleNamespace(name=f"seat{i}") for i in range(6)},
        stacks=dict.fromkeys(range(6), 200),
        button_seat=5,
        hand_number=1,
        total_hands=30,
        seed=0,
        small_blind=1,
        big_blind=2,
    )
    state = runner.state
    # Unknown opponent cards affect neither betting nor legal action bounds.
    for i in range(6):
        state.deal_hole("????", player_index=i)
    actions, folded = [], set()

    def actor():
        if not state.status or state.actor_index is None:
            raise ValueError("action prefix ended before the requested decision")
        return runner.order[state.actor_index]

    def apply(move):
        seat = actor()
        legal = legal_actions(state)
        requested = Decision(move.lower())
        if move.lower() == "allin":
            requested = Decision(legal.raise_type, legal.max_raise_to)
        elif re.fullmatch(r"[0-9.]+bb", move.lower()):
            requested = Decision("raise", chips(move))
        elif match := re.fullmatch(r"(BET|RAISE)_([0-9.]+)", move.upper()):
            requested = Decision(match[1].lower(), chips(match[2]))
        if requested.type not in ("fold", "check", "call", "bet", "raise"):
            raise ValueError("unsupported action")
        applied, error = resolve(requested, legal)
        if error or applied != requested:
            raise ValueError("illegal source action")
        actions.append(
            {
                "player": f"seat{seat}",
                "seat": seat,
                "street": STREETS[state.street_index],
                "action": {"type": applied.type}
                | ({"amount": applied.amount} if applied.amount is not None else {}),
            }
        )
        if applied.type == "fold":
            folded.add(seat)
        runner._apply(applied)

    def fold_to(seat):
        for _ in range(6):
            if actor() == seat:
                return
            apply("fold")
        raise ValueError("cannot reach source actor")

    for seat, move in sequence:
        if state.street_index != 0:
            raise ValueError("preflop prefix crossed streets")
        fold_to(seat)
        apply(move)
    if kind == "preflop":
        hero = SEATS[row["hero_pos"]]
        fold_to(hero)
    else:
        # Complete only omitted folds; never invent a missing call or check.
        while state.actor_index is not None and state.street_index == 0:
            apply("fold")
        live = [i for i, active in enumerate(state.statuses) if active]
        if len(live) != 2:
            raise ValueError("postflop source is not a two-player pot")
        roles = {"OOP": runner.order[min(live)], "IP": runner.order[max(live)]}
        hero = roles[row["hero_position"]]

        def deal(expected):
            if state.can_burn_card():
                state.burn_card("??")
            if not state.can_deal_board() or state.board_dealing_count != len(expected):
                raise ValueError("unexpected board transition")
            state.deal_board("".join(expected))

        deal(board[:3])
        tokens = row["postflop_action"].split("/") if row["postflop_action"] else []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token == "dealcards":
                i += 1
                if i >= len(tokens):
                    raise ValueError("missing dealt card")
                next_index = len(runner._board())
                if tokens[i] != "".join(board[next_index : next_index + 1]):
                    raise ValueError("board transition exceeds visible street")
                deal([tokens[i]])
            else:
                role, move = token.split("_", 1)
                if actor() != roles[role]:
                    raise ValueError("postflop actor mismatch")
                apply(move)
            i += 1
    if (
        actor() != hero
        or STREETS[state.street_index] != street
        or runner._board() != board
    ):
        raise ValueError("decision state mismatch")
    if state.total_pot_amount != chips(row["pot_size"]):
        raise ValueError("source pot does not match engine replay")
    legal = legal_actions(state)
    label = row["correct_decision"].strip().lower()
    if label == "allin":
        target = {"action": legal.raise_type, "amount": legal.max_raise_to}
    elif re.fullmatch(r"[0-9.]+bb", label):
        target = {"action": "raise", "amount": chips(label)}
    elif match := re.fullmatch(r"(bet|raise) ([0-9.]+)", label):
        target = {"action": match[1], "amount": chips(match[2])}
    else:
        target = {"action": label}
    requested = Decision(target["action"], target.get("amount"))
    applied, error = resolve(requested, legal)
    if (
        requested.type not in ("fold", "check", "call", "bet", "raise")
        or error
        or applied != requested
    ):
        raise ValueError("illegal solver target")
    ctx = DecisionContext(
        1,
        30,
        street,
        hero,
        runner.order.index(hero),
        5,
        holding,
        board,
        state.total_pot_amount,
        runner._seat_views(folded),
        actions,
        legal,
    )
    identity = spot_identity(actions, hero, board, holding)
    bucket = int(identity[:8], 16) % 10
    split = "eval" if source_split == "test" else "select" if bucket == 0 else "train"
    rules = table_rules(with_preset({"preset": "event"}))
    return {
        "input": [
            {"role": "system", "content": system_prompt(rules)},
            {"role": "user", "content": decision_prompt(ctx, talk=False)},
        ],
        "target": target,
        "legal": asdict(legal),
        "position": ctx.position,
        "hole_cards": holding,
        "split": split,
        "deal_identity": identity,
        "observation_kind": "solver_cash_spot_without_private_memory",
        "provenance": {
            "source": REPO,
            "revision": revision,
            "file": filename,
            "row": index,
            "street": street,
            "seat": hero,
            "teacher": "PokerBench-solver",
            "adapter": "pokerbench-exact-v1",
            "source_split": source_split,
        },
    }


def download(root, revision=REVISION):
    manifest_path = root / "release.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if manifest["revision"] != revision:
            raise ValueError("release revision changed; choose a new directory")
    else:
        manifest = {"repository": REPO, "revision": revision, "files": {}}
    if not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise ValueError("a pinned full Hugging Face commit is required")
    for filename in FILES.values():
        path = root / "raw" / filename
        if (
            path.exists()
            and manifest["files"].get(filename)
            == hashlib.sha256(path.read_bytes()).hexdigest()
        ):
            continue
        url = f"https://huggingface.co/datasets/{REPO}/resolve/{revision}/{filename}"
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".part")
        with httpx.stream("GET", url, follow_redirects=True, timeout=120) as response:
            response.raise_for_status()
            with temporary.open("wb") as stream:
                for chunk in response.iter_bytes():
                    stream.write(chunk)
        temporary.replace(path)
        manifest["files"][filename] = hashlib.sha256(path.read_bytes()).hexdigest()
        write_json(manifest_path, manifest)
    return manifest


def build(root, output, max_rows=10000):
    release = json.loads((root / "release.json").read_text())
    rows, rejected = [], Counter()
    examples = []
    for (kind, source_split), filename in FILES.items():
        path = root / "raw" / filename
        if hashlib.sha256(path.read_bytes()).hexdigest() != release["files"][filename]:
            raise ValueError(f"source hash changed: {filename}")
        with path.open(newline="") as stream:
            for index, row in enumerate(csv.DictReader(stream)):
                if (
                    source_split == "train"
                    and max_rows is not None
                    and index >= max_rows
                ):
                    break
                try:
                    rows.append(
                        convert_row(
                            row,
                            kind,
                            source_split,
                            filename=filename,
                            index=index,
                            revision=release["revision"],
                        )
                    )
                except (
                    ValueError,
                    KeyError,
                    TypeError,
                    IndexError,
                    ArithmeticError,
                ) as exc:
                    reason = f"{type(exc).__name__}: {exc}"
                    rejected[reason] += 1
                    if len(examples) < 100:
                        examples.append(
                            {"file": filename, "row": index, "reason": reason}
                        )
    test = {r["deal_identity"] for r in rows if r["split"] == "eval"}
    seen, kept, overlap = set(), [], 0
    for row in sorted(rows, key=lambda r: r["split"] != "eval"):
        identity = row["deal_identity"]
        if row["split"] != "eval" and identity in test:
            overlap += 1
            continue
        if identity not in seen:
            kept.append(row)
            seen.add(identity)
    for split in ("train", "select", "eval"):
        write_jsonl(output / f"{split}.jsonl", (r for r in kept if r["split"] == split))
    report = {
        "release": release,
        "max_training_source_rows_per_file": max_rows,
        "accepted_before_deduplication": len(rows),
        "duplicates": len(rows) - overlap - len(kept),
        "test_overlap_removed": overlap,
        "rejected": dict(rejected),
        "rejection_examples": examples,
        "coverage": dict(
            Counter(
                f"{r['split']}:{r['provenance']['street']}:{r['target']['action']}"
                for r in kept
            )
        ),
    }
    write_json(output / "quality.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["download", "build"])
    parser.add_argument("--root", type=Path, default=Path("data/pokerbench"))
    parser.add_argument(
        "--out", type=Path, default=Path("data/experiments/pokerbench-exact")
    )
    parser.add_argument("--revision", default=REVISION)
    parser.add_argument("--max-rows", type=int, default=10000)
    args = parser.parse_args()
    if args.max_rows < 1:
        parser.error("max-rows must be positive")
    result = (
        download(args.root, args.revision)
        if args.command == "download"
        else build(args.root, args.out, args.max_rows)
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

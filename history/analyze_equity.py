"""Mine the replay archive with reproducible 1,000-trial eval7 equity estimates."""

import hashlib
import json
import math
import random
import statistics
import sys
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from importlib.metadata import version
from pathlib import Path

import eval7

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "analysis"
TRIALS = 1000
ENTRY = "org_cd68943dd947"
DECK = [eval7.Card(r + s) for r in "23456789TJQKA" for s in "cdhs"]


def equity(hero, villains, board, dead, seed, random_hands=False):
    """Expected share of a single showdown pot; ties split among all winners."""
    rng = random.Random(seed)
    blocked = set(hero + board + ([] if random_hands else dead))
    deck = [c for c in DECK if c not in blocked]
    missing = 5 - len(board)
    n = len(villains)
    shares = []
    for _ in range(TRIALS):
        draw = rng.sample(deck, missing + (2 * n if random_hands else 0))
        runout = board + draw[:missing]
        opponent_hands = (
            [draw[missing + 2 * i : missing + 2 * i + 2] for i in range(n)]
            if random_hands
            else villains
        )
        scores = [eval7.evaluate(hero + runout)] + [
            eval7.evaluate(h + runout) for h in opponent_hands
        ]
        best = max(scores)
        shares.append(1.0 / scores.count(best) if scores[0] == best else 0.0)
    mean = statistics.fmean(shares)
    return {"equity": mean, "mc_se": statistics.stdev(shares) / math.sqrt(TRIALS)}


def position(seat, hand):
    seats = sorted(p["seat"] for p in hand["players"])
    button = hand["button_seat"]
    clockwise = sorted(seats, key=lambda s: (s - button - 1) % 6)
    n = len(seats)
    if n == 2:
        return (
            "BTN/SB" if hand["blinds"].get(str(seat)) == hand["small_blind"] else "BB"
        )
    labels = ["SB", "BB"] + ["UTG", "HJ", "CO", "BTN"][-(n - 2) :]
    return labels[clockwise.index(seat)]


def allin_value(hero_seat, hole, active, contributions, board, seed):
    """Hindsight final-pot EV when all remaining actions occur on the all-in street."""
    levels = sorted({v for v in contributions.values() if v > 0})
    pots = []
    previous = 0
    for level in levels:
        contributors = [s for s, v in contributions.items() if v >= level]
        eligible = [s for s in contributors if s in active]
        assert eligible
        pots.append(((level - previous) * len(contributors), eligible))
        previous = level
    dead = {c for h in hole.values() for c in h} | set(board)
    deck = [c for c in DECK if c not in dead]
    rng = random.Random(seed)
    winnings = []
    for _ in range(TRIALS):
        runout = board + rng.sample(deck, 5 - len(board))
        scores = {s: eval7.evaluate(hole[s] + runout) for s in active}
        won = 0
        for amount, eligible in pots:
            if hero_seat not in eligible:
                continue
            best = max(scores[s] for s in eligible)
            winners = [s for s in eligible if scores[s] == best]
            if hero_seat in winners:
                won += amount / len(winners)
        winnings.append(won - contributions[hero_seat])
    return statistics.fmean(winnings), statistics.stdev(winnings) / math.sqrt(TRIALS)


def process(path):
    data = json.loads(Path(path).read_bytes())
    target = next(s for s in data["seats"] if s["entry"]["id"] == ENTRY)
    seat = target["seat"]
    submission = target["entry"]["submission_name"]
    big_blind = data["format"]["big_blind"]
    match_result = next(r for r in data["results"] if r["entry_id"] == ENTRY)
    decisions, hand_rows = [], []
    for hand in data["hands"]:
        players = {p["seat"]: p for p in hand["players"]}
        if seat not in players:
            continue
        hole = {s: [eval7.Card(c) for c in p["hole_cards"]] for s, p in players.items()}
        dead = [c for h in hole.values() for c in h]
        assert len(dead) == len(set(dead)), data["id"]
        active = set(players)
        stacks = {
            s: p["starting_stack"] - hand["blinds"].get(str(s), 0)
            for s, p in players.items()
        }
        contributions = {s: hand["blinds"].get(str(s), 0) for s in players}
        hand_start = len(decisions)
        preflop_raise = False
        preflop_voluntary = False
        cache = {}
        for index, action in enumerate(hand["actions"]):
            actor = action["seat"]
            assert math.isclose(
                stacks[actor] + action["chip_change"], action["stack_after"]
            ), (data["id"], index)
            if actor == seat:
                assert seat in active
                board = [eval7.Card(c) for c in action["board"]]
                assert action["board"] == hand["board"][: len(board)]
                opponents = sorted(active - {seat})
                assert opponents, (data["id"], hand["hand_number"], index)
                key = (tuple(action["board"]), tuple(opponents))
                if key not in cache:
                    seed_text = f"{data['id']}:{hand['hand_number']}:{key}"
                    seed = int.from_bytes(
                        hashlib.sha256(seed_text.encode()).digest()[:8], "big"
                    )
                    fixed = equity(
                        hole[seat], [hole[s] for s in opponents], board, dead, seed
                    )
                    uniform = equity(
                        hole[seat],
                        [hole[s] for s in opponents],
                        board,
                        dead,
                        seed + 1,
                        True,
                    )
                    cache[key] = fixed, uniform
                fixed, uniform = cache[key]
                call_cost = min(action["to_call"], stacks[seat])
                pot = action["pot_before"]
                odds = call_cost / (pot + call_cost) if call_cost else None
                heads_up = len(opponents) == 1
                other = opponents[0]
                # A HU call closes betting on the river or against an all-in.
                # Reject unmatched commitments, which imply side-pot/refund issues.
                equal_commitments = (
                    contributions[seat] + call_cost == contributions[other]
                )
                no_sidepot = (
                    equal_commitments
                    and max(contributions.values()) <= contributions[other]
                )
                terminal_call = bool(
                    heads_up
                    and call_cost > 0
                    and no_sidepot
                    and (len(board) == 5 or stacks[other] == 0)
                )
                r = {
                    "match_id": data["id"],
                    "submission": submission,
                    "hand_number": hand["hand_number"],
                    "action_index": index,
                    "replay_url": f"https://www.pokerbots.ac/matches/{data['id']}?hand={hand['hand_number']}",
                    "seat": seat,
                    "position": position(seat, hand),
                    "players_dealt": len(players),
                    "street": action["street"],
                    "hole_cards": players[seat]["hole_cards"],
                    "board": action["board"],
                    "active_opponents": opponents,
                    "opponent_cards_oracle": {
                        str(s): players[s]["hole_cards"] for s in opponents
                    },
                    "action": action["action"],
                    "tool_args": action["tool_args"],
                    "pot_bb": pot / big_blind,
                    "call_cost_bb": call_cost / big_blind,
                    "stack_before_bb": stacks[seat] / big_blind,
                    "hero_allin": action["stack_after"] == 0
                    and action["chip_change"] < 0,
                    "invested_bb": -action["chip_change"] / big_blind,
                    "call_pot_odds": odds,
                    "oracle_equity": fixed["equity"],
                    "oracle_mc_se": fixed["mc_se"],
                    "uniform_equity": uniform["equity"],
                    "uniform_mc_se": uniform["mc_se"],
                    "trials": TRIALS,
                    "oracle_call_edge": fixed["equity"] - odds
                    if odds is not None
                    else None,
                    "uniform_call_edge": uniform["equity"] - odds
                    if odds is not None
                    else None,
                    "terminal_hu_call_opportunity": terminal_call,
                    "terminal_oracle_call_ev_bb": (
                        fixed["equity"] * (pot + call_cost) - call_cost
                    )
                    / big_blind
                    if terminal_call
                    else None,
                    "unopened_preflop": action["street"] == "preflop"
                    and not preflop_voluntary,
                    "facing_preflop_raise": action["street"] == "preflop"
                    and preflop_raise,
                    "hand_net_bb": hand["deltas"].get(str(seat), 0) / big_blind,
                    "format_error": action["format_error"],
                    "fallback": action["fallback"],
                    "coerced": action["coerced"],
                    "token_cap": action["token_cap"],
                    "error": action["error"],
                    "afk_reason": action["afk_reason"],
                    "tokens": action["tokens"],
                    "latency_s": action["latency_s"],
                }
                decisions.append(r)
            if action["action"] == "fold":
                active.discard(actor)
            stacks[actor] = action["stack_after"]
            contributions[actor] -= action["chip_change"]
            if action["street"] == "preflop":
                preflop_raise |= action["action"] in ["bet", "raise"]
                preflop_voluntary |= (
                    action["action"] in ["bet", "raise", "call"]
                    and action["chip_change"] < 0
                )
        own = decisions[hand_start:]
        pre = [r for r in own if r["street"] == "preflop"]
        vpip = any(
            r["action"] in ["bet", "raise", "call"] and r["invested_bb"] > 0
            for r in pre
        )
        pfr = any(r["action"] in ["bet", "raise"] for r in pre)
        first = pre[0] if pre else None
        lock = next((r for r in own if r["hero_allin"]), None)
        allin_ev = allin_se = None
        if lock and all(
            len(a["board"]) == len(lock["board"])
            for a in hand["actions"][lock["action_index"] + 1 :]
        ):
            seed = int.from_bytes(
                hashlib.sha256(
                    f"allin:{data['id']}:{hand['hand_number']}".encode()
                ).digest()[:8],
                "big",
            )
            allin_ev, allin_se = allin_value(
                seat,
                hole,
                active,
                contributions,
                [eval7.Card(c) for c in lock["board"]],
                seed,
            )
            allin_ev /= big_blind
            allin_se /= big_blind
        hand_rows.append(
            {
                "match_id": data["id"],
                "submission": submission,
                "hand_number": hand["hand_number"],
                "position": position(seat, hand),
                "players_dealt": len(players),
                "hole_cards": players[seat]["hole_cards"],
                "net_bb": hand["deltas"].get(str(seat), 0) / big_blind,
                "vpip": vpip,
                "pfr": pfr,
                "limp_only": vpip and not pfr,
                "open_opportunity": bool(first and first["unopened_preflop"]),
                "open_action": first["action"]
                if first and first["unopened_preflop"]
                else None,
                "table_showdown": hand["showdown"],
                "hero_showdown": hand["showdown"] and seat in active,
                "decisions": len(own),
                "allin_lock_street": lock["street"] if lock else None,
                "allin_final_pots_ev_bb": allin_ev,
                "allin_final_pots_mc_se_bb": allin_se,
                "allin_luck_bb": hand["deltas"].get(str(seat), 0) / big_blind - allin_ev
                if allin_ev is not None
                else None,
                "format_error": any(r["format_error"] for r in own),
                "postflop": any(r["street"] != "preflop" for r in own),
                "eliminated": hand["stacks_after"][str(seat)] == 0,
                "match_place": match_result["place"],
            }
        )
    return decisions, hand_rows


def average(values):
    values = [v for v in values if v is not None]
    return statistics.fmean(values) if values else None


def decision_stats(rows):
    facing = [r for r in rows if r["call_cost_bb"] > 0]
    calls = [r for r in facing if r["action"] == "call"]
    folds = [r for r in facing if r["action"] == "fold"]
    terminal = [
        r
        for r in rows
        if r["terminal_hu_call_opportunity"] and r["action"] in ["call", "fold"]
    ]
    return {
        "n": len(rows),
        "actions": dict(Counter(r["action"] for r in rows)),
        "format_errors": sum(r["format_error"] for r in rows),
        "coerced": sum(r["coerced"] for r in rows),
        "token_caps": sum(r["token_cap"] for r in rows),
        "mean_oracle_equity": average([r["oracle_equity"] for r in rows]),
        "mean_uniform_equity": average([r["uniform_equity"] for r in rows]),
        "facing_bet": len(facing),
        "calls_facing_bet": len(calls),
        "calls_oracle_below_odds_by_5pp": sum(
            r["oracle_call_edge"] < -0.05 for r in calls
        ),
        "calls_uniform_below_odds_by_5pp": sum(
            r["uniform_call_edge"] < -0.05 for r in calls
        ),
        "folds_oracle_above_odds_by_10pp": sum(
            r["oracle_call_edge"] > 0.10 for r in folds
        ),
        "folds_uniform_above_odds_by_10pp": sum(
            r["uniform_call_edge"] > 0.10 for r in folds
        ),
        "terminal_hu_calls_or_folds": len(terminal),
        "terminal_hindsight_call_regret_bb": sum(
            max(0, -r["terminal_oracle_call_ev_bb"])
            for r in terminal
            if r["action"] == "call"
        ),
        "terminal_hindsight_fold_regret_bb": sum(
            max(0, r["terminal_oracle_call_ev_bb"])
            for r in terminal
            if r["action"] == "fold"
        ),
    }


def hand_stats(rows):
    opened = [r for r in rows if r["open_opportunity"]]
    n = len(rows)
    return {
        "hands": n,
        "net_bb": sum(r["net_bb"] for r in rows),
        "bb_per_100": 100 * average([r["net_bb"] for r in rows]) if rows else None,
        "vpip_pct": 100 * sum(r["vpip"] for r in rows) / n if n else None,
        "pfr_pct": 100 * sum(r["pfr"] for r in rows) / n if n else None,
        "limp_only_pct": 100 * sum(r["limp_only"] for r in rows) / n if n else None,
        "open_opportunities": len(opened),
        "open_actions": dict(Counter(r["open_action"] for r in opened)),
        "format_error_hands": sum(r["format_error"] for r in rows),
        "hero_showdown_hands": sum(r["hero_showdown"] for r in rows),
        "hero_showdown_net_bb": sum(r["net_bb"] for r in rows if r["hero_showdown"]),
        "nonshowdown_net_bb": sum(r["net_bb"] for r in rows if not r["hero_showdown"]),
        "allin_final_pots_hands": sum(
            r["allin_final_pots_ev_bb"] is not None for r in rows
        ),
        "allin_final_pots_ev_bb": sum(r["allin_final_pots_ev_bb"] or 0 for r in rows),
        "allin_luck_bb": sum(r["allin_luck_bb"] or 0 for r in rows),
        "eliminations": sum(r["eliminated"] for r in rows),
    }


def grouped(rows, key, summarize):
    groups = defaultdict(list)
    for row in rows:
        groups[key(row)].append(row)
    return {
        str(k): summarize(v)
        for k, v in sorted(groups.items(), key=lambda kv: str(kv[0]))
    }


def bootstrap_matches():
    """Descriptive whole-match bootstrap; no paired or causal comparison."""
    matches = [json.loads(line) for line in (ROOT / "matches.jsonl").open()]
    rng = random.Random(20261115)
    results = {}
    for submission in sorted({r["entry"]["submission_name"] for r in matches}):
        rows = [
            r["result"] for r in matches if r["entry"]["submission_name"] == submission
        ]
        fields = {}
        for field in ["net_bb", "ev_net_bb"]:
            samples = []
            for _ in range(5000):
                sample = rng.choices(rows, k=len(rows))
                samples.append(
                    100
                    * math.fsum(r[field] for r in sample)
                    / sum(r["hands"] for r in sample)
                )
            samples.sort()
            fields[field] = {
                "bb_per_100": 100
                * math.fsum(r[field] for r in rows)
                / sum(r["hands"] for r in rows),
                "match_bootstrap_95_percentile_ci": [samples[124], samples[4874]],
            }
        results[submission] = fields
    (OUT / "match_bootstrap.json").write_text(
        json.dumps(
            {
                "resamples": 5000,
                "seed": 20261115,
                "unit": "whole match",
                "results": results,
            },
            indent=2,
        )
        + "\n"
    )


def main():
    OUT.mkdir(exist_ok=True)
    files = sorted((ROOT / "raw").glob("*.json"))
    decisions, hands = [], []
    with ProcessPoolExecutor(max_workers=4) as pool:
        for i, (dd, hh) in enumerate(pool.map(process, map(str, files)), 1):
            decisions.extend(dd)
            hands.extend(hh)
            if i % 10 == 0:
                print(
                    f"Analyzed {i}/{len(files)} matches; {len(decisions)} decisions",
                    flush=True,
                )
    for name, rows in [
        ("decision_equity.jsonl", decisions),
        ("hand_features.jsonl", hands),
    ]:
        with (OUT / name).open("w") as output:
            for row in rows:
                output.write(json.dumps(row, separators=(",", ":")) + "\n")

    def band(r):
        x = r["oracle_equity"]
        return (
            "0-20%"
            if x < 0.2
            else "20-40%"
            if x < 0.4
            else "40-60%"
            if x < 0.6
            else "60-80%"
            if x < 0.8
            else "80-100%"
        )

    summary = {
        "method": {
            "eval7_version": version("eval7"),
            "trials_per_context_per_estimator": TRIALS,
            "python_version": sys.version,
            "entry": ENTRY,
            "matches": len(files),
            "decisions": len(decisions),
            "hands": len(hands),
            "seed": "SHA256(match ID, hand number, board, active opponent seats)",
            "oracle": "Actual active opponent cards; all dealt hole cards removed from runout deck.",
            "uniform": "Uniform random opponent hands; only hero cards and current board blocked.",
            "ties": "Split the pot equally among tied winners; multiway, not pairwise averaging.",
        },
        "hands_by_submission": grouped(hands, lambda r: r["submission"], hand_stats),
        "hands_by_submission_position": grouped(
            hands, lambda r: (r["submission"], r["position"]), hand_stats
        ),
        "hands_by_submission_preflop": grouped(
            hands,
            lambda r: (
                r["submission"],
                "raised"
                if r["pfr"]
                else "limped_or_called"
                if r["vpip"]
                else "no_vpip",
            ),
            hand_stats,
        ),
        "decisions_by_submission": grouped(
            decisions, lambda r: r["submission"], decision_stats
        ),
        "decisions_by_submission_street": grouped(
            decisions, lambda r: (r["submission"], r["street"]), decision_stats
        ),
        "decisions_by_submission_street_equity": grouped(
            decisions, lambda r: (r["submission"], r["street"], band(r)), decision_stats
        ),
        "errors_by_reason": dict(
            Counter(
                str(r["error"] or r["afk_reason"])
                for r in decisions
                if r["format_error"]
            )
        ),
        "error_equity": grouped(
            [r for r in decisions if r["format_error"]],
            lambda r: r["submission"],
            decision_stats,
        ),
    }
    (OUT / "metrics.json").write_text(json.dumps(summary, indent=2) + "\n")
    examples = {
        "largest_winning_hands": sorted(hands, key=lambda r: -r["net_bb"])[:15],
        "largest_losing_hands": sorted(hands, key=lambda r: r["net_bb"])[:15],
        "high_equity_format_errors": sorted(
            [r for r in decisions if r["format_error"]],
            key=lambda r: -r["oracle_equity"],
        )[:15],
        "terminal_bad_calls_hindsight": sorted(
            [
                r
                for r in decisions
                if r["terminal_hu_call_opportunity"]
                and r["action"] == "call"
                and r["terminal_oracle_call_ev_bb"] < 0
            ],
            key=lambda r: r["terminal_oracle_call_ev_bb"],
        )[:15],
        "terminal_missed_calls_hindsight": sorted(
            [
                r
                for r in decisions
                if r["terminal_hu_call_opportunity"]
                and r["action"] == "fold"
                and r["terminal_oracle_call_ev_bb"] > 0
            ],
            key=lambda r: -r["terminal_oracle_call_ev_bb"],
        )[:15],
    }
    (OUT / "examples.json").write_text(json.dumps(examples, indent=2) + "\n")
    bootstrap_matches()
    print(
        json.dumps(
            {
                k: summary[k]
                for k in [
                    "hands_by_submission",
                    "decisions_by_submission",
                    "errors_by_reason",
                ]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

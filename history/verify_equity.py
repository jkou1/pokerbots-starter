"""Check evaluator semantics and join every equity row back to its source action."""

import json
import math

import eval7
from analyze_equity import OUT, ROOT, TRIALS, allin_value, equity


def cards(text):
    return [eval7.Card(c) for c in text.split()]


def main():
    hero, villain, board = cards("Ah Kh"), cards("2c 2d"), cards("Qh Jh Th 3c 4d")
    assert equity(hero, [villain], board, hero + villain, 1)["equity"] == 1
    hero, villains, board = (
        cards("2c 2d"),
        [cards("3c 3d"), cards("4c 4d")],
        cards("Ah Kh Qh Jh Th"),
    )
    assert math.isclose(
        equity(hero, villains, board, hero + [c for h in villains for c in h], 1)[
            "equity"
        ],
        1 / 3,
    )
    hole = {0: cards("As Ad"), 1: cards("Ah Kh"), 2: cards("Ks Kd")}
    mean, se = allin_value(
        0, hole, {0, 1, 2}, {0: 100, 1: 50, 2: 100}, cards("2h 3h 4h 5h 9c"), 123
    )
    assert mean == 0 and se == 0  # Lose the main pot, win the side pot.
    args = cards("As Ad"), [cards("Kc Kd")], [], cards("As Ad Kc Kd"), 123
    value = equity(*args)
    assert 0.76 < value["equity"] < 0.88
    assert value == equity(*args)
    original = [json.loads(line) for line in (ROOT / "decisions.jsonl").open()]
    computed = [json.loads(line) for line in (OUT / "decision_equity.jsonl").open()]
    key = lambda r: (r["match_id"], r["hand_number"], r["action_index"])
    source = {key(r): r for r in original}
    assert len(source) == len(original) == len(computed)
    assert len({key(r) for r in computed}) == len(computed)
    raw = {p.stem: json.loads(p.read_bytes()) for p in (ROOT / "raw").glob("*.json")}
    for row in computed:
        action = source[key(row)]["action"]
        assert row["board"] == action["board"]
        assert row["action"] == action["action"]
        assert row["trials"] == TRIALS == 1000
        for estimator in ["oracle", "uniform"]:
            assert 0 <= row[f"{estimator}_equity"] <= 1
            assert 0 <= row[f"{estimator}_mc_se"] <= 0.5 / math.sqrt(TRIALS - 1) + 1e-10
        if row["call_cost_bb"]:
            assert math.isclose(
                row["call_pot_odds"],
                row["call_cost_bb"] / (row["pot_bb"] + row["call_cost_bb"]),
            )
        else:
            assert row["call_pot_odds"] is None
        # River fixed-card equity has no runout sampling uncertainty.
        if len(row["board"]) == 5:
            assert row["oracle_mc_se"] == 0
    hands = [json.loads(line) for line in (OUT / "hand_features.jsonl").open()]
    for row in hands:
        hand = next(
            h
            for h in raw[row["match_id"]]["hands"]
            if h["hand_number"] == row["hand_number"]
        )
        seat = next(
            s["seat"]
            for s in raw[row["match_id"]]["seats"]
            if s["entry"]["id"] == "org_cd68943dd947"
        )
        assert row["eliminated"] == (hand["stacks_after"][str(seat)] == 0)
    print(
        f"Verified {len(computed)} decision equities and {len(hands)} hand features; evaluator sanity checks passed."
    )


if __name__ == "__main__":
    main()

"""Print preflop showdown equities for the calculated hint.

Run: cd harness && uv run --with eval7 python ../opsd/hint_monte_carlo.py
The strong range is 77+, A9s+, AJo+, KJs+, QJs, JTs, KQo (132 combinations).
"""

import argparse

import eval7

HEROES = {
    "AA": "AcAd", "KK": "KcKd", "QQ": "QcQd", "TT": "TcTd", "22": "2c2d",
    "AKs": "AcKc", "AKo": "AcKd", "AQs": "AcQc", "AJo": "AcJd", "KQs": "KcQc",
    "QJs": "QcJc", "JTs": "JcTc", "76s": "7c6c", "72o": "7c2d",
}
STRONG = eval7.HandRange("77+, A9s+, AJo+, KJs+, QJs, JTs, KQo")
RANKS = "AKQJT98765432"
ALL_HANDS = eval7.HandRange(", ".join(
    [a + b + kind for i, a in enumerate(RANKS) for b in RANKS[i + 1:] for kind in ("s", "o")]
    + [rank * 2 for rank in RANKS]
))


def equities(heroes, opponents, trials):
    results = eval7.py_all_hands_vs_range(heroes, opponents, [], trials)
    return {frozenset(hand): value for hand, value in results.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=100_000)
    args = parser.parse_args()
    heroes = eval7.HandRange(", ".join(HEROES.values()))
    columns = [equities(heroes, opponents, args.trials) for opponents in (ALL_HANDS, STRONG)]
    print(f"trials per cell={args.trials}, strong range={len(STRONG)}/1326 combinations")
    print("| Hand | vs random | vs strong 10% |\n| --- | ---: | ---: |")
    for label, cards in HEROES.items():
        hand = frozenset(eval7.Card(code) for code in (cards[:2], cards[2:]))
        print(f"| {label} | {columns[0][hand]:.1%} | {columns[1][hand]:.1%} |")


if __name__ == "__main__":
    main()

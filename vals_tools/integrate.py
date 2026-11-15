"""Export successful talk targets on official observations, without fixed-action helpers.

Requires matched silence controls and positive game-level bootstrap evidence across seeds.
"""

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

from vals_tools.arena import write_json, write_jsonl
from vals_tools.export_policy import policy_records
from vals_tools.game_score import bootstrap
from vals_tools.game_study import fingerprint
from vals_tools.pete import split_for
from vals_tools.talk_experiment import ORDINARY


def integration_records(experiments, min_seeds=6):
    by_seed = defaultdict(dict)
    splits = defaultdict(set)
    for experiment in experiments:
        splits[experiment["seed"]].add(
            experiment.get("split", split_for(str(experiment["seed"])))
        )
    if any(len(values) > 1 for values in splits.values()):
        raise ValueError(
            "talk seeds cannot cross training, selection and evaluation splits"
        )
    reference = {
        fingerprint(e["model_identity"]) for e in experiments if e.get("model_identity")
    }
    if len(reference) > 1:
        raise ValueError(
            "talk targets require one frozen reference policy for both training arms"
        )
    for result in experiments:
        if result.get("status") != "complete":
            continue
        seed = result["seed"]
        if result.get("split", split_for(str(seed))) != "select":
            continue  # message selection must never use training or final-evaluation outcomes
        if not result.get("model_identity") or not result.get("opponent_identity"):
            continue
        identity = fingerprint(
            result.get("opponent_identity", {"model": result.get("opponent")})
        )
        key = (seed, identity, result["policy_seat"])
        if key in by_seed:
            raise ValueError(
                "duplicate experiment seed; combine repetitions in one experiment"
            )
        groups = defaultdict(dict)
        for game in result["games"]:
            repeat = game.get("repeat", 0)
            if repeat in groups[game["message"]]:
                raise ValueError("duplicate message/repeat in talk experiment")
            groups[game["message"]][repeat] = game
        if "" not in groups or ORDINARY not in groups:
            continue
        for message, values in groups.items():
            if (
                message in ("", ORDINARY)
                or set(values) != set(groups[""])
                or set(values) != set(groups[ORDINARY])
            ):
                continue
            if any(
                g["format_errors"]
                for collection in (values, groups[""], groups[ORDINARY])
                for g in collection.values()
            ):
                continue
            by_seed[key][message] = {
                control: statistics.fmean(
                    values[r]["realized_bb"] - groups[control][r]["realized_bb"]
                    for r in values
                )
                for control in ("", ORDINARY)
            }
    messages = sorted({message for group in by_seed.values() for message in group})
    evidence = {}
    for message in messages:
        grouped = defaultdict(list)
        opponents = defaultdict(dict)
        for (seed, opponent, seat), group in by_seed.items():
            if message in group:
                grouped[seed].append(group[message])
                opponents[opponent].setdefault(seed, []).append(group[message])
        silence = [
            statistics.fmean(v[""] for v in values) for values in grouped.values()
        ]
        ordinary = [
            statistics.fmean(v[ORDINARY] for v in values) for values in grouped.values()
        ]
        interval, ordinary_interval = bootstrap(silence), bootstrap(ordinary)
        by_opponent = {
            opponent: {
                "seeds": len(seeds),
                "incremental_bb": statistics.fmean(
                    v[""] for values in seeds.values() for v in values
                ),
                "over_ordinary_bb": statistics.fmean(
                    v[ORDINARY] for values in seeds.values() for v in values
                ),
            }
            for opponent, seeds in opponents.items()
        }
        evidence[message] = {
            "seeds": len(grouped),
            "opponent_configurations": len(opponents),
            "mean_incremental_bb": statistics.fmean(silence),
            "ci95": interval,
            "ordinary_control_ci95": ordinary_interval,
            "by_opponent": by_opponent,
            "accepted": len(grouped) >= min_seeds
            and len(opponents) >= 2
            and interval[0] is not None
            and interval[0] > 0
            and ordinary_interval[0] > 0
            and all(
                o["seeds"] >= min_seeds
                and o["incremental_bb"] > 0
                and o["over_ordinary_bb"] > 0
                for o in by_opponent.values()
            ),
        }
    rows = []
    for experiment in experiments:
        if experiment.get("status") != "complete":
            continue
        if experiment.get("split", split_for(str(experiment["seed"]))) != "train":
            continue
        if not experiment.get("model_identity") or not experiment.get(
            "opponent_identity"
        ):
            continue
        for game in experiment["games"]:
            if (
                not evidence.get(game["message"], {}).get("accepted")
                or game["format_errors"]
            ):
                continue
            seat = experiment["policy_seat"]
            log = game["log"] | {"split": "train"}
            for row in policy_records(
                log, seat, experiment.get("model", "frozen-policy")
            ):
                if row["provenance"]["street"] not in ("flop", "turn", "river"):
                    continue
                row["target"]["say"] = game["message"]
                row["provenance"]["message_evidence"] = evidence[game["message"]]
                row["provenance"]["reference_identity"] = experiment["model_identity"]
                rows.append(row)
                break  # first post-flop policy decision is the nominated intervention
    return rows, evidence


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--experiments", type=Path, nargs="+", required=True)
    p.add_argument("--out", type=Path, default=Path("data/experiments/integration"))
    args = p.parse_args()
    rows, evidence = integration_records(
        [json.loads(path.read_text()) for path in args.experiments]
    )
    for split in ("train", "select", "eval"):
        write_jsonl(
            args.out / f"{split}.jsonl", [r for r in rows if r["split"] == split]
        )
    write_json(args.out / "evidence.json", evidence)
    print(
        json.dumps(
            {
                "records": len(rows),
                "accepted_messages": sum(e["accepted"] for e in evidence.values()),
            }
        )
    )


if __name__ == "__main__":
    main()

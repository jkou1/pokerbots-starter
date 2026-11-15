"""Build staged RL and official-game datasets locally; --upload publishes them to AC2."""

import argparse
import json
from pathlib import Path

from ac2.sdk import Client

from vals_tools.arena import write_jsonl
from vals_tools.tasks import Opponents, datasets, hand_tasks


def curriculum(
    prefix, opponents, stage="integration", frozen_model=None, talk_enabled=False
):
    if stage != "integration" and not frozen_model:
        raise ValueError("preflop/postflop stages require --frozen-model")
    built = datasets(prefix, opponents)
    for tasks in built.values():
        for task in tasks:
            task.env_params["record_training_metadata"] = True
    for task in built[f"{prefix}-train"]:
        task.grader_params = {
            "silence": "preflop" if stage == "talk" or talk_enabled else "all"
        }
        if stage != "integration":
            task.env_params.update(training_stage=stage, frozen_model=frozen_model)
    for split, count, seed in [
        ("game-select", 120, 7_710_001),
        ("game-eval", 300, 7_720_002),
    ]:
        tasks = hand_tasks(count, seed, opponents)
        for task in tasks:
            task.env_params["total_hands"] = 30
            task.env_params["record_training_metadata"] = True
        built[f"{prefix}-{split}"] = tasks
    return built


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--prefix", default="pokerbots-preflop")
    p.add_argument(
        "--stage",
        choices=["integration", "preflop", "postflop", "talk"],
        default="integration",
    )
    p.add_argument(
        "--enable-talk",
        action="store_true",
        help="allow post-flop talk during integration",
    )
    p.add_argument("--frozen-model")
    p.add_argument("--opponent-model", default="vals-hackathon/ac-vals-model")
    p.add_argument("--project", default="vals-hackathon")
    p.add_argument("--out", type=Path, default=Path("data/experiments/tasks"))
    p.add_argument("--upload", action="store_true")
    args = p.parse_args()
    built = curriculum(
        args.prefix,
        Opponents(args.opponent_model, api="chat", reasoning_effort=None),
        args.stage,
        args.frozen_model,
        args.enable_talk,
    )
    client = Client(project=args.project) if args.upload else None
    for name, tasks in built.items():
        write_jsonl(
            args.out / f"{name}.jsonl", (t.model_dump(mode="json") for t in tasks)
        )
        if client:
            client.datasets.create(
                name, description=f"{args.stage} curriculum", exist_ok=True
            )
            for start in range(0, len(tasks), 500):
                client.datasets.add_tasks(name, tasks=tasks[start : start + 500])
        print(
            json.dumps({"dataset": name, "tasks": len(tasks), "uploaded": bool(client)})
        )


if __name__ == "__main__":
    main()

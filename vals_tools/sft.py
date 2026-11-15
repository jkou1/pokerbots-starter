"""Upload canonical training records or launch supervised training; defaults to dry-run.

python -m vals_tools.sft --records data/arena/pete-preflop/train.jsonl --dataset pokerbots-pete-train
Add --upload to upload; add --launch to start training. --replay mixes clean parent targets 50:50.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
from datetime import UTC, datetime
from pathlib import Path

from ac2.runtime import compute_content_hash
from ac2.sdk import Client
from ac2.sdk.run_config import (
    EvalConfig,
    ExperimentConfig,
    InternalConfig,
    InternalLaunchConfig,
    RolloutConfig,
    RunConfig,
    SFTConfig,
    StepConfig,
    TasksConfig,
    TrainDatasetConfig,
    TrainerConfig,
)

from vals_tools.arena import read_jsonl, write_json
from vals_tools.training import SFT_TARGET_FORMAT, model_source, supervised_task


def training_rows(records, replay=None):
    rows = read_jsonl(records)
    if not rows or any(r.get("split") != "train" for r in rows):
        raise ValueError("training requires nonempty, exclusively train-split records")
    if replay:
        clean = read_jsonl(replay)
        if not clean or any(r.get("split") != "train" for r in clean):
            raise ValueError("replay requires nonempty train-split records")
        rng = random.Random(42)
        sampled = [copy.deepcopy(row) for row in rng.choices(clean, k=len(rows))]
        for index, row in enumerate(sampled):
            # Dataset membership deduplicates identical task contents. Keep intended replay weights
            # in metadata outside the model prompt by giving each sampled copy distinct content.
            row["sampling_copy"] = f"replay-{index}"
        rows = rows + sampled
        rng.shuffle(rows)
    else:
        random.Random(42).shuffle(rows)
    return rows


def run_config(args):
    origin = "checkpoint" if args.checkpoint else "base"
    return RunConfig(
        model=model_source(args),
        name=f"pokerbots-{args.stage}-{origin}-sft-{datetime.now(UTC):%Y%m%d-%H%M%S}",
        tags={
            "stage": args.stage,
            "dataset": args.dataset,
            "parent_checkpoint": args.checkpoint,
            "initialization": origin,
        },
        experiment_cfg=ExperimentConfig(
            method=SFTConfig(),
            step=StepConfig(
                num_train_steps=args.steps,
                problem_batch_size=args.batch,
                checkpoint_interval=args.checkpoint_every,
                samples_per_problem=1,
                seed=42,
            ),
            tasks=TasksConfig(
                datasets=(TrainDatasetConfig(ac2_dataset_name=args.dataset),),
            ),
            rollout=RolloutConfig(
                n_inference_replicas=0,
                max_response_len=args.max_response_len,
                max_total_len=args.max_total_len,
            ),
            eval=EvalConfig(mode="off"),
            trainer=TrainerConfig(
                **({"learning_rate": args.lr} if args.lr is not None else {})
            ),
        ),
        internal_cfg=InternalConfig(
            launch=InternalLaunchConfig(tensorboard_enabled=True)
        ),
    )


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--records", type=Path, required=True)
    p.add_argument("--replay", type=Path)
    p.add_argument("--dataset", required=True)
    p.add_argument("--project", default="vals-hackathon")
    source = p.add_mutually_exclusive_group()
    source.add_argument("--checkpoint")
    source.add_argument(
        "--from-base",
        action="store_true",
        help="start fresh from --model, with no checkpoint or replay requirement",
    )
    p.add_argument("--model", default="Qwen/Qwen3.6-35B-A3B")
    p.add_argument(
        "--stage",
        choices=["pete", "combined", "defense", "integration"],
        default="pete",
    )
    p.add_argument("--steps", type=int, default=20)
    p.add_argument("--batch", type=int, default=64)
    p.add_argument("--checkpoint-every", type=int, default=20)
    p.add_argument("--max-response-len", type=int)
    p.add_argument("--max-total-len", type=int)
    p.add_argument("--lr", type=float)
    p.add_argument(
        "--receipt",
        type=Path,
        help="persist exact inputs, configuration, and submitted run ID",
    )
    p.add_argument("--upload", action="store_true")
    p.add_argument("--launch", action="store_true")
    return p


def validate_launch(args):
    if args.steps < 1 or args.batch < 1 or args.checkpoint_every < 1:
        raise ValueError("steps, batch, and checkpoint interval must be positive")
    if args.lr is not None and args.lr <= 0:
        raise ValueError("learning rate must be positive")
    if args.launch and not (args.checkpoint or args.from_base):
        raise ValueError(
            "choose --from-base or --checkpoint explicitly before launching"
        )
    if args.launch and args.stage == "pete" and not args.from_base and not args.replay:
        raise ValueError(
            "checkpoint-based Pete training requires --replay; use --from-base for pure teacher SFT"
        )


def dataset_hashes(client, name):
    result, offset = set(), 0
    while True:
        page = client.datasets.list_tasks(name, limit=1000, offset=offset)
        result.update(row.content_hash for row in page)
        if len(page) < 1000:
            return result
        offset += len(page)


def main():
    p = parser()
    args = p.parse_args()
    try:
        validate_launch(args)
    except ValueError as exc:
        p.error(str(exc))
    rows = training_rows(args.records, args.replay)
    tasks = [supervised_task(row) for row in rows]
    if args.stage == "pete" and any(
        r.get("provenance", {}).get("street") != "preflop" for r in rows
    ):
        p.error("Pete training accepts pre-flop targets only")
    config = run_config(args)
    print(
        json.dumps(
            {"records": len(tasks), "config": config.to_json()}, indent=2, default=str
        )
    )
    receipt = (
        args.receipt
        or args.records.parent
        / f"sft-{args.stage}-{'base' if args.from_base else 'checkpoint'}.json"
    )
    if (
        args.launch
        and receipt.exists()
        and json.loads(receipt.read_text()).get("train_id")
    ):
        p.error(
            f"a run is already recorded in {receipt}; choose a new receipt for a new experiment"
        )
    manifest = {
        "status": "prepared",
        "dataset": args.dataset,
        "records": len(tasks),
        "target_format": SFT_TARGET_FORMAT,
        "source_sha256": hashlib.sha256(args.records.read_bytes()).hexdigest(),
        "replay_sha256": hashlib.sha256(args.replay.read_bytes()).hexdigest()
        if args.replay
        else None,
        "config": config.to_json(),
    }
    if args.upload or args.launch:
        write_json(receipt, manifest)
    if args.upload or args.launch:
        client = Client(project=args.project)
        client.datasets.create(
            args.dataset,
            description=f"{args.stage}: canonical final-reply supervision",
            exist_ok=True,
        )
        expected = {compute_content_hash(task) for task in tasks}
        if not dataset_hashes(client, args.dataset).issubset(expected):
            raise ValueError(
                "existing dataset contains unexpected tasks; use a fresh dataset name"
            )
        for start in range(0, len(tasks), 500):
            client.datasets.add_tasks(args.dataset, tasks=tasks[start : start + 500])
        actual = dataset_hashes(client, args.dataset)
        if actual != expected:
            raise ValueError(
                "uploaded dataset does not match the validated training tasks"
            )
        manifest.update(
            status="uploaded",
            unique_tasks=len(actual),
            uploaded_task_hashes_sha256=hashlib.sha256(
                "\n".join(sorted(actual)).encode()
            ).hexdigest(),
        )
        write_json(receipt, manifest)
        if args.launch:
            train_id = client.train.run(config).train_id
            manifest.update(status="submitted", train_id=train_id)
            write_json(receipt, manifest)
            print(
                json.dumps(
                    {
                        "train_id": train_id,
                        "initialization": "base" if args.from_base else args.checkpoint,
                    }
                )
            )


if __name__ == "__main__":
    main()

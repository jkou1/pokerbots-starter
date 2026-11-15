"""Build selected-parent pre-flop OPSD data and optionally launch a distillation pilot.

Requires explicit parent checkpoint and source deployment. --wait waits for a complete trace export.
"""

import argparse
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

from ac2.sdk import Client

from opsd.build_dataset import decision_tasks
from opsd.hint import PRE_FLOP_HINT
from opsd.train import parser as training_parser
from opsd.train import run_config
from vals_tools.arena import read_jsonl, write_json


def prepare(traces, deployment):
    tasks, totals = [], {}
    hands = 0
    seen = set()
    for trace in traces:
        if trace.get("model") != deployment or trace.get("split") != "train":
            raise ValueError(
                "traces must come from the selected parent deployment's train split"
            )
        identity = trace.get("trace_id")
        if not identity or identity in seen:
            raise ValueError("training traces must identify distinct hands")
        seen.add(identity)
        built, stats = decision_tasks(trace, PRE_FLOP_HINT, 5000, "preflop")
        tasks.extend(built)
        hands += bool(built)
        for key, value in stats.items():
            totals[key] = totals.get(key, 0) + value
    if hands < 8:
        raise ValueError(
            f"need at least eight distinct usable training hands, found {hands}"
        )
    return tasks, totals


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--deployment", required=True)
    p.add_argument("--traces", type=Path, required=True)
    p.add_argument("--dataset", default="pokerbots-principles-step2-v1-train")
    p.add_argument("--project", default="vals-hackathon")
    p.add_argument("--steps", type=int, default=2)
    p.add_argument("--batch", type=int, default=8)
    p.add_argument("--lr", type=float, default=1e-6)
    p.add_argument("--wait", action="store_true")
    p.add_argument("--launch", action="store_true")
    args = p.parse_args()
    receipt = args.traces.parent / "principles-run.json"
    if receipt.exists() and json.loads(receipt.read_text()).get("train_id"):
        p.error(
            "this trace collection already launched a run; inspect principles-run.json"
        )
    status = {
        "checkpoint": args.checkpoint,
        "deployment": args.deployment,
        "dataset": args.dataset,
        "status": "waiting_for_traces",
    }
    if args.wait:
        write_json(receipt, status)
        while not args.traces.exists():
            time.sleep(10)
    tasks, stats = prepare(read_jsonl(args.traces), args.deployment)
    arguments = [
        "--dataset",
        args.dataset,
        "--checkpoint",
        args.checkpoint,
        "--steps",
        str(args.steps),
        "--batch",
        str(args.batch),
        "--checkpoint-every",
        str(args.steps),
        "--lr",
        str(args.lr),
    ]
    config = run_config(
        training_parser().parse_args(arguments),
        f"pokerbots-principles-pilot-{datetime.now(UTC):%Y%m%d-%H%M%S}",
    )
    config.tags.update(
        stage="preflop-principles", parent_checkpoint=args.checkpoint, pilot=True
    )
    status.update(
        status="prepared",
        tasks=len(tasks),
        statistics=stats,
        trace_sha256=hashlib.sha256(args.traces.read_bytes()).hexdigest(),
        config=config.to_json(),
    )
    write_json(receipt, status)
    print(
        json.dumps(
            {"tasks": len(tasks), "checkpoint": args.checkpoint, "launch": args.launch}
        ),
        flush=True,
    )
    if args.launch:
        client = Client(project=args.project)
        # Check deployment identity at submission time, not merely when collection began.
        name = args.deployment.rsplit("/", 1)[-1]
        deployed = [d for d in client.inference.list() if d.name == name]
        if (
            len(deployed) != 1
            or client.inference.get(deployed[0].id).checkpoint_id != args.checkpoint
        ):
            raise ValueError(
                "source deployment does not match the requested parent checkpoint"
            )
        client.datasets.create(args.dataset, required_types=["hinted"], exist_ok=True)
        for start in range(0, len(tasks), 500):
            client.datasets.add_tasks(args.dataset, tasks=tasks[start : start + 500])
        status.update(status="submitted", train_id=client.train.run(config).train_id)
        write_json(receipt, status)
        print(
            json.dumps(
                {"train_id": status["train_id"], "parent_checkpoint": args.checkpoint}
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()

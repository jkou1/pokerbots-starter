"""Prepare an audited shared curriculum and launch either arm of the paired study.

Preparation is local; training defaults to dry-run. Both arms use the same dataset,
order, fresh optimizer configuration and incremental budget. Existing receipts
prevent accidental duplicate launches; historical checkpoint compute is separate.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import httpx
from ac2.runtime import compute_content_hash

from vals_tools import sft
from vals_tools.arena import read_jsonl, write_json, write_jsonl
from vals_tools.defense import MESSAGES, perturb
from vals_tools.pete_eval import legal_prediction
from vals_tools.training import (
    PROTOCOL_MARKER,
    SFT_TARGET_FORMAT,
    TOOLS,
    supervised_task,
)

PARENT = "ckpt_51eee61470f7"
MODEL = "Qwen/Qwen3.6-35B-A3B"
TOKENIZER_REVISION = "345d467b117d1fd5eda9b879a5988de9ae5f47a7"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def group(row):
    if identity := row.get("deal_identity"):
        return identity
    if (seed := row.get("provenance", {}).get("seed")) is not None:
        return f"seed:{seed}"
    raise ValueError("every example needs a deal_identity or source seed")


def check_disjoint(train, holdouts, history=()):
    trained = {group(r) for r in [*train, *history]}
    held = defaultdict(set)
    for row in holdouts:
        if row.get("split") not in ("select", "eval"):
            raise ValueError("holdout inputs must contain only select/eval records")
        identity = group(row)
        if identity in trained:
            raise ValueError("a held-out deal overlaps new or historical training")
        held[row["split"]].add(identity)
    if held["select"] & held["eval"]:
        raise ValueError("selection and final evaluation deals overlap")


def target_text(row):
    # Qwen's XML function-call format, captured in actual managed-trainer token
    # samples. Counts must still be checked against sft_audit after an update.
    parameters = "\n".join(
        f"<parameter={key}>\n{value if isinstance(value, str) else json.dumps(value)}\n</parameter>"
        for key, value in row["target"].items()
    )
    return (
        f"{PROTOCOL_MARKER}\n</think>\n\n<tool_call>\n"
        f"<function={row.get('tool', 'submit_action')}>\n{parameters}\n"
        "</function>\n</tool_call><|im_end|>\n"
    )


def token_counter(path):
    from tokenizers import Tokenizer

    tokenizer = Tokenizer.from_file(str(path))
    return lambda text: len(tokenizer.encode(text, add_special_tokens=False).ids)


def download_tokenizer(directory):
    path = directory / "tokenizer.json"
    receipt = directory / "release.json"
    if path.exists() or receipt.exists():
        metadata = json.loads(receipt.read_text())
        if metadata != {
            "model": MODEL,
            "revision": TOKENIZER_REVISION,
            "sha256": sha(path),
        }:
            raise ValueError(
                "existing tokenizer does not match the pinned model revision"
            )
        return metadata
    response = httpx.get(
        f"https://huggingface.co/{MODEL}/resolve/{TOKENIZER_REVISION}/tokenizer.json",
        follow_redirects=True,
        timeout=120,
    )
    response.raise_for_status()
    directory.mkdir(parents=True, exist_ok=True)
    path.write_bytes(response.content)
    metadata = {"model": MODEL, "revision": TOKENIZER_REVISION, "sha256": sha(path)}
    write_json(receipt, metadata)
    return metadata


def sampler(rows, rng):
    buckets = defaultdict(list)
    for row in rows:
        key = (
            row["provenance"]["street"],
            row.get("position"),
            row["target"].get("action", "cleanup"),
        )
        buckets[key].append(row)
    keys = sorted(buckets, key=str)
    if not keys:
        raise ValueError("a required training source is empty")
    for values in buckets.values():
        rng.shuffle(values)
    indices = Counter()
    while True:
        rng.shuffle(keys)
        for key in keys:
            values = buckets[key]
            yield copy.deepcopy(values[indices[key] % len(values)])
            indices[key] += 1


def curriculum(
    pokerbench,
    arena,
    cleanup,
    count_tokens,
    *,
    count=4096,
    holdouts=(),
    history=(),
    seed=42,
):
    if count < 20:
        raise ValueError("curriculum requires at least 20 records")
    sources = {"pokerbench": pokerbench, "arena": arena, "cleanup": cleanup}
    for source, rows in sources.items():
        if not rows or any(r.get("split") != "train" for r in rows):
            raise ValueError(
                f"{source} requires nonempty, exclusively train-split records"
            )
        for row in rows:
            supervised_task(row)
            group(row)
            if source == "cleanup":
                if (
                    row.get("tool") != "update_scratchpad"
                    or row["provenance"].get("teacher") != "public-facts"
                ):
                    raise ValueError(
                        "cleanup must use explicitly factual public targets"
                    )
            elif row.get(
                "tool", "submit_action"
            ) != "submit_action" or not legal_prediction(row, row["target"]):
                raise ValueError("action sources require replay-verified legal targets")
            if row["provenance"]["street"] not in (
                "preflop",
                "flop",
                "turn",
                "river",
                "cleanup",
            ):
                raise ValueError("unknown training street")
    check_disjoint(pokerbench + arena + cleanup, holdouts, history)
    rng = random.Random(seed)
    generators = {name: sampler(rows, rng) for name, rows in sources.items()}
    quotas = {"pokerbench": count // 2, "cleanup": round(count * 0.05)}
    quotas["arena"] = count - sum(quotas.values())
    result = []
    for name, quota in quotas.items():
        for _ in range(quota):
            row = next(generators[name])
            row["curriculum_source"] = name
            result.append(row)
    # Identical perturbations in both arms. Ordinary and instruction-like chatter
    # keep the clean betting target; the actual source split remains unchanged.
    for index, row in enumerate(result):
        if index % 5 == 0:
            category, message = MESSAGES["train"][index % len(MESSAGES["train"])]
            changed = perturb(row, message)
            if changed["perturbation"]["changed"]:
                changed["perturbation"]["category"] = category
                result[index] = changed
    sizes = [count_tokens(target_text(row)) for row in result]
    cleanup_tokens = sum(
        n for row, n in zip(result, sizes) if row["curriculum_source"] == "cleanup"
    )
    total_tokens = sum(sizes)
    # Replace the longest cleanup targets first; never truncate factual notes or
    # substitute character counts for tokenizer measurements.
    for index in sorted(range(len(result)), key=lambda i: sizes[i], reverse=True):
        if cleanup_tokens <= 0.1 * total_tokens:
            break
        if result[index]["curriculum_source"] != "cleanup":
            continue
        row = next(generators["arena"])
        row["curriculum_source"] = "arena"
        size = count_tokens(target_text(row))
        cleanup_tokens -= sizes[index]
        total_tokens += size - sizes[index]
        result[index], sizes[index] = row, size
    rng.shuffle(result)
    for index, row in enumerate(result):
        row["sampling_copy"] = f"matched-{seed}-{index}"
    # Conservative context preflight; the real managed serialization is also
    # audited. JSON escaping and an extra 512 tokens reserve template overhead.
    context_sizes = [
        count_tokens(json.dumps(r["input"]) + json.dumps(TOOLS) + target_text(r)) + 512
        for r in result
    ]
    if max(context_sizes) > 8192:
        raise ValueError("a supervised example exceeds the pilot context budget")
    hashes = [compute_content_hash(supervised_task(row)) for row in result]
    if len(set(hashes)) != count:
        raise ValueError("dataset deduplication would change the curriculum weights")
    report = {
        "records": count,
        "seed": seed,
        "target_format": SFT_TARGET_FORMAT,
        "source_sampled_counts": dict(Counter(r["curriculum_source"] for r in result)),
        "source_unique_available": {
            k: len({json.dumps(r["provenance"], sort_keys=True) for r in rows})
            for k, rows in sources.items()
        },
        "source_unique_sampled": {
            k: len(
                {
                    json.dumps(r["provenance"], sort_keys=True)
                    for r in result
                    if r["curriculum_source"] == k
                }
            )
            for k in sources
        },
        "coverage": dict(
            Counter(
                f"{r['provenance']['street']}:{r['target'].get('action', 'cleanup')}"
                for r in result
            )
        ),
        "supervised_target_tokens": total_tokens,
        "cleanup_target_tokens": cleanup_tokens,
        "cleanup_token_fraction": cleanup_tokens / total_tokens,
        "token_count_method": "pinned tokenizer; Qwen XML target rendering; confirm against managed samples",
        "max_context_preflight_tokens": max(context_sizes),
        "perturbed_records": sum(
            bool(r.get("perturbation", {}).get("changed")) for r in result
        ),
        "unique_task_count": len(set(hashes)),
        "ordered_task_hashes_sha256": hashlib.sha256(
            "\n".join(hashes).encode()
        ).hexdigest(),
    }
    return result, report


def prepare(args):
    tokenizer_metadata = json.loads(
        (args.tokenizer.parent / "release.json").read_text()
    )
    if (
        tokenizer_metadata.get("model") != MODEL
        or tokenizer_metadata.get("revision") != TOKENIZER_REVISION
        or tokenizer_metadata.get("sha256") != sha(args.tokenizer)
    ):
        raise ValueError("tokenizer must match the pinned base-model revision")
    pb, arena = read_jsonl(args.pokerbench), read_jsonl(args.arena)
    actions = [r for r in arena if r.get("tool", "submit_action") == "submit_action"]
    cleanup = [r for r in arena if r.get("tool") == "update_scratchpad"]
    holdout_paths = [*args.holdout]
    for path in (args.pokerbench, args.arena):
        for split in ("select", "eval"):
            sibling = path.parent / f"{split}.jsonl"
            if not sibling.exists():
                raise ValueError(f"missing source holdout: {sibling}")
            holdout_paths.append(sibling)
    held = [r for path in holdout_paths for r in read_jsonl(path)]
    history = [r for path in args.history for r in read_jsonl(path)]
    if any(not path.exists() for path in [*args.history, *holdout_paths]):
        raise ValueError("historical training or holdout source is missing")
    rows, report = curriculum(
        pb,
        actions,
        cleanup,
        token_counter(args.tokenizer),
        count=args.count,
        holdouts=held,
        history=history,
    )
    path = args.out / "train.jsonl"
    if (args.out / "experiment.json").exists():
        raise ValueError("experiment already exists; use a fresh output directory")
    write_jsonl(path, rows)
    report.update(
        {
            "dataset": args.dataset,
            "checkpoint": args.checkpoint,
            "base_model": MODEL,
            "train_sha256": sha(path),
            "tokenizer_sha256": sha(args.tokenizer),
            "tokenizer": tokenizer_metadata,
            "inputs": {
                str(p): sha(p)
                for p in [
                    args.pokerbench,
                    args.arena,
                    args.tokenizer,
                    *holdout_paths,
                    *args.history,
                ]
            },
            "historical_training_accounting": "reported separately; equal incremental training",
            "training": {
                "steps": 64,
                "batch": 64,
                "checkpoint_every": 32,
                "lr": 5e-6,
                "max_total_len": 8192,
            },
            "conditions": {
                "B0": MODEL,
                "C0": args.checkpoint,
                "B1": "base + shared curriculum",
                "C1": "checkpoint + shared curriculum",
            },
        }
    )
    write_json(args.out / "experiment.json", report)
    return report


def training_args(directory, arm, project="vals-hackathon"):
    manifest = json.loads((directory / "experiment.json").read_text())
    if sha(directory / "train.jsonl") != manifest["train_sha256"]:
        raise ValueError("frozen curriculum changed")
    t = manifest["training"]
    argv = [
        "--records",
        str(directory / "train.jsonl"),
        "--dataset",
        manifest["dataset"],
        "--stage",
        "matched",
        "--project",
        project,
        "--model",
        manifest["base_model"],
        "--steps",
        str(t["steps"]),
        "--batch",
        str(t["batch"]),
        "--lr",
        str(t["lr"]),
        "--checkpoint-every",
        str(t["checkpoint_every"]),
        "--max-total-len",
        str(t["max_total_len"]),
        "--receipt",
        str(directory / f"{arm}-run.json"),
    ]
    return argv + (
        ["--from-base"] if arm == "base" else ["--checkpoint", manifest["checkpoint"]]
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("tokenizer")
    p.add_argument("--out", type=Path, required=True)
    p = commands.add_parser("prepare")
    p.add_argument("--pokerbench", type=Path, required=True)
    p.add_argument("--arena", type=Path, required=True)
    p.add_argument("--tokenizer", type=Path, required=True)
    p.add_argument("--history", type=Path, nargs="+", required=True)
    p.add_argument("--holdout", type=Path, nargs="*", default=[])
    p.add_argument("--count", type=int, default=4096)
    p.add_argument("--checkpoint", default=PARENT)
    p.add_argument("--dataset", default="pokerbots-matched-public-v1-train")
    p.add_argument("--out", type=Path, required=True)
    p = commands.add_parser("train")
    p.add_argument("--experiment", type=Path, required=True)
    p.add_argument("--arm", choices=["base", "continuation"], required=True)
    p.add_argument("--project", default="vals-hackathon")
    p.add_argument("--launch", action="store_true")
    args = parser.parse_args()
    if args.command == "tokenizer":
        print(json.dumps(download_tokenizer(args.out), indent=2))
    elif args.command == "prepare":
        print(json.dumps(prepare(args), indent=2))
    else:
        argv = training_args(args.experiment, args.arm, args.project)
        if args.launch:
            subprocess.run(
                [sys.executable, "-m", "vals_tools.sft", *argv, "--launch"], check=True
            )
        else:
            config = sft.run_config(sft.parser().parse_args(argv))
            print(json.dumps(config.to_json(), indent=2))


if __name__ == "__main__":
    main()

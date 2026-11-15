"""Build fresh-deal GRPO tasks from real six-player hand-start stacks.

python rl/make_history_dataset.py                 # local deterministic build
python rl/make_history_dataset.py --upload        # build, upload, verify

Only source stacks, button and blinds become gameplay parameters. Historical
cards, actions, board, results and scratchpads are never included in tasks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import partial
from pathlib import Path

import httpx
from ac2.runtime import Message, Task
from ac2.sdk import Client

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from vals_tools.tasks import TABLE_RULES

PREFIX = "pokerbots-history-20k-v1"
COUNTS = {"train": 20_000, "select": 500, "eval": 1_000, "smoke": 8}
SEED = 20261115
BUCKETS = ("(0,10]", "(10,25]", "(25,50]", "(50,100]", "(100,200]", "(200,inf)")


@dataclass(frozen=True)
class Scenario:
    match_id: str
    hand_number: int
    stacks: tuple[int, ...]
    button_seat: int
    small_blind: int
    big_blind: int
    archive_file: str
    archive_sha256: str


def load_scenarios(raw_dir: Path) -> list[Scenario]:
    scenarios = []
    for path in sorted(raw_dir.glob("*.json")):
        body = path.read_bytes()
        match = json.loads(body)
        if match.get("status") != "complete":
            continue
        for hand in match["hands"]:
            players = sorted(hand["players"], key=lambda p: p["seat"])
            if [p["seat"] for p in players] != list(range(6)):
                continue
            stacks = tuple(p["starting_stack"] for p in players)
            if any(type(s) is not int or s <= 0 for s in stacks):
                continue
            scenarios.append(
                Scenario(
                    match_id=match["id"],
                    hand_number=hand["hand_number"],
                    stacks=stacks,
                    button_seat=hand["button_seat"],
                    small_blind=hand["small_blind"],
                    big_blind=hand["big_blind"],
                    archive_file=f"history/raw/{path.name}",
                    archive_sha256=hashlib.sha256(body).hexdigest(),
                )
            )
    if not scenarios:
        raise ValueError("No complete, positive-stack, six-player hand starts found")
    return scenarios


def depth_bucket(bb: float) -> str:
    for threshold, label in zip((10, 25, 50, 100, 200, float("inf")), BUCKETS):
        if bb <= threshold:
            return label
    raise AssertionError(bb)


def posted_blind(scenario: Scenario, seat: int) -> int:
    if seat == (scenario.button_seat + 1) % 6:
        return scenario.small_blind
    if seat == (scenario.button_seat + 2) % 6:
        return scenario.big_blind
    return 0


def effective_bb(scenario: Scenario, seat: int) -> float:
    return (
        min(
            scenario.stacks[seat],
            max(s for i, s in enumerate(scenario.stacks) if i != seat),
        )
        / scenario.big_blind
    )


def split_scenarios(scenarios: list[Scenario], seed: int) -> dict[str, list[Scenario]]:
    matches = sorted({s.match_id for s in scenarios})
    if len(matches) < 8:
        raise ValueError(
            "At least eight source matches required for four independent splits"
        )
    random.Random(seed).shuffle(matches)
    sizes = {
        "smoke": max(1, round(len(matches) * 0.025)),
        "select": max(1, round(len(matches) * 0.10)),
        "eval": max(1, round(len(matches) * 0.10)),
    }
    sizes["train"] = len(matches) - sum(sizes.values())
    assignments = {}
    cursor = 0
    for split in ("smoke", "select", "eval", "train"):
        for match in matches[cursor : cursor + sizes[split]]:
            assignments[match] = split
        cursor += sizes[split]
    return {
        split: [s for s in scenarios if assignments[s.match_id] == split]
        for split in COUNTS
    }


def task_for(
    scenario: Scenario, policy_seat: int, seed: int, opponent_model: str
) -> Task:
    return Task(
        input=[
            Message(
                role="user",
                content=f"Play one hand of 6-seat no-limit hold'em from seat {policy_seat}.",
            )
        ],
        env_params=TABLE_RULES
        | {
            "seed": seed,
            "seats": 6,
            "total_hands": 1,
            "reset_stacks": False,
            "starting_stacks": list(scenario.stacks),
            "button_seat": scenario.button_seat,
            "small_blind": scenario.small_blind,
            "big_blind": scenario.big_blind,
            "policy_seats": [policy_seat],
            "ev_labels": True,
            "ev_runouts": 64,
            "opponent_model": opponent_model,
            "opponent_timeout_seconds": 60,
            "history_source": {
                "match_id": scenario.match_id,
                "hand_number": scenario.hand_number,
                "archive_file": scenario.archive_file,
                "archive_sha256": scenario.archive_sha256,
            },
        },
    )


def statistics(tasks: list[Task], sources: list[Scenario]) -> dict:
    hero, effective, all_stacks = [], [], []
    unique_sources = set()
    vectors = set()
    source_buckets = defaultdict(set)
    hero_buckets = Counter()
    effective_buckets = Counter()
    seats = Counter()
    uniform = 0
    for task in tasks:
        p = task.env_params
        seat = p["policy_seats"][0]
        stacks = p["starting_stacks"]
        source = p["history_source"]
        source_key = (source["match_id"], source["hand_number"])
        unique_sources.add(source_key)
        vectors.add(tuple(stacks))
        bb = p["big_blind"]
        h = stacks[seat] / bb
        e = min(stacks[seat], max(s for i, s in enumerate(stacks) if i != seat)) / bb
        hero.append(h)
        effective.append(e)
        all_stacks.extend(s / bb for s in stacks)
        hero_buckets[depth_bucket(h)] += 1
        effective_buckets[depth_bucket(e)] += 1
        source_buckets[depth_bucket(e)].add((*source_key, seat))
        seats[seat] += 1
        uniform += len(set(stacks)) == 1

    def distribution(values):
        values = sorted(values)
        return {
            "min": values[0],
            "p05": values[int(0.05 * (len(values) - 1))],
            "median": values[len(values) // 2],
            "p95": values[int(0.95 * (len(values) - 1))],
            "max": values[-1],
        }

    excluded = sum(
        s.stacks[seat] <= posted_blind(s, seat) for s in sources for seat in range(6)
    )
    available = defaultdict(set)
    for s in sources:
        for seat in range(6):
            if s.stacks[seat] > posted_blind(s, seat):
                available[depth_bucket(effective_bb(s, seat))].add(
                    (s.match_id, s.hand_number, seat)
                )
    return {
        "tasks": len(tasks),
        "source_matches": sorted({s.match_id for s in sources}),
        "available_source_hands": len(sources),
        "available_nonuniform_source_hands": sum(
            len(set(s.stacks)) > 1 for s in sources
        ),
        "excluded_blind_allin_policy_seats": excluded,
        "unique_sampled_source_hands": len(unique_sources),
        "unique_sampled_stack_vectors": len(vectors),
        "repeated_source_hand_tasks": len(tasks) - len(unique_sources),
        "uniform_stack_tasks": uniform,
        "nonuniform_stack_tasks": len(tasks) - uniform,
        "policy_seat_counts": dict(sorted(seats.items())),
        "hero_stack_bb": distribution(hero),
        "effective_stack_bb": distribution(effective),
        "all_seat_stack_bb": distribution(all_stacks),
        "hero_stack_bucket_counts": {b: hero_buckets[b] for b in BUCKETS},
        "effective_stack_bucket_counts": {b: effective_buckets[b] for b in BUCKETS},
        "available_source_hand_seat_pairs_by_effective_bucket": {
            b: len(available[b]) for b in BUCKETS
        },
        "sampled_unique_source_hand_seat_pairs_by_effective_bucket": {
            b: len(source_buckets[b]) for b in BUCKETS
        },
    }


def build_dataset(
    scenarios: list[Scenario],
    prefix: str = PREFIX,
    counts: dict[str, int] | None = None,
    seed: int = SEED,
    opponent_model: str = "vals-hackathon/ac-vals-model",
) -> tuple[dict[str, list[Task]], dict]:
    counts = COUNTS if counts is None else counts
    if set(counts) != set(COUNTS) or any(n < 1 for n in counts.values()):
        raise ValueError("counts must provide positive train/select/eval/smoke sizes")
    pools = split_scenarios(scenarios, seed)
    used_seeds = set()
    built = {}
    manifest = {
        "schema": "pokerbots-history-training/1",
        "prefix": prefix,
        "seed": seed,
        "source_hand_starts": len(scenarios),
        "source_matches": len({s.match_id for s in scenarios}),
        "semantics": "Real pre-blind six-seat stacks/button/blinds; fresh seeded decks, not historical cards or mid-hand replay.",
        "effective_stack_definition": "min(policy stack, largest opponent stack), divided by big blind",
        "sampling": "Policy seats cycle 0..5; 10% uniform profiles when available, otherwise nonuniform. Nonuniform effective-depth buckets cycle separately per seat, then a source candidate is sampled uniformly.",
        "splits": {},
    }
    for split_index, split in enumerate(COUNTS):
        rng = random.Random(f"{seed}:{split}")
        candidates = defaultdict(lambda: defaultdict(list))
        for s in pools[split]:
            for seat in range(6):
                if s.stacks[seat] <= posted_blind(s, seat):
                    continue
                kind = "uniform" if len(set(s.stacks)) == 1 else "nonuniform"
                candidates[(seat, kind)][depth_bucket(effective_bb(s, seat))].append(s)
        counters = Counter()
        tasks = []
        for i in range(counts[split]):
            seat = i % 6
            kind = "uniform" if (i // 6) % 10 == 0 else "nonuniform"
            groups = candidates[(seat, kind)]
            if not groups:
                groups = candidates[
                    (seat, "nonuniform" if kind == "uniform" else "uniform")
                ]
            if not groups:
                raise ValueError(
                    f"No actionable source policy seat {seat} in split {split}"
                )
            buckets = [b for b in BUCKETS if groups.get(b)]
            bucket = buckets[counters[(seat, kind)] % len(buckets)]
            counters[(seat, kind)] += 1
            source = rng.choice(groups[bucket])
            deal_seed = rng.getrandbits(48)
            while deal_seed in used_seeds:
                deal_seed = rng.getrandbits(48)
            used_seeds.add(deal_seed)
            tasks.append(task_for(source, seat, deal_seed, opponent_model))
        built[split] = tasks
        manifest["splits"][split] = {
            "dataset_name": f"{prefix}-{split}",
            **statistics(tasks, pools[split]),
        }
    return built, manifest


def write_exports(built: dict[str, list[Task]], manifest: dict, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for split, tasks in built.items():
        path = output / f"{split}.jsonl"
        with path.open("w") as stream:
            for task in tasks:
                stream.write(
                    json.dumps(
                        task.model_dump(mode="json", exclude_none=True),
                        separators=(",", ":"),
                    )
                    + "\n"
                )
        manifest["splits"][split].update(
            {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        )
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def retry_api(operation, label: str):
    """Retry read calls and content-addressed, idempotent task uploads."""
    for attempt in range(5):
        try:
            return operation()
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            status = (
                exc.response.status_code
                if isinstance(exc, httpx.HTTPStatusError)
                else None
            )
            if attempt == 4 or status is not None and status != 429 and status < 500:
                raise
            print(
                f"Retrying {label} after {'HTTP ' + str(status) if status else 'transport failure'}",
                flush=True,
            )
            time.sleep(2**attempt)


def upload_and_verify(
    built: dict[str, list[Task]], manifest: dict, output: Path, project: str
) -> dict:
    client = Client(project=project)
    existing = {d.name: d for d in client.datasets.list()}
    receipt_path = output / "upload.json"
    receipt = (
        json.loads(receipt_path.read_text())
        if receipt_path.exists()
        else {
            "project": project,
            "prefix": manifest["prefix"],
            "datasets": {},
            "complete": False,
        }
    )
    if receipt["project"] != project or receipt["prefix"] != manifest["prefix"]:
        raise ValueError("Existing upload receipt belongs to another project/prefix")
    for split, tasks in built.items():
        spec = manifest["splits"][split]
        name = spec["dataset_name"]
        prior = receipt["datasets"].get(split)
        if name in existing and (
            not prior
            or prior["dataset_id"] != existing[name].id
            or prior["sha256"] != spec["sha256"]
        ):
            raise ValueError(
                f"Refusing to append to existing dataset {name}; choose a new --prefix"
            )
        if prior and prior["sha256"] != spec["sha256"]:
            raise ValueError(
                f"Local task export changed since partial upload for {name}"
            )
    for split, tasks in built.items():
        spec = manifest["splits"][split]
        name = spec["dataset_name"]
        prior = receipt["datasets"].get(split)
        if prior:
            dataset = client.datasets.get(name)
        else:
            dataset = client.datasets.create(
                name,
                description=f"{len(tasks)} six-seat fresh-deal history stack scenarios; source-match-disjoint {split} split.",
                tags={
                    "benchmark": "pokerbots",
                    "source": "arena-history",
                    "split": split,
                },
            )
            prior = {
                "dataset_id": dataset.id,
                "dataset_name": name,
                "sha256": spec["sha256"],
                "task_ids": [],
            }
            receipt["datasets"][split] = prior
            receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
        # Skip the acknowledged prefix on resume. A failed/unknown batch may be
        # retried because exact task membership is content-addressed/idempotent.
        ids = list(prior["task_ids"])
        if len(ids) > len(tasks) or len(ids) != len(set(ids)):
            raise ValueError(f"Invalid recorded upload prefix for {name}")
        if ids:
            present = {
                ref.id
                for ref in retry_api(partial(client.datasets.active_tasks, name), name)
            }
            if not set(ids) <= present:
                raise ValueError(f"Previously uploaded tasks disappeared from {name}")
            if present != set(ids):
                if len(present - set(ids)) > 500 or len(ids) == len(tasks):
                    raise ValueError(
                        f"Unexpected remote membership beyond recorded prefix for {name}"
                    )
                print(
                    f"{name}: replaying next batch to reconcile unacknowledged membership",
                    flush=True,
                )
            print(f"{name}: resuming after {len(ids)} verified task IDs", flush=True)
        for start in range(len(ids), len(tasks), 500):
            ids.extend(
                retry_api(
                    partial(
                        client.datasets.add_tasks,
                        name,
                        tasks=tasks[start : start + 500],
                    ),
                    name,
                )
            )
            prior["task_ids"] = ids
            receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
            print(f"{name}: uploaded {len(ids)}/{len(tasks)}", flush=True)
        remote = retry_api(partial(client.datasets.get, name), name)
        remote_ids = {
            ref.id
            for ref in retry_api(partial(client.datasets.active_tasks, name), name)
        }
        if (
            len(ids) != len(set(ids))
            or len(remote_ids) != len(tasks)
            or remote_ids != set(ids)
            or remote.task_count != len(tasks)
        ):
            raise ValueError(f"Remote membership mismatch for {name}")
        for offset in sorted({0, len(tasks) // 2, len(tasks) - 1}):
            loaded = retry_api(partial(client.datasets.load_task, ids[offset]), name)
            if (
                loaded.env_params != tasks[offset].env_params
                or loaded.input != tasks[offset].input
            ):
                raise ValueError(f"Remote task content mismatch: {name} index {offset}")
        prior.update(
            {
                "task_count": remote.task_count,
                "verified_membership": True,
                "verified_content_indices": sorted(
                    {0, len(tasks) // 2, len(tasks) - 1}
                ),
            }
        )
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    receipt.update({"complete": True, "verified_at": datetime.now(UTC).isoformat()})
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", default=PREFIX)
    parser.add_argument("--project", default="vals-hackathon")
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "history" / "raw")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--opponent-model", default="vals-hackathon/ac-vals-model")
    parser.add_argument("--upload", action="store_true")
    args = parser.parse_args()
    built, manifest = build_dataset(
        load_scenarios(args.raw_dir),
        prefix=args.prefix,
        seed=args.seed,
        opponent_model=args.opponent_model,
    )
    output = args.output or ROOT / "history" / "training" / args.prefix
    write_exports(built, manifest, output)
    print(json.dumps(manifest, indent=2), flush=True)
    if args.upload:
        upload_and_verify(built, manifest, output, args.project)


if __name__ == "__main__":
    main()

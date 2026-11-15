import hashlib
import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest

from rl import make_history_dataset
from rl.make_history_dataset import (
    COUNTS,
    PREFIX,
    ROOT,
    build_dataset,
    load_scenarios,
    posted_blind,
    write_exports,
)


@pytest.fixture(scope="module")
def history_build():
    scenarios = load_scenarios(ROOT / "history" / "raw")
    return scenarios, *build_dataset(scenarios)


def test_full_dataset_uses_real_profiles_without_future_information(history_build):
    scenarios, built, manifest = history_build
    source = {(s.match_id, s.hand_number): s for s in scenarios}
    allowed = {
        "preset",
        "submit_fields",
        "decision_timeout_seconds",
        "seed",
        "seats",
        "total_hands",
        "reset_stacks",
        "starting_stacks",
        "button_seat",
        "small_blind",
        "big_blind",
        "policy_seats",
        "ev_labels",
        "ev_runouts",
        "opponent_model",
        "opponent_timeout_seconds",
        "history_source",
    }
    for split, tasks in built.items():
        assert len(tasks) == COUNTS[split]
        for task in tasks:
            p = task.env_params
            provenance = p["history_source"]
            s = source[provenance["match_id"], provenance["hand_number"]]
            assert set(p) == allowed
            assert set(provenance) == {
                "match_id",
                "hand_number",
                "archive_file",
                "archive_sha256",
            }
            assert p["starting_stacks"] == list(s.stacks)
            assert (p["button_seat"], p["small_blind"], p["big_blind"]) == (
                s.button_seat,
                s.small_blind,
                s.big_blind,
            )
            assert (
                p["seats"] == 6 and p["total_hands"] == 1 and p["reset_stacks"] is False
            )
            assert p["ev_labels"] and p["preset"] == "event"
            assert s.stacks[p["policy_seats"][0]] > posted_blind(
                s, p["policy_seats"][0]
            )
            assert len(task.input) == 1
            assert (
                task.input[0].content
                == f"Play one hand of 6-seat no-limit hold'em from seat {p['policy_seats'][0]}."
            )
        assert manifest["splits"][split]["tasks"] == len(tasks)


def test_sources_and_seeds_do_not_cross_splits_and_seats_are_balanced(history_build):
    _, built, manifest = history_build
    all_seeds = []
    sources = {}
    for split, tasks in built.items():
        sources[split] = {t.env_params["history_source"]["match_id"] for t in tasks}
        all_seeds.extend(t.env_params["seed"] for t in tasks)
        seats = Counter(t.env_params["policy_seats"][0] for t in tasks)
        assert max(seats.values()) - min(seats.values()) <= 1
    assert len(all_seeds) == len(set(all_seeds)) == sum(COUNTS.values())
    for split, match_ids in sources.items():
        for other, other_ids in sources.items():
            if split != other:
                assert match_ids.isdisjoint(other_ids)
    train = manifest["splits"]["train"]
    assert train["nonuniform_stack_tasks"] >= 0.85 * COUNTS["train"]
    assert (
        sum(count > 0 for count in train["effective_stack_bucket_counts"].values()) >= 5
    )
    assert train["all_seat_stack_bb"]["max"] > 200
    assert train["hero_stack_bb"]["min"] < 10


def test_builder_is_reproducible_and_exports_hashes(tmp_path: Path):
    scenarios = load_scenarios(ROOT / "history" / "raw")
    counts = {"train": 60, "select": 12, "eval": 12, "smoke": 6}
    first, manifest = build_dataset(scenarios, counts=counts)
    second, again = build_dataset(scenarios, counts=counts)
    assert first == second and manifest == again
    write_exports(first, manifest, tmp_path)
    loaded = json.loads((tmp_path / "manifest.json").read_text())
    assert loaded["prefix"] == PREFIX
    for split, tasks in first.items():
        data = (tmp_path / f"{split}.jsonl").read_bytes()
        assert hashlib.sha256(data).hexdigest() == loaded["splits"][split]["sha256"]
        assert len(data.splitlines()) == len(tasks)


def test_builder_rejects_too_few_source_matches(history_build):
    scenarios, _, _ = history_build
    match = scenarios[0].match_id
    with pytest.raises(ValueError, match="eight source matches"):
        build_dataset([s for s in scenarios if s.match_id == match])


def test_upload_refuses_unowned_existing_names_before_writing(
    history_build, monkeypatch, tmp_path: Path
):
    _, built, manifest = history_build

    def forbidden(*args, **kwargs):
        pytest.fail("Existing dataset collision must not create or mutate datasets")

    datasets = SimpleNamespace(
        list=lambda: [SimpleNamespace(name=f"{PREFIX}-train", id="ds_existing")],
        create=forbidden,
        add_tasks=forbidden,
    )
    monkeypatch.setattr(
        make_history_dataset,
        "Client",
        lambda **kwargs: SimpleNamespace(datasets=datasets),
    )
    with pytest.raises(ValueError, match="Refusing to append"):
        make_history_dataset.upload_and_verify(
            built, manifest, tmp_path, "vals-hackathon"
        )

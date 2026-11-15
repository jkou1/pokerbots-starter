import copy

import pytest

from vals_tools.collect_policy import deal_seeds
from vals_tools.combined import mixture
from vals_tools.tasks import Opponents, datasets


def sources():
    teacher = [
        {
            "input": [{"role": "user", "content": f"pete decision {i}"}],
            "target": {"action": "fold"},
            "provenance": {"teacher": "house-professor-pete", "street": "preflop"},
            "split": "train",
        }
        for i in range(12)
    ]
    provenance = {"seed": deal_seeds("train", 1, "starter")[0]}
    replay = [
        {
            "input": [{"role": "user", "content": "flop decision"}],
            "target": {"action": "check"},
            "provenance": provenance | {"street": "flop"},
            "split": "train",
        },
        {
            "input": [{"role": "user", "content": "cleanup"}],
            "tool": "update_scratchpad",
            "target": {"contents": "public hand facts"},
            "provenance": provenance | {"street": "cleanup"},
            "split": "train",
        },
    ]
    return teacher, replay


def test_starter_collection_uses_exact_original_deals_and_disjoint_splits():
    original = datasets("p", Opponents("opponent"))
    sets = []
    for split in ("train", "select", "eval"):
        expected = [t.env_params["seed"] for t in original[f"p-{split}"][:48]]
        assert deal_seeds(split, 48, "starter") == expected
        sets.append(set(expected))
    assert all(not sets[i] & sets[j] for i in range(3) for j in range(i))


def test_combined_preserves_source_weights_and_never_changes_source_inputs():
    teacher, replay = sources()
    snapshot = copy.deepcopy((teacher, replay))
    rows, report = mixture(teacher, replay)
    assert (teacher, replay) == snapshot
    assert report["actual_teacher_fraction"] == 0.75
    assert report["unique_uploaded_tasks"] == 16
    assert report["by_street"] == {"preflop": 12, "flop": 3, "cleanup": 1}
    sampled = [r for r in rows if "sampling_copy" in r]
    assert all(r["input"] in [v["input"] for v in replay] for r in sampled)
    assert rows == mixture(teacher, replay)[0]


def test_combined_refuses_holdouts_wrong_teacher_and_nonstarter_replay():
    teacher, replay = sources()
    teacher[0]["split"] = "select"
    with pytest.raises(ValueError, match="held-out"):
        mixture(teacher, replay)
    teacher, replay = sources()
    teacher[0]["provenance"]["teacher"] = "unknown"
    with pytest.raises(ValueError, match="Pete"):
        mixture(teacher, replay)
    teacher, replay = sources()
    replay[0]["provenance"]["seed"] = deal_seeds("eval", 1, "starter")[0]
    with pytest.raises(ValueError, match="original starter training"):
        mixture(teacher, replay)
    teacher, replay = sources()
    with pytest.raises(ValueError, match="both postflop and cleanup"):
        mixture(teacher, replay[:1])

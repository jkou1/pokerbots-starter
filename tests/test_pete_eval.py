import json

import pytest

from vals_tools.pete_eval import heldout_rows, imitation_metrics


def examples():
    return [
        {
            "target": {"action": action}
            | ({"amount": 20} if action == "raise" else {}),
            "position": i,
            "legal": {
                "can_fold": action != "check",
                "can_check": action == "check",
                "call_amount": 0 if action == "check" else 2,
                "raise_type": "raise",
                "min_raise_to": 4,
                "max_raise_to": 200,
            },
        }
        for i, action in enumerate(["fold", "call", "check", "raise"])
    ]


def test_imitation_metrics_expose_passive_policy_and_illegal_sizing():
    predictions = [
        {"action": "fold"},
        {"action": "fold"},
        {"action": "check"},
        {"action": "raise", "amount": 999},
    ]
    metrics = imitation_metrics(examples(), predictions)
    assert metrics["action_accuracy"] == 0.5
    assert metrics["macro_action_recall"] == 0.5
    assert metrics["legal_rate"] == 0.75
    assert metrics["per_action"]["call"]["recall"] == 0
    assert metrics["per_action"]["raise"]["recall"] == 0
    assert metrics["raise_amount_comparisons"] == 0
    assert metrics["raise_amount_mae_chips"] is None


def test_action_agreement_and_sizing_are_separate():
    predictions = [row["target"].copy() for row in examples()]
    predictions[-1]["amount"] = 10
    metrics = imitation_metrics(examples(), predictions)
    assert metrics["action_accuracy"] == 1
    assert metrics["exact_action_amount_accuracy"] == 0.75
    assert metrics["raise_amount_mae_chips"] == 10
    with pytest.raises(ValueError):
        imitation_metrics(examples(), predictions[:-1])


def test_tool_calls_inside_reasoning_do_not_count_as_actions():
    from poker_harness.seat import Completion
    from poker_harness.training import action_args

    reply = Completion(
        text="",
        reasoning="<tool_call><function=submit_action>fold</function></tool_call>",
    )
    with pytest.raises(ValueError, match="one complete"):
        action_args(reply)


def test_heldout_eval_refuses_train_or_mixed_splits(tmp_path):
    path = tmp_path / "rows.jsonl"
    path.write_text(json.dumps({"split": "train"}) + "\n")
    with pytest.raises(ValueError, match="held-out"):
        heldout_rows(path)
    path.write_text(
        json.dumps({"split": "select"}) + "\n" + json.dumps({"split": "eval"}) + "\n"
    )
    with pytest.raises(ValueError, match="held-out"):
        heldout_rows(path)


def test_paired_comparison_requires_complete_identical_observations():
    from vals_tools.compare_pete import compare

    rows = examples()
    for i, row in enumerate(rows):
        row["provenance"] = {"match_id": f"match-{i // 2}", "action_index": i}
    candidate = {
        "status": "complete",
        "model": "candidate",
        "results": [
            {"provenance": row["provenance"], "action": row["target"]} for row in rows
        ],
    }
    base = candidate | {
        "model": "base",
        "results": [r | {"action": {}} for r in candidate["results"]],
    }
    report = compare(rows, base, candidate)
    assert report["candidate_minus_baseline"]["action_accuracy"] == 1
    assert report["action_accuracy_delta_match_bootstrap_ci95"] == [1, 1]
    with pytest.raises(ValueError, match="complete"):
        compare(rows, base | {"status": "running"}, candidate)
    with pytest.raises(ValueError, match="provenance"):
        compare(
            rows, base, candidate | {"results": list(reversed(candidate["results"]))}
        )

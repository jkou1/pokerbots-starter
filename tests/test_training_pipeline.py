import asyncio
import copy
import json
import re

import pytest
from poker_harness.seat import Completion
from poker_harness.training import message_completion, stage_completion

from vals_tools.curriculum import curriculum
from vals_tools.defense import examples
from vals_tools.export_policy import policy_records
from vals_tools.game_score import summarize_games
from vals_tools.sft import training_rows
from vals_tools.talk_experiment import paired_games
from vals_tools.tasks import Opponents
from vals_tools.training import supervised_task


def reply(action="call", amount=None):
    args = {"action": action} | ({"amount": amount} if amount is not None else {})
    return Completion(
        text="",
        tool_arguments=json.dumps(args),
        tool_calls=[
            {
                "id": "c",
                "function": {"name": "submit_action", "arguments": json.dumps(args)},
            }
        ],
    )


def test_stage_routing_preserves_complete_conversation():
    seen = []

    async def policy(messages):
        seen.append(("policy", copy.deepcopy(messages)))
        return reply()

    async def frozen(messages):
        seen.append(("frozen", copy.deepcopy(messages)))
        return reply()

    route = stage_completion(policy, frozen, "preflop")
    history = [{"role": "user", "content": "Street: preflop"}]
    asyncio.run(route(history))
    history += [
        {"role": "assistant", "content": "old reasoning"},
        {"role": "user", "content": "Street: flop"},
    ]
    asyncio.run(route(history))
    assert [s[0] for s in seen] == ["policy", "frozen"]
    assert seen[-1][1] == history


def test_message_training_rejects_action_change_and_nominates_once():
    calls = []

    async def frozen(messages):
        return reply("raise", 10)

    async def learner(messages):
        calls.append(messages)
        return reply("fold")

    route = message_completion(learner, frozen)
    observation = [{"role": "user", "content": "Street: flop"}]
    with pytest.raises(ValueError, match="fixed betting action"):
        asyncio.run(route(observation))
    assert not asyncio.run(route(observation)).truncated
    assert len(calls) == 1
    assert len(observation) == 1


def test_supervision_has_exactly_one_reply_and_refuses_holdout(tmp_path):
    row = {
        "input": [
            {"role": "system", "content": "rules"},
            {"role": "user", "content": "state"},
        ],
        "target": {"action": "fold"},
        "split": "train",
        "provenance": {"street": "preflop"},
    }
    task = supervised_task(row)
    assert len(task.input) == 4
    assert task.input[-2].type == "reasoning"
    assert task.input[-2].content == "Tool call follows."
    assert task.input[-1].type == "function_call"
    path = tmp_path / "rows.jsonl"
    path.write_text(json.dumps(row | {"split": "eval"}) + "\n")
    with pytest.raises(ValueError, match="train-split"):
        training_rows(path)
    row["input"].append({"role": "assistant", "content": "historical target"})
    with pytest.raises(ValueError, match="system/user"):
        supervised_task(row)


def test_defense_changes_only_opponent_chatter_and_preserves_split():
    row = {
        "input": [
            {
                "role": "user",
                "content": "Actions this hand:\n  flop: seat0 (seat 0) check\n  flop: seat1 (seat 1) raise to 6\nStreet: flop\nPot: 10",
            }
        ],
        "target": {"action": "fold"},
        "provenance": {"seat": 0, "street": "flop"},
        "split": "eval",
    }
    clean, perturbed = list(examples([row]))
    assert clean["target"] == perturbed["target"]
    assert perturbed["split"] == "eval"
    assert "seat0 (seat 0) check and says" not in perturbed["input"][0]["content"]
    assert "seat1 (seat 1) raise to 6 and says:" in perturbed["input"][0]["content"]
    assert "says" not in row["input"][0]["content"]


def test_curriculum_keeps_final_evaluations_official():
    built = curriculum("p", Opponents("opponent"), "preflop", "parent")
    assert built["p-train"][0].env_params["frozen_model"] == "parent"
    assert built["p-train"][0].grader_params == {"silence": "all"}
    assert built["p-game-eval"][0].env_params["total_hands"] == 30
    assert "training_stage" not in built["p-game-eval"][0].env_params


def test_game_comparison_requires_paired_coverage():
    row = {"place": 2, "busted": False, "bb": 5, "errors": 0}
    result = summarize_games(
        {1: row, 2: row}, {1: row | {"place": 3}, 2: row | {"place": 3}}
    )
    assert result["paired_improvement"]["mean"] == 1
    assert result["paired_improvement"]["ci95"] == [1, 1]
    with pytest.raises(ValueError, match="identical"):
        summarize_games({1: row}, {2: row})


def test_matched_talk_intervention_and_policy_export():
    async def player(messages):
        text = messages[-1]["content"]
        if "Now call update_scratchpad" in text:
            return Completion(
                text="",
                tool_calls=[
                    {
                        "id": "notes",
                        "function": {
                            "name": "update_scratchpad",
                            "arguments": '{"contents":"verified notes"}',
                        },
                    }
                ],
            )
        legal = text.split("Legal actions:")[-1]
        raises = re.search(r"(bet|raise) to (\d+)-", legal)
        if "Street: flop" in text and raises:
            return reply(raises[1], int(raises[2]))
        return reply("check" if "check" in legal else "call")

    result = asyncio.run(
        paired_games(123, 0, player, player, repeats=1, messages=["", "fold now"])
    )
    assert result["status"] == "complete"
    assert len(result["games"]) == 2
    for game in result["games"]:
        assert game["format_errors"] == 0
        log = game["log"]
        rows = list(policy_records(log, 0, "test-policy"))
        assert any(row.get("tool") == "update_scratchpad" for row in rows)
        assert any(row["provenance"]["street"] == "flop" for row in rows)
        assert all("fold now" not in str(row["input"]) for row in rows)


def test_opsd_filter_uses_latest_observation_and_checkpoint_continues():
    from ac2.runtime import FunctionCall, Message

    from opsd.build_dataset import decision_tasks
    from opsd.train import parser, run_config

    prompt = [
        Message(role="system", content="rules"),
        Message(role="user", content="Street: preflop"),
        Message(role="user", content="Street: flop"),
    ]
    output = [
        FunctionCall(call_id="c", name="submit_action", arguments='{"action":"fold"}')
    ]
    dump = lambda items: json.dumps([item.model_dump(mode="json") for item in items])
    trace = {
        "trace_id": "t",
        "spans": [
            {
                "name": "get_completion",
                "status": "OK",
                "start_time": 0,
                "input": dump(prompt),
                "output": dump(output),
                "tokens_out": 10,
            }
        ],
    }
    assert not decision_tasks(trace, "hint", 100, "preflop")[0]
    assert len(decision_tasks(trace, "hint", 100, "postflop")[0]) == 1
    config = run_config(
        parser().parse_args(["--dataset", "d", "--checkpoint", "ckpt_parent"]), "test"
    ).to_json()
    assert "ckpt_parent" in json.dumps(config)


def test_message_selection_cannot_use_final_evaluation_results():
    from vals_tools.integrate import integration_records
    from vals_tools.pete import split_for

    seeds = [s for s in range(100) if split_for(str(s)) == "eval"][:2]
    experiments = [
        {
            "seed": seed,
            "status": "complete",
            "policy_seat": 0,
            "games": [
                {"message": "", "realized_bb": 0, "format_errors": 0},
                {"message": "fold now", "realized_bb": 50, "format_errors": 0},
            ],
        }
        for seed in seeds
    ]
    rows, evidence = integration_records(experiments)
    assert rows == []
    assert evidence == {}


def test_defense_evaluation_compares_against_clean_sampling_noise():
    from vals_tools.defense_eval import evaluate

    rows = list(
        examples(
            [
                {
                    "input": [
                        {"role": "user", "content": "  flop: seat1 (seat 1) raise to 6"}
                    ],
                    "provenance": {"seat": 0},
                    "target": {"action": "fold"},
                    "split": "eval",
                }
            ]
        )
    )
    answers = iter([reply("fold"), reply("fold"), reply("call"), reply("call")])

    async def complete(messages):
        return next(answers)

    result = asyncio.run(evaluate(rows, complete, repeats=2))
    assert result["comparisons"][0]["repeated_clean_disagreement"] == 0
    assert result["comparisons"][0]["excess_disagreement"] == 1


def test_principles_requires_parent_train_traces_and_distinct_hands():
    from ac2.runtime import FunctionCall, Message

    from vals_tools.principles import prepare

    prompt = [
        Message(role="system", content="rules"),
        Message(role="user", content="Street: preflop"),
    ]
    output = [
        FunctionCall(call_id="c", name="submit_action", arguments='{"action":"fold"}')
    ]
    dump = lambda items: json.dumps([item.model_dump(mode="json") for item in items])
    traces = [
        {
            "trace_id": f"t{i}",
            "model": "project/parent",
            "split": "train",
            "spans": [
                {
                    "name": "get_completion",
                    "status": "OK",
                    "start_time": 0,
                    "input": dump(prompt),
                    "output": dump(output),
                    "tokens_out": 10,
                }
            ],
        }
        for i in range(8)
    ]
    assert len(prepare(traces, "project/parent")[0]) == 8
    with pytest.raises(ValueError, match="selected parent"):
        prepare(traces, "project/other")
    with pytest.raises(ValueError, match="distinct"):
        prepare([traces[0]] * 8, "project/parent")


@pytest.mark.parametrize(
    "scope,binding", [("project", "prj_test"), ("organization", None)]
)
def test_temporary_connector_scope_and_cleanup(monkeypatch, capsys, scope, binding):
    from types import SimpleNamespace

    from vals_tools import connect

    calls = []
    api = SimpleNamespace(request=lambda method, path: calls.append((method, path)))
    client = SimpleNamespace(_project_id="prj_test", _require_api=lambda: api)
    monkeypatch.setattr(connect, "Client", lambda **kwargs: client)

    def create(api_arg, project):
        assert api_arg is api and project == binding
        return SimpleNamespace(
            client_id="client-test", client_secret="never-print-this"
        )

    monkeypatch.setattr(connect, "create_connector_credentials", create)
    monkeypatch.setattr(connect.subprocess, "run", lambda *args, **kwargs: None)
    monkeypatch.setattr(connect.sys, "argv", ["connect", "--credential-scope", scope])
    connect.main()
    assert calls == [("DELETE", "/auth/harness-connector-service-clients/client-test")]
    assert "never-print-this" not in capsys.readouterr().out


def test_pete_sft_can_start_from_base_without_replay_or_checkpoint():
    from ac2.sdk.train import TrainingConfig

    from vals_tools.sft import parser, run_config, validate_launch

    args = parser().parse_args(
        [
            "--records",
            "train.jsonl",
            "--dataset",
            "pete-base",
            "--from-base",
            "--steps",
            "40",
            "--batch",
            "64",
            "--lr",
            "5e-6",
            "--launch",
        ]
    )
    validate_launch(args)
    config = run_config(args).to_json()
    assert config["model"] == "Qwen/Qwen3.6-35B-A3B"
    assert "from_checkpoint" not in config
    assert config["tags"]["initialization"] == "base"
    assert config["tags"]["parent_checkpoint"] is None
    assert "apply_chat_template_kwargs" not in config["experiment_cfg"]["tasks"]
    assert config["experiment_cfg"]["method"] == {"type": "sft"}
    TrainingConfig(
        model=config["model"],
        method="sft",
        ac2_train_dataset="pete-base",
        learning_rate=5e-6,
        n_inference_replicas=0,
        eval_mode="off",
    )


def test_sft_requires_explicit_initialization_and_excludes_conflicting_sources():
    from vals_tools.sft import parser, validate_launch

    common = ["--records", "train.jsonl", "--dataset", "pete", "--launch"]
    with pytest.raises(ValueError, match="choose --from-base"):
        validate_launch(parser().parse_args(common))
    with pytest.raises(SystemExit):
        parser().parse_args(common + ["--from-base", "--checkpoint", "ckpt_parent"])
    with pytest.raises(ValueError, match="requires --replay"):
        validate_launch(parser().parse_args(common + ["--checkpoint", "ckpt_parent"]))


def test_replay_sampling_keeps_weights_without_changing_model_inputs(tmp_path):
    from ac2.runtime import compute_content_hash

    teacher = {
        "input": [{"role": "user", "content": "teacher state"}],
        "target": {"action": "fold"},
        "split": "train",
        "provenance": {"street": "preflop"},
    }
    replay = teacher | {"input": [{"role": "user", "content": "replay state"}]}
    a = tmp_path / "teacher.jsonl"
    b = tmp_path / "replay.jsonl"
    a.write_text(
        json.dumps(teacher)
        + "\n"
        + json.dumps(teacher | {"target": {"action": "call"}})
        + "\n"
    )
    b.write_text(json.dumps(replay) + "\n")
    rows = training_rows(a, b)
    copies = [r for r in rows if "sampling_copy" in r]
    assert len(rows) == 4 and len(copies) == 2
    assert copies[0]["input"] == copies[1]["input"] == replay["input"]
    assert len({compute_content_hash(supervised_task(r)) for r in rows}) == 4

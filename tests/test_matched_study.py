import asyncio
import copy

import pytest
from poker_harness.completions import table_rules, with_preset
from poker_harness.engine.table import Decision
from poker_harness.game import play_session
from poker_harness.grading import GradingError, check_grader_params, grade_log

from vals_tools import sft
from vals_tools.game_score import cluster_bootstrap, game_rows, summarize_games
from vals_tools.game_study import (
    deployment_identity,
    evaluation_plan,
    score_directory,
    validate_plan,
)
from vals_tools.matched import check_disjoint, curriculum, training_args
from vals_tools.pete import extract_match
from vals_tools.pokerbench import convert_row, spot_identity


def preflop(**updates):
    return {
        "prev_line": "",
        "hero_pos": "BTN",
        "hero_holding": "Ac9s",
        "correct_decision": "2.5bb",
        "pot_size": "1.5",
    } | updates


def postflop(**updates):
    return {
        "preflop_action": "SB/3.0bb/BB/call",
        "board_flop": "6s8d7c",
        "board_turn": "9s",
        "board_river": "3c",
        "evaluation_at": "Turn",
        "postflop_action": "OOP_CHECK/IP_CHECK/dealcards/9s/OOP_BET_5/IP_RAISE_16",
        "hero_position": "OOP",
        "holding": "Tc9c",
        "correct_decision": "Call",
        "pot_size": "27",
    } | updates


def test_pokerbench_replays_implicit_folds_and_raise_to():
    row = convert_row(preflop(), "preflop", "train")
    assert row["target"] == {"action": "raise", "amount": 5}
    assert row["legal"]["call_amount"] == 2
    assert "Pot (including current bets): 3" in row["input"][-1]["content"]
    assert row["position"] == 5


def test_pokerbench_turn_has_exact_pot_and_hides_future_river():
    a = convert_row(postflop(), "postflop", "train")
    b = convert_row(postflop(board_river="Tc"), "postflop", "train")
    assert a == b  # even an impossible future card cannot affect this input
    assert a["target"] == {"action": "call"}
    assert a["legal"]["call_amount"] == 22  # raise TO 32 minus our 10
    assert "Pot (including current bets): 54" in a["input"][-1]["content"]
    assert "3c" not in a["input"][-1]["content"]


@pytest.mark.parametrize(
    "row,kind,reason",
    [
        (preflop(correct_decision="2.3bb"), "preflop", "integer-chip"),
        (preflop(pot_size="2"), "preflop", "pot"),
        (preflop(correct_decision="check"), "preflop", "target"),
        (postflop(holding="6s9c"), "postflop", "overlap"),
        (postflop(postflop_action="IP_CHECK"), "postflop", "actor"),
        (postflop(evaluation_at="Flop"), "postflop", "visible street"),
    ],
)
def test_pokerbench_rejects_ambiguous_or_impossible_states(row, kind, reason):
    with pytest.raises(ValueError, match=reason):
        convert_row(row, kind, "train")


def test_suit_isomorphic_duplicates_share_identity():
    assert spot_identity("x", 2, ["Ac", "Th", "9s"], ["Kd", "Qc"]) == spot_identity(
        "x", 2, ["Ah", "Tc", "9d"], ["Ks", "Qh"]
    )


def public_match(raise_first=False):
    class Calling:
        def __init__(self, seat):
            self.name = f"seat{seat}"

        async def decide(self, ctx, history):
            if raise_first:
                if ctx.seat == 0 and ctx.legal.raise_type:
                    return Decision(ctx.legal.raise_type, 100)
                return Decision("check" if ctx.legal.can_check else "fold")
            return Decision("check" if ctx.legal.can_check else "call")

    log = asyncio.run(
        play_session(
            "fixture",
            123,
            [Calling(i) for i in range(6)],
            table_rules(with_preset({"preset": "event", "total_hands": 1})),
        )
    )
    h = log["hands"][0]
    hand = {
        "hand_number": 1,
        "button_seat": h["button_seat"],
        "blinds": {str(i): v for i, v in enumerate([1, 2, 0, 0, 0, 0])},
        "players": [dict(p, starting_stack=200) for p in h["starting_state"].values()],
        "actions": [],
        "stacks_after": {str(i): log["final_stacks"][f"seat{i}"] for i in range(6)},
        "deltas": {str(i): log["final_stacks"][f"seat{i}"] - 200 for i in range(6)},
        "board": h["final_board"],
        "showdown": h["showdown"],
        "shown": {},
        "eliminated": [],
    }
    for action in h["actions"]:
        hand["actions"].append(
            dict(
                action,
                action=action["action"]["type"],
                amount=action["action"].get("amount"),
                to_call=action["call_amount"],
                tool_args={"action": action["action"]["type"]}
                | (
                    {"amount": action["action"]["amount"]}
                    if "amount" in action["action"]
                    else {}
                ),
            )
        )
    # The public archive records pre-award stack_after on the final action.
    last = hand["actions"][-1]
    last["stack_after"] -= h["pot_won"].get(last["player"], 0)
    return {
        "schema": "vals-arena.match/1",
        "runner_version": "0.1.0",
        "status": "complete",
        "id": "fixture",
        "seed": 123,
        "format": {"small_blind": 1, "big_blind": 2, "total_hands": 1},
        "seats": [
            {"seat": i, "entry": {"id": "house-professor-pete" if i == 0 else "other"}}
            for i in range(6)
        ],
        "hands": [hand],
    }


def test_arena_all_streets_preserves_default_and_cleanup_privacy():
    match = public_match()
    old = extract_match(match)[0]
    rows = extract_match(
        match, streets=("preflop", "flop", "turn", "river"), cleanup=True
    )[0]
    assert all(r["provenance"]["street"] == "preflop" for r in old)
    assert {r["provenance"]["street"] for r in rows} == {
        "preflop",
        "flop",
        "turn",
        "river",
        "cleanup",
    }
    cleanup = rows[-1]
    for p in match["hands"][0]["players"]:
        if p["seat"] != 0:
            assert " ".join(p["hole_cards"]) not in str(cleanup["input"])
    assert cleanup["provenance"]["teacher"] == "public-facts"


def test_cleanup_awards_exclude_refunded_uncalled_bets_and_unseen_boards():
    match = public_match(raise_first=True)
    rows = extract_match(match, cleanup=True)[0]
    assert "Pot: seat0 won 2." in rows[-1]["input"][-1]["content"]
    assert "seat0 won 102" not in rows[-1]["input"][-1]["content"]
    match["hands"][0]["board"] = ["As", "Kd", "Qh"]
    with pytest.raises(ValueError, match="dealt public board"):
        extract_match(match, cleanup=True)


def source_rows():
    pb = convert_row(preflop(), "preflop", "train")
    pb["split"] = "train"
    arena = copy.deepcopy(pb)
    arena["deal_identity"] = "arena-train"
    arena["provenance"].update(teacher="house-professor-pete", seat=5)
    cleanup = {
        "input": [{"role": "user", "content": "cleanup"}],
        "target": {"contents": "factual notes " * 100},
        "split": "train",
        "tool": "update_scratchpad",
        "deal_identity": "cleanup-train",
        "provenance": {"teacher": "public-facts", "street": "cleanup", "seat": 0},
    }
    return [pb], [arena], [cleanup]


def test_shared_curriculum_caps_tokens_and_preserves_sources():
    sources = source_rows()
    rows, report = curriculum(*sources, len, count=100)
    again, second = curriculum(*sources, len, count=100)
    assert rows == again and report == second
    assert len(rows) == 100 and report["unique_task_count"] == 100
    assert report["cleanup_token_fraction"] <= 0.1
    assert report["source_unique_available"] == {
        "pokerbench": 1,
        "arena": 1,
        "cleanup": 1,
    }
    assert "sampling_copy" not in sources[0][0]
    for index in (0, 1, 2):
        invalid = copy.deepcopy(sources)
        invalid[index][0]["split"] = "eval"
        with pytest.raises(ValueError, match="train-split"):
            curriculum(*invalid, len, count=100)


def test_historical_training_never_becomes_a_holdout():
    pb, _, _ = source_rows()
    held = copy.deepcopy(pb)
    held[0]["split"] = "eval"
    with pytest.raises(ValueError, match="historical"):
        check_disjoint([], held, pb)


def test_second_arm_reuses_shared_tasks_and_partial_uploads_resume():
    from types import SimpleNamespace

    from ac2.runtime import compute_content_hash

    from vals_tools.training import supervised_task

    rows = source_rows()[0]
    other = copy.deepcopy(rows[0])
    other["sampling_copy"] = "another-sample"
    tasks = [supervised_task(rows[0]), supervised_task(other)]

    class Datasets:
        def __init__(self):
            self.present = {compute_content_hash(tasks[0])}
            self.added = []

        def list_tasks(self, name, limit, offset):
            return [SimpleNamespace(content_hash=h) for h in sorted(self.present)][
                offset : offset + limit
            ]

        def add_tasks(self, name, tasks):
            self.added.extend(tasks)
            self.present.update(compute_content_hash(task) for task in tasks)

    service = Datasets()
    client = SimpleNamespace(datasets=service)
    assert len(sft.sync_tasks(client, "shared", tasks)) == 2
    assert len(service.added) == 1
    sft.sync_tasks(client, "shared", tasks)
    assert len(service.added) == 1
    service.present.add("unexpected")
    with pytest.raises(ValueError, match="unexpected"):
        sft.sync_tasks(client, "shared", tasks)


def test_both_training_configs_share_budget_dataset_and_seed(tmp_path):
    from vals_tools.arena import write_json
    from vals_tools.matched import sha

    (tmp_path / "train.jsonl").write_text("[]")
    write_json(
        tmp_path / "experiment.json",
        {
            "train_sha256": sha(tmp_path / "train.jsonl"),
            "checkpoint": "ckpt_parent",
            "dataset": "shared",
            "base_model": "Qwen/Qwen3.6-35B-A3B",
            "training": {
                "steps": 64,
                "batch": 64,
                "lr": 5e-6,
                "checkpoint_every": 32,
                "max_total_len": 8192,
            },
        },
    )
    configs = [
        sft.run_config(sft.parser().parse_args(training_args(tmp_path, arm))).to_json()
        for arm in ("base", "continuation")
    ]
    assert configs[0]["experiment_cfg"] == configs[1]["experiment_cfg"]
    assert configs[0]["model"] != configs[1]["model"]
    (tmp_path / "train.jsonl").write_text("changed")
    with pytest.raises(ValueError, match="changed"):
        training_args(tmp_path, "base")


def test_game_plan_rotates_all_seats_and_keeps_splits_separate(tmp_path):
    opponents = [
        {"model": "a", "identity": {"version": 1}},
        {"model": "b", "identity": {"version": 2}},
    ]
    select, final = [evaluation_plan(opponents, s) for s in ("select", "eval")]
    assert len(select["cases"]) == 24 and len(final["cases"]) == 120
    assert not {c["seed"] for c in select["cases"]} & {
        c["seed"] for c in final["cases"]
    }
    assert {c["seat"] for c in final["cases"]} == set(range(6))
    with pytest.raises(ValueError, match="missing"):
        score_directory(tmp_path, select)
    with pytest.raises(ValueError, match="validation"):
        score_directory(tmp_path, select, require_validated=True)
    changed = copy.deepcopy(select)
    changed["params"]["strict_actions"] = False
    with pytest.raises(ValueError, match="official rules"):
        validate_plan(changed)
    changed = copy.deepcopy(select)
    changed["cases"].pop()
    with pytest.raises(ValueError, match="all scheduled"):
        validate_plan(changed)


def test_deployment_identity_cannot_resolve_another_projects_same_name():
    from types import SimpleNamespace

    inference = SimpleNamespace(
        list=lambda: [SimpleNamespace(name="base", id="infer1")],
        get=lambda _: SimpleNamespace(project_name="ours"),
    )
    with pytest.raises(ValueError, match="different project"):
        deployment_identity(SimpleNamespace(inference=inference), "theirs/base")


def test_missing_cleanup_is_a_failure_in_game_reports(tmp_path):
    from vals_tools.arena import write_json

    log = {
        "complete": True,
        "policy_seats": ["seat0"],
        "ranking": {"places": {"seat0": 1}},
        "session_info": {"seed": 123, "big_blind": 2, "starting_stacks": [200]},
        "final_stacks": {"seat0": 200},
        "hands": [{"starting_state": {"seat0": {}}, "actions": []}],
    }
    write_json(tmp_path / "game.json", log)
    assert summarize_games(game_rows(tmp_path))["cleanup_failures"] == 1
    log["private"] = {"seat0": {"hands": {"1": {"cleanup": {"result": "updated"}}}}}
    write_json(tmp_path / "game.json", log)
    assert summarize_games(game_rows(tmp_path))["cleanup_failures"] == 0


def test_uncertainty_resamples_seeds_not_individual_seats():
    values = [1] * 6 + [-1] * 6
    assert cluster_bootstrap(values, [123] * 6 + [456] * 6) == [-1, 1]
    assert cluster_bootstrap(values, [123] * 12) == [None, None]
    parent = {
        (s, seat): {"place": 3, "bb": 0, "busted": False, "errors": 0}
        for s in [123, 456]
        for seat in range(6)
    }
    candidate = copy.deepcopy(parent)
    for row in candidate.values():
        row["place"] = 2
    assert summarize_games(candidate, parent)["paired_improvement"]["seed_groups"] == 2
    candidate.pop((123, 0))
    with pytest.raises(ValueError, match="identical"):
        summarize_games(candidate, parent)


def test_placement_reward_requires_full_official_games():
    params = check_grader_params({"objective": "placement"})
    with pytest.raises(GradingError, match="30-hand"):
        # Build a real log through the same deterministic test players.
        class Folding:
            def __init__(self, n):
                self.name = f"seat{n}"

            async def decide(self, ctx, history):
                return Decision("check" if ctx.legal.can_check else "fold")

        log = asyncio.run(
            play_session(
                "short",
                2,
                [Folding(i) for i in range(6)],
                table_rules(with_preset({"preset": "event", "total_hands": 1})),
            )
        )
        grade_log(log, ["seat0"], params)
    log["hands"] = [copy.deepcopy(log["hands"][0]) for _ in range(30)]
    for i, hand in enumerate(log["hands"]):
        hand["hand_number"] = i + 1
    log["ranking"]["places"]["seat0"] = 1
    assert grade_log(log, ["seat0"], params)["score"] == 11
    log["ranking"]["places"]["seat0"] = 6
    assert grade_log(log, ["seat0"], params)["score"] == 1


def test_talk_selection_requires_ordinary_control_and_never_trains_on_holdouts():
    from vals_tools.integrate import integration_records
    from vals_tools.talk_experiment import ORDINARY

    experiments = [
        {
            "status": "complete",
            "seed": seed,
            "split": "select",
            "policy_seat": 0,
            "model_identity": {"checkpoint": "frozen"},
            "opponent_identity": {"version": opponent},
            "games": [
                {
                    "message": message,
                    "realized_bb": value,
                    "format_errors": 0,
                    "repeat": repeat,
                }
                for repeat in range(3)
                for message, value in [("", 0), (ORDINARY, 1), ("fold now", 2)]
            ],
        }
        for seed in range(6)
        for opponent in range(2)
    ]
    rows, evidence = integration_records(experiments)
    assert evidence["fold now"]["accepted"]
    assert rows == []  # selected message's held-out actions never enter SFT
    for result in experiments:
        result["games"] = [g for g in result["games"] if g["message"] != ORDINARY]
    assert integration_records(experiments) == ([], {})
    crossed = copy.deepcopy(experiments[0])
    crossed["split"] = "train"
    with pytest.raises(ValueError, match="cannot cross"):
        integration_records([*experiments, crossed])

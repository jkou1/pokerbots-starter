"""Play actual exported training tasks through the HTTP harness and its grader."""

import json
from pathlib import Path

import httpx
import pytest
from test_event_rules import recording_relay
from test_grading import grade
from test_server import play

from poker_harness.server import create_app

ROOT = Path(__file__).resolve().parents[2]
EXPORT = ROOT / "history" / "training" / "pokerbots-history-20k-v1" / "train.jsonl"


@pytest.fixture(scope="module")
def historical_tasks():
    with EXPORT.open() as source:
        tasks = [json.loads(line) for line in source]
    assert len(tasks) == 20_000

    def hero_stack(task):
        params = task["env_params"]
        return params["starting_stacks"][params["policy_seats"][0]]

    shallow = min(tasks, key=hero_stack)
    deep = max(tasks, key=hero_stack)
    asymmetric = max(
        (task for task in tasks if task["env_params"]["button_seat"] != 5),
        key=lambda task: max(task["env_params"]["starting_stacks"]) / min(task["env_params"]["starting_stacks"]),
    )
    return [shallow, deep, asymmetric]


@pytest.mark.parametrize("sample", range(3), ids=["shallow", "deep", "asymmetric-button"])
async def test_exported_task_plays_and_grades_with_exact_historical_stacks(
    historical_tasks, sample, tmp_path, monkeypatch
):
    task = historical_tasks[sample]
    params = task["env_params"]
    # The connector forwards harness fields, not SDK storage metadata such as content_hash/tags.
    harness_task = {"input": task["input"], "env_params": params}
    monkeypatch.setenv("AC2_API_KEY", "fake-opponent-key")
    monkeypatch.setenv("POKER_OPPONENT_BASE_URL", "http://relay/job/trace/v1")
    policy_calls, opponent_calls = [], []
    app = create_app(
        relay_transport=httpx.ASGITransport(app=recording_relay(policy_calls)),
        opponent_transport=httpx.ASGITransport(app=recording_relay(opponent_calls)),
        runs_dir=tmp_path,
    )
    async with app.router.lifespan_context(app):
        status, outputs = await play(app, harness_task)
        assert status["status"] == "completed", status
        assert policy_calls and opponent_calls
        log = json.loads(next(tmp_path.glob("*.json")).read_text())
        initial = {f"seat{i}": chips for i, chips in enumerate(params["starting_stacks"])}
        assert log["session_info"]["starting_stacks"] == params["starting_stacks"]
        assert len(log["hands"]) == 1
        hand = log["hands"][0]
        assert hand["stacks_before"] == initial
        assert len(hand["starting_state"]) == 6
        assert hand["button_seat"] == params["button_seat"]
        assert sum(log["final_stacks"].values()) == sum(initial.values())
        assert sum(log["net_chips"].values()) == 0
        assert outputs["rules"]["starting_stacks"] == params["starting_stacks"]
        assert outputs["rules"]["button_seat"] == params["button_seat"]
        hero = f"seat{params['policy_seats'][0]}"
        assert any(action["player"] == hero for action in hand["actions"])
        for request in policy_calls:
            system = request["messages"][0]["content"]
            assert all(f"seat {i}: {chips} chips" in system for i, chips in enumerate(params["starting_stacks"]))
            assert params["history_source"]["match_id"] not in json.dumps(request["messages"])
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://harness") as client:
            grading_status, response = await grade(
                client,
                {"rollout_id": "gw_1", "rollout_status": "completed", "task": harness_task},
            )
        assert grading_status["status"] == "completed", grading_status
        assert response.is_success
        score = response.json()
        assert score["artifacts"]["policy_format_errors"] == 0
        assert score["artifacts"]["policy_decisions"] > 0
        assert score["artifacts"]["realized_bb"] == (log["final_stacks"][hero] - initial[hero]) / params["big_blind"]
        assert score["score"] > 0

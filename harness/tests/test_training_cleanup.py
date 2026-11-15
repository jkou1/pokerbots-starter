"""Training-only terminal cleanup optimization, with unchanged poker and grading."""

import httpx
import pytest
from test_event_rules import recording_relay
from test_server import play

from poker_harness.game import play_session
from poker_harness.grading import grade_log
from poker_harness.prompts import TableRules
from poker_harness.server import create_app


async def test_single_hand_skip_removes_only_cleanup_and_preserves_reward(tmp_path):
    results = []
    for flag in (None, False, True):
        requests = []
        app = create_app(
            relay_transport=httpx.ASGITransport(app=recording_relay(requests)),
            runs_dir=tmp_path / str(flag),
        )
        params = {"preset": "event", "seed": 123, "total_hands": 1}
        if flag is not None:
            params["training_skip_final_cleanup"] = flag
        status, outputs = await play(app, {"input": [], "env_params": params})
        assert status["status"] == "completed"
        cleanups = [r for r in requests if "is over" in r["messages"][-1]["content"]]
        assert len(cleanups) == (0 if flag else 6)
        log = outputs["log"]
        assert log.get("training_skip_final_cleanup", False) is bool(flag)
        action_keys = ("player", "street", "action", "put_in", "stack_after", "board")
        actions = [
            {key: action[key] for key in action_keys}
            for hand in log["hands"] for action in hand["actions"]
        ]
        results.append((actions, log["final_stacks"], grade_log(log, ["seat0"])))
    assert results[0] == results[1] == results[2]


@pytest.mark.parametrize("hands, flag", [(2, True), (30, True), (1, "false")])
async def test_server_rejects_unsafe_cleanup_configuration(tmp_path, hands, flag):
    app = create_app(runs_dir=tmp_path)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://harness") as client:
        response = await client.post("/submit", json={
            "ac_api_url": "http://unused/v1", "ac_api_key": "unused",
            "task": {"input": [], "env_params": {
                "preset": "event", "seed": 123, "total_hands": hands,
                "training_skip_final_cleanup": flag,
            }},
        })
        assert response.status_code == 422
        assert "training_skip_final_cleanup" in response.json()["detail"]


async def test_direct_game_rejects_multi_hand_skip_before_playing():
    with pytest.raises(ValueError, match="requires exactly one hand"):
        await play_session("unused", 123, [], TableRules(total_hands=30), training_skip_final_cleanup=True)

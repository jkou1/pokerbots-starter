"""Unequal hand-start stacks preserve accounting, blinds, and request validation."""

from dataclasses import replace
from pathlib import Path

import httpx
import pytest

from poker_harness.completions import rules_output, table_rules, with_preset
from poker_harness.engine import Decision
from poker_harness.ev import label_ev
from poker_harness.game import play_session
from poker_harness.grading import seat_result
from poker_harness.labels import label_folds
from poker_harness.prompts import TableRules, system_prompt
from poker_harness.server import create_app

STACKS = (3, 7, 15, 40, 100, 200)


class Player:
    def __init__(self, seat: int, shove: bool = False):
        self.name = f"seat{seat}"
        self.shove = shove

    async def decide(self, ctx, history):
        if self.shove and ctx.legal.raise_type:
            return Decision(ctx.legal.raise_type, ctx.legal.max_raise_to)
        return Decision("call")


def players(shove: bool = False):
    return [Player(i, shove) for i in range(6)]


def rules(**values):
    return TableRules(total_hands=values.pop("total_hands", 1), seats=6, starting_stacks=STACKS,
                      ranking="elimination", **values)


def test_rules_are_strict_and_report_optional_stack_configuration():
    r = table_rules(with_preset({"preset": "event", "starting_stacks": list(STACKS), "button_seat": 2}))
    assert r.starting_stacks == STACKS and r.button_seat == 2
    assert rules_output(r)["starting_stacks"] == STACKS
    default = rules_output(table_rules({}))
    assert "starting_stacks" not in default and "button_seat" not in default
    assert "Everyone starts with 200" not in system_prompt(r)
    assert "seat 0: 3 chips" in system_prompt(r) and "seat 5: 200 chips" in system_prompt(r)
    reset = system_prompt(replace(r, reset_stacks=True))
    assert "restores each seat to its own starting stack" in reset
    assert "every player at 200 chips" not in reset


async def test_six_distinct_stacks_and_nondefault_button_reach_the_engine():
    log = await play_session("stacks", 17, players(), rules(button_seat=2))
    hand = log["hands"][0]
    assert log["session_info"]["starting_stacks"] == list(STACKS)
    assert log["session_info"]["button_seat"] == hand["button_seat"] == 2
    assert hand["stacks_before"] == {f"seat{i}": stack for i, stack in enumerate(STACKS)}
    assert hand["blinds_posted"] == {"seat3": 1, "seat4": 2}
    assert hand["starting_state"]["seat3"]["position"] == 0
    assert hand["starting_state"]["seat4"]["position"] == 1
    assert hand["starting_state"]["seat2"]["position"] == 5
    assert sum(log["final_stacks"].values()) == sum(STACKS)
    for seat, initial in enumerate(STACKS):
        name = f"seat{seat}"
        assert log["net_chips"][name] == log["final_stacks"][name] - initial
        assert seat_result(log, [name]).realized_bb == log["net_chips"][name] / 2


async def test_unequal_allins_sidepots_and_carry_conserve_chips_and_rank_busts():
    log = await play_session("allins", 7, players(shove=True), rules(total_hands=8))
    assert sum(log["final_stacks"].values()) == sum(STACKS)
    assert sum(log["net_chips"].values()) == 0
    for hand in log["hands"]:
        assert sum(hand["stacks_before"].values()) == sum(STACKS)
        assert sum(hand["ending_stacks"].values()) == sum(STACKS)
        assert len(set(hand["blinds_posted"].values())) <= 2
    for previous, current in zip(log["hands"], log["hands"][1:]):
        assert current["stacks_before"] == {n: s for n, s in previous["ending_stacks"].items() if s > 0}
    assert log["eliminated_on_hand"]
    for name, hand_number in log["eliminated_on_hand"].items():
        assert name in log["hands"][hand_number-1]["eliminated"]
    assert set(log["ranking"]["places"]) == {f"seat{i}" for i in range(6)}
    labeled = label_ev(log, {f"seat{i}" for i in range(6)}, variants=1, runouts=16)
    first = labeled["hands"][0]
    assert any(v["method"] == "side-pot" for v in first["ev"].values())
    for name, value in first["ev"].items():
        assert value["realized_bb"] == (first["ending_stacks"][name] - first["stacks_before"][name]) / 2
    assert sum(v["realized_bb"] for v in first["ev"].values()) == 0


async def test_reset_restores_each_seats_own_stack_and_final_log_uses_its_baseline():
    log = await play_session("reset", 31, players(shove=True), rules(total_hands=3, reset_stacks=True))
    assert len(log["hands"]) == 3
    initial = {f"seat{i}": stack for i, stack in enumerate(STACKS)}
    assert all(hand["stacks_before"] == initial for hand in log["hands"])
    for name, start in initial.items():
        net = sum(hand["ending_stacks"][name] - start for hand in log["hands"])
        assert log["net_chips"][name] == net
        assert log["final_stacks"][name] == start + net
    assert log["eliminated_on_hand"] == {}


async def test_allin_blind_ev_uses_actual_preblind_stack_not_engine_snapshot():
    short = replace(rules(), starting_stacks=(1, 1, 1, 1, 1, 1))
    log = await play_session("tiny", 3, players(), short)
    label_ev(log, {f"seat{i}" for i in range(6)}, variants=1, runouts=8)
    for name, ev in log["hands"][0]["ev"].items():
        assert ev["realized_bb"] == (log["final_stacks"][name] - 1) / 2


def test_fold_labels_do_not_price_ineligible_sidepots_as_a_single_pot():
    log = {"session_info": {"starting_stacks": list(STACKS), "big_blind": 2}, "hands": [{
        "starting_state": {"seat0": {"hole_cards": ["As", "Ad"]}, "seat1": {"hole_cards": ["7h", "2c"]}},
        "actions": [{"player": "seat0", "action": {"type": "fold"}, "call_amount": 100, "pot_before": 200,
                     "board": []}],
    }]}
    label_folds(log, {"seat0"})
    action = log["hands"][0]["actions"][0]
    assert action["fold_regret_bb"] is None
    assert action["fold_regret_unavailable"] == "unequal-starting-stacks"


@pytest.mark.parametrize("params", [
    {"starting_stacks": [10] * 5}, {"starting_stacks": [10] * 7},
    {"starting_stacks": "10,10,10,10,10,10"}, {"starting_stacks": {"0": 10}},
    {"starting_stacks": [True, 10, 10, 10, 10, 10]},
    {"starting_stacks": [1.5, 10, 10, 10, 10, 10]},
    {"starting_stacks": [0, 10, 10, 10, 10, 10]},
    {"starting_stacks": [-1, 10, 10, 10, 10, 10]},
    {"button_seat": True}, {"button_seat": 1.5}, {"button_seat": "2"},
    {"button_seat": -1}, {"button_seat": 6},
])
async def test_submit_rejects_invalid_stack_and_button_shapes(tmp_path: Path, params: dict):
    app = create_app(runs_dir=tmp_path)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://harness") as client:
        response = await client.post("/submit", json={
            "ac_api_url": "http://unused", "ac_api_key": "unused",
            "task": {"input": [], "env_params": {"seed": 1, "seats": 6, **params}},
        })
    assert response.status_code == 422
    assert "env_params." in response.json()["detail"]

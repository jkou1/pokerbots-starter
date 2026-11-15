import copy
import json
from pathlib import Path

import pytest

from vals_tools.arena import collect, discover
from vals_tools.pete import build, extract_match, split_for

FIXTURE = Path(__file__).parent / "fixtures" / "pete_match.json"


def sample():
    return json.loads(FIXTURE.read_text())


def test_pagination_and_resume(tmp_path):
    match = sample()
    match_id = match["id"]
    pages = {
        "https://example.test/matches": f'<a href="/matches/{match_id}">Replay</a><a href="/matches?page=2">Older</a>',
        "https://example.test/matches?page=2": f'<a href="/matches/{match_id}">Replay</a>',
        f"https://example.test/matches/{match_id}": '<a href="https://blob.test/raw.json">Raw JSON</a>',
        "https://blob.test/raw.json": json.dumps(match),
    }
    calls = []

    def fetch(url):
        calls.append(url)
        return pages[url].encode()

    assert len(discover(fetch, "https://example.test")) == 1
    assert collect(tmp_path, fetch, base="https://example.test")["complete"] == 1
    calls.clear()
    assert collect(tmp_path, fetch, base="https://example.test")["complete"] == 1
    assert "https://blob.test/raw.json" not in calls


def test_replay_targets_are_legal_and_private():
    match = sample()
    rows, _, stats = extract_match(match)
    assert stats["kept"] == 1
    assert rows[0]["target"] == {"action": "raise", "amount": 5}
    assert "say" not in rows[0]["target"]
    prompt = rows[0]["input"][-1]["content"]
    assert "6h 6c" in prompt
    for player in match["hands"][0]["players"]:
        if player["seat"] != rows[0]["provenance"]["seat"]:
            assert " ".join(player["hole_cards"]) not in prompt


def test_future_information_cannot_change_earlier_input():
    match = sample()
    before = extract_match(match)[0]
    match["results"] = []
    match["hands"][0]["board"] = ["As"] * 5
    match["hands"][0]["deltas"] = {}
    assert extract_match(match)[0] == before


def test_corruption_is_quarantined_and_duplicates_do_not_cross_splits(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    match = sample()
    (raw / "one.json").write_text(json.dumps(match))
    duplicate = copy.deepcopy(match)
    duplicate["id"] = "another-id"
    (raw / "two.json").write_text(json.dumps(duplicate))
    bad = copy.deepcopy(match)
    bad["schema"] = "unknown"
    bad["seed"] += 1
    (raw / "bad.json").write_text(json.dumps(bad))
    quality = build(tmp_path)
    assert quality["duplicates"] == 1
    assert len(quality["quarantined"]) == 1
    assert sum(quality["splits"].values()) == 1


def test_failure_targets_removed_and_missing_cards_rejected():
    match = sample()
    for action in match["hands"][0]["actions"]:
        if action["seat"] == 5:
            action["coerced"] = True
    assert extract_match(match)[0] == []
    del match["hands"][0]["players"][0]["hole_cards"]
    with pytest.raises(KeyError):
        extract_match(match)


def test_replay_rejects_wrong_amount():
    match = sample()
    match["hands"][0]["actions"][3]["amount"] = 99999
    with pytest.raises(ValueError):
        extract_match(match)


def test_split_is_stable():
    assert split_for("same-game") == split_for("same-game")


def test_discovery_follows_older_links_past_newer_navigation():
    pages = {
        "https://example.test/matches": '<a href="/matches?page=2">Older</a>',
        "https://example.test/matches?page=2": '<a href="/matches?page=1">Newer</a><a href="/matches?page=3">Older</a>',
        "https://example.test/matches?page=3": '<a href="/matches/m_last">Replay</a><a href="/matches?page=2">Newer</a>',
    }
    assert list(discover(lambda url: pages[url].encode(), "https://example.test")) == [
        "m_last"
    ]

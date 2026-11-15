#!/usr/bin/env python3
"""Verify archive coverage, source hashes, and derived rows without network access."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from crawl import Links, derive

ROOT = Path(__file__).resolve().parent


def main():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    assert not manifest["errors"], manifest["errors"]
    listed = set()
    for page in manifest["listing_pages"]:
        body = (ROOT / page["file"]).read_bytes()
        assert hashlib.sha256(body).hexdigest() == page["sha256"]
        listed.update(link.rsplit("/", 1)[-1] for link in Links(body.decode()).links
                      if re.fullmatch(r"/matches/m_[A-Za-z0-9_]+", link))
    records = manifest["matches"]
    ids = [r["match_id"] for r in records]
    assert len(ids) == len(set(ids))
    assert set(ids) == listed, (listed - set(ids), set(ids) - listed)
    assert {p.stem for p in (ROOT / "raw").glob("*.json")} == listed
    target_hands = target_actions = 0
    for record in records:
        body = (ROOT / record["file"]).read_bytes()
        assert len(body) == record["bytes"]
        assert hashlib.sha256(body).hexdigest() == record["sha256"]
        data = json.loads(body)
        assert data["id"] == record["match_id"]
        seats = [s for s in data["seats"] if s["entry"]["id"] == manifest["entry_id"]]
        assert len(seats) == 1 and seats[0]["seat"] == record["seat"]
        seat = record["seat"]
        result = next(r for r in data["results"] if r["entry_id"] == manifest["entry_id"])
        hands = [h for h in data["hands"] if any(p["seat"] == seat for p in h["players"])]
        actions = [a for h in hands for a in h["actions"] if a["seat"] == seat]
        assert len(hands) == result["hands"], data["id"]
        assert len(actions) == result["decisions"], data["id"]
        assert sum(h["deltas"].get(str(seat), 0) for h in hands) == result["net_chips"], data["id"]
        assert sum(r["net_chips"] for r in data["results"]) == 0, data["id"]
        target_hands += len(hands)
        target_actions += len(actions)
    names = ["matches.jsonl", "hands.jsonl", "decisions.jsonl", "summary.json"]
    before = {name: (ROOT / name).read_bytes() for name in names}
    summary = derive(manifest)
    assert all((ROOT / name).read_bytes() == before[name] for name in names), "Derived files are stale"
    assert summary["target_hand_rows"] == target_hands
    assert summary["target_decision_rows"] == target_actions
    actions = [json.loads(line) for line in (ROOT / "decisions.jsonl").read_text().splitlines()]
    keys = [(a["match_id"], a["hand_number"], a["action_index"]) for a in actions]
    assert len(keys) == len(set(keys))
    print(json.dumps({"verified_matches": len(ids), "verified_hands": target_hands,
                      "verified_decisions": target_actions,
                      "statuses": dict(Counter(r["status"] for r in records))}, indent=2))


if __name__ == "__main__":
    main()

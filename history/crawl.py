#!/usr/bin/env python3
"""Archive the public replay JSON linked from an entry's complete match history.

Standard library only. Run from any directory: python3 history/crawl.py
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from urllib.parse import parse_qs, urlencode, urljoin, urlparse
from urllib.request import Request, urlopen

BASE = "https://www.pokerbots.ac"
ROOT = Path(__file__).resolve().parent
ENTRY = "org_cd68943dd947"


def now():
    return datetime.now(timezone.utc).isoformat()


def fetch(url):
    for attempt in range(5):
        try:
            request = Request(url, headers={"User-Agent": "PokerbotsHistoryArchive/1.0", "Cache-Control": "no-cache"})
            with urlopen(request, timeout=60) as response:
                return response.read()
        except Exception:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)


class Links(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def discover(entry, pass_number):
    pending = {1}
    visited = set()
    matches = set()
    pages = []
    while pending:
        page = min(pending)
        pending.remove(page)
        url = BASE + "/matches?" + urlencode({"entry": entry, "page": page})
        body = fetch(url)
        path = ROOT / "listings" / f"pass-{pass_number}-page-{page}.html"
        path.write_bytes(body)
        pages.append({"url": url, "file": str(path.relative_to(ROOT)), "fetched_at": now(),
                      "sha256": hashlib.sha256(body).hexdigest()})
        visited.add(page)
        for link in Links(body.decode()).links:
            parsed = urlparse(link)
            if re.fullmatch(r"/matches/m_[A-Za-z0-9_]+", parsed.path):
                matches.add(parsed.path.rsplit("/", 1)[-1])
            if parsed.path == "/matches":
                query = parse_qs(parsed.query)
                if query.get("entry") == [entry]:
                    linked_page = int(query.get("page", ["1"])[0])
                    if linked_page not in visited:
                        pending.add(linked_page)
        print(f"Listing pass {pass_number}, page {page}: {len(matches)} unique matches", flush=True)
    return matches, pages


def download(match_id, entry):
    replay_url = BASE + "/matches/" + match_id
    replay = fetch(replay_url)
    links = Links(replay.decode()).links
    raw_links = [urljoin(replay_url, link) for link in links if urlparse(link).path.endswith(".json")]
    if len(set(raw_links)) != 1:
        raise ValueError(f"{match_id}: expected one Raw JSON link; found {raw_links}")
    raw_url = raw_links[0]
    body = fetch(raw_url)
    data = json.loads(body)
    if data["id"] != match_id:
        raise ValueError(f"ID mismatch for {match_id}")
    seats = [s for s in data["seats"] if s["entry"]["id"] == entry]
    if len(seats) != 1:
        raise ValueError(f"{match_id}: expected exactly one seat for {entry}")
    path = ROOT / "raw" / f"{match_id}.json"
    path.write_bytes(body)  # Preserve the downloaded bytes, including original formatting.
    return {"match_id": match_id, "replay_url": replay_url, "raw_url": raw_url,
            "file": str(path.relative_to(ROOT)), "fetched_at": now(),
            "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body),
            "status": data["status"], "kind": data["kind"], "seat": seats[0]["seat"],
            "entry": seats[0]["entry"], "hands_recorded": len(data["hands"])}


def derive(manifest):
    results, hands, decisions = [], [], []
    for record in sorted(manifest["matches"], key=lambda r: r["match_id"]):
        data = json.loads((ROOT / record["file"]).read_bytes())
        seat = record["seat"]
        common = {"match_id": data["id"], "kind": data["kind"], "status": data["status"],
                  "started_at": data["started_at"], "finished_at": data["finished_at"],
                  "seat": seat, "entry": record["entry"]}
        for result in data["results"]:
            if result["entry_id"] == manifest["entry_id"]:
                results.append(common | {"result": result})
        for hand in data["hands"]:
            player = next((p for p in hand["players"] if p["seat"] == seat), None)
            if player is None:
                continue
            hand_common = {"match_id": data["id"], "hand_number": hand["hand_number"], "seat": seat}
            own_actions = [(i, a) for i, a in enumerate(hand["actions"]) if a["seat"] == seat]
            hands.append(hand_common | {"button_seat": hand["button_seat"],
                         "hole_cards": player["hole_cards"], "starting_stack": player["starting_stack"],
                         "net_chips": hand["deltas"].get(str(seat), 0),
                         "ending_stack": hand["stacks_after"].get(str(seat)),
                         "board": hand["board"], "showdown": hand["showdown"],
                         "decision_count": len(own_actions)})
            for index, action in own_actions:
                decisions.append(hand_common | {"action_index": index, "button_seat": hand["button_seat"],
                                 "hole_cards": player["hole_cards"], "starting_stack": player["starting_stack"],
                                 "action": action})
    for filename, rows in [("matches.jsonl", results), ("hands.jsonl", hands), ("decisions.jsonl", decisions)]:
        with (ROOT / filename).open("w") as output:
            for row in rows:
                output.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    def aggregate(rows):
        completed = [r["result"] for r in rows if r["status"] == "complete"]
        n_hands = sum(r["hands"] for r in completed)
        net = sum(r["net_bb"] for r in completed)
        ev = sum(r.get("ev_net_bb", r["net_bb"]) for r in completed)
        return {"completed_matches": len(completed), "hands": n_hands,
                "decisions": sum(r["decisions"] for r in completed),
                "wins": sum(r["place"] == 1 for r in completed),
                "places": dict(sorted(Counter(r["place"] for r in completed).items())),
                "net_bb": net, "ev_net_bb": ev,
                "bb_per_100": 100 * net / n_hands if n_hands else None,
                "ev_bb_per_100": 100 * ev / n_hands if n_hands else None,
                "fallbacks": sum(r["fallbacks"] for r in completed),
                "coerced": sum(r["coerced"] for r in completed),
                "afk": sum(r["afk"] for r in completed),
                "timeouts": sum(r["timeouts"] for r in completed)}

    groups = defaultdict(list)
    kinds = defaultdict(list)
    for row in results:
        entry = row["entry"]
        key = (entry.get("submission_name"), entry.get("deployment_id"),
               entry.get("deployment", {}).get("checkpoint_id"), entry.get("deployment", {}).get("version"))
        groups[key].append(row)
        kinds[row["kind"]].append(row)
    summary = {"entry_id": manifest["entry_id"], "snapshot_finished_at": manifest["finished_at"],
               "raw_matches": len(manifest["matches"]), "statuses": dict(Counter(r["status"] for r in manifest["matches"])),
               "target_hand_rows": len(hands), "target_decision_rows": len(decisions),
               "target_action_flags": dict(Counter(flag for row in decisions for flag in
                   ["format_error", "fallback", "coerced", "afk", "timed_out", "token_cap", "sat_out"]
                   if row["action"].get(flag))),
               "overall": aggregate(results), "by_kind": {k: aggregate(v) for k, v in sorted(kinds.items())},
               "by_submission": [{"submission_name": k[0], "deployment_id": k[1], "checkpoint_id": k[2],
                                  "version": k[3], **aggregate(v)} for k, v in sorted(groups.items(), key=lambda x: str(x[0]))]}
    write_json(ROOT / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entry", default=ENTRY)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    for directory in ["raw", "listings"]:
        (ROOT / directory).mkdir(exist_ok=True)
    manifest = {"entry_id": args.entry, "source_url": BASE + "/matches?entry=" + args.entry,
                "started_at": now(), "listing_pages": [], "matches": [], "errors": []}
    seen = set()
    for pass_number in [1, 2]:
        match_ids, pages = discover(args.entry, pass_number)
        manifest["listing_pages"].extend(pages)
        pending = sorted(match_ids - seen)
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            jobs = {pool.submit(download, match_id, args.entry): match_id for match_id in pending}
            for future in as_completed(jobs):
                match_id = jobs[future]
                try:
                    record = future.result()
                    manifest["matches"].append(record)
                    seen.add(match_id)
                    print(f"Downloaded {len(seen)}: {match_id} ({record['bytes']} bytes)", flush=True)
                except Exception as exc:
                    manifest["errors"].append({"match_id": match_id, "error": str(exc)})
                    print(f"ERROR {match_id}: {exc}", flush=True)
    manifest["errors"] = [e for e in manifest["errors"] if e["match_id"] not in seen]
    manifest["matches"].sort(key=lambda r: r["match_id"])
    manifest["finished_at"] = now()
    write_json(ROOT / "manifest.json", manifest)
    summary = derive(manifest)
    print(json.dumps(summary, indent=2))
    if manifest["errors"]:
        raise SystemExit("Some replays could not be downloaded; see manifest.json")


if __name__ == "__main__":
    main()

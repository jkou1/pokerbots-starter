"""Bounded public-dashboard execution-failure miner; standard library only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

from vals_tools.arena import BASE, MATCH_ID, Fetcher, Links, atomic_write, read_jsonl, write_json, write_jsonl

ROOT = Path(__file__).resolve().parent
STATUS_PATH = Path("/tmp/pokerbots-public-failure-status.json")
OUR_ORG = "org_cd68943dd947"
PETE_ID = "house-professor-pete"
ACCORD_ORG = "org_4aab0c8828ea"
DEADLINE = datetime.fromisoformat("2026-11-15T17:00:00+00:00")
TEAMS = {
    "own": (OUR_ORG, f"{BASE}/teams/{OUR_ORG}"),
    "pete": (PETE_ID, f"{BASE}/teams/{PETE_ID}"),
    "accord": (ACCORD_ORG, f"{BASE}/teams/{ACCORD_ORG}"),
}
LIMITS = {"own": 8, "pete": 3, "accord": 3}
CACHE_SPECS = [
    ("pete_postflop", "pete", Path("/Users/lance/Documents/pokerbots-pokerbench/experiments/pete-postflop-v1"), "manifest.jsonl"),
    ("pete_incumbent_audit", "pete", Path("/Users/lance/Documents/pokerbots-overnight-eval/data/experiments/arena-incumbent-audit"), "manifest.jsonl"),
    ("accord_leader_audit", "accord", Path("/Users/lance/Documents/pokerbots-overnight-eval/data/experiments/arena-leader-audit"), "manifest.jsonl"),
    ("older_own_history", "own", Path("/Users/lance/Documents/pokerbots-starter-sft/history"), "manifest.json"),
]
ENUM = {"fold", "check", "call", "bet", "raise"}
TALK_PATTERNS = {
    "threat": re.compile(r"\b(kill|hurt|beat you up|threaten|violence)\b", re.I),
    "slur": re.compile(r"\b(faggot|nigger|kike|chink|retard)\b", re.I),
    "sexual_content": re.compile(r"\b(sex|sexy|nude|naked|porn|orgasm)\b", re.I),
    "harassment_or_profanity": re.compile(r"\b(fuck|shit|bitch|asshole|idiot|stupid|loser)\b", re.I),
    "instruction_manipulation": re.compile(r"ignore (?:all |previous |prior )|system prompt|jailbreak|instructions", re.I),
}
UNSUPPORTED = {
    "cleanup_and_private_scratchpads": "unsupported: not published in public match Raw JSON",
    "private_reasoning": "unsupported: only token counts and public actions/talk are available; never fabricate reasoning",
    "optimal_action_labels": "unsupported: no verified strategic engine label is produced; lucky wins are not optimal-play evidence",
    "student_inputs": "not produced; hidden cards, future boards/actions, outcomes, and current-action stack_after must not become student inputs",
}


def now() -> datetime:
    return datetime.now(UTC)


def stamp(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def match_links(raw: bytes) -> list[str]:
    found = []
    for link in Links(raw.decode()).links:
        url = urljoin(BASE, link)
        path = urlparse(url).path
        match_id = path.removeprefix("/matches/")
        if path.startswith("/matches/") and MATCH_ID.fullmatch(match_id) and match_id not in found:
            found.append(match_id)
    return found


def valid_cached(row: dict, path: Path) -> bool:
    return bool(
        row.get("result") == "complete"
        and path.exists()
        and sha256(path.read_bytes()) == row.get("sha256")
    )


def source_cache() -> tuple[dict, dict]:
    external = {}
    summaries = []
    for name, scope, root, manifest_name in CACHE_SPECS:
        manifest = root / manifest_name
        if manifest_name.endswith(".jsonl"):
            source_rows = read_jsonl(manifest)
        else:
            source_rows = json.loads(manifest.read_text()).get("matches", [])
        valid = 0
        for source_row in source_rows:
            match_id = source_row.get("id") or source_row.get("match_id")
            if source_row.get("source_bytes_path"):
                path = Path(source_row["source_bytes_path"])
            elif source_row.get("file"):
                path = root / source_row["file"]
            else:
                path = root / "raw" / f"{match_id}.json"
            if not match_id or not path.exists():
                continue
            raw = path.read_bytes()
            if sha256(raw) != source_row.get("sha256"):
                continue
            status = source_row.get("result") or source_row.get("status") or json.loads(raw).get("status")
            if status != "complete":
                continue
            row = source_row | {
                "id": match_id,
                "result": "complete",
                "source_bytes_path": str(path),
                "cache_name": name,
                "cache_scopes": [scope],
            }
            valid += 1
            if match_id in external:
                external[match_id]["cache_scopes"] = sorted(set(external[match_id]["cache_scopes"]) | {scope})
            else:
                external[match_id] = row
        summaries.append({"name": name, "scope": scope, "manifest": str(manifest), "manifest_rows": len(source_rows), "hash_validated_complete_rows": valid})
    return external, {
        "sources": summaries,
        "manifest_rows": sum(item["manifest_rows"] for item in summaries),
        "hash_validated_complete_rows": sum(item["hash_validated_complete_rows"] for item in summaries),
        "unique_matches": len(external),
        "access": "read-only",
    }


def collect_match(fetch: Fetcher, match_id: str, old: dict, external: dict) -> dict:
    path = ROOT / "raw" / f"{match_id}.json"
    replay_url = f"{BASE}/matches/{match_id}"
    if valid_cached(old, path):
        return old | {"replay_url": replay_url, "collection": "local_cache"}
    if old.get("result") == "failed" and old.get("retry_after", "") > stamp(now()):
        return old | {"collection": "failure_backoff"}
    source = external.get(match_id)
    if source:
        source_path = Path(source["source_bytes_path"])
        raw = source_path.read_bytes()
        atomic_write(path, raw)
        return source | {
            "id": match_id,
            "replay_url": source.get("replay_url") or replay_url,
            "collection": source["cache_name"],
            "local_sha256": sha256(raw),
            "locally_saved_at": stamp(now()),
            "result": "complete",
        }
    row = {"id": match_id, "replay_url": replay_url, "fetched_at": stamp(now())}
    try:
        replay = fetch(replay_url)
        atomic_write(ROOT / "replays" / f"{match_id}.html", replay)
        row["replay_sha256"] = sha256(replay)
        raw_urls = [
            urljoin(BASE, link)
            for link in Links(replay.decode()).links
            if urlparse(urljoin(BASE, link)).path.endswith(".json")
        ]
        if len(raw_urls) != 1:
            raise ValueError(f"expected one actual Raw JSON link, found {len(raw_urls)}")
        row["raw_url"] = raw_urls[0]
        raw = fetch(raw_urls[0])
        atomic_write(path, raw)
        row["sha256"] = sha256(raw)
        match = json.loads(raw)
        if match.get("id") != match_id:
            raise ValueError("raw match ID does not match replay")
        row.update(schema=match.get("schema"), status=match.get("status"), started_at=match.get("started_at"), finished_at=match.get("finished_at"))
        if match.get("status") != "complete":
            row["result"] = "incomplete"
        elif datetime.fromisoformat(match["finished_at"].replace("Z", "+00:00")) > DEADLINE:
            row["result"] = "after_cutoff"
        else:
            row["result"] = "complete"
        row["collection"] = "public_http"
        row.pop("retry_after", None)
    except Exception as error:
        row.update(
            result="failed",
            error=f"{type(error).__name__}: {error}",
            retry_after=stamp(now() + timedelta(minutes=30)),
            collection="public_http",
        )
    return row


def target_seats(match: dict, scope: str) -> set[int]:
    seats = set()
    for seat in match.get("seats", []):
        entry = seat.get("entry") or {}
        if scope == "own" and (entry.get("org_id") == OUR_ORG or entry.get("id") == OUR_ORG):
            seats.add(seat["seat"])
        if scope == "pete" and entry.get("id") == PETE_ID:
            seats.add(seat["seat"])
        if scope == "accord" and (entry.get("org_id") == ACCORD_ORG or entry.get("id") == ACCORD_ORG):
            seats.add(seat["seat"])
    return seats


def entry_metadata(entry: dict) -> dict:
    deployment = entry.get("deployment") or {}
    return {
        "submission_name": entry.get("submission_name"),
        "deployment_id": entry.get("deployment_id"),
        "deployment_version": deployment.get("version"),
        "checkpoint_id": deployment.get("checkpoint_id"),
        "model": entry.get("model"),
    }


def current_entry_records(records: dict) -> tuple[dict, dict]:
    own = []
    for row in records.values():
        if "own" not in row.get("scopes", []) or row.get("result") != "complete":
            continue
        match = json.loads((ROOT / "raw" / f"{row['id']}.json").read_bytes())
        if target_seats(match, "own"):
            own.append((row, match))
    if not own:
        return {}, {"selection": "unavailable", "limitation": "No complete own match is available."}
    latest_row, latest_match = max(own, key=lambda item: item[1].get("started_at") or "")
    latest_seat = next(seat for seat in latest_match["seats"] if seat["seat"] in target_seats(latest_match, "own"))
    identity = entry_metadata(latest_seat["entry"])
    if identity["deployment_id"] or identity["submission_name"]:
        selected = {}
        for row, match in own:
            entries = [seat["entry"] for seat in match["seats"] if seat["seat"] in target_seats(match, "own")]
            if any(entry_metadata(entry) == identity for entry in entries):
                selected[row["id"]] = row | {"scopes": ["own"]}
        return selected, identity | {
            "selection": "exact_published_entry_metadata",
            "observed_in_match": latest_match["id"],
            "observed_started_at": latest_match.get("started_at"),
            "limitation": None,
        }
    latest_finished = datetime.fromisoformat(latest_match["finished_at"].replace("Z", "+00:00"))
    cutoff = latest_finished - timedelta(hours=2)
    selected = {
        row["id"]: row | {"scopes": ["own"]}
        for row, match in own
        if datetime.fromisoformat(match["finished_at"].replace("Z", "+00:00")) >= cutoff
    }
    return selected, identity | {
        "selection": "recent_two_hour_window_fallback",
        "window_start": stamp(cutoff),
        "window_end": stamp(latest_finished),
        "limitation": "Published entry/deployment metadata was insufficient; this recent window is not an exact deployment split.",
    }


def failure_categories(action: dict) -> list[tuple[str, str]]:
    categories = []
    args = action.get("tool_args")
    error = str(action.get("error") or "")
    if action.get("token_cap"):
        categories.append(("token_cap", "published token_cap=true"))
    if not isinstance(args, dict):
        categories.append(("missing_tool", "published tool_args is absent/not an object"))
    else:
        proposed = args.get("action")
        executed = action.get("action")
        if proposed not in ENUM:
            categories.append(("invalid_enum", f"published tool action {proposed!r} is outside the official enum"))
        if proposed == "check" and (
            (action.get("to_call") or 0) > 0
            or (executed != "check" and (action.get("format_error") or action.get("coerced") or action.get("fallback")))
        ):
            categories.append(("invalid_check", f"proposed check with to_call={action.get('to_call')} executed={executed!r}"))
        if proposed in {"bet", "raise"}:
            amount = args.get("amount")
            invalid_amount = not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0
            changed = executed != proposed or action.get("amount") != amount
            coerced = action.get("format_error") or action.get("coerced") or action.get("fallback")
            if invalid_amount:
                categories.append(("invalid_bet_raise_amount", f"proposed {proposed} amount={amount!r} is not a positive integer"))
            elif proposed == "raise" and executed == "bet" and coerced:
                categories.append(("invalid_raise", f"raise was illegal on an unopened street; engine applied bet amount={amount!r}"))
            elif changed and coerced:
                categories.append(("invalid_bet_raise_amount", f"proposed {proposed} amount={amount!r}; executed {executed!r} amount={action.get('amount')!r}"))
    if error and error.lower() not in {"none", "null"}:
        categories.append(("explicit_engine_error", f"published error: {error}"))
    if action.get("format_error") and not categories:
        categories.append(("unclassified_format_error", "format_error=true without enough public evidence for a narrower label"))
    return categories


def talk_categories(text: str) -> list[str]:
    return [category for category, pattern in TALK_PATTERNS.items() if pattern.search(text)]


def execution_outcome(action: dict) -> str:
    if action.get("fallback") and action.get("action") == "fold":
        return "forced_fold_fallback"
    if action.get("fallback"):
        return "other_fallback"
    if action.get("coerced") and not action.get("fallback"):
        return "legal_executed_coercion"
    return "other_execution_failure"


def mine(records: dict) -> tuple[list[dict], list[dict], dict]:
    pending = {scope: [] for scope in TEAMS}
    talk_pending = {scope: [] for scope in TEAMS}
    aggregate = {}
    for scope in TEAMS:
        rows = [row for row in records.values() if scope in row.get("scopes", []) and row.get("result") == "complete"]
        category_counts = Counter()
        talk_counts = Counter()
        action_denominator = say_denominator = 0
        windows = []
        per_match = []
        for row in sorted(rows, key=lambda item: item["id"]):
            path = ROOT / "raw" / f"{row['id']}.json"
            match = json.loads(path.read_bytes())
            seats = target_seats(match, scope)
            match_counts = Counter()
            match_affected = set()
            match_actions = 0
            windows.append({"started_at": match.get("started_at"), "finished_at": match.get("finished_at")})
            for hand in match.get("hands", []):
                for index, action in enumerate(hand.get("actions", [])):
                    if action.get("seat") not in seats:
                        continue
                    action_denominator += 1
                    match_actions += 1
                    base = {
                        "match_id": match["id"],
                        "hand_number": hand.get("hand_number"),
                        "action_index": index,
                        "street": action.get("street"),
                        "seat": action.get("seat"),
                        "source_url": row.get("raw_url"),
                        "replay_url": row.get("replay_url"),
                        "source_sha256": row.get("sha256"),
                        "time_window": {"started_at": match.get("started_at"), "finished_at": match.get("finished_at")},
                        "say": action.get("say"),
                        "entry_metadata": entry_metadata(next(seat["entry"] for seat in match["seats"] if seat["seat"] == action["seat"])),
                    }
                    categories = failure_categories(action)
                    for category, reason in categories:
                        action_key = (hand.get("hand_number"), index)
                        match_affected.add(action_key)
                        category_counts[category] += 1
                        match_counts[category] += 1
                        pending[scope].append(base | {
                            "failure_category": category,
                            "failure_reason": reason,
                            "execution_outcome": execution_outcome(action),
                            "tool_args": action.get("tool_args"),
                            "executed_action": action.get("action"),
                            "executed_amount": action.get("amount"),
                            "published_fallback": action.get("fallback"),
                            "published_coerced": action.get("coerced"),
                            "published_format_error": action.get("format_error"),
                            "published_error": action.get("error"),
                        })
                    say = action.get("say")
                    if say:
                        say_denominator += 1
                        for category in talk_categories(say):
                            talk_counts[category] += 1
                            talk_pending[scope].append(base | {"appropriateness_flag": category, "review_required": True, "flag_reason": "deterministic pattern match on actual published say text; human review required"})
            per_match.append({"match_id": match["id"], "target_seats": sorted(seats), "actions": match_actions, "unique_affected_actions": len(match_affected), "unique_affected_action_rate": len(match_affected) / match_actions if match_actions else None, "failure_counts_nonadditive": dict(match_counts), "started_at": match.get("started_at"), "finished_at": match.get("finished_at")})
        findings = []
        for item in pending[scope]:
            match_row = next(row for row in per_match if row["match_id"] == item["match_id"])
            findings.append(item | {
                "numerator": category_counts[item["failure_category"]],
                "denominator": action_denominator,
                "match_numerator": match_row["failure_counts_nonadditive"].get(item["failure_category"], 0),
                "match_denominator": match_row["actions"],
                "scope": scope,
            })
        talk_findings = []
        for item in talk_pending[scope]:
            match_row = next(row for row in per_match if row["match_id"] == item["match_id"])
            talk_findings.append(item | {
                "numerator": talk_counts[item["appropriateness_flag"]],
                "denominator": say_denominator,
                "match_denominator": match_row["actions"],
                "scope": scope,
            })
        pending[scope] = findings
        talk_pending[scope] = talk_findings
        affected = {(item["match_id"], item["hand_number"], item["action_index"]) for item in findings}
        outcome_by_action = {(item["match_id"], item["hand_number"], item["action_index"]): item["execution_outcome"] for item in findings}
        outcome_counts = Counter(outcome_by_action.values())
        aggregate[scope] = {
            "aggregation_scope": "all_history_including_previous_deployments",
            "matches": len(rows),
            "target_actions": action_denominator,
            "unique_affected_actions": len(affected),
            "unique_affected_action_rate": len(affected) / action_denominator if action_denominator else None,
            "execution_outcome_counts": dict(outcome_counts),
            "failure_counts_nonadditive": dict(category_counts),
            "category_rates_nonadditive": {key: value / action_denominator for key, value in category_counts.items()} if action_denominator else {},
            "tag_counts_warning": "Failure categories are non-additive tags; use unique_affected_actions for incident counts.",
            "published_say_messages": say_denominator,
            "appropriateness_flag_counts": dict(talk_counts),
            "appropriateness_flag_rates": {key: value / say_denominator for key, value in talk_counts.items()} if say_denominator else {},
            "time_window": {
                "started_at": min((w["started_at"] for w in windows if w["started_at"]), default=None),
                "finished_at": max((w["finished_at"] for w in windows if w["finished_at"]), default=None),
            },
            "per_match": per_match,
        }
    return sum((pending[scope] for scope in TEAMS), []), sum((talk_pending[scope] for scope in TEAMS), []), aggregate


def regression_examples(findings: list[dict], aggregate: dict, current_match_ids: set[str] | None = None) -> list[dict]:
    current_match_ids = current_match_ids or set()
    grouped = {}
    for finding in findings:
        key = (finding["scope"], finding["match_id"], finding["hand_number"], finding["action_index"])
        if key not in grouped:
            grouped[key] = {
                key_name: value
                for key_name, value in finding.items()
                if key_name not in {"failure_category", "failure_reason", "numerator", "match_numerator"}
            } | {
                "numerator": 1,
                "denominator": aggregate[finding["scope"]]["target_actions"],
                "is_current_entry": finding["scope"] == "own" and finding["match_id"] in current_match_ids,
                "failure_categories": [],
                "failure_reasons": {},
            }
        grouped[key]["failure_categories"].append(finding["failure_category"])
        grouped[key]["failure_reasons"][finding["failure_category"]] = finding["failure_reason"]
    return list(grouped.values())


def write_report(snapshot: dict, findings: list[dict], talk_findings: list[dict]) -> None:
    lines = [
        "# Public failure miner latest report",
        "",
        f"Updated: {snapshot['updated_at']}  ",
        f"Deadline: {snapshot['deadline']}  ",
        "Scope: hash-validated historical caches plus latest own, Professor Pete, and Accord samples; no whole-archive HTTP crawling.",
        "",
        "## Current published entry/version",
        "",
        f"Identity: `{json.dumps(snapshot['current_entry']['entry'], sort_keys=True)}`",
        "",
        f"- **current own**: {snapshot['current_entry']['unique_affected_actions']}/{snapshot['current_entry']['target_actions']} unique affected actions ({snapshot['current_entry']['unique_affected_action_rate']:.6%}), outcomes `{json.dumps(snapshot['current_entry']['execution_outcome_counts'], sort_keys=True)}`. This is the only current-entry incident rate.",
        "",
        "## All-history aggregates (includes earlier deployments; not current-entry regression)",
        "",
    ]
    for scope, summary in snapshot["aggregate"].items():
        lines.append(f"- **{scope}**: {summary['unique_affected_actions']}/{summary['target_actions']} unique affected actions ({summary['unique_affected_action_rate']:.6%}), outcomes `{json.dumps(summary['execution_outcome_counts'], sort_keys=True)}`, non-additive tags `{json.dumps(summary['failure_counts_nonadditive'], sort_keys=True)}`, talk flags `{json.dumps(summary['appropriateness_flag_counts'], sort_keys=True)}`.")
    lines.extend(["", "## Recent findings for review", ""])
    if not findings:
        lines.append("No supported execution findings in the collected scope.")
    for finding in findings[-30:]:
        lines.append(f"- `{finding['match_id']}` hand {finding['hand_number']} action {finding['action_index']} ({finding['street']}): **{finding['failure_category']}** — {finding['failure_reason']}; {finding['numerator']}/{finding['denominator']} in scope; [Raw JSON]({finding['source_url']}).")
    if talk_findings:
        lines.extend(["", "## Table-talk appropriateness review", ""])
        for finding in talk_findings[-20:]:
            lines.append(f"- `{finding['match_id']}` hand {finding['hand_number']} action {finding['action_index']}: **{finding['appropriateness_flag']}**, actual say: {finding['say']!r}; [Raw JSON]({finding['source_url']}).")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {value}" for value in UNSUPPORTED.values())
    lines.append("- Leader sampling is small and nonrepresentative; rates are descriptive, not proof of leaderboard causality or poker optimality.")
    lines.append("- Table-talk flags are deterministic review aids, not final safety judgments. No table-talk search is performed.")
    atomic_write(ROOT / "REPORT.md", ("\n".join(lines) + "\n").encode())


def run_once(fetch: Fetcher | None = None) -> dict:
    fetch = fetch or Fetcher(interval=1.0)
    cycle_time = now()
    cycle_id = cycle_time.strftime("%Y%m%dT%H%M%SZ")
    cycle_dir = ROOT / "cycles" / cycle_id
    external, external_summary = source_cache()
    records = {row["id"]: row for row in read_jsonl(ROOT / "manifest.jsonl")}
    for match_id, source in external.items():
        old = records.get(match_id, {})
        old_scopes = {"pete" if scope == "leader" else scope for scope in old.get("scopes", [])}
        if valid_cached(old, ROOT / "raw" / f"{match_id}.json"):
            row = old
        else:
            raw = Path(source["source_bytes_path"]).read_bytes()
            atomic_write(ROOT / "raw" / f"{match_id}.json", raw)
            row = source | {
                "id": match_id,
                "result": "complete",
                "collection": source["cache_name"],
                "local_sha256": sha256(raw),
                "locally_saved_at": stamp(now()),
            }
        row["scopes"] = sorted(old_scopes | set(source["cache_scopes"]))
        records[match_id] = row
    write_jsonl(ROOT / "manifest.jsonl", records.values())
    coverage = {}
    selected = {}
    for scope, (entry_id, team_url) in TEAMS.items():
        team_raw = fetch(team_url)
        team_path = cycle_dir / f"{scope}-team.html"
        atomic_write(team_path, team_raw)
        listing_urls = []
        for link in Links(team_raw.decode()).links:
            url = urljoin(BASE, link)
            if urlparse(url).path == "/matches" and parse_qs(urlparse(url).query).get("entry") == [entry_id] and url not in listing_urls:
                listing_urls.append(url)
        if not listing_urls:
            raise ValueError(f"team page has no actual match-listing link for {entry_id}")
        listing_url = listing_urls[0]
        raw = fetch(listing_url)
        listing_path = cycle_dir / f"{scope}-listing.html"
        atomic_write(listing_path, raw)
        discovered = match_links(raw)
        selected[scope] = discovered[: LIMITS[scope]]
        coverage[scope] = {
            "team_url": team_url,
            "team_file": str(team_path.relative_to(ROOT)),
            "team_sha256": sha256(team_raw),
            "url": listing_url,
            "file": str(listing_path.relative_to(ROOT)),
            "sha256": sha256(raw),
            "discovered_on_first_page": len(discovered),
            "selected": len(selected[scope]),
            "not_selected": len(discovered) - len(selected[scope]),
            "pagination": "first page only by design; listing URL followed from team page",
        }
    for scope, match_ids in selected.items():
        for match_id in match_ids:
            if now() >= DEADLINE:
                break
            row = collect_match(fetch, match_id, records.get(match_id, {}), external)
            row["scopes"] = sorted({"pete" if value == "leader" else value for value in row.get("scopes", [])} | {scope})
            row["last_selected_at"] = stamp(cycle_time)
            records[match_id] = row
            write_jsonl(ROOT / "manifest.jsonl", records.values())
    findings, talk_findings, aggregate = mine(records)
    current_records, current_identity = current_entry_records(records)
    _, _, current_aggregate = mine(current_records)
    current_entry = current_aggregate["own"] | {
        "aggregation_scope": current_identity["selection"],
        "entry": current_identity,
        "warning": "This is the only own aggregate representing the current published entry/version.",
    }
    regressions = regression_examples(findings, aggregate, set(current_records))
    current_regressions = [row for row in regressions if row["is_current_entry"]]
    write_jsonl(ROOT / "findings.jsonl", findings)
    write_jsonl(ROOT / "regression_examples.jsonl", regressions)
    write_jsonl(ROOT / "current_entry_regression_examples.jsonl", current_regressions)
    write_jsonl(ROOT / "table_talk_review.jsonl", talk_findings)
    snapshot = {
        "schema_version": 1,
        "updated_at": stamp(now()),
        "cycle_id": cycle_id,
        "deadline": stamp(DEADLINE),
        "code_sha256": sha256(Path(__file__).read_bytes()),
        "team_url": f"{BASE}/teams/{OUR_ORG}",
        "coverage": coverage,
        "collection_results": dict(Counter(row.get("result", "unknown") for row in records.values())),
        "selected_results": {scope: dict(Counter(records[match_id].get("result", "missing") for match_id in match_ids if match_id in records)) for scope, match_ids in selected.items()},
        "manifest_rows": len(records),
        "historical_cache_matches_ingested": len(external),
        "raw_downloads_this_cycle": sum(row.get("last_selected_at") == stamp(cycle_time) and row.get("collection") == "public_http" and row.get("fetched_at", "") >= stamp(cycle_time) for row in records.values()),
        "external_cache": external_summary,
        "aggregate_scope": "all_history_including_previous_deployments_not_current_entry_regression",
        "aggregate": aggregate,
        "current_entry": current_entry,
        "unsupported": UNSUPPORTED,
        "table_talk_search": "stopped_permanently_unless_separately_instructed",
    }
    write_json(ROOT / "latest.json", snapshot)
    write_report(snapshot, findings, talk_findings)
    status = snapshot | {
        "pid": os.getpid(),
        "poller_alive": True,
        "status": "running",
        "next_poll_earliest": stamp(now() + timedelta(seconds=600)),
        "alerts": current_regressions[-20:],
        "paths": {"root": str(ROOT), "latest": str(ROOT / "latest.json"), "report": str(ROOT / "REPORT.md"), "findings": str(ROOT / "findings.jsonl"), "regression_examples": str(ROOT / "regression_examples.jsonl"), "current_entry_regression_examples": str(ROOT / "current_entry_regression_examples.jsonl")},
    }
    write_json(STATUS_PATH, status)
    return snapshot


def poll() -> None:
    while now() < DEADLINE:
        cycle_started = now()
        try:
            snapshot = run_once()
            print(json.dumps({"cycle": snapshot["cycle_id"], "collection": snapshot["collection_results"], "current_entry_unique_affected": snapshot["current_entry"]["unique_affected_actions"], "current_entry_actions": snapshot["current_entry"]["target_actions"], "current_entry_outcomes": snapshot["current_entry"]["execution_outcome_counts"]}), flush=True)
        except Exception as error:
            status = {"pid": os.getpid(), "poller_alive": True, "status": "cycle_failed", "updated_at": stamp(now()), "deadline": stamp(DEADLINE), "error": f"{type(error).__name__}: {error}", "next_poll_earliest": stamp(now() + timedelta(seconds=600))}
            write_json(STATUS_PATH, status)
            print(json.dumps(status), flush=True)
        remaining = 600 - (now() - cycle_started).total_seconds()
        if remaining > 0 and now() < DEADLINE:
            time.sleep(min(remaining, max(0, (DEADLINE - now()).total_seconds())))
    prior = {}
    if STATUS_PATH.exists():
        prior = json.loads(STATUS_PATH.read_text())
    write_json(STATUS_PATH, prior | {"pid": os.getpid(), "poller_alive": False, "status": "stopped_deadline", "stopped_at": stamp(now()), "deadline": stamp(DEADLINE)})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["once", "poll"])
    args = parser.parse_args()
    ROOT.mkdir(parents=True, exist_ok=True)
    release = ROOT / "release.json"
    release_data = json.loads(release.read_text()) if release.exists() else {"created_at": stamp(now())}
    release_data.update(cutoff=stamp(DEADLINE), code_sha256=sha256(Path(__file__).read_bytes()), sources={scope: team_url for scope, (_, team_url) in TEAMS.items()}, team=f"{BASE}/teams/{OUR_ORG}")
    write_json(release, release_data)
    if args.command == "once":
        print(json.dumps(run_once(), indent=2))
    else:
        poll()


if __name__ == "__main__":
    main()

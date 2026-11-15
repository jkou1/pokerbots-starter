"""Resumable public match archive collection: python -m vals_tools.arena collect."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urljoin, urlparse
from urllib.request import Request, urlopen

BASE = "https://www.pokerbots.ac"
MATCH_ID = re.compile(r"m_[a-zA-Z0-9_]+\Z")


def write_json(path: Path, value) -> None:
    atomic_write(path, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


def read_jsonl(path: Path) -> list[dict]:
    return (
        [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        if path.exists()
        else []
    )


def write_jsonl(path: Path, rows) -> None:
    atomic_write(
        path,
        b"".join((json.dumps(row, sort_keys=True) + "\n").encode() for row in rows),
    )


class Links(HTMLParser):
    def __init__(self, html: str):
        super().__init__()
        self.links: list[str] = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "a" and (href := dict(attrs).get("href")):
            self.links.append(href)


class Fetcher:
    def __init__(self, interval: float = 1):
        self.interval = interval
        self.last = 0.0

    def __call__(self, url: str) -> bytes:
        for attempt in range(4):
            time.sleep(max(0, self.last + self.interval - time.monotonic()))
            self.last = time.monotonic()
            try:
                request = Request(
                    url, headers={"User-Agent": "pokerbots-training-archive/1.0"}
                )
                with urlopen(request, timeout=30) as response:
                    return response.read()
            except (HTTPError, URLError, TimeoutError) as exc:
                if isinstance(exc, HTTPError) and exc.code not in (
                    408,
                    429,
                    500,
                    502,
                    503,
                    504,
                ):
                    raise
                if attempt == 3:
                    raise
                retry = (
                    exc.headers.get("Retry-After", "0")
                    if isinstance(exc, HTTPError)
                    else "0"
                )
                try:
                    delay = float(retry)
                except ValueError:
                    from email.utils import parsedate_to_datetime

                    delay = max(
                        0, parsedate_to_datetime(retry).timestamp() - time.time()
                    )
                time.sleep(max(2**attempt, delay))
        raise AssertionError("unreachable")


def discover(fetch, base: str = BASE) -> dict[str, str]:
    url, visited, found = base + "/matches", set(), {}
    while url and url not in visited:
        visited.add(url)
        links = Links(fetch(url).decode()).links
        for link in links:
            path = urlparse(urljoin(base, link)).path
            match_id = path.removeprefix("/matches/")
            if path.startswith("/matches/") and MATCH_ID.fullmatch(match_id):
                found[match_id] = urljoin(base, path)
        page = int(parse_qs(urlparse(url).query).get("page", [1])[0])
        older = [
            urljoin(base, link)
            for link in links
            if urlparse(urljoin(base, link)).path == "/matches"
            and parse_qs(urlparse(urljoin(base, link)).query).get("page")
            == [str(page + 1)]
        ]
        url = next((link for link in older if link not in visited), None)
    return found


def collect(root: Path, fetch, *, limit: int | None = None, base: str = BASE) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    release_path = root / "release.json"
    if not release_path.exists():
        write_json(
            release_path,
            {"cutoff": datetime.now(UTC).isoformat(), "source": base + "/matches"},
        )
    cutoff = datetime.fromisoformat(json.loads(release_path.read_text())["cutoff"])
    records = {r["id"]: r for r in read_jsonl(root / "manifest.jsonl")}
    discovered, previous, passes = {}, None, 0
    while True:
        batch = discover(fetch, base)
        discovered.update(batch)
        passes += 1
        if set(batch) == previous:
            break
        previous = set(batch)
        if passes >= 5:
            break
    downloaded = 0
    for match_id, replay_url in sorted(discovered.items()):
        old = records.get(match_id, {})
        path = root / "raw" / f"{match_id}.json"
        if (
            old.get("result") == "complete"
            and path.exists()
            and hashlib.sha256(path.read_bytes()).hexdigest() == old.get("sha256")
        ):
            continue
        if limit is not None and downloaded >= limit:
            break
        row = {
            "id": match_id,
            "replay_url": replay_url,
            "fetched_at": datetime.now(UTC).isoformat(),
        }
        try:
            links = Links(fetch(replay_url).decode()).links
            raw_urls = [
                urljoin(base, link)
                for link in links
                if urlparse(urljoin(base, link)).path.endswith(".json")
            ]
            if len(raw_urls) != 1:
                raise ValueError(f"expected one Raw JSON link, found {len(raw_urls)}")
            row["raw_url"] = raw_urls[0]
            raw = fetch(raw_urls[0])
            match = json.loads(raw)
            if match.get("id") != match_id:
                raise ValueError("raw match ID does not match replay")
            row.update(
                schema=match.get("schema"),
                runner_version=match.get("runner_version"),
                kind=match.get("kind"),
                status=match.get("status"),
                sha256=hashlib.sha256(raw).hexdigest(),
            )
            if match.get("status") != "complete":
                row["result"] = "incomplete"
            elif datetime.fromisoformat(match["finished_at"]) > cutoff:
                row["result"] = "after_cutoff"
            else:
                atomic_write(path, raw)
                row["result"] = "complete"
                downloaded += 1
        except (OSError, ValueError, KeyError) as exc:
            row.update(result="failed", error=f"{type(exc).__name__}: {exc}")
        records[match_id] = row
        write_jsonl(root / "manifest.jsonl", records.values())
        print(json.dumps({"id": match_id, "result": row["result"]}), flush=True)
    summary = {
        "discovered": len(discovered),
        "complete": sum(r.get("result") == "complete" for r in records.values()),
        "failed": sum(r.get("result") == "failed" for r in records.values()),
        "passes": passes,
        "discovery_stable": set(batch) == previous and passes < 5,
        "cutoff": cutoff.isoformat(),
    }
    write_json(root / "collection.json", summary)
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["collect"])
    p.add_argument("--root", type=Path, default=Path("data/arena"))
    p.add_argument("--limit", type=int)
    p.add_argument("--interval", type=float, default=1)
    args = p.parse_args()
    if args.interval < 0 or (args.limit is not None and args.limit < 1):
        p.error("interval must be nonnegative and limit positive")
    print(json.dumps(collect(args.root, Fetcher(args.interval), limit=args.limit)))


if __name__ == "__main__":
    main()

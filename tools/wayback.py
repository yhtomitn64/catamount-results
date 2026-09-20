#!/usr/bin/env python3
"""A polite Wayback Machine client: slow, identified, and cached on disk.

The Internet Archive is a public service that asks for gentle use, so this never
runs concurrently, waits several seconds between requests, backs off hard on a
rate limit or its "Temporarily Offline" page, and stores every page it fetches
under cache/wayback/ (gitignored) so a page is only ever requested once.

    python tools/wayback.py cdx "catamountoutdoor.com/results/*" --from 2017 --to 2019
    python tools/wayback.py get 20191108075234 "http://catamountoutdoor.com/results/2019/062619.htm"

Nothing here is specific to Catamount; scrape-specific parsing lives elsewhere.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import random
import re
import sys
import time

import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "wayback"
UA = "catamount-results/1.0 (personal race-results archive; contact via github.com/yhtomitn64/catamount-results)"

MIN_GAP = 4.0        # seconds between any two requests
JITTER = 2.0         # plus up to this much, so requests are not metronomic
BACKOFF = (60, 180, 600)   # waits after a failure, then give up

_session = requests.Session()
_session.headers["User-Agent"] = UA
_last = 0.0


class ArchiveUnavailable(RuntimeError):
    pass


def _slow_get(url: str, params: dict | None = None) -> requests.Response:
    """GET with a minimum gap, and patient retries when the Archive pushes back."""
    global _last
    for attempt in range(len(BACKOFF) + 1):
        wait = MIN_GAP + random.random() * JITTER - (time.time() - _last)
        if wait > 0:
            time.sleep(wait)
        try:
            resp = _session.get(url, params=params, timeout=60)
            _last = time.time()
        except requests.RequestException as exc:
            _last = time.time()
            problem = f"network error: {exc}"
        else:
            offline = "Temporarily Offline" in resp.text[:2000]
            if resp.status_code == 200 and not offline:
                return resp
            if resp.status_code == 404:
                return resp
            problem = "offline page" if offline else f"HTTP {resp.status_code}"
        if attempt == len(BACKOFF):
            raise ArchiveUnavailable(f"{problem} for {url}; giving up so we do not hammer it")
        pause = BACKOFF[attempt]
        print(f"  wayback: {problem}; waiting {pause}s before retrying", file=sys.stderr)
        time.sleep(pause)
    raise AssertionError("unreachable")


def _key(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode()).hexdigest()[:16]


def cdx(url: str, *, year_from: str | None = None, year_to: str | None = None,
        match: str | None = None, limit: int = 5000) -> list[tuple[str, str]]:
    """List captures as (timestamp, original_url), one per distinct URL. Cached."""
    params = {"url": url, "output": "json", "fl": "timestamp,original", "filter": "statuscode:200",
              "collapse": "urlkey", "limit": limit}
    if year_from: params["from"] = year_from
    if year_to: params["to"] = year_to
    if match: params["matchType"] = match
    path = CACHE / f"cdx_{_key(json.dumps(params, sort_keys=True))}.json"
    if path.exists():
        return [tuple(r) for r in json.loads(path.read_text())]
    resp = _slow_get("https://web.archive.org/cdx/search/cdx", params)
    rows = resp.json()[1:] if resp.text.strip() else []      # first row is the header
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows))
    return [tuple(r) for r in rows]


def _path(timestamp: str, url: str) -> pathlib.Path:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", url)[-60:]
    return CACHE / f"{timestamp}_{slug}_{_key(timestamp, url)}.html"


def cached(timestamp: str, url: str) -> str | None:
    """The page if it is already on disk; never touches the network."""
    path = _path(timestamp, url)
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else None


def get(timestamp: str, url: str) -> str | None:
    """The archived page as originally served ("id_" = no Wayback toolbar). None if not archived."""
    path = _path(timestamp, url)
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    resp = _slow_get(f"https://web.archive.org/web/{timestamp}id_/{url}")
    if resp.status_code == 404:
        return None
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(resp.text, encoding="utf-8")
    return resp.text


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("cdx"); c.add_argument("url"); c.add_argument("--from", dest="year_from"); c.add_argument("--to", dest="year_to"); c.add_argument("--match")
    g = sub.add_parser("get"); g.add_argument("timestamp"); g.add_argument("url")
    args = ap.parse_args()
    if args.cmd == "cdx":
        for ts, url in cdx(args.url, year_from=args.year_from, year_to=args.year_to, match=args.match):
            print(ts, url)
    else:
        text = get(args.timestamp, args.url)
        print(text if text is not None else "(not archived)")


if __name__ == "__main__":
    main()

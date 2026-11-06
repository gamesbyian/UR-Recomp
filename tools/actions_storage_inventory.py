#!/usr/bin/env python3
"""Read-only GitHub Actions artifact inventory across accessible repositories.

Uses the caller's authenticated GitHub CLI. Never downloads or deletes artifacts.
Current bytes are an estimate from GitHub's compressed artifact metadata, NOT
the account's accrued GB-hours or a billing statement.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import time

REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
PAGE_SIZE = 100
ALLOWED_PAGE_SIZES = (25, 50, 100)


def gh_json(*args):
    """Read GitHub JSON with small transient retries and status-only errors.

    Never print raw stderr, request headers or credentials. Stable denial is
    an error, and a failed repository remains excluded from account totals.
    """
    for attempt in range(3):
        try:
            result = subprocess.run(
                ["gh", *args], text=True, capture_output=True,
                timeout=45, check=False,
            )
        except subprocess.TimeoutExpired as exc:
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError("GitHub CLI timed out after 3 attempts") from exc
        except OSError as exc:
            raise RuntimeError("GitHub CLI unavailable") from exc
        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError as exc:
                raise RuntimeError("GitHub CLI returned invalid JSON") from exc
        # gh's stderr may contain sensitive request information: only expose
        # an HTTP status code parsed from it, never the underlying text.
        match = re.search(r"\bHTTP\s*([1-5][0-9]{2})\b", result.stderr or "")
        status = int(match.group(1)) if match else None
        transient = status in (429, 502, 503, 504) or (
            "secondary rate limit" in (result.stderr or "").lower()
            # Large artifact pages can be truncated in transport. Retry
            # twice, never accept malformed JSON as valid evidence.
            or "unexpected end of json input" in (result.stderr or "").lower()
        )
        if transient and attempt < 2:
            time.sleep(2 ** attempt)
            continue
        kind = f"HTTP {status}" if status is not None else "status unavailable"
        raise RuntimeError(f"GitHub CLI failed ({kind}); no storage count claimed")
    raise RuntimeError("GitHub CLI transient retries exhausted")


def repositories(owner, api=gh_json):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", owner):
        raise ValueError("invalid GitHub owner")
    rows = api("repo", "list", owner, "--limit", "200", "--json", "nameWithOwner")
    if not isinstance(rows, list) or len(rows) >= 200:
        raise ValueError("repository listing is invalid or potentially truncated")
    names = [row.get("nameWithOwner") for row in rows if isinstance(row, dict)]
    if len(names) != len(rows) or any(not isinstance(n, str) or not REPO.fullmatch(n) for n in names):
        raise ValueError("invalid repository record")
    return sorted(set(names))


def artifact_inventory(repo, api=gh_json, max_pages=200, *,
                       page_size=PAGE_SIZE, recheck_first_page=False):
    if not isinstance(repo, str) or not REPO.fullmatch(repo):
        raise ValueError("invalid repository")
    if type(max_pages) is not int or not 1 <= max_pages <= 1000:
        raise ValueError("invalid max_pages")
    if type(page_size) is not int or page_size not in ALLOWED_PAGE_SIZES:
        raise ValueError("invalid page_size")
    if type(recheck_first_page) is not bool:
        raise ValueError("invalid recheck_first_page")
    artifacts, seen = [], set()
    expected = None
    first_page_ids = None
    for page in range(1, max_pages + 1):
        response = api("api", f"repos/{repo}/actions/artifacts?per_page={page_size}&page={page}")
        if not isinstance(response, dict) or not isinstance(response.get("artifacts"), list):
            raise ValueError(f"{repo}: invalid artifact page {page}")
        total = response.get("total_count")
        if type(total) is not int or total < 0:
            raise ValueError(f"{repo}: missing artifact total_count")
        if expected is None:
            expected = total
        elif expected != total:
            raise RuntimeError(f"{repo}: artifact count changed during pagination, rerun inventory")
        batch = response["artifacts"]
        if len(batch) > page_size:
            raise ValueError(f"{repo}: oversized artifact page")
        if page == 1:
            first_page_ids = [x.get("id") if isinstance(x, dict) else None for x in batch]
        for item in batch:
            if not isinstance(item, dict) or type(item.get("id")) is not int or item["id"] <= 0:
                raise ValueError(f"{repo}: invalid artifact identifier")
            if item["id"] in seen:
                raise RuntimeError(f"{repo}: duplicate artifact across pages, rerun inventory")
            if type(item.get("size_in_bytes")) is not int or item["size_in_bytes"] < 0:
                raise ValueError(f"{repo}: invalid artifact byte count")
            if not isinstance(item.get("name"), str) or not item["name"]:
                raise ValueError(f"{repo}: invalid artifact name")
            seen.add(item["id"])
            artifacts.append(item)
        if len(batch) < page_size:
            if len(artifacts) != expected:
                raise RuntimeError(f"{repo}: incomplete inventory ({len(artifacts)}/{expected}), rerun")
            if recheck_first_page:
                check = api("api", f"repos/{repo}/actions/artifacts?per_page={page_size}&page=1")
                if not isinstance(check, dict) or type(check.get("total_count")) is not int \
                        or not isinstance(check.get("artifacts"), list) \
                        or check["total_count"] != expected \
                        or [a.get("id") if isinstance(a, dict) else None
                            for a in check["artifacts"]] != first_page_ids:
                    raise RuntimeError(f"{repo}: first page changed during census, rerun inventory")
            return artifacts
    raise RuntimeError(f"{repo}: reached {max_pages} pages; refusing truncated inventory")


def parse_date(value):
    if not isinstance(value, str):
        raise ValueError("missing artifact timestamp")
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid artifact timestamp") from exc
    if date.tzinfo is None:
        raise ValueError("artifact timestamp lacks timezone")
    return date.astimezone(timezone.utc)


def summarize(repo, artifacts, *, now=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    active, expired = [], 0
    for a in artifacts:
        expiry = parse_date(a.get("expires_at"))
        created = parse_date(a.get("created_at"))
        if expiry < created or type(a.get("expired")) is not bool:
            raise ValueError("invalid artifact lifetime/status")
        if a["expired"] or expiry <= now:
            expired += 1
            continue
        active.append({
            "id": a["id"], "name": a["name"],
            "bytes": a["size_in_bytes"], "created_at": created.isoformat(),
            "expires_at": expiry.isoformat(),
        })
    by_name = defaultdict(lambda: {"count": 0, "bytes": 0})
    for a in active:
        family = by_name[a["name"]]
        family["count"] += 1
        family["bytes"] += a["bytes"]
    families = sorted(
        ({"name": n, **v} for n, v in by_name.items()),
        key=lambda x: (-x["bytes"], x["name"]),
    )
    return {
        "repository": repo, "complete": True, "listed_count": len(artifacts),
        "expired_count": expired, "active_count": len(active),
        "current_artifact_bytes_estimate": sum(a["bytes"] for a in active),
        "largest": sorted(active, key=lambda x: (-x["bytes"], x["id"]))[:20],
        "largest_name_groups": families[:20],
    }


def markdown(rows):
    total = sum(r["current_artifact_bytes_estimate"] for r in rows)
    lines = [
        "# Actions artifact inventory (read only)",
        "",
        "Metadata-based compressed-byte estimates, not billing GB-hours. "
        "No download, deletion or preservation judgement was performed.",
        "",
        "| Repository | Retained artifacts | Estimated MiB |",
        "|---|---:|---:|",
    ]
    for row in sorted(rows, key=lambda r: -r["current_artifact_bytes_estimate"]):
        size = row["current_artifact_bytes_estimate"] / 1048576
        lines.append(f"| {row['repository']} | {row['active_count']} | {size:.1f} |")
    lines += ["", f"**Total across inventoried repositories:** {total / 1048576:.1f} MiB", "",
              "## Largest currently retained objects", "",
              "| Repository | Name | MiB | Artifact ID | Expiry (UTC) |",
              "|---|---|---:|---:|---|"]
    large = sorted(
        ((row["repository"], a) for row in rows for a in row["largest"]),
        key=lambda x: -x[1]["bytes"],
    )[:30]
    for repo, a in large:
        safe_name = a["name"].replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {repo} | {safe_name} | {a['bytes'] / 1048576:.1f} "
            f"| {a['id']} | {a['expires_at'][:10]} |"
        )
    lines += ["", "This report is **not** a deletion list. Review exact-source "
              "evidence, release/research dependencies, and preservation requirements "
              "before selecting any artifact for irreversible removal.", ""]
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--owner", default="gamesbyian")
    p.add_argument("--repo", action="append", help="Owner/name; repeat for a specific subset")
    p.add_argument("--max-pages", type=int, default=200)
    p.add_argument("--page-size", type=int, choices=ALLOWED_PAGE_SIZES, default=PAGE_SIZE,
                   help="bounded artifacts per API page (smaller for very large repositories)")
    p.add_argument("--recheck-first-page", action="store_true",
                   help="fail if the newest artifact IDs or count changed while paging")
    p.add_argument("--json-out", type=Path)
    args = p.parse_args()
    repos = args.repo or repositories(args.owner)
    if not repos:
        raise SystemExit("No repositories discovered")
    rows = [summarize(repo, artifact_inventory(
        repo, max_pages=args.max_pages, page_size=args.page_size,
        recheck_first_page=args.recheck_first_page))
            for repo in sorted(set(repos))]
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps({"schema": "actions-artifact-inventory/v1",
                        "repositories": rows}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(markdown(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

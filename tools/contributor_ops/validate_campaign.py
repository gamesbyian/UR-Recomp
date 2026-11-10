#!/usr/bin/env python3
"""Validate public, stateless Uniracers contributor outreach records.

No network access, authentication, forum posting, emails or private records.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

REPO = Path(__file__).resolve().parents[2]
VALID_STATES = {"draft", "blocked", "reported_posted", "posted", "closed"}
MANDATORY_TERMS = ("Baldosa", "malmazuke", "Uniracers", "Unirally", "unpaid")


def is_https_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        url = urlsplit(value)
        return url.scheme == "https" and bool(url.netloc) and not url.username and not url.password
    except ValueError:
        return False


def validate(root: Path = REPO) -> list[str]:
    errors: list[str] = []
    index = root / "docs/contributors/campaign.json"
    try:
        manifest = json.loads(index.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"unable to read campaign manifest: {exc}"]
    if manifest.get("schema_version") != 1:
        errors.append("unsupported manifest schema_version")
    venues = manifest.get("venues")
    if not isinstance(venues, list) or not venues:
        return errors + ["no venue records in manifest"]
    ids: set[str] = set()
    paths: set[str] = set()
    for row in venues:
        if not isinstance(row, dict):
            errors.append("venue must be an object")
            continue
        vid = row.get("id")
        if not isinstance(vid, str) or not vid or vid in ids:
            errors.append(f"missing or duplicate venue id: {vid!r}")
        ids.add(str(vid))
        if row.get("state") not in VALID_STATES:
            errors.append(f"{vid}: invalid state")
        if not is_https_url(row.get("forum_url")):
            errors.append(f"{vid}: forum_url must be an HTTPS URL")
        if row.get("state") == "posted":
            if not is_https_url(row.get("posted_url")) or not row.get("posted_at_utc"):
                errors.append(f"{vid}: a posted record requires actual permalink and timestamp")
            elif row.get("posted_url").rstrip("/") == row.get("forum_url").rstrip("/"):
                errors.append(f"{vid}: posted permalink cannot be the subreddit homepage")
        elif row.get("state") == "reported_posted":
            # Owner confirmed posting, but did not provide an individual post URL.
            # Preserve evidence of outreach without inventing a permalink or date.
            if row.get("report_source") != "owner" or not row.get("reported_posted_on"):
                errors.append(f"{vid}: reported posting requires owner report and report date")
            if row.get("posted_url") or row.get("posted_at_utc"):
                errors.append(f"{vid}: unverified report must not claim a permalink or timestamp")
        elif row.get("posted_url") or row.get("posted_at_utc"):
            errors.append(f"{vid}: non-posted record must not claim a posted URL/time")
        rel = row.get("post_file")
        if not isinstance(rel, str):
            errors.append(f"{vid}: missing post_file")
            continue
        subpath = Path(rel)
        if (
            subpath.is_absolute()
            or ".." in subpath.parts
            or not rel.startswith("docs/contributors/posts/")
            or subpath.suffix != ".md"
        ):
            errors.append(f"{vid}: unsafe post_file path")
            continue
        if rel in paths:
            errors.append(f"{vid}: duplicate post_file")
        paths.add(rel)
        target = root / subpath
        if not target.is_file():
            errors.append(f"{vid}: missing draft {rel}")
            continue
        body = target.read_text(encoding="utf-8")
        for term in MANDATORY_TERMS:
            if term.lower() not in body.lower():
                errors.append(f"{vid}: missing {term} disclosure")
        if "https://github.com/gamesbyian/UR-Recomp" not in body:
            errors.append(f"{vid}: missing project evidence link")
        if row.get("forum_url") not in body:
            errors.append(f"{vid}: draft does not identify its target venue")
        if len(body) < 450:
            errors.append(f"{vid}: insufficient explanatory content")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    problems = validate(args.root)
    if args.json:
        print(json.dumps({"ok": not problems, "errors": problems}, indent=2))
    else:
        for problem in problems:
            print("ERROR:", problem)
        print("PASS: campaign validated; no posts or email sent" if not problems else "FAIL")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Cheap, bounded, advisory unit feedback for in-progress *draft* PRs.

The full 'unit' check is still REQUIRED after ready_for_review. This tool
never chooses or certifies the full dependency population, product behaviour,
original/native parity or release QA. Untrusted/incomplete PR census gives
zero extra tests, not an invented safe subset.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

MAX_PAGES = 3
MAX_MODULES = 6
MAX_ESTIMATED_SECONDS = 12.0
MAX_ONE_MODULE_SECONDS = 4.0
UNKNOWN_TEST_SECONDS = 1.0
HEX_MODULE = re.compile(r"test_[A-Za-z0-9_]+\.py\Z")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
PR = re.compile(r"[1-9][0-9]{0,8}\Z")
SOURCE = re.compile(r"tools/([A-Za-z0-9_]+)\.py\Z")
UNIT_TEST = re.compile(r"tests/unit/(test_[A-Za-z0-9_]+\.py)\Z")
WORKFLOW = re.compile(r"\.github/workflows/[A-Za-z0-9_.-]+\.ya?ml\Z")


def census(fetch_page):
    """Return a complete validated changed-filename set, otherwise None."""
    observed = set()
    for page in range(1, MAX_PAGES + 1):
        try:
            items = fetch_page(page)
        except (OSError, HTTPError, URLError, TimeoutError, TypeError,
                ValueError, KeyError, UnicodeError):
            return None
        if type(items) is not list or len(items) > 100:
            return None
        for item in items:
            if type(item) is not dict:
                return None
            path = item.get("filename")
            if (type(path) is not str or not path or path in observed
                    or item.get("status") not in ("modified", "added")):
                return None
            observed.add(path)
        if len(items) < 100:
            return observed if observed else None
    # Exact 300 files has unknown fourth page.
    return None


def select(changed, timings, available):
    """Select only inexpensive, directly related modules; no completeness claim.

    Explicit changed tests take precedence over guessed source mappings.
    Never infer cross-module dependencies from names. Genuine full suite runs
    at ready-for-review, independent of this draft diagnostic.
    """
    if (type(changed) is not set or not changed
            or type(timings) is not dict or type(available) is not set):
        return []
    candidates = []
    seen = set()

    def add(name):
        if name in available and name not in seen and HEX_MODULE.fullmatch(name + ".py"):
            candidates.append(name)
            seen.add(name)

    for path in sorted(changed):
        m = UNIT_TEST.fullmatch(path)
        if m:
            add(m.group(1)[:-3])
    for path in sorted(changed):
        m = SOURCE.fullmatch(path)
        if m:
            add("test_" + m.group(1))
        if WORKFLOW.fullmatch(path):
            add("test_ci_trigger_policy")
            if path == ".github/workflows/tooling-unit-tests.yml":
                add("test_tooling_unit_workflow_contract")
    if changed.intersection({"AGENTS.md", "docs/HOURLY-AGENT-LINES.md",
                             "docs/WORK-QUEUE.md", "docs/AGENT-COORDINATION.md"}):
        add("test_agent_control")

    result = []
    cost = 0.0
    for name in candidates:
        mod = "tests.unit." + name
        value = timings.get(mod, UNKNOWN_TEST_SECONDS)
        if (type(value) not in (int, float) or not math.isfinite(value)
                or value < 0 or value > MAX_ONE_MODULE_SECONDS):
            continue
        if len(result) >= MAX_MODULES or cost + value > MAX_ESTIMATED_SECONDS:
            break
        result.append(mod)
        cost += value
    return result


def github_census(repo, pr_number, token, fetch=None):
    if (type(repo) is not str or not REPO.fullmatch(repo)
            or type(pr_number) is not str or not PR.fullmatch(pr_number)
            or not token):
        return None

    def get(page):
        if fetch is not None:
            return fetch(page)
        url = (f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
               f"?per_page=100&page={page}")
        headers = {
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "UR-Recomp-draft-targeted-tests",
        }
        with urlopen(Request(url, headers=headers), timeout=8) as response:
            return json.load(response)

    return census(get)


def main():
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    pr = os.environ.get("GH_PR_NUMBER", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    root = Path(__file__).resolve().parents[1]
    changed = github_census(repo, pr, token)
    try:
        timings = json.loads((root / "tools/unit_test_timings.json").read_text())
    except (OSError, ValueError, TypeError):
        timings = {}
    unit_dir = root / "tests/unit"
    available = {p.stem for p in unit_dir.glob("test_*.py")
                 if p.is_file() and not p.is_symlink()}
    selected = select(changed, timings, available)
    # Pure, validated Python module names. GitHub workflow uses mapfile, not eval.
    # Empty selection must emit zero lines: bash mapfile otherwise treats
    # a lone newline as one empty unittest module ("Empty module name").
    if selected:
        print("\n".join(selected))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fail-closed selection of the small operations-only unit suite.

The existing unit status remains mandatory. Only an exhaustive, clean
GitHub PR-files response with every changed file in this isolated allowlist
selects the focused suite. Every API, pagination, rename, deleted-file, mixed,
manual dispatch or unrecognised-state case runs the original full suite.
"""
from __future__ import annotations

import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OPERATIONS_ONLY = frozenset({
    "tools/agent_control.py",
    "tools/ops_live_status.py",
    "tools/ci_cancelled_job_sample.py",
    "tools/report_ci_runtime.py",
    "tools/validate_history_custody.py",
    "tools/backup_main_history.py",
    "tests/unit/test_agent_control.py",
    "tests/unit/test_ops_live_status.py",
    "tests/unit/test_ci_cancelled_job_sample.py",
    "tests/unit/test_report_ci_runtime.py",
    "tests/unit/test_validate_history_custody.py",
    "tests/unit/test_backup_main_history.py",
})
# These specific documents are dispatch CONTEXT, not executable product or
# release configuration. A PR changing them alongside only the isolated ops
# tools above needs the existing agent-control/custody regression, not all 5k+
# product/graphics/native tests. Keep the list exact and deliberately tiny.
# The shared board is exercised by the focused test_agent_control suite.
OPS_CONTEXT_DOCS = frozenset({
    "AGENTS.md",
    "docs/AGENT-COORDINATION.md",
    "docs/HOURLY-AGENT-LINES.md",
    "docs/WORK-QUEUE.md",
    # Only this exact documentation marker requests an already guarded build.
    "docs/playtest/REQUEST-WINDOWS-PLAYTEST.md",
})
OPERATIONS_ONLY = OPERATIONS_ONLY | OPS_CONTEXT_DOCS
# Research workflow edits are *configuration-only*, never native/gameplay
# source changes. Their own producer jobs and repository hygiene independently
# validate execution/actionlint. The focused suite already includes the global
# trigger-policy regression, and the full suite remains mandatory for any tool,
# test, product, release workflow, or mixed-source edit.
#
# Exact filenames are intentionally listed; do not wildcard qa01 or accept the
# authoritative qa01-event-campaign orchestration under this reduced scope.
BOUNDED_RESEARCH_WORKFLOWS = frozenset({
    ".github/workflows/qa01-rf062-evidence-factorization.yml",
    ".github/workflows/qa01-rf062-four-zip-source-archive.yml",
    ".github/workflows/qa01-rf066-rf062-full-raw-crosswalk.yml",
    ".github/workflows/qa01-rf066-same-host-return-raw.yml",
    ".github/workflows/qa01-rf066-source-controller-archive.yml",
    ".github/workflows/qa01-rf071-getter-vs-script-dump.yml",
    ".github/workflows/qa01-rf075-rti-source-contract.yml",
})

FOCUSED_TEST_MODULES = (
    "tests.unit.test_agent_control",
    "tests.unit.test_ops_live_status",
    "tests.unit.test_ci_cancelled_job_sample",
    "tests.unit.test_validate_history_custody",
    "tests.unit.test_backup_main_history",
    "tests.unit.test_report_ci_runtime",
    "tests.unit.test_ci_select_unit_suite",
    "tests.unit.test_ci_trigger_policy",
    "tests.unit.test_ci_playtest_request_guard",
    "tests.unit.test_verify_baldosa_playtest_release",
)
ALLOWED_STATES = frozenset({"added", "modified"})
MAX_PAGES = 3


def classify(files: list[dict]) -> str:
    """Never skip the full suite on absent, duplicate or ambiguous changes."""
    if not isinstance(files, list) or not files or len(files) > MAX_PAGES * 100:
        return "full"
    seen = set()
    for item in files:
        if not isinstance(item, dict):
            return "full"
        path = item.get("filename")
        if (not isinstance(path, str)
                or path in seen or item.get("status") not in ALLOWED_STATES):
            return "full"
        seen.add(path)
    # A mixed ops/research-workflow change may affect both execution policy
    # and its consumer: default to the complete test population.
    if seen.issubset(OPERATIONS_ONLY) or seen.issubset(BOUNDED_RESEARCH_WORKFLOWS):
        return "ops"
    return "full"


def classify_paged(fetch_page, *, max_pages=MAX_PAGES) -> str:
    """A full page is ambiguous until a succeeding short page is observed."""
    if type(max_pages) is not int or not 1 <= max_pages <= MAX_PAGES:
        raise ValueError("unsupported page bound")
    changed = []
    for page in range(1, max_pages + 1):
        data = fetch_page(page)
        if not isinstance(data, list) or len(data) > 100:
            return "full"
        changed.extend(data)
        if len(data) < 100:
            return classify(changed)
    return "full"


def github_mode(repo: str, pr_number: str, token: str, *, fetch=None) -> str:
    """Consume only fixed GitHub API origin and narrowly validated identifiers."""
    if (not isinstance(repo, str)
            or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo)
            or not isinstance(pr_number, str)
            or not re.fullmatch(r"[1-9][0-9]{0,8}", pr_number)
            or not token):
        return "full"

    def request(page: int):
        url = (f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
               f"?per_page=100&page={page}")
        if fetch is not None:
            return fetch(page)
        headers = {
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "UR-Recomp-unit-scope",
        }
        with urlopen(Request(url, headers=headers), timeout=8) as response:
            return json.load(response)

    try:
        return classify_paged(request)
    except (HTTPError, URLError, TimeoutError, OSError,
            ValueError, UnicodeError, TypeError, KeyError):
        return "full"


def main():
    print(github_mode(
        os.environ.get("GITHUB_REPOSITORY", ""),
        os.environ.get("GH_PR_NUMBER", ""),
        os.environ.get("GITHUB_TOKEN", ""),
    ))


if __name__ == "__main__":
    main()

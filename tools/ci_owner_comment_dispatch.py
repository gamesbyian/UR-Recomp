#!/usr/bin/env python3
"""Dispatch narrowly allowlisted CI workflows via repository-owner PR comments.

A successful dispatch is NOT a successful test: inspect the target run's
actual checkout SHA and full evidence before using it for PR qualification.
"""
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

COMMAND = re.compile(
    r"/ur-ci run (tooling-unit-tests\.yml|ghost-target-native-acceptance\.yml|modern-results-navigation-acceptance\.yml) ([0-9a-f]{40})(?: (earned))?\Z"
)
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,119}\Z")

SCIENCE_COMMAND = "/ur-ci hp-research"
SCIENCE_WORKFLOW = "owner-hp-seeded-2p-research.yml"
SCIENCE_COOLDOWN = timedelta(minutes=90)
SCIENCE_SHA = re.compile(r"[0-9a-f]{40}\Z")


def intent(event, repo, owner):
    if not isinstance(event, dict) or event.get("action") != "created":
        return None
    issue, comment = event.get("issue"), event.get("comment")
    if not isinstance(issue, dict) or not isinstance(comment, dict) or not issue.get("pull_request"):
        return None
    body = comment.get("body")
    match = COMMAND.fullmatch(body.strip()) if isinstance(body, str) else None
    if not match:
        return None
    workflow, sha, shard = match.groups()
    # The native earned route is deliberately draft-only and fixed-input.
    # Existing ready-state qualification commands cannot acquire inputs.
    if (workflow == "modern-results-navigation-acceptance.yml") != (shard == "earned"):
        return None
    user = comment.get("user")
    record = event.get("repository")
    if (not isinstance(repo, str) or not REPO.fullmatch(repo)
            or not isinstance(owner, str) or repo.split("/")[0].lower() != owner.lower()
            or not isinstance(record, dict) or record.get("full_name") != repo
            or not isinstance(user, dict) or not isinstance(user.get("login"), str)
            or user["login"].lower() != owner.lower()
            or comment.get("author_association") != "OWNER"):
        raise ValueError("Not a repository-owner command")
    number = issue.get("number")
    if type(number) is not int or number < 1 or number > 999999999:
        raise ValueError("Invalid pull request number")
    return number, workflow, sha, shard


def exact_head(pr, number, repo, sha, *, require_draft=False):
    if (not isinstance(pr, dict) or pr.get("number") != number
            or pr.get("state") != "open" or pr.get("draft") is not require_draft
            or not isinstance(pr.get("head"), dict)):
        raise ValueError("PR has wrong open/draft state or no actual head")
    head = pr["head"]
    origin, branch = head.get("repo"), head.get("ref")
    if (not isinstance(origin, dict) or origin.get("full_name") != repo
            or head.get("sha") != sha
            or not isinstance(branch, str) or not REF.fullmatch(branch)
            or branch == "main" or ".." in branch or "//" in branch
            or branch.endswith(("/", "."))):
        raise ValueError("Stale, forked or unsafe PR head: no dispatch")
    return branch


ACTIVE = frozenset({"queued", "in_progress", "waiting", "pending", "requested"})


def active_run_id(reply, ref, sha):
    """An incomplete or malformed run census must never greenlight a retry."""
    if not isinstance(reply, dict):
        raise ValueError("Cannot inspect existing dispatches")
    runs, count = reply.get("workflow_runs"), reply.get("total_count")
    if (not isinstance(runs, list) or type(count) is not int
            or count < len(runs) or count > len(runs) or len(runs) > 100):
        raise ValueError("Incomplete workflow dispatch census: no retry")
    for row in runs:
        if not isinstance(row, dict):
            raise ValueError("Malformed workflow dispatch census")
        if (row.get("head_branch") == ref and row.get("head_sha") == sha
                and row.get("event") == "workflow_dispatch"
                and row.get("status") in ACTIVE):
            run_id = row.get("id")
            if type(run_id) is not int or run_id <= 0:
                raise ValueError("Ambiguous active workflow run")
            return run_id
    return None


def process(event, repo, owner, get_pr, get_runs, dispatch):
    request = intent(event, repo, owner)
    if request is None:
        return None
    number, workflow, sha, shard = request
    ref = exact_head(get_pr(number), number, repo, sha, require_draft=(shard == "earned"))
    active = active_run_id(get_runs(workflow, ref), ref, sha)
    if active is not None:
        return (number, workflow, sha, ref, active)
    if shard == "earned":
        dispatch(workflow, ref, {"results_shard": "earned"})
    else:
        dispatch(workflow, ref)
    return (number, workflow, sha, ref, None)


def science_intent(event, repo, owner):
    """Require one exact owner-created PR comment, no PR branch execution."""
    if not isinstance(event, dict) or event.get("action") != "created":
        return None
    issue, comment = event.get("issue"), event.get("comment")
    if (not isinstance(issue, dict) or not isinstance(comment, dict)
            or not issue.get("pull_request")
            or not isinstance(comment.get("body"), str)
            or comment["body"].strip() != SCIENCE_COMMAND):
        return None
    record, user = event.get("repository"), comment.get("user")
    if (not isinstance(repo, str) or not REPO.fullmatch(repo)
            or not isinstance(owner, str) or owner.lower() != repo.split("/")[0].lower()
            or not isinstance(record, dict) or record.get("full_name") != repo
            or not isinstance(user, dict) or not isinstance(user.get("login"), str)
            or user["login"].lower() != owner.lower()
            or comment.get("author_association") != "OWNER"):
        raise ValueError("Not an exact repository-owner HP science command")
    number = issue.get("number")
    if type(number) is not int or not 0 < number < 1_000_000_000:
        raise ValueError("Invalid PR number for science dispatch")
    return number


def recent_science_run(reply, now):
    """Reject duplicate HP trials; refuse incomplete or untrustworthy evidence."""
    if not isinstance(reply, dict) or not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError("Unverifiable science run census")
    rows, count = reply.get("workflow_runs"), reply.get("total_count")
    if (not isinstance(rows, list) or type(count) is not int
            or count < len(rows) or len(rows) > 100
            or (count > len(rows) and len(rows) != 100)):
        raise ValueError("Incomplete science run census")
    last_time = None
    recent = None
    for item in rows:
        if (not isinstance(item, dict) or type(item.get("id")) is not int
                or item["id"] < 1 or item.get("head_branch") != "main"
                or not isinstance(item.get("head_sha"), str)
                or not SCIENCE_SHA.fullmatch(item["head_sha"])
                or item.get("event") not in ("schedule", "workflow_dispatch")
                or item.get("status") not in
                   ("queued", "in_progress", "pending", "waiting", "requested", "completed")):
            raise ValueError("Malformed HP science run evidence")
        raw = item.get("created_at")
        if not isinstance(raw, str):
            raise ValueError("Unbound HP science timestamp")
        try:
            when = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("Invalid HP science timestamp") from exc
        if when.tzinfo is None or when > now or (last_time is not None and when > last_time):
            raise ValueError("Future, naive or unordered HP science runs")
        last_time = when
        if recent is None and (item["status"] != "completed"
                              or now - when < SCIENCE_COOLDOWN):
            recent = item["id"]
    if count > len(rows) and (last_time is None or now - last_time < SCIENCE_COOLDOWN):
        raise ValueError("Recent HP science run census truncated")
    return recent


def science_process(event, repo, owner, get_repo, get_runs, dispatch, now):
    """Use only trusted main; the actual trial receipt binds checked-out SHA."""
    number = science_intent(event, repo, owner)
    if number is None:
        return None
    info = get_repo()
    if (not isinstance(info, dict) or info.get("full_name") != repo
            or info.get("default_branch") != "main" or info.get("archived") is not False):
        raise ValueError("Default branch not a live trusted main")
    existing = recent_science_run(get_runs(SCIENCE_WORKFLOW, "main"), now)
    if existing is None:
        dispatch(SCIENCE_WORKFLOW, "main")
    return (number, SCIENCE_WORKFLOW, existing)


def api(repo, token, method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = Request("https://api.github.com/repos/" + repo + path,
        data=data, method=method, headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "UR-Recomp-owner-CI-dispatch",
            **({"Content-Type": "application/json"} if data is not None else {}),
        })
    with urlopen(request, timeout=15) as response:
        content = response.read()
    return json.loads(content) if content else None


def main():
    repo = os.environ["GITHUB_REPOSITORY"]
    owner = os.environ["GITHUB_REPOSITORY_OWNER"]
    token = os.environ["GH_TOKEN"]
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf8"))
    science = science_process(
        event, repo, owner,
        lambda: api(repo, token, "GET", ""),
        lambda workflow, ref: api(repo, token, "GET",
            "/actions/workflows/" + workflow + "/runs?" +
            urlencode({"branch": ref, "per_page": 100})),
        lambda workflow, ref: api(repo, token, "POST",
            "/actions/workflows/" + workflow + "/dispatches", {"ref": ref}),
        datetime.now(timezone.utc))
    if science is not None:
        number, workflow, existing = science
        if existing is None:
            message = ("Requested one trusted-main HP science run from owner PR #"
                       + str(number) + "; only the eventual actual GitHub-run "
                       "SHA and source-bound eight-worker signed receipt can "
                       "establish results. Not evidence of scheduled cron delivery.")
        else:
            message = ("SKIPPED recent/in-flight HP science run #"
                       + str(existing) + "; no redundant owner dispatch.")
        print(message)
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf8") as out:
                out.write(message + "\n")
        return
    result = process(event, repo, owner,
        lambda number: api(repo, token, "GET", "/pulls/" + str(number)),
        lambda name, ref: api(repo, token, "GET",
            "/actions/workflows/" + name + "/runs?" +
            urlencode({"branch": ref, "event": "workflow_dispatch", "per_page": 100})),
        lambda name, ref, inputs=None: api(repo, token, "POST",
            "/actions/workflows/" + name + "/dispatches",
            {"ref": ref, **({"inputs": inputs} if inputs is not None else {})}))
    if result is not None:
        number, workflow, sha, ref, existing_id = result
        qualifier = " (results_shard=earned)" if workflow == "modern-results-navigation-acceptance.yml" else ""
        if existing_id is None:
            message = ("Requested " + workflow + qualifier + " for PR #" + str(number) +
                       " at branch " + ref + " (expected source " + sha +
                       "). Dispatch only, NOT test qualification. Verify checkout SHA.")
        else:
            message = ("SKIPPED duplicate dispatch for PR #" + str(number) +
                       ": existing in-flight workflow " + workflow + qualifier +
                       " run #" + str(existing_id) + " already targets " + sha +
                       ". Verify that run; do not restart it.")
        print(message)
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf8") as out:
                out.write(message + "\n")


if __name__ == "__main__":
    main()

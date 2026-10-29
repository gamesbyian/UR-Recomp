#!/usr/bin/env python3
"""Dispatch only two existing manual CI workflows, via owner PR comments.

A successful dispatch is NOT a successful test: inspect the target run's
actual checkout SHA and full evidence before using it for PR qualification.
"""
import json
import os
import re
from pathlib import Path
from urllib.request import Request, urlopen

COMMAND = re.compile(r"/ur-ci run (tooling-unit-tests\.yml|ghost-target-native-acceptance\.yml) ([0-9a-f]{40})\Z")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,119}\Z")


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
    return number, match.group(1), match.group(2)


def exact_head(pr, number, repo, sha):
    if (not isinstance(pr, dict) or pr.get("number") != number
            or pr.get("state") != "open" or pr.get("draft") is not False
            or not isinstance(pr.get("head"), dict)):
        raise ValueError("PR is not open/ready with an actual head")
    head = pr["head"]
    origin, branch = head.get("repo"), head.get("ref")
    if (not isinstance(origin, dict) or origin.get("full_name") != repo
            or head.get("sha") != sha
            or not isinstance(branch, str) or not REF.fullmatch(branch)
            or branch == "main" or ".." in branch or "//" in branch
            or branch.endswith(("/", "."))):
        raise ValueError("Stale, forked or unsafe PR head: no dispatch")
    return branch


def process(event, repo, owner, get_pr, dispatch):
    request = intent(event, repo, owner)
    if request is None:
        return None
    number, workflow, sha = request
    ref = exact_head(get_pr(number), number, repo, sha)
    dispatch(workflow, ref)
    return (number, workflow, sha, ref)


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
    result = process(event, repo, owner,
        lambda number: api(repo, token, "GET", "/pulls/" + str(number)),
        lambda name, ref: api(repo, token, "POST",
            "/actions/workflows/" + name + "/dispatches", {"ref": ref}))
    if result is not None:
        number, workflow, sha, ref = result
        message = ("Requested " + workflow + " for PR #" + str(number) +
                   " at branch " + ref + " (expected source " + sha +
                   "). Dispatch only, NOT test qualification. Verify checkout SHA.")
        print(message)
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf8") as out:
                out.write(message + "\n")


if __name__ == "__main__":
    main()

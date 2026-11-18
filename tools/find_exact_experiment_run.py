#!/usr/bin/env python3
"""Find the exact push-triggered bounded experiment run, including runs omitted by commit lookups."""
import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API = "https://api.github.com/repos/gamesbyian/UR-Recomp/actions/runs"
WORKFLOW = "Agent bounded experiment execution"

def discover(sha, *, opener=urlopen, max_pages=30, per_page=100):
    if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha.lower()):
        raise ValueError("head_sha must be a complete 40-character hexadecimal commit SHA")
    if max_pages < 1:
        raise ValueError("max_pages must be positive")
    for page in range(1, max_pages + 1):
        url = f"{API}?per_page={per_page}&page={page}"
        req = Request(url, headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "ur-recomp-exact-experiment-run-discovery",
            "X-GitHub-Api-Version": "2022-11-28",
            **({"Authorization": "Bearer " + os.environ["GH_TOKEN"]} if os.environ.get("GH_TOKEN") else {}),
        })
        with opener(req, timeout=30) as response:
            data = json.load(response)
        runs = data.get("workflow_runs")
        if not isinstance(runs, list):
            raise ValueError(f"missing workflow_runs array on page {page}")
        for run in runs:
            if (run.get("head_sha") == sha and run.get("event") == "push"
                    and run.get("name") == WORKFLOW):
                return {"found": True, "run_id": run["id"], "head_sha": sha,
                        "event": run["event"], "workflow_name": run["name"],
                        "status": run.get("status"), "conclusion": run.get("conclusion"),
                        "html_url": run.get("html_url"), "page": page}
        if len(runs) < per_page:
            return {"found": False, "head_sha": sha, "pages_checked": page, "exhausted": True}
    return {"found": False, "head_sha": sha, "pages_checked": max_pages,
            "exhausted": False, "warning": "pagination limit reached; absence NOT established"}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("head_sha")
    p.add_argument("--max-pages", type=int, default=30)
    args = p.parse_args()
    try:
        result = discover(args.head_sha.lower(), max_pages=args.max_pages)
    except (HTTPError, URLError, ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc), "head_sha": args.head_sha}), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result["found"] else 1

if __name__ == "__main__":
    sys.exit(main())

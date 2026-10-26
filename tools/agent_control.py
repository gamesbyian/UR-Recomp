#!/usr/bin/env python3
"""Read-only control-plane projection for scheduled-agent dispatch and recovery.

GitHub's dispatch board remains the sole assignment writer. The curated Drive
registry is a disposition index, not evidence of GitHub/Drive live status, and
cannot grant release credit. No network access or third-party dependencies.
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "docs/HOURLY-AGENT-LINES.md"
REGISTRY = ROOT / "docs/recovery/agent-candidates.json"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
# Old immutable work IDs remain valid provenance. The current dispatch board
# may instead assign dated, multi-part integration-campaign identifiers.
WORK_ID = re.compile(r"UR-[A-Z0-9]+(?:-[A-Z0-9]+)*-(?:[0-9]{2}|20[0-9]{6})\Z")
# Known retired IDs from the 2026-10-21 ten-line dispatch board. A historical
# recovery receipt may continue to refer to one, but an active task cannot.
RETIRED_WORK_IDS = frozenset({
    "UR-CPU-01", "UR-QA01-01", "UR-WINSTORAGE-01", "UR-WINQA-01",
    "UR-PPU-01", "UR-UHD-01", "UR-RECORDS-01", "UR-P2P-01",
    "UR-INTEGRATION-01", "UR-KNOWLEDGE-01",
})
STATUSES = frozenset({
    "merged", "superseded", "rejected", "pending_review",
    "blocked", "research_only", "unknown",
})
FAILURE_CLASSES = frozenset({
    "none", "technical_retryable", "source_conflict",
    "tool_safety_block", "explicit_policy_denial", "unknown",
})
ACTIVE = frozenset({"pending_review"})
COMPLETED = frozenset({"merged", "superseded", "rejected"})


def _unique_pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate JSON key: " + key)
        out[key] = value
    return out


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"),
                      object_pairs_hook=_unique_pairs)


def extract_board(markdown):
    """Parse the five equal scheduled workers and the ranked shared work pool.

    The board specifies priorities, not permanent agent ownership. Reject old
    two-anchor board contracts rather than silently treating them as active.
    """
    agents, jobs = {}, {}
    for raw in markdown.splitlines():
        if not raw.startswith("|"):
            continue
        cells = [c.strip() for c in raw.strip().strip("|").split("|")]
        if len(cells) == 4 and re.fullmatch(r"\*\*Agent [1-5]\*\*", cells[0]):
            number = int(re.search(r"\d", cells[0]).group())
            m = re.fullmatch(r"\*\*:(\d{2})\*\*", cells[1])
            if number in agents or not m or int(m.group(1)) >= 60:
                raise ValueError("duplicate agent or invalid scheduled minute")
            if "Shared ranked pool" not in cells[2] or "inspect five jobs" not in cells[2]:
                raise ValueError("agent assigned a lane instead of shared five-job pool")
            agents[number] = {"number": number, "minute": int(m.group(1)),
                              "selection": "shared_pool_top_five",
                              "independence": cells[3]}
        elif len(cells) == 6 and re.fullmatch(r"\d{1,3}", cells[0]):
            rank = int(cells[0])
            if rank in jobs:
                raise ValueError("duplicate work rank")
            if not WORK_ID.fullmatch(cells[1]):
                raise ValueError("invalid work ID on rank " + str(rank))
            if cells[2] not in {"ready", "in_review", "hold", "deferred"}:
                raise ValueError("invalid work state on rank " + str(rank))
            if any(not value.strip() for value in cells[3:]):
                raise ValueError("work job missing actionable outcome, receipt, or stop rule")
            jobs[rank] = {"position": rank, "work_id": cells[1],
                          "state": cells[2], "objective": cells[3],
                          "receipt": cells[4], "acceptance": cells[5]}
    if len(agents) != 5 or set(agents) != set(range(1, 6)):
        raise ValueError("expected five scheduled agents")
    expected_minutes = {1: 0, 2: 12, 3: 24, 4: 36, 5: 48}
    for number, minute in expected_minutes.items():
        if agents[number]["minute"] != minute:
            raise ValueError("agent start minute differs from installed schedule: Agent " + str(number))
    if len(jobs) < 5 or set(jobs) != set(range(1, len(jobs) + 1)):
        raise ValueError("expected contiguous ranked shared jobs, at least five")
    if len({v["work_id"] for v in jobs.values()}) != len(jobs):
        raise ValueError("duplicate work ID")
    if sum(v["state"] in {"ready", "in_review"} for v in jobs.values()) < 5:
        raise ValueError("fewer than five selectable jobs")
    return {"schema": "ur-agent-control/2",
            "authority": "docs/HOURLY-AGENT-LINES.md",
            "selection": "ranked_shared_pool_top_five",
            "agents": [agents[n] for n in sorted(agents)],
            "work": [jobs[n] for n in sorted(jobs)]}


def validate_registry(registry, board):
    if type(registry) is not dict or registry.get("schema") != "ur-recovery-registry/1":
        raise ValueError("unknown recovery registry schema")
    if registry.get("scope") != "curated_not_exhaustive":
        raise ValueError("registry must advertise nonexhaustive scope")
    entries = registry.get("candidates")
    if type(entries) is not list:
        raise ValueError("candidates must be a list")
    work_ids = {entry["work_id"] for entry in board["work"]}
    ids, drive_ids, active_keys = set(), set(), set()
    for item in entries:
        if type(item) is not dict:
            raise ValueError("candidate must be an object")
        required = ("candidate_id", "work_id", "discriminator", "state", "drive_id",
                    "failure_class", "next_action", "release_gate_credit")
        if any(key not in item for key in required):
            raise ValueError("candidate missing mandatory fields")
        cid, wid = item["candidate_id"], item["work_id"]
        if (type(cid) is not str or not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,95}", cid)
                or cid in ids):
            raise ValueError("invalid or duplicate candidate_id")
        ids.add(cid)
        if wid not in work_ids and wid not in RETIRED_WORK_IDS:
            raise ValueError("orphan work ID for " + cid)
        if type(item["discriminator"]) is not str or not item["discriminator"].strip():
            raise ValueError("missing discriminator")
        if item["state"] not in STATUSES:
            raise ValueError("invalid candidate state")
        if wid in RETIRED_WORK_IDS and item["state"] in ACTIVE:
            raise ValueError("retired work ID cannot accept new active recovery: " + cid)
        if item["failure_class"] not in FAILURE_CLASSES:
            raise ValueError("invalid failure class")
        if item["release_gate_credit"] is not False:
            raise ValueError("recovery cannot award a release gate")
        if type(item["next_action"]) is not str or not item["next_action"].strip():
            raise ValueError("missing next action")
        did = item["drive_id"]
        if type(did) is not str or not re.fullmatch(r"[A-Za-z0-9_-]{15,}", did):
            raise ValueError("invalid Drive ID")
        if did in drive_ids:
            raise ValueError("same Drive item appears as two recovery candidates")
        drive_ids.add(did)
        digest = item.get("archive_sha256")
        if digest is not None and (type(digest) is not str or not HEX64.fullmatch(digest)):
            raise ValueError("invalid archive sha256")
        pr, merge = item.get("github_pr"), item.get("merge_sha")
        if item["state"] == "merged":
            if type(pr) is not int or pr <= 0 or not isinstance(merge, str) or not HEX40.fullmatch(merge):
                raise ValueError("merged disposition needs PR and exact commit SHA")
        elif merge is not None:
            raise ValueError("unmerged candidate cannot claim a merge SHA")
        if item["state"] == "blocked" and item["failure_class"] == "none":
            raise ValueError("blocked candidate needs a failure classification")
        if item["failure_class"] in {"tool_safety_block", "explicit_policy_denial"} and item["state"] in ACTIVE:
            raise ValueError("denied operation is not an actionable retry")
        if item["state"] in ACTIVE:
            key = (wid, item["discriminator"])
            if key in active_keys:
                raise ValueError("duplicate active candidate for one discriminator")
            active_keys.add(key)
    return {"candidates": len(entries), "states": dict(Counter(x["state"] for x in entries))}


def summary(board, registry):
    counts = Counter(x["state"] for x in registry["candidates"])
    lines = [
        "# UR-Recomp agent control / recovery (offline snapshot)",
        "",
        f"**Dispatch:** {len(board['agents'])} interchangeable hourly agents, "
        f"{len(board['work'])} shared jobs, five candidates considered per run.",
        "**Recovery:** curated historical dispositions, not a live Drive or GitHub API scan.",
        "**Release:** only docs/RELEASE-QUALITY-LEDGER.json can establish QA gates.",
        "",
        "| Agent / start minute | Selection |",
        "| --- | --- |",
    ]
    for agent in board["agents"]:
        lines.append(f"| {agent['number']} / :{agent['minute']:02d} | Shared ranked pool (five-candidate scan) |")
    lines.extend(["", "| Rank | Work ID | State |",
                  "| --- | --- | --- |"])
    for job in board["work"]:
        lines.append(f"| {job['position']} | {job['work_id']} | {job['state']} |")
    lines.extend(["", "**Recovery index:** " +
                  ", ".join(f"{counts[k]} {k.replace('_', ' ')}" for k in sorted(counts)) +
                  f" ({len(registry['candidates'])} indexed).", ""])
    for entry in registry["candidates"]:
        if entry["state"] not in COMPLETED:
            lines.append(f"- **{entry['work_id']} / {entry['candidate_id']}**: "
                         f"{entry['state'].replace('_', ' ')}; {entry['next_action']}")
    lines.extend(["", "Next: verify current PR heads and Drive item identities before action.",
                  "No blocked write may be retried or rerouted to evade a safety/policy restriction."])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", type=Path, default=BOARD)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--agent", type=int, choices=range(1, 6),
                        help="show shared top-five candidate jobs for the specified agent")
    parser.add_argument("--check", action="store_true", help="validate without displaying report")
    args = parser.parse_args()
    board = extract_board(args.board.read_text(encoding="utf-8"))
    registry = load_json(args.registry)
    checked = validate_registry(registry, board)
    if args.check:
        print(f"OK: {len(board['agents'])} agents, {len(board['work'])} shared jobs, "
              f"{checked['candidates']} curated recovery candidates")
    elif args.agent is not None:
        selected = board["agents"][args.agent - 1]
        selected["candidate_jobs"] = [job for job in board["work"] if job["state"] in {"ready", "in_review"}][:5]
        print(json.dumps(selected, indent=2, ensure_ascii=False))
    elif args.format == "json":
        print(json.dumps({"board": board, "registry": registry, "validation": checked},
                         indent=2, ensure_ascii=False))
    else:
        print(summary(board, registry), end="")


if __name__ == "__main__":
    main()

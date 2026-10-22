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
    """Parse only the current two named tables, never historical prose."""
    agents, lines = {}, {}
    for raw in markdown.splitlines():
        if not raw.startswith("|"):
            continue
        cells = [c.strip() for c in raw.strip().strip("|").split("|")]
        if len(cells) != 4 and len(cells) != 5:
            continue
        if len(cells) == 4 and re.fullmatch(r"\*\*Agent [1-5]\*\*", cells[0]):
            number = int(re.search(r"\d", cells[0]).group())
            m = re.fullmatch(r"\*\*:(\d{2})\*\*", cells[1])
            if not m or int(m.group(1)) >= 60:
                raise ValueError("invalid agent minute")
            pieces = re.split(r"\s+\+\s+", cells[2].replace("**", ""))
            anchors = []
            for piece in pieces:
                match = re.match(r"^(\d+)\s+\S", piece)
                if not match:
                    raise ValueError("invalid anchor: " + piece)
                anchors.append(int(match.group(1)))
            if number in agents or len(anchors) != 2 or anchors[0] == anchors[1]:
                raise ValueError("duplicate or invalid agent anchors")
            agents[number] = {"number": number, "minute": int(m.group(1)),
                              "anchors": anchors,
                              "independence": cells[3]}
        elif len(cells) == 5 and re.fullmatch(r"\d{1,2}", cells[0]) and WORK_ID.fullmatch(cells[1]):
            number = int(cells[0])
            if number in lines:
                raise ValueError("duplicate work line " + str(number))
            shards = {}
            for part in re.split(r";\s*(?=\d{1,2}[abc]:)", cells[3]):
                match = re.fullmatch(r"(\d{1,2})([abc]):\s*(.+)", part)
                if not match or int(match.group(1)) != number:
                    raise ValueError("malformed shard " + part)
                if match.group(2) in shards:
                    raise ValueError("duplicate shard " + part)
                shards[match.group(2)] = match.group(3)
            if set(shards) != {"a", "b", "c"}:
                raise ValueError("expected a/b/c shards on line " + str(number))
            lines[number] = {"position": number, "work_id": cells[1],
                             "objective": cells[2], "shards": shards,
                             "ownership": cells[4]}
    if set(lines) != set(range(1, 11)) or len({v["work_id"] for v in lines.values()}) != 10:
        raise ValueError("expected ten unique active work lines")
    if set(agents) != set(range(1, 6)):
        raise ValueError("expected five scheduled agents")
    anchors = [n for v in agents.values() for n in v["anchors"]]
    if sorted(anchors) != list(range(1, 11)):
        raise ValueError("each work line must have exactly one scheduled anchor")
    if len({v["minute"] for v in agents.values()}) != 5:
        raise ValueError("scheduled start minutes must be distinct")
    expected_minutes = {1: 0, 2: 12, 3: 24, 4: 36, 5: 48}
    for agent_id, minute in expected_minutes.items():
        if agents[agent_id]["minute"] != minute:
            raise ValueError("agent start minute differs from installed schedule: Agent " + str(agent_id))
    for item in agents.values():
        item["work_ids"] = [lines[n]["work_id"] for n in item["anchors"]]
    return {"schema": "ur-agent-control/1",
            "authority": "docs/HOURLY-AGENT-LINES.md",
            "agents": [agents[n] for n in sorted(agents)],
            "work": [lines[n] for n in sorted(lines)]}


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
        "**Assignments:** 5 schedules, 10 work IDs; source is the live Markdown board.",
        "**Recovery:** curated historical dispositions, not a live Drive or GitHub API scan.",
        "**Release:** only docs/RELEASE-QUALITY-LEDGER.json can establish QA gates.",
        "",
        "| Agent / start minute | Primary / fallback |",
        "| --- | --- |",
    ]
    for agent in board["agents"]:
        lines.append(f"| {agent['number']} / :{agent['minute']:02d} | "
                     f"{' → '.join(agent['work_ids'])} |")
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
                        help="show one hourly agent's primary and fallback work")
    parser.add_argument("--check", action="store_true", help="validate without displaying report")
    args = parser.parse_args()
    board = extract_board(args.board.read_text(encoding="utf-8"))
    registry = load_json(args.registry)
    checked = validate_registry(registry, board)
    if args.check:
        print(f"OK: {len(board['agents'])} agents, {len(board['work'])} lines, "
              f"{checked['candidates']} curated recovery candidates")
    elif args.agent is not None:
        selected = board["agents"][args.agent - 1]
        selected["owned_lines"] = [board["work"][n - 1] for n in selected["anchors"]]
        print(json.dumps(selected, indent=2, ensure_ascii=False))
    elif args.format == "json":
        print(json.dumps({"board": board, "registry": registry, "validation": checked},
                         indent=2, ensure_ascii=False))
    else:
        print(summary(board, registry), end="")


if __name__ == "__main__":
    main()

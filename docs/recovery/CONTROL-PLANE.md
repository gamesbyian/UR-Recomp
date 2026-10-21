# Five-agent control and recoverability

This is an **incremental, fail-closed operational control**. It does not change the five schedules, their permissions, GitHub PR boundaries, the authoritative QA ledger, or the Media/Modern work owners. [The live ten-line board](../HOURLY-AGENT-LINES.md) remains the *single dispatch authority* while Agent 4 owns shared assignment edits. The new tool reads that board; it does not create a second hand-edited assignment list.

## Use on a checked-out repository

```sh
python3 tools/agent_control.py --check
python3 tools/agent_control.py --agent 4
python3 tools/agent_control.py                 # bounded phone-readable Markdown
python3 tools/agent_control.py --format json   # machine-readable ten-line dispatch + recovery
python3 -m unittest tests.unit.test_agent_control
```

The parser validates exactly **five distinct scheduled agents, two nonoverlapping anchors per agent, exactly ten uniquely assigned work IDs and all three ordered shards per line**. The JSON output is generated directly from the board, so it cannot drift as a competing manual control file. Scheduled prompts may read the projection for fast orientation but must still refresh the actual board, work queue, PRs, current HEAD, and specialist authority before any write.

## Recovery reconciliation

[agent-candidates.json](agent-candidates.json) is a **curated, nonexhaustive historical source-candidate index**, keyed by stable candidate ID, original Drive item ID, work ID and discriminator. Agent 4 or a specifically delegated reviewer may add facts only after verifying the original archive identity and live PR/source state. Existing evidence archives and work-ID Drive journals are preserved unchanged.

Disposition states are `pending_review`, `blocked`, `research_only`, `merged`, `superseded`, `rejected`, and `unknown`. A disposition requires an explicit next action. A merged record must name an actual PR and 40-character merge commit; an archive SHA-256 may be included only when independently observed. Duplicate live candidates for the same work ID **and discriminator** are rejected, as are repeated Drive IDs, invalid relationships and any attempt to grant release gate credit from recovery metadata.

**A blocked tool-safety or explicit policy write is NOT a pending retry.** Preserve its exact error, never repeat/disguise/reroute the denied operation, and seek independent authorized review. Actual technical timeouts, API 429/5xx, stale blob and policy denials must not be conflated. The board's legacy phrase “temporary transport/provider safety rejection” conflicts with this rule and should be removed by the single shared-board owner when integrating this PR. Ordinary code and test review of a distinct independently justified change remains permissible, never as a disguised retry.

A Drive candidate becomes source-integrated only after exact source/patch comparison, required tests and an independently qualified PR merger. Any registry entry is **a recorded claim**, not a live GitHub API attestation. Update the entry after actually inspecting the PR and Drive record; do not convert merged source into original/native event, real Windows hardware, HD art, or physical acceptance.

## Cheap CI and status viewing

The `Agent control and recovery contract` PR check runs only when the board, recovery index, or its own workflow changes. Existing tooling-unit-test CI exercises the Python code when code/tests change. Both are read-only; neither modifies main, approves PRs, accesses Drive, grants QA credit, or restarts a denied request. Workflow Job Summary prints a bounded offline status snapshot.

**Dashboard distinction:** the generated Markdown lists schedules and curated recovery dispositions. It deliberately does **not** claim to be a real-time GitHub PR status monitor, exhaustive Drive intake count, stalled-agent detector, or actual release readiness score. Those require live connector reconciliation and must show a fetch timestamp and explicit UNKNOWN on API errors. When the status view is next extended, derive PR/CI data from live GitHub and Drive and gate results exclusively from `docs/RELEASE-QUALITY-LEDGER.json`.

## Next integration steps without adding agents

1. Agent 4 reconciles the machine-readable projection against any post-PR board changes, then adopts the contract and settles the legacy retry-language contradiction.
2. One candidate per independently discriminating deliverable. Before a new recovery ZIP, search current main/PR source bytes and the exact Drive-ID index, then update/supersede the existing case. Never discard unique archived evidence automatically.
3. Use existing independent reviewers for exact-source PR admission, preserving producer-versus-QA separation and configured branch protection. No extra scheduled agent or subscription is required.
4. Add an *opt-in* live GitHub/Drive snapshot later only when the required trusted API fetches are available. Prefer a small exception report during Agent 4's existing slot over a sixth recurring schedule.
5. A restorable GitHub history backup into restricted Drive remains a separate verified operation. A GitHub ZIP/source snapshot alone does not back up history, PRs or issues; no such backup is claimed here.

The initial seed reflects the recovery index as inspected on 2026-10-21; the Drive vault root was observed to contain only its six named subfolders, while substantive candidate archives remain in Incoming/Integrated. This document deliberately does not infer that removal of legacy root files removed every previously inventoried unique source or evidence dependency.

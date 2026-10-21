# Scheduled agent coordination and recovery protocol

This is the authoritative protocol for all five hourly agents and manually launched integrators. The live ten-position dispatch board is `docs/HOURLY-AGENT-LINES.md`. Position numbers are **mutable slots**, not domain identities. Every scheduled prompt must resolve anchor positions from the board's *current agent table*, then three rotating support positions using its current formula. Ignore historical topic names and assignments in prior handoffs. Assign each active objective a stable work ID, independent of its board position, and preserve its journal when moved.

## Recovery vault

Root: https://drive.google.com/drive/folders/1AAZyC49ZXFY81GB0hI31CAJnUd6iKcTn
- Integration inbox: https://drive.google.com/drive/folders/1iq2MP6yzsMK6f-0VIhIUL43IfIL6GT3o
- Work journals: https://drive.google.com/drive/folders/1QvlB3V-aa8so0HPx_1dTcV8jL9TeD3kr
- Incoming: https://drive.google.com/drive/folders/1cdovDqle9IRYKX2lCt513mtWge75HywX
- Evidence library: https://drive.google.com/drive/folders/1t0J4GT0N9PQEJkf2TqDt1P6lbYlLArx2
- Integrated receipts: https://drive.google.com/drive/folders/1deqU6Z6IdeudIVvfCmXggW8gV3JRGqsU
- Superseded/rejected: https://drive.google.com/drive/folders/1XuTGwAE7zsMhw20mvSPm3WYX94PiNxhY

**Legacy archive safety:** Existing root files remain in place; they are an immutable legacy archive. Never bulk-move, overwrite, delete, or classify historical files merely by filename. Do not infer that inbox contents are already validated. Never treat a Drive proposal as permission to override independent QA, source provenance, art veto, or release gates.

## Mandatory preflight before new research

1. Fetch fresh GitHub main board, WORK-QUEUE, agent journals, current source/blob SHAs, relevant recent/open/merged/closed PRs, and issue comments.
2. List the Vault root **and** the inbox, incoming, journals, integration receipts and recent evidence folders. Read new submissions and recent relevant material for **all five resolved assignments**; compare with the prior checkpoint and candidate identities, not just filenames.
3. Reconcile every intended deliverable with both GitHub HEAD/PRs and Drive packages. Classify existing work as pending, in-review, merged, superseded, rejected, blocked, or unknown. Read dependencies, provenance, test results and actual remaining gaps.
4. Record a preflight receipt containing UTC timestamp, main SHA, board SHA, work IDs/positions, folder inventory watermark, relevant Drive file IDs, PR/head SHAs, duplicates/supersessions and selected next actions. If a source cannot be accessed, say what was inaccessible; do not certify the preflight or assume absence.
5. Prioritize qualified pending integration/extension and exact new discriminating tests. Five assigned lines require meaningful review and honest outcomes, **not** five invented new patches. Avoid rerunning inherited suites unless necessary for validation; distinguish new tests from inherited tests.

## Candidate package schema (one independent deliverable per candidate)

Use a stable `candidate_id`, `work_id`, `board_position_at_submission`, `agent_id`, `timestamp_utc`, `title`, `status`, `relationship` (new/extends/supersedes/duplicate), `related_candidate_ids`, `source_main_sha`, `source_blob_shas`, `target_paths`, `patch_drive_id`, `bundle_drive_id`, `tests` (commands and observed results), `evidence_drive_ids`, `relevant_prs`, `dependencies`, `limitations`, `next_action`, `release_credit=false`. Never assert a completed test or a merge without verifying it.

Preserve an immutable complete archive in Incoming or Evidence; submit current independently actionable patch+manifest to Integration Inbox only after reviewing duplicates and identifying the latest compatible source. Avoid growing competing cumulative proposals: designate a superseding candidate and retain prior versions as evidence. If upload of structured raw files is unsupported, use native Docs with the full payload or link an already saved root artifact; do not claim a nonexistent upload. Verify Drive readback.

## Continuity and ownership

Maintain one **work-ID journal** (stable across position changes) with established results, rejected hypotheses, source-bound references, pending candidates, next discriminating step and last reconciliation. Maintain one short **agent continuation record** per hourly agent, listing active candidate IDs and unpublished state. Prefer append-only immutable run receipts if concurrent writers cannot safely update a shared document. Agent 4 is the *Drive triage coordinator* for inbox dedup/indexing, but is not authorized to award independent QA or resolve GitHub write denials; other agents may submit independent candidate manifests. A task claim is advisory, scoped to a deliverable, and expires after the next missed scheduled checkpoint; it never blocks independent QA or recovery.

## Manual integration

Manual integrators must reconcile the inbox with GitHub at the start and before **each** publication. Order qualified independent packages by priority and dependency; verify source exactness and tests, create narrow PRs, respect checks and approval. Write resolution receipt with candidate ID, actual PR/commit/head, status and rationale in Integrated or Superseded/Rejected. Update journals/index where safe. Do not bulk-apply unreviewed recovery archives.

## Failure and publication rules

Refresh exact HEAD immediately before a write. Never bypass or retry an explicit safety/policy denial. On blocked GitHub publication, preserve full source/patch, evidence, SHA, tests and exact error in Drive; continue other worthwhile work. On transient errors retry only if genuinely permitted and elapsed time is measurable. If Drive also fails, preserve the content in the session artifact and report failure. No fake commits, CI, devices, source parity, approval or release credit.

# Scheduled agent coordination and recovery protocol

This is the workflow protocol for all five hourly agents and manually launched integrators. **Assignment content and ordered a/b/c work shards exist only in `docs/HOURLY-AGENT-LINES.md`**; do not duplicate topical priorities or stable work IDs in scheduled prompts. The live ten-position dispatch board is `docs/HOURLY-AGENT-LINES.md`. Position numbers are **mutable slots**, not domain identities. Every scheduled prompt resolves anchors from the board's *current agent table*. While closure-first mode is active, work one primary anchored deliverable to disposition and choose another anchor only if justified; historical three-support rotation is read-only awareness, never an extra publication quota. This overrides older five-line requirements but does not change hourly starting times. Ignore historical topic names and assignments in prior handoffs. Assign each active objective a stable work ID, independent of its board position, and preserve its journal when moved.

## Execution modes: manual GitHub-first vs scheduled recovery

**Manually dispatched agents (including visual, product, QA and manual integrators) use GitHub as the sole routine progress, status and handoff authority.** Work in dedicated branches/PRs; write updates, logs, tests, screenshots, decisions and next actions to the PR, issues or repository docs. Read the Drive Vault at startup *only to locate relevant unresolved research and avoid duplication*. Do **not** create routine Drive journals, progress summaries, integration receipts, candidate manifests or redundant mirrors of GitHub changes. A manual agent may write to Drive only when GitHub publication is genuinely impossible and substantive unpublished bytes/evidence would otherwise be lost, or when the owner explicitly requests a Drive artifact. Such an exception must include exact failed write, source identity, artifact, readback and intended later GitHub recovery. When GitHub is restored, reconcile and retire the exception without deleting evidence. In particular, **a successful GitHub PR/commit is already the handoff**; no Drive report is needed.

**Scheduled hourly agents** use Drive recovery workflows where GitHub source publication is unavailable. Their immutable recovery proposals and continuity data are for the manual integrator to consume, not a reporting obligation imposed on manual agents. Both modes read the relevant GitHub/Drive history before duplicating work, but only the recovery-blocked mode routinely writes to Drive.

## Recovery vault

Root: https://drive.google.com/drive/folders/1AAZyC49ZXFY81GB0hI31CAJnUd6iKcTn
- Integration inbox: https://drive.google.com/drive/folders/1iq2MP6yzsMK6f-0VIhIUL43IfIL6GT3o
- Work journals: https://drive.google.com/drive/folders/1QvlB3V-aa8so0HPx_1dTcV8jL9TeD3kr
- Incoming: https://drive.google.com/drive/folders/1cdovDqle9IRYKX2lCt513mtWge75HywX
- Evidence library: https://drive.google.com/drive/folders/1t0J4GT0N9PQEJkf2TqDt1P6lbYlLArx2
- Integrated receipts: https://drive.google.com/drive/folders/1deqU6Z6IdeudIVvfCmXggW8gV3JRGqsU
- Superseded/rejected: https://drive.google.com/drive/folders/1XuTGwAE7zsMhw20mvSPm3WYX94PiNxhY

**Legacy archive safety:** The live Vault root currently *lists* only its six folders, but historic root artifacts are **not all confirmed present in those folders**. The historical 393-ID census overlaps the 90 current direct-child file IDs by only six, while some unlisted legacy IDs still resolve through exact-ID metadata/read. Their Drive retention/trash status is **UNKNOWN**, not independently certified deleted or integrated. See the dated warning in [the recovery entrypoint](recovery/README.md). Never bulk-restore, bulk-move, overwrite, delete, or classify historical files merely by filename, listing absence or an old parent ID. Do not infer that inbox contents are already validated. Never treat a Drive proposal as permission to override independent QA, source provenance, art veto, or release gates.

## Mandatory preflight before new research

1. Fetch fresh GitHub main board, WORK-QUEUE, agent journals, current source/blob SHAs, relevant recent/open/merged/closed PRs, and issue comments.
2. List the Vault root **and** the inbox, incoming, journals, integration receipts and recent evidence folders. Read new submissions for the primary deliverable and direct dependencies; scan the full Inbox for conflicting/duplicate ownership without deeply reading unrelated support-line archives. Compare candidate IDs and source hashes, not merely filenames.
3. Reconcile every intended deliverable with both GitHub HEAD/PRs and Drive packages. Classify existing work as pending, in-review, merged, superseded, rejected, blocked, or unknown. Read dependencies, provenance, test results and actual remaining gaps.
4. Record a preflight receipt containing UTC timestamp, main SHA, board SHA, work IDs/positions, folder inventory watermark, relevant Drive file IDs, PR/head SHAs, duplicates/supersessions and selected next actions. If a source cannot be accessed, say what was inaccessible; do not certify the preflight or assume absence.
5. Prioritize qualified pending integration/extension and exact new discriminating tests. One primary deliverable requires a meaningful closure attempt and honest outcome, **not** five new patches, PRs or handoff archives. Avoid rerunning inherited suites unless necessary for validation; distinguish new tests from inherited tests.

## Candidate package schema (scheduled/recovery-blocked submissions only)

Use a stable `candidate_id`, `work_id`, `board_position_at_submission`, `agent_id`, `timestamp_utc`, `title`, `status`, `relationship` (new/extends/supersedes/duplicate), `related_candidate_ids`, `source_main_sha`, `source_blob_shas`, `target_paths`, `patch_drive_id`, `bundle_drive_id`, `tests` (commands and observed results), `evidence_drive_ids`, `relevant_prs`, `dependencies`, `limitations`, `next_action`, `release_credit=false`. Never assert a completed test or a merge without verifying it.

Preserve an immutable complete archive in Incoming or Evidence; submit current independently actionable patch+manifest to Integration Inbox only after reviewing duplicates and identifying the latest compatible source. Avoid growing competing cumulative proposals: designate a superseding candidate and retain prior versions as evidence. If upload of structured raw files is unsupported, use native Docs with the full payload or link an already saved root artifact; do not claim a nonexistent upload. Verify Drive readback.

## Continuity and ownership

For scheduled/recovery-blocked agents, maintain one **work-ID journal** (stable across position changes) with established results, rejected hypotheses, source-bound references, pending candidates, next discriminating step and last reconciliation. Maintain one short **agent continuation record** per hourly agent, listing active candidate IDs and unpublished state. Prefer append-only immutable run receipts if concurrent writers cannot safely update a shared document. Agent 4 is the *Drive triage coordinator* for inbox dedup/indexing, but is not authorized to award independent QA or resolve GitHub write denials; other agents may submit independent candidate manifests. A task claim is advisory, scoped to a deliverable, and expires after the next missed scheduled checkpoint; it never blocks independent QA or recovery.

## Manual integration

Manual integrators must reconcile the inbox with GitHub at the start and before **each** publication. They write normal resolutions and handoffs to GitHub PRs/issues or versioned recovery index docs, **not** to Drive. Order qualified independent packages by priority and dependency; verify source exactness and tests, create narrow PRs, respect checks and approval. Record resolution with candidate ID, actual PR/commit/head, status and rationale in GitHub. A Drive receipt is optional only when a specifically pending Drive-only recovery requires a disposition that scheduled agents cannot otherwise discover from the GitHub index. Update the GitHub journals/index where safe. Do not bulk-apply unreviewed recovery archives.

**Operational GitHub-first runbook:** [docs/recovery/GITHUB-FIRST-PUBLICATION-RUNBOOK.md](recovery/GITHUB-FIRST-PUBLICATION-RUNBOOK.md). All agents must attempt normal GitHub publication of independently qualified changes before fallback. Do not turn a single invocation-level tool safety check into a permanent judgment about source content. Use bounded retries for transport/API failures, preserve blocked work losslessly, and reconsider it on future runs without circumventing explicit restrictions.

## Failure and publication rules

Refresh exact HEAD immediately before a write. **Classify the actual failure, not an agent's historical shorthand.** Retriable transport timeout, rate limit, expired token, GitHub 5xx, conflict/stale blob or service instability: preserve exact response and source SHA, refetch HEAD, back off appropriately, and retry a bounded number of times in the same run if execution permits. Continue other meaningful work between attempts. On the next scheduled/manual integration, revisit every unresolved technical failure; do not let a stale historic HOLD prevent an independent comparison against already merged code. If the original error is unavailable, label it UNKNOWN and seek the original receipt before claiming it was a safety denial or safe to resubmit.

**An explicit safety/policy denial is not a transient transport failure and must not be retried, reworded, repackaged or rerouted to evade the restriction.** Preserve the exact error and applicable artifacts; seek an appropriate authorized review rather than repeating the denied operation. Distinguish that from an unrelated, independently justified code change, which needs normal source/approval review and must not be a disguised retry.

On blocked GitHub publication preserve unpublished substantive patch/source, evidence, SHA, tests and exact error in Drive only as needed to avoid loss. If Drive also fails preserve the session artifact and report failure. Never invent elapsed wait time, attempts, commits, CI, devices, source parity, approval or release credit.

### Failure triage ledger (mandatory for historical recovery)
For each unresolved historical write attempt record: stable work ID; Drive evidence URL; exact operation and path/PR; original response verbatim where available; failure classification `technical-retryable | source-conflict | explicit-safety-denial | unknown | resolved-in-main`; source and current-main SHAs; whether a later PR already incorporated the intended change; retry count and timestamp; next authorized action. Revisit technical/unknown rows on subsequent passes by examining evidence, not by blindly resubmitting. Never allow the mere word `denied` in a progress summary to substitute for the original response.

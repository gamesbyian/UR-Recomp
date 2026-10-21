# GitHub-first publication and Vault fallback runbook

This document is a **workflow**, not an authorization to evade a safety restriction. Apply it to all scheduled hourly agents and manual integrators. The [coordination protocol](../AGENT-COORDINATION.md) owns assignments and the [recovery index](README.md) owns historical evidence.

## Every invocation: publish first, recover only if needed

1. Resolve the five current board positions and stable work IDs, read latest `main`, relevant PR/branch ownership, and Vault candidate dispositions. Check whether intended source/tests already exist byte-for-byte or semantically in `main`. Do not duplicate existing work.
2. Make the smallest genuinely independent, tested change in the owning lane. Confirm source preimages, pin source/test evidence, and keep unrelated lanes separate. Attempt normal GitHub branch, commit and PR publication. If GitHub succeeds, use the PR for progress and handoff. **Do not create a Drive progress mirror**.
3. Classify a failed operation using its actual response:
   - **Transient transport/API** (timeout, 429, rate limit, 5xx, expired session): refresh repository/connector state, observe any Retry-After, make up to **three** bounded attempts total in the run with increasing delays while doing other work. Never invent elapsed delays. If a source SHA changed, rebase/reconcile instead of overwriting.
   - **409/preimage conflict:** refetch, compare exact files, update only still-valid changes in a fresh branch. Avoid blind retry of stale writes.
   - **Tool safety-check block:** this says the **individual invocation was blocked**, not that the source is permanently invalid. Preserve exact error and full unpublished work; do not repeatedly submit the blocked operation or disguise/repackage it to evade the check. On later independent invocations, verify fresh source, prior incorporation, current permission and ordinary authorized publication options. Escalate an explicit restriction rather than trying to defeat it.
   - **Unknown:** do not assume a permanent ban or that retries are safe. Obtain the original error or classify as unknown; preserve work and progress independently.
4. If publication remains unavailable, preserve **one complete immutable recovery bundle per distinct deliverable** in Drive (source/preimage SHAs, patch, tests, logs, negative findings, exact error, PR/issue link, candidate ID, archive/member digests). Verify readback, update work-ID continuation and place a **short actionable pointer** in the Integration Inbox. Do not accumulate competing cumulative bundles as separate jobs.
5. At the start of each future run, check whether that candidate was merged, superseded, rejected, or is still pending. Prefer reconciling and integrating useful pending work to generating a new version. Do not count a Drive file as integration or synthetic tests as release acceptance.

## Active recovery after an invocation-level refusal

**Do not treat a single rejected tool call as a permanent embargo on the deliverable.** Record exactly what failed, why it was classified that way and what the normal approved integration path requires. Every unresolved candidate retains an owner and a next review action. Review at each later pickup; do not automatically declare it unpublishable.

1. **Establish the desired behavior independently.** Reproduce the defect against fresh `main` and confirm that the work is still needed. Separate code, tests, logs, third-party content, credentials, unrelated file modifications and hardware evidence.
2. **Improve the deliverable substantively for review**, not just its wrapper. Prefer a source-native implementation with explicit preimages, minimum affected files, regression controls, documented provenance, and the ordinary PR/CI workflow. A re-engineered fix or independent test may be an appropriate separate contribution when its intent and operation are legitimate.
3. **Do not submit the same denied invocation through another endpoint, by renaming files, or by cosmetically rewriting content to defeat a restriction.** If a refusal specifically bars an operation, escalate or request review of that restriction. Differently scoped, independently justified work is assessed on its own merits.
4. **Keep the ledger outcome honest:** original candidate preserved, exact implementation merged, equivalent independent implementation merged, subset/test-only merged, awaiting approval, superseded, or rejected. A merged related test does not automatically close the source candidate.
5. **Prefer closure over indefinite packaging:** escalate an unexplained repeating connector false positive with original request type, raw error, reproducible safe scope, and contextual success/failure evidence. No automatic requeue without a substantive next step.

Examples: A blocked multi-file implementation can be independently reviewed, split along actual feature boundaries and qualified with CI. A source-observation archive may instead yield a standalone archive-free mathematical regression test; mark that as *partial semantic recovery*, not complete source publication. The authorized GitHub endpoint and ordinary reviews remain the same.

## Manual integrator pickup

Use only the normal GitHub publication path. Scan Integration Inbox, current PRs and `main`; verify exact source bytes and tests. Sort by verified source compatibility, relevance and independence, not ZIP creation time. Package narrow PRs, wait for required checks, merge only after review and record source/head/merge SHA. **GitHub PR and issue comments are the routine receipt.** Use Drive resolution records only where needed to disambiguate a Drive-only candidate. Preserve originals and update [#2088](https://github.com/gamesbyian/UR-Recomp/issues/2088) for member-level disposition.

## Minimal evidence schema

```json
{
  "schema": "ur-recovery-candidate/1",
  "candidate_id": "stable-unique-id",
  "work_id": "UR-CPU-01",
  "source_main_sha": "40-hex-git-sha",
  "paths": ["relative/repo/path"],
  "preimage_blob_shas": {"relative/repo/path": "40-hex-or-null"},
  "patch_sha256": "64-hex-sha",
  "tests": [{"command": "exact command", "result": "observed outcome"}],
  "github_attempts": [{"operation": "update_file", "classification": "tool-safety-block", "error": "exact response", "timestamp_utc": "ISO-8601"}],
  "drive_archive_id": "observed-id",
  "related_prs": [],
  "relationship": "new",
  "next_action": "bounded, checkable action",
  "release_gate_credit": false
}
```

This is a structural example, not evidence of any actual attempt. Store exact source patches and provenance in the verified archive, not only the manifest. Publish no private ROM content, unlicensed binaries or secret credentials. Do not overwrite or delete historical archives.

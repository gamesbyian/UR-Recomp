# Vault actionable review: runbook

**Current agent assignment:** Any of the five interchangeable scheduled agents may select this recovery job from the [shared priority board](../HOURLY-AGENT-LINES.md). Semantic classification, first-party source implementation and independent merge review are distinct tasks/roles **for a particular candidate**, not permanent Agent 1/2/3/5 lanes. Coordinate in [#2468](https://github.com/gamesbyian/UR-Recomp/issues/2468), and retain authoritative human findings in [#2088](https://github.com/gamesbyian/UR-Recomp/issues/2088).

## The read-only workflow

[Vault Actionable Review](../../.github/workflows/vault-actionable-review.yml) is automatically triggered when [Vault Recurring Intake](RECURRING-VAULT-INTAKE.md) completes on main. It also supports manual dispatch. Pull requests run only isolated tests, not another live Drive ingestion.

It downloads checkpoint.json, queue.json and report.json for **both** per-folder scopes, using the most recent complete artifact from main even after a partially failed run. A missing artifact, inconsistent checkpoint or unavailable GitHub PR snapshot fails closed. It uses the existing [historical candidate register](agent-candidates.json) for context and [member disposition ledger](vault-member-dispositions.json) for independently reviewed candidate-specific decisions.

It uploads a bounded actionable.md summary and complete metadata-only actionable.json. These provide archive/member SHA-256, stable member candidate ID, shared-pool owner hint, disposition, Drive source link, links to open PRs and outstanding intake exceptions. The machine-readable `owner: shared_ranked_pool` is a routing hint, not a reservation or specialist assignment; candidate state and the live board control selection. Every succeeding run recomputes the same identities from retained checkpoint fingerprints. Hash-identical members from different archives share one engineering triage lead while **retaining all original Drive IDs**.

A fresh SHA mismatch proves only byte inequality. It is not proof of missing behavior, rights, publication authorization or semantic novelty. A legacy archive-level merged record never automatically marks a newly surfaced nested member integrated.

## Member ledger: independently qualified classification

The ledger uses schema ur-vault-member-dispositions/1 and an items array. Each record names the exact candidate_id (vm1- plus 24 lowercase SHA-derived hex digits) published in actionable.json, with one state among engineering, merged, superseded, held, evidence_only, unresolved or rejected.

* For engineering: require a specific source_path, reason, provenance_verified true and publication_authorized true. Only then does a candidate become eligible for source implementation by any available agent. Historical test results, Drive readability and lack of Git blob match do not alone grant those flags.
* For superseded: require a current source_path, detailed evidence and tests documenting the precise behavior already present on main.
* For held or rejected: supply the exact reason. Preserve old refusal/authorization evidence and the original archive.
* For merged: require numeric PR, exact 40-character merge_commit, source_path, tests, original archive_sha256, original member_sha256 and a concrete evidence receipt. The workflow cross-checks the *live GitHub* merged_at and SHA before granting the merged state, and refuses merge credit when hashes/evidence are missing.
* For every member disposition: optional scope, drive_id, archive_sha256, member and member_sha256 fields must agree with the actual checkpoint fingerprint. Any conflict results in identity_conflict with a shared-pool review hint; a plausible vm1 candidate_id cannot disguise misidentified archive bytes. Include both SHA-256 fields on new adjudications wherever observed.
* For unresolved and evidence_only: supply an accurate reason and a follow-up owner. The original evidence survives.

The authoritative member ledger is now populated: Agent 1's 33 reviewed dispositions were merged in [#2481](https://github.com/gamesbyian/UR-Recomp/pull/2481), and four separately source-qualified QA08/audio decisions in [#2528](https://github.com/gamesbyian/UR-Recomp/pull/2528), for **37 scoped fingerprinted members (34 superseded, 3 evidence-only)**. A ledger decision applies only to its exact vm1 key/verified member identity; **newly encountered source members still need semantic review**. The full Vault inventory and unsampled H26 nested content remain distinct from those 37 records. Ledger IDs absent from available checkpoint artifacts are surfaced as orphaned/retained records rather than silently deleted. A green PR's *offline* review checks do not prove that the next scheduled `main` run has executed the updated ledger.

## Engineering and PR qualification

The review generator emits at most **two** explicitly approved engineering leads as an inert staging_handoff array. Each includes the exact Drive ID, `expected_archive_sha256` matching the checkpoint's entire original ZIP, **outer/nested `stage_member` path**, exact `stage_member_sha256`, source destination, workflow URL and confirmation-required state. No unattended dispatch or source staging occurs. Since [#2485](https://github.com/gamesbyian/UR-Recomp/pull/2485), the manually dispatched Direct Intake accepts both exact member fields and emits **only one approved, hash-verified source member**, including inside bounded nested ZIPs. The agent staging the candidate must enter both fields and separately review the member's rights/privacy and historical package holds. Leave both fields empty only when archive-wide staging of all eligible members has genuinely been reviewed and authorized. A missing Drive ID in the latest public listing becomes `unavailable_source_hold` even if previously verified.


A selected source-implementation agent takes only queued_engineering cases. Recompare actual member bytes against latest main and open PRs, check provenance and rights, and use the existing single-Drive-ID [Direct Vault Intake](DIRECT-VAULT-INTAKE.md) for reviewed source staging. Preserve negative evidence and failed publication history. Add the candidate_id or the exact token vault-member-sha256:<digest> to the narrow PR body so the consumer finds an existing claim and avoids duplicate PR work. Include the archive SHA-256, member SHA-256, Drive ID, source destination, exact base and head, test receipts, and qualification limits.

A distinct agent independently verifies the newest head, relevant targeted tests and required CI, coordinates genuine concurrent writes, then merges only qualified PRs. No named agent has a shared-main merge monopoly. Update the member ledger and #2088 with actual merge SHA and tests. An open PR, a historic merged claim, or a source hash alone never gets integration or release credit.

The existing recurring workflow has no source publication permission. This consumer also uses read-only GitHub permissions and does not publish ZIPs, source, branches or PRs. Reviewed staging remains an explicit source-owner operation. Automatic PR creation from raw review leads is intentionally forbidden until rights, source bytes and destinations are independently established.

## Commands

Run the isolated test suite:

    python3 -m unittest tests.unit.test_vault_integration_review -v

Generate a review from two downloaded scope directories and a live GitHub snapshot:

    python3 tools/vault_integration_review.py --incoming /tmp/state/incoming --evidence /tmp/state/evidence --github /tmp/state/github.json --out /tmp/actionable

github.json has a prs array with number, state, body, merged_at and merge_commit_sha. A failed or missing GitHub snapshot does not produce a false merged disposition.

## Operational limits

* The workflow uses one runner, not a new heavy research factory, and issues no source downloads beyond those the established recurring pipeline has already done.
* The latest scoped artifacts may come from different run IDs after partial failures. Metadata-only review therefore reconciles the latest complete data per scope.
* Its read-only GitHub snapshot includes all open PRs, up to 500 recently merged PRs, and direct verification of older registered PRs. Anything without live verification stays unresolved.
* The review summary is an artifact and job summary rather than noisy six-hour issue comments. Issue #2468 remains the single coordination thread.
* No original ROM, restricted capture, private data, media, raw archive, art signoff, hardware QA result or release gate is published or awarded by this system.

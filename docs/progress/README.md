# Product-completion measurement v2: atomic Windows beta inventory

**Status:** 2026-10-24 candidate for independent review. This system supplements, does not replace, the [release quality ledger](../RELEASE-QUALITY-LEDGER.json), the [USA event census](../ORIGINAL-COURSE-EVENT-CENSUS.md), the [existing v1 maturity score](../PROGRESS-INVENTORY.json), or the owner-approved product plan.

## What is frozen

[windows-beta-v2-inventory.json](windows-beta-v2-inventory.json) enumerates **135 fixed binary requirements** with a **4,500-integer-unit denominator** and an immutable criterion fingerprint checked by source-controlled validator. There are 90 product criteria (45 units = 1 percentage point each) and **45 original/native complete-USA-event slots** (10 units = 0.2222 percentage points each). Requirements are grouped under Windows packaging/host, 1P, 2P, Modern UI, profiles/Records, recovery, widescreen, art, physical QA, accessibility, and authentic event parity. All slots in the latter group require a unique canonical event identity and independent QA acceptance before credit.

Each small criterion has a binary `bounded_verified` / `unverified` status (or `regressed`) with specific evidence. Source-linked *bounded* verification means a narrow behavior has been exercised by an existing merged PR/test. It does **not** imply source-parity or physical release acceptance. Separate `audit_state` and `audit_receipt` document **independently reviewed coverage**. In the candidate snapshot, 50 criterion receipts are provisionally inherited from merged PR tests, but none has yet been separately promoted as independently audited. This intentional conservative separation prevents source-claimed tests from being mistaken for release qualification.

**First candidate baseline: 50.000% bounded product coverage; 0.000% independently audited criterion coverage; 0/45 official USA event admissions; 0/12 release QA gates.** The previous **48.5%** v1 maturity estimate and the historical subjective **60%** describe different instruments and must never be subtracted from this 50% or silently relabeled as regressions. Do not switch the official headline to this candidate until criterion/evidence classifications receive an independent QA/product audit. Retain all scales during a named, explicit handoff.

## Run it

From repo root, with Python 3 and no third-party packages:

```sh
python3 tools/atomic_progress_v2.py --format markdown
python3 tools/atomic_progress_v2.py --format json
# For a claim of CURRENT status, independently review main and supply that HEAD:
python3 tools/atomic_progress_v2.py --format json --reviewed-head FULL_REVIEWED_UPSTREAM_SHA
python3 tools/atomic_progress_delta.py --format markdown
python3 tools/progress_yield_audit.py --format markdown
python3 -m unittest discover -s tests -p 'test_atomic_progress*.py'
python3 -m unittest discover -s tests -p 'test_progress_yield_audit.py'
```

`atomic_progress_delta.py` compares each current status against [the immutable starting snapshot](windows-beta-v2-baseline.json) and reports **newly verified IDs, regressions, and exact percentage-point change**. The tests enforce immutable IDs/wording/weights, 135-item membership, 4,500 total integer units, named per-event identities for fidelity admissions, separate reviewer receipts, and count parity with QA-01's sole authoritative event count. The v1 historical scores remain untouched.

To make tomorrow's update meaningful, the integration owner inspects new merges, maps them to **one of these fixed, unmet individual criteria** (or explicitly says no criterion was closed), includes the exact executable verification link, and changes only the corresponding evidence/status on a pinned reviewed source SHA. If a previous verified item regresses, mark it `regressed` with a failure link and see the negative delta. A single resolved non-fidelity criterion gains 1.000 percentage point. One independently admitted USA event gains roughly 0.222 percentage points. Work in already-verified areas is still recorded in the regular change log but earns no ungrounded extra points.

Changing or splitting an existing criterion is **scope v3**, not an edit to v2. Every new proposed feature is put in a separate scope-change list until v3 approval. Existing source/PR links are screening receipts only, not independently re-executed tests.

## Is the engineering effective?

[The complete interval audit](merge-outcome-audit-20261024.json) covers **57 actual main commits** after the evening Oct 23 checkpoint (`9ca9fd77`), through a specific Oct 24 main SHA. First-pass intent categories: **11 direct-product, 19 release-risk-reduction, 20 enabling-infrastructure, 2 coordination/operations, 2 documentation, and 3 deferred/research**. This supports a decision about *work mix*, not a verdict on agent productivity. These are **commits rather than agent-hours**; the larger or harder PR may dwarf ten trivial commits. The taxonomy is deliberately marked title-and-PR first pass, with actual bug significance/ROI and labor time unknown. Never announce a percentage of productive labor based on this ratio.

An enabling-infrastructure PR should identify the next shipping criterion it will unblock, with a stopping rule and measurable future outcome. A research task should identify its decisive falsifiable test before consuming another evidence-factory batch. If an iteration neither advances a criterion nor reduces a specific release-blocker risk, either narrow it, postpone it or independently justify continued investment. In priority order: (1) first independently accepted complete USA event, (2) exact integrated Windows release candidate and real hardware QA, (3) observed real data loss/NTFS hazards, (4) coherent player journeys/UI, (5) visual/art approval. Vault integration matters when it recovers actionable first-party code/tests, not just counts archive entries.

## Reporting invariant

Every project update must show the **date and exact reviewed upstream SHA**, v2 candidate score **and** independent-audit score (or explicitly say not reviewed), v2 change versus the frozen v2 baseline (and new/retracted criterion IDs), authoritative 0..45/0..12 counters, directly observed merged product advances, and unscored enabling/deferred work separately. If latest main has advanced after review, timestamp the review as of the pinned SHA instead of pretending to be live. No "zero progress" inference from a zero QA-gate delta, and no score promotion from an unexamined PR title.

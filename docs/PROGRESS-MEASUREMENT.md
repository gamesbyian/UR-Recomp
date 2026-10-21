# Frozen project progress measurement

**Status:** baseline introduced 2026-10-21; do not confuse estimates with acceptance.

## Purpose and scope

The flagship Windows native Uniracers remaster is the fixed denominator. Deferred console and non-Windows ports, online P2P, elective cosmetics, course editors and encyclopedic long-term archaeology get separately scoped backlogs; do not silently enlarge the denominator. Preserve all non-negotiable release requirements: original fidelity, sound, true widescreen, approved racer art, functioning controllers, save integrity and physical Windows acceptance.

The canonical frozen anchor is [PROGRESS-BASELINE.json](PROGRESS-BASELINE.json). It memorializes the previously communicated **60% ±10 percentage points** estimate as an explicitly **subjective historical estimate**. Neither the weights nor the individual percentages are proof of completed acceptance requirements. The estimate **must not move** simply because a new subjective judgment is offered. It may be replaced only by a formally enumerated, reviewed fixed-scope inventory with stable acceptance IDs.

The evidence ledger [PROGRESS-CHANGELOG.json](PROGRESS-CHANGELOG.json) records changes against that frozen anchor. The existing [RELEASE-QUALITY-LEDGER.json](RELEASE-QUALITY-LEDGER.json) alone awards release gates. [ORIGINAL-COURSE-EVENT-CENSUS.md](ORIGINAL-COURSE-EVENT-CENSUS.md) alone determines independently admitted complete USA events.

## Progress reporting contract

Every report must state:
1. Compared source main SHAs and UTC timestamps; if previous source SHA is missing, explicitly mark baseline comparison as conversational/date-bounded, not a Git diff.
2. Implemented behavior newly merged, with evidence URL and named acceptance condition. Do **not** infer player-visible readiness from a PR title alone.
3. Validated behavior on the exact source/binary, including negative findings, and whether it is automated, independent, source-authentic or physical.
4. Formal accepted course event count and formal Windows gate count, with changes since previous report.
5. Regressions/retractions, net movement, and highest-impact blocking unknowns.
6. Frozen estimated percentage **unchanged**, plus quantitative completion delta only if computed against a fixed enumerated inventory; otherwise display **not yet measurable**. PR count, CI green count, line count, commit count, activity time and agent-hours are throughput metrics, **never completion numerators**.

Record advancement as `criterion_id, previous_status, new_status, owner, source_sha, evidence_uri, verified_utc, verifier_type`. Status progression: `planned -> implemented -> tested -> independently_accepted`; `blocked` and `regressed` are explicit states and can lower a calculated score. A test on another commit is historical evidence, not candidate acceptance.

## How to build the first objective percentage

1. Establish a named, frozen `windows-beta-v1` acceptance inventory with finite criteria and fixed integer point weights, derived from the existing project plan, UI acceptance, gameplay census and QA gate requirements. Assign every criterion one owning authority and one concrete pass condition. No double counting between a capability and its release gate.
2. For each item, record implementation and independently admitted acceptance separately. Use `unknown` until inspected, never award points from inferred progress. For a first conservative score, count only independently verified completion; report coverage (fraction audited) independently from completion (fraction accepted).
3. Compute completion as `100 * sum(weight of accepted criteria) / sum(all frozen criterion weights)`. Do not create a metric based on partially completed tasks unless explicitly labeled as provisional engineering progress. The course-event census and physical QA gates remain separate unweighted acceptance counters.
4. Freeze the inventory version and original denominator. New features create a *proposed scope v2* sidecar and do not mutate v1 or retroactively drag down its percentage. Corrections and retractions append dated evidence and can lower the accepted score.
5. Review the initial inventory with independent QA and product owners, test a validator that rejects duplicate IDs, missing evidence, invalid transitions and denominator changes, then place the automatically generated report in a deterministic pipeline without adding unnecessary recurring Actions.

**Until step 5 is complete:** headline `historical estimate 60% (unchanged)`, `audited fixed-scope completion: unavailable`, alongside objective deltas. Never claim there was zero engineering progress because a release gate has not yet closed.

## Operational integration

An existing operations/integration owner should maintain this changelog by extracting concrete merged changes from the interval; specialist owners provide evidence and independent QA alone updates its release ledger. Future agents should add changelog entries rather than rewriting history. Report failures and historical false positives as first-class negative changes. This is reporting infrastructure, not a substitute for fixing actual product/QA blockers; avoid assigning an additional hourly agent solely to maintaining it.

## First measurement

October 20 to October 21: current `main` at baseline commit `550307d5f6adf5de72d2074168b6420b7a217a35`; modern menu and title work, Windows capture/contrast quality, source provenance and concurrent racer preservation merged. See exact PR links in changelog. **Formal accepted USA events: 0/45 (delta 0). Windows release gates: 0/12 (delta 0).** No calculated percentage delta is defensible without an item-level inventory.

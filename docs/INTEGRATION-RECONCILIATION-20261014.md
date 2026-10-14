# Integrated source / Windows release engineering reconciliation: 2026-10-14

**Dated snapshot, not a mutable gate authority.** Checked `main` at `08e454eba77765f72435ec5fc93102e9d7720a23`, after merged #1537 and #1583. Refresh GitHub before making any merge decision; `docs/WORK-QUEUE.md` owns tasks and `docs/RELEASE-QUALITY-LEDGER.json` alone owns release-gate and candidate status.

## Three-project reuse preflight

Read `tools/select_three_project_reuse.py`, its source-grounded register, capability matrix and lane registry. In the **CI** lane, `agent-work-packets` is ready to reuse, while `gate-cache-dependencies` is **conditional on a demonstrated duplicate-gate blocker**, not permission to bypass tests. For the adjoining release-QA handoff, the registered `candidate-evidence-envelope` and `route-input-identity` opportunities already point to UR's `tools/evidence_contract.py` / controller-input consumers, Baldosa's pinned route inputs and Malmazuke's replay manifest technique. No new runner, branch cache, workflow or second release ledger was justified. Current authoritative original/native gameplay and release evidence must still be independently qualified.

## Open-PR integration boundary

- **#1584, Modern Practice process hard-kill:** initial head `0c38bbe5f062477f90bd56b466aaa0cc4ec8e771`, then updated to `a59ba2064a4b9fb02bf1cb1ff258c08b2f1254bd` during this audit. Implementation ownership remains Modern; initial exact-head tooling and hygiene passed, native Win32 was running and its superseded run was cancelled after the update. Source changes are confined to the established Practice probe/tests, Modern status document and, at revised head, native Windows workflow. Integration flagged the initial conditional `proc.kill()` proof gap in [PR discussion](https://github.com/gamesbyian/UR-Recomp/pull/1584#issuecomment-6178734238): a prior GO line plus child already exited is insufficient to assert actual `TerminateProcess`. Require current-head green Win32 evidence and independent QA acceptance before merging. Neither original USA full-event parity nor power-loss/hardware credit follows.
- **#1585, original APU acknowledgement / branch pairing:** opened during reconciliation, head `1e4018050e8633e5165053099ab66bc8c4e1e7e0`. Docs and read-only QA-01 observer/unit changes only; hygiene passed and tooling unit job was running when inspected. No runtime overlap with Modern or release packaging. Leave first-difference authority, original evidence and acceptance decision to gameplay/CPU/APU owners; do not reinterpret its result as a release win.

No cross-lane conflict repair or speculative merge was warranted in this snapshot.

## Branch and orphan-work classification

GitHub's historical branch collection is alphabetically ordered, not recently updated. A bounded search for branch names containing `20261014` returned **100** branches when this integration worktree existed. Matching those branch names to the latest **175 PRs by creation** gave **97 PR-associated branches** and **three not yet PR-associated**:

| Branch | Evidence and disposition |
| --- | --- |
| `graphics/qa08-37frame-original-native-window-source-20261014` | `main...branch` compared as 7 ahead / 12 behind, four changes including a manual source raster workflow and its tool/tests. No matching PR among the queried recent PRs. **Preserve for the graphics owner**; active development vs intentionally deferred instrument not yet adjudicated. Do not transplant on top of newer #1582 evidence. |
| `qa/source-bound-windows-candidate-audit-20261014` | No matching PR in queried set. **Preserve for the independent release-QA owner**; likely ongoing candidate work, no integration claim or branch mutation. |
| `integration/romless-readme-practice-20261014` | This integration change, intended for a focused reviewed PR. |

A separate spot-check of stale-looking branches (`agent/ci-shared-native-candidate`, `agent/ci-modern-manual-campaign-20261011`, `agent/integration-audit-20261008`, and 2026-10-14 QA/graphics branches) initially yielded positive ahead counts despite being behind current `main`. The corresponding PRs #723, #1379, #900, #1486, #1497, #1516 and #1541 are **already merged**. This is expected with squash/indirect history and is not independent evidence of lost work. Four sampled `ccr-` branches were ancestor/behind with **zero ahead**, so no recovery PR was needed. The alphabetic first two pages (200 branches) contain older CI/audio work; this is **not an exhaustive forensic audit of all historical branches**. No branch was deleted or force-pushed.

## Integrated test, packaging and release identity

- The last observed complete Windows feasibility validation before this snapshot was #1583 exact PR head `22b22c418eae40c2bea774291021065d79819084`, [run 38634778559](https://github.com/gamesbyian/UR-Recomp/actions/runs/38634778559), successful. `main` then advanced through merged research #1537. The subsequently triggered #1584 head must be evaluated on its *own* SHA. Do not combine tests on different heads into a fictitious integrated Windows acceptance.
- `tools/assemble_baldosa_windows_candidate.py` is the existing **ROM-free** ZIP authority: normalized ZIP members, explicit source revision and SHA-256/size per immutable member, original ROM verification at launch, external per-user roots and a printed final ZIP SHA-256. `tools/assemble_windows_package.py` is a separate older complete ZIP producer with its own checksum sidecar. Do not merge these artifact identities or suggest the current ROM-free ZIP includes a ROM.
- The ROM-free generated candidate README still stated that Practice was unavailable after #1578/#1583 had already merged source-qualified first-course Dragster Practice and sandboxed save isolation. This integration PR corrects **only consumer-facing package text** and pins that factual statement in the existing packager unit test. It does **not** change session implementation, guest execution, source/artifact hashes or QA credit.
- The release-ledger candidate remains `commit_sha: null`, `zip_sha256: null`, physical verification false, and official complete-USA event acceptance 0/45. Archived premerge Windows/native source artifacts prove bounded components, not an exact final-main package, hardware journey or cross-lane source-original correctness. A final nominee must record **the same executable/ZIP SHA and exact source revision** for build, original/guest route, true P1/P2 source results, raw pre/post Records bytes and physical evidence. Independent QA owns certification, never the packager.

## Exact next integration actions

1. Refresh every open PR/head/check and run **only** the exact current native Windows head for #1584. Ensure its kill assertion and source logs demonstrate an actual OS termination, then obtain independent QA review; merge only with accepted evidence and unchanged ownership boundaries.
2. Inspect #1585's exact unit check and defer its source correctness to QA-01. A red or cancelled superseded run is not interchangeable with the newest head.
3. Revisit the two unpaired owner-lane branches after their agents stop/open PRs. If either has unique unmerged evidence, have its owner submit a focused, current-main PR; preserve discarded experiments, never bulk cherry-pick stale workflows.
4. Build one final merged-main ROM-free Windows ZIP after active merges settle, retain the canonical member manifest, original source revision, PE hash, outer artifact and inner ZIP hashes; hand **that exact candidate** to independent QA. Physical Windows pads/audio/graphics, full event parity and OS fault journeys remain explicit negative/missing categories.
5. Prefer reusing existing manual cohort/packaging workflows and first-failed-step logs. No new scheduled CI, duplicate native compilation or workload just to saturate the account-wide 20-runner ceiling.

**No release quality gate is changed by this report.**

# CI and research-apparatus audit: October 10, 2026

**Evidence window:** live GitHub Actions REST first three pages (300 most recent runs, 2026-10-10 23:13:55Z through 2026-10-11 02:15:12Z). A point-in-time audit, not a claim to have inspected every historical workflow run or a replacement for [the CI policy](CI-WORKFLOW-BEST-PRACTICES.md). The [work queue](WORK-QUEUE.md) still selects priorities. No new scheduled workflow or branch-protection gate was added.

## Observed run concentration and classification

| Workflow | Sampled runs | Successful | Failed | Cancelled | Skipped |
| --- | ---: | ---: | ---: | ---: | ---: |
| Project tooling unit tests | 88 | 26 | 25 | 37 | 0 |
| Modern native heavy router | 81 | 64 | 0 | 12 | 5 |
| Repository hygiene | 64 | 57 | 0 | 7 | 0 |
| All other workflows combined | 67 | — | — | — | — |

The top three accounted for **233/300 runs (78%)**, across a sample of **97 distinct head SHAs** and 298 PR events plus 2 push events. These counts are **run-start and cancellation exposure**, not independent failure rates, compute minutes, CI economics or currently failing main. Cancelled jobs on superseded heads are not regressions. Strong repeated cancellations, especially the 37 tooling cancellations, indicate rapid commit cadence incompatible with the gate's observed two-minute execution time. Prefer a completed local test batch and one coherent push rather than multiple rapidly superseded checks.

Concrete root-cause check: [tooling run 38104347536](https://github.com/gamesbyian/UR-Recomp/actions/runs/38104347536) failed the documentation authority bound for `docs/WORK-QUEUE.md` (**16,513 vs cap 16,000 characters**), not game code. The current logging required opening a large unit-test log to identify that one assertion.

## Changes integrated on main

1. **No more classification-only native CI on unrelated research.** `.github/workflows/modern-native-heavy-router.yml` previously woke for entire `tools/**`, `tests/**`, `native/**`, `analysis/**` and `reference/**` changes while its classifier used only the narrow `.github/ci/modern-native-{shared,onboarding,ui}-paths.txt` ownership manifests. Its PR trigger now includes the exact union of those manifests. Changing a manifest or the classifier itself triggers its owning suite; an unexpected selected-none result now fails visibly rather than showing a green no-op. [Example former no-op run 38104544169](https://github.com/gamesbyian/UR-Recomp/actions/runs/38104544169).
2. **Correct PR diff domain.** The router now compares merge-base `base...head`, matching GitHub's PR path-filter semantics, rather than `base head` two-point differences.
3. **One native build for two or three suites.** The router had shared the canonical build only when *all three* suites were required. The build now executes for any selected pair or all three. One selected suite continues to use its independent path. This avoids two parallel identical builds for pairwise overlaps. Real runner-minute savings still require measurement.
4. **Pin trigger ownership in tests.** `tests/unit/test_classify_modern_native_ci.py` guards exact event-filter/manifests agreement, selector/manifest self-invalidation and pairwise build selection. Future input-manifest changes must update the event filter and keep the contract green.
5. **Make tooling results cheap to read.** The unit workflow retains fast syntax preflight and stable two-shard parallelism, but now publishes the compact `ci-tooling-unit-result.json` plus an Actions job summary naming shard, observed count, failure examples, durations and provenance. Full verbose shard logs are uploaded only on failure. The publisher distinguishes pass, fail, harness error, not-run and incomplete states without changing the original test job verdict.
6. **Pilot Pathfinder-style research result packaging.** The existing manual-only jump-versus-control execution coverage workflow now emits a direct `GITHUB_STEP_SUMMARY` and a compact hashed run receipt alongside its existing primary JSON and Markdown. `tools/publish_experiment_result.py` preserves exact result/fixture/code/toolchain-file hashes and source-run identity. It labels research production `produced_not_adjudicated`, never independent original/native acceptance, and refuses missing, duplicate or invalid inputs. Its unit tests cover success and invalid evidence. No extra experiment was run or new automated trigger added.

## Pathfinder research apparatus lessons, applied narrowly

Source example: `gamesbyian/Pathfinder-Game` `scripts/publish-solver-sweep-result.mjs`, `scripts/fetch-gha-result.mjs`, `scripts/check-solver-sweep-result-contract.mjs`. Pathfinder consistently separates (a) producer data, (b) small summary and manifest, (c) artifact hashes/run/attempt/dispatch identity, and (d) a convenient retrieval path. It keeps raw shard material for fault diagnosis and uses deliberate control/treatment and input-population identity before causal claims. UR already has `tools/evidence_contract.py`, `tools/tool_interop.json`, existing source run archives and its own canonical research/QA ledgers. **Reuse them; do not create a second acceptance owner or copy Pathfinder's solver-specific schemas.**

### Design contract for the next genuine experiment

Before launch, record the decision/hypothesis, current baseline, exact ROM/core/toolchain/candidate, comparable input/clock domains, cheapest bounded discriminator and stop criterion. Check existing prior findings and retained artifacts first. Prefer one frozen matched-control/treatment route and one candidate build feeding multiple independent assertions; do not generate `+8/+16/+24` sibling workflow copies for a parameter sweep. Separate `completed_positive`, `completed_negative`, `invariant_violation`, `harness_error`, `infrastructure_error`, `timeout` and `not_adjudicated`. A completed run is not automatically a positive scientific result.

Every **maintained, decision-bearing** experimental workflow should make its primary metrics/verdict discoverable on the Actions summary and upload one compact machine result with source revision, exact actual inputs and digests, expected/observed cohort or frame count, missingness, canonical evidence paths and reproduced invocation. If the producer fails before generating a result, label the report incomplete and retain the original failure; never turn no data into success. For new domains, use `tools/publish_experiment_result.py` as the **transport** receipt and the existing domain validator/`evidence_contract.py` as the semantic adjudicator; the pilot does not pretend that a hash proves correct simulation.

Promote **small decision-bearing** artifacts from worthwhile runs into `analysis/data/`, existing `docs/RESEARCH-LEDGER.md`, technical-reference entries or owning native tests by reviewed commit. Do not automatically commit every run to `main` or carry multi-gigabyte raw outputs into Git; preserve the exact regeneration command, hashes and source-run ID. Retained CI artifacts expire, so results needed for future work must be promoted intentionally.

## Follow-up validation and repaired policy regression

Live [tooling run 38107403781](https://github.com/gamesbyian/UR-Recomp/actions/runs/38107403781) exposed a previously missed **existing assertion** in `tests/unit/test_ci_trigger_policy.py` still requiring *all three* suite flags before the canonical shared build. That outdated test failed after the optimization intentionally changed the build to run for *any pair*. The policy test was updated to require all three pairwise conjunctions while continuing to enforce exactly one build command, all three reusable consumers and the candidate-artifact handoff. The suite-specific classifier tests additionally enforce merge-base PR diff selection and fail-visible no-owner routing. This was a **test/policy disagreement**, not evidence of a broken native game, and it needed explicit correction before a green result could be claimed.

Separate live [run 38107618717](https://github.com/gamesbyian/UR-Recomp/actions/runs/38107618717) failed its early Python syntax preflight in a new media/showcase script; it is unrelated to the native-router path narrowing. The tooling workflow appropriately identifies that first failure and now publishes an incomplete summary instead of declaring success. Avoid “fixing” legitimate tool-source syntax validation by excluding the new script from `tools/**`.

The manual jump/control workflow additionally now writes a **specific inconclusive Actions summary if its producer fails before a valid receipt exists**. This summary is diagnostic; it cannot turn a failed run green or establish a positive or negative scientific outcome. Its regression test requires that fallback. As before, no executed jump/control result from the modified workflow has been claimed.

## Remaining work and limits

- The sample demonstrates **trigger exposure**, not reliable runner-minute savings. Measure actual no-op native runs eliminated and whether two-suite canonical builds reduce elapsed time and runner usage after a real PR hits those paths. No live post-change PR workflow has been executed in this direct-main edit.
- The catalog contains **132 workflow YAML files**. A follow-up source-header census fetched **131/132** and classified their trigger types, finding **23 automatic workflows** (PR or push) and **108 manual/reusable-only** among the readable files; `switch-s2-link-surface.yml` could not be fetched because of a transient remote disconnect and remains unclassified in this audit. No schedule triggers were found in the 131 examined. These counts classify triggers, not whether a workflow is currently enabled on GitHub. This audit did **not** execute every YAML body or prove every trigger economically optimal. `tests/unit/test_ci_trigger_policy.py` remains the broad static policy gate; audit rare automatic workflows when their owning surface changes.
- Some existing research workflows already output JSON and artifacts without a top-level summary. Expand the publisher by **demand and active question**, not a bulk 132-file rewrite. The first manual pilot is execution coverage A/B; no new ROM run was performed to validate its new receipt.
- A separate CI workflow selection optimization (per-test dependency closure or cache skips) is not justified until exact dependency invalidation and adversarial mutation testing exist. Pathfinder's cache lessons strongly argue against false-green dependency assumptions.
- Check any prior open PR, ownership lane and latest head before broad trigger changes. Preserve standalone native suite invocation and the final-main Windows packaging smoke.

## Quick operations for agents

Use the Actions **Summary** first; download the compact named result artifact second; open bounded failure logs or raw capture only if the summary shows a specific missing assertion or ambiguity. Cite run URL/ID, head SHA, outcome, input hashes and exact scientific limitations when promoting useful findings. Start with `docs/WORK-QUEUE.md` and `docs/CI-WORKFLOW-BEST-PRACTICES.md`; this dated report explains why current policy is configured this way, but is not another queue.

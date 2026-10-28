# CI acceleration: measured rollout and owner handoff (2026-10-14)

**Scope:** integration / CI only. This is a bounded implementation record that supplements [CI-WORKFLOW-BEST-PRACTICES.md](CI-WORKFLOW-BEST-PRACTICES.md), [OPERATIONS-ACCELERATION.md](OPERATIONS-ACCELERATION.md), [HYBRID-AGENT-RESEARCH-CAPACITY.md](HYBRID-AGENT-RESEARCH-CAPACITY.md), and the live [WORK-QUEUE.md](WORK-QUEUE.md). Those authorities and the release-quality ledger remain authoritative. Do not overwrite work from Modern, gameplay, graphics, CPU/APU, or independent QA. Latest measured base at start: `main` `915fa8d70c460bd4f931ef71d8cd115017be07a2`; recheck before implementation.

## Goal and non-negotiable boundaries

Improve **elapsed hours to independently accepted, player-visible functionality**, not the number of PRs closed or runner occupancy. GitHub Actions supplies Windows compiler/emulator/test compute to agents: compute-trigger PRs are useful. Encourage persistent branch workspaces with meaningful incremental pushes; don't force each experiment into a separately merged PR. Never reduce original/native acceptance criteria, source/ROM/movie/seed identity, real crash/process proof, result integrity, release evidence independence, or ROM-free package rules to save CI.

The three-project reuse preflight for `ci` currently identifies existing UR lane packets and a **conditional** Malmazuke transitive dependency-identity pilot; it does not justify a second runner, ledger or automatic research framework. Reuse existing tools and source-pinned candidates before building new machinery.

## Measured baseline: workload starts are not resource cost

A read-only GitHub Actions sample of the 300 most recent workflow **runs** through 2026-10-15 01:50 UTC gave:

| Observation | Value | Interpretation |
|---|---:|---|
| Sampled workflow runs | 300 | Roughly six hours of intense PR activity, not a seven-day census |
| PR-triggered / dispatched / push | 293 / 5 / 2 | PRs act as compute triggers |
| Tooling-unit / repository-hygiene starts | 115 / 98 | 213/300 starts are routine validation, not necessarily 71% of runner-minutes |
| Cancelled / failed runs | 68 / 33 | Failed and cancelled are different; superseded cancellation is not a game regression |
| Workflow definition files | 148 | Inventory count is not by itself overhead |

Existing measured 24-hour data in [HYBRID-AGENT-RESEARCH-CAPACITY.md](HYBRID-AGENT-RESEARCH-CAPACITY.md) gives a stronger cost clue: approximately 748 runner-minutes, 68.5% of sampled time with zero active jobs but peaks of 20; previously cancelled Modern and tooling jobs consumed meaningful runner-minutes. Confirm these numbers with a fresh job-level baseline; the `ci-runtime-report.yml` workflow was limited to 100 recent runs and could silently imply seven-day coverage despite much less.

The successful native Windows [run 38645114899](https://github.com/gamesbyian/UR-Recomp/actions/runs/38645114899) was approximately **9m11s**. Its single job built the executable in about 93 seconds, then performed approximately six minutes of sequential Windows journeys. This is a candidate for build-once, fan-out acceptance, but its source-pinned executable, package manifest, raw saves, guest outcomes and current QA negative controls must survive unchanged.

## This PR's deliberately small, useful pilot

1. **More truthful, wider runtime reporting.** Manual `.github/workflows/ci-runtime-report.yml` can inspect up to 300 runs using bounded pages and six concurrent job-API readers. `tools/report_ci_runtime.py` reports earliest/latest sampled run, whether the requested lookback is actually covered, cancelled **runner-minutes** separately from cancelled workflow wall-minutes, and event counts. Missing timing stays excluded rather than inferred as zero observed cost. Default 100 runs and manual-only triggering remain.
2. **No-cost Windows fan-out control.** The existing shared-build `baldosa-windows-reliability-campaign.yml` gets a bounded 1/2/4 `max_parallel` option, default **2**. Its four pre-existing source-bound `guest-0/guest-1/launcher-0/launcher-1` cohorts, results, artifact names, SHA checks, aggregate and release-credit boundary are unchanged. This makes four-way computation possible when runner headroom exists without automatically dispatching more experiments or modifying the Windows build owner.
3. **Synthetic contract tests** retain the exact four-cohort acceptance population and verify report sample integrity. These changes do not yet assert real elapsed speedup or release QA credit.

## Next audits and decisions, in order

**A. Seven-day job-cost and trigger audit (integration/CI).** Dispatch the existing runtime report on the merged revision, first `runs=100`, then `runs=300` only if useful. Use the report's coverage flags; when 300 runs don't span seven days, collect several non-overlapping paginated observation windows or extend the manual reporter with a time-bound cursor and rate budget. Measure actual job/step minutes by workflow, p50/p90 wall time, cancellation runner-minutes, queue delays, setup/build/test/artifact durations, critical path, and identical build hashes. Do **not** claim the truncated sample is a week. GitHub App access to other repositories may be absent.

**B. Original/native event and Windows workload topology (owners consulted).** Map each expensive workflow's immutable producer and independent consumer cases. Preserve sequence inside each user-data or original input journey. Candidate: `baldosa-windows-native-bridge.yml` is currently one expensive Windows job; `qa01-event-campaign.yml` builds once and uses two parallel case shards; `qa02-real-fault-endurance.yml` owns five cases at max three concurrent; `qa-adaptive-frontier.yml` already has source-bounded 1/2/4 sharding and `candidate_only`. Don't reimplement optimizations already landed.

**C. Shared-build Windows acceptance pilot (highest major implementation priority, after PR ownership clears).** Convert the long Windows bridge's independent post-build journeys to 2-shard then 4-shard consumer jobs. Build one exact source-pinned executable/ROM-free ZIP, verify SHA256 and immutable inputs before each consumer, give each an isolated temporary root, and retain every existing original 1P/2P result, fresh Records, Practice/kill, CMD startup and input assertion. Aggregate with fail-closed missing/duplicate/source-mismatch checks. Independent release QA must review the exact actual Windows evidence. Benchmark same cases on same source against sequential baseline. **Do not touch the bridge while another owner changes it**, especially PR #1609 at this checkpoint.

**D. PR compute-workspace audit.** Separate (a) computational PRs used to obtain Windows/GHA execution, (b) integrated feature PRs, and (c) manual branch-dispatched research. Allow persistent PR head for bounded experiments; prefer a main-registered `workflow_dispatch` against a pinned branch commit where workflow mechanics permit. A new workflow definition absent from `main` may need PR execution. The Modern heavy router skips draft PRs, so do not assume draft PRs trigger its heavy work. Use meaningful pushes rather than fast cancellation chains, but never wait for CI when independent work can proceed.

**E. Cumulative research serialization redesign (high risk, conditional).** Today `qa-cumulative-research.yml` wraps reservation, all seven selectable producers and final ledger write under one global non-cancelling concurrency group. Before changing it, measure whether **useful independent campaigns are actually queued behind the ledger lock**. If yes, implement short globally serialized atomic reservation and append phases with immutable unique seed namespaces, parallel independent producers, no overlapping writers, reviewable signed identities and reconciliation of failed/cancelled reservations. Negative, missing, repeated, stale or forged receipts must never earn credit. Pilot two disjoint producer families before broad deployment. If no decision-bearing campaigns are waiting, defer.

**F. Capacity-aware parallelism.** The operational assumption is **20 account-wide runners**, not 20 reserved slots. Current research admission retains unseen-repo and agent headroom and distinguishes `admit`, `admit_downsized`, `defer`; preserve it. Prefer short high-priority engineering CI, then source-qualified original/native, Windows, graphics and recovery experiments, then optional frontier work. Tune four-way Windows reliability only during spare capacity and compare actual runner-minutes. Never fill idle runners with low-yield research for appearance's sake.

## Comparative test and rollback contracts

- **Reporter:** source-window completeness clearly false for truncated coverage; counts preserve run event and conclusion; no partial job pagination accepted as complete; cancelled runner time derived from actual job intervals, not run elapsed. Regression/unit tests must be green.
- **Fan-out:** original four cohorts and exact executable/fixture/package/ROM/script input identity are unchanged, no extra test case or release credit. Compare manual `max_parallel=2` and `4` on equal independent populations and the same source. A failure must still retain an incomplete-or-negative aggregate. If faster wall time costs unreasonable runner-minutes or creates queue starvation, use default 2.
- **Windows main candidate:** do not confuse legacy Windows package with native Baldosa product, mix PR-head and merged-main artifact bytes, or replace physical two-pad/audio/GPU checks with semantic headless scripts.
- **Stop:** if 2-shard shared-build acceptance cannot preserve all existing Windows journey evidence or provenance, restore the original monolithic route rather than narrowing acceptance. If the cumulative coordinator cannot reserve/commit without races or lost negative results, retain its current serial form.

## Outcomes to review

Compare before/after **runner-minutes wasted on superseded execution**, **p50/p90 time to actionable result**, **critical-path Windows candidate minutes**, **job-level occupancy**, **accepted stable functionality per productive agent-hour**, and **first original/native complete event**. Initial experimental goals (not promises): reduce cancelled runner-minutes by 25%, shorten unchanged Windows acceptance wall time by at least 20%, and preserve 100% of source/evidence coverage. Report implementation, independent verification, and release readiness separately, with fixed denominators. Do not count a PR or green research transport as a released game feature.

**Change-control:** One owned integration/CI PR per coherent pilot; document exact source/CI result and affected hashes. Merge only independently safe and green. Another agent's in-flight native/core/graphics/QA work is not an excuse to patch its files. No extra automatic GHA triggers are introduced by this pilot.

## Rejected three-worker post-baseline schedule and next overlap experiment

[PR #1630](https://github.com/gamesbyian/UR-Recomp/pull/1630) was **closed unmerged** after a complete genuine Windows acceptance run on [38675027884](https://github.com/gamesbyian/UR-Recomp/actions/runs/38675027884). All eleven live cases and the strict seven existing evidence artifacts passed, but three workers started **after** the serial baseline made performance *worse*: **530 s** total job and **310 s** journey step, versus the prior two-worker **451 s** total and **269 s** journey step on [38673087609](https://github.com/gamesbyian/UR-Recomp/actions/runs/38673087609). Build duration also varied (118 s vs 94 s), so this is a decision-supporting adjacent-run negative, not a controlled same-revision timing distribution. More local workers alone are not an improvement.

The next bounded PR tests a different critical path: baseline **starts first and exclusively creates its shared parent root**, then independent native processes may execute while the baseline is still running. The two source-backed Records cases remain blocked until the baseline **finishes successfully and produces the genuine 8192-byte seed**, never a synthetic substitute. Every existing case, command and strict artifact path stays unchanged. This mode uses up to three in-job Windows workers **only on PR heads for the pilot**; the existing manual/call two-worker post-baseline path and full serial fallback remain intact. Abort or revert if any root/seed race, old artifact membership change, functional regression or absent meaningful elapsed-time benefit appears. Do not call a Windows PR-head smoke pass independent hardware/45-event/release acceptance.

### First actual baseline-overlap pilot result

[Windows run 38676202874](https://github.com/gamesbyian/UR-Recomp/actions/runs/38676202874) completed the full **eleven genuine source-bound Win32 journeys**, package/manifest hash binding, real extracted CMD launcher, and all **seven** original bounded evidence artifact names, plus the eighth timing receipt. The overlap journey step was **222 s**, versus **269 s** from the accepted two-worker [run 38673087609](https://github.com/gamesbyian/UR-Recomp/actions/runs/38673087609): a **47 s / 17.5%** phase reduction. The complete Windows job was **430 s** versus **451 s**, a **21 s / 4.7%** elapsed saving. Build duration varied **104 s vs 94 s**; these are different pinned source revisions and runners, not a same-source statistical benchmark. Both runs passed complete original test populations; no release gate or hardware credit. The first PR head had a stale workflow-comment assertion in the synthetic unit test (other suites green), corrected before the final acceptance head is evaluated. Retain or reject after the new final-head real Windows and full unit results.

## Rejected two-runner split for the ordinary eleven-case Windows gate (2026-10-14)

[Experimental PR #1633](https://github.com/gamesbyian/UR-Recomp/pull/1633) tested the real end-to-end architecture in [run 38678799401](https://github.com/gamesbyian/UR-Recomp/actions/runs/38678799401). The one pinned Baldosa producer compiled the real PE32+ executable and profile fixture, verified clean-machine dependencies, assembled the ROM-free ZIP and exported exact SHA256-bound bytes **without first running player journeys**. Two separate `windows-2022` consumer jobs downloaded those same bytes. One ran the original baseline plus both genuinely SRAM-seeded Records tests; the other ran all eight independent original Win32 routes plus the real extracted CMD/ROM test. An Ubuntu aggregate required eleven disjoint passing cases and identical source/EXE/fixture/ZIP digests. All **four experiment jobs succeeded**, including the aggregate; the original full Windows bridge [run 38678799269](https://github.com/gamesbyian/UR-Recomp/actions/runs/38678799269) also passed unchanged against that PR revision.

| Path | Producer (runner-s) | Baseline/Records | Independent | Aggregate | Runner-s | Elapsed |
|---|---:|---:|---:|---:|---:|---:|
| Existing single Windows runner | included | included | included | included | **402** | **402s** |
| Experimental two-runner fanout | 183 | 208 | 169 | 9 | **569** | **~403s** |

**Disposition: completed functional experiment, rejected performance optimization.** The separate runners correctly execute the original cases, but the critical path is producer **183s** followed by the baseline-dependent Windows consumer **208s**, then a short aggregate. Total elapsed was effectively unchanged; consumption rose by approximately **42%**. This is the opposite of the desired GHA efficiency. The full producer/consumer architecture was **not merged**: the PR was reduced to this documentation-only negative result, removing its extra workflow, new harness, synthetic tests and the `candidate_only` modification from the final diff. Original automatic Windows acceptance on `main` remains source-identical and unchanged. The experimental branch/CI receipts retain the source-bound proof if later research needs it.

The first synthetic unit suite failed because its proposed duplicate-index negative control assigned an index to its **existing value**, not because the real Windows execution failed. Do not describe the abandoned implementation as having a fully green suite. Production 11-case Windows acceptance and both experimental scenario jobs passed; that does **not** earn independent release/physical-hardware/strict 45-event credit.

**Reopening threshold:** consider multi-VM fanout only when one source-pinned build supplies significantly **more than eleven** genuinely independent acceptance tasks, or when repeated long-running scenarios change the bottleneck enough that baseline serialization ceases to dominate. Use the existing `baldosa-windows-reliability-campaign.yml` shared-build four-cohort matrix (optional 1/2/4 way) and existing original/native QA batch infrastructure first. Measure complete wall time **and total runner-minutes**. Do not create duplicate automatically triggered native builds just to use spare runners. For ordinary product PRs, retain the previously merged baseline-overlap Windows route (#1632).

## 2026-10-26: measured fast-path operations validation

**Production evidence, scoped conclusion:** [#2642](https://github.com/gamesbyian/UR-Recomp/pull/2642) extends the original fail-closed `ci_select_unit_suite.py` allowlist by exactly `tools/report_ci_runtime.py` and its corresponding `tests/unit/test_report_ci_runtime.py`; its previously existing operations suite already exercises the runtime reporter and cancelled-run and live-ops consumers. [#2643](https://github.com/gamesbyian/UR-Recomp/pull/2643) became the first subsequent *actual* reporter-only PR. GitHub's exact Actions job steps demonstrate that it selected `ops`, passed the bounded operations regression and skipped the full four-shard suite; the existing `unit` check and hygiene passed, then the PR merged. Mixed changes, test selector edits, unknown files, missing GitHub data, deleted/renamed changes and product source still use the complete suite.

| Checked PR / source | Observed Actions unit run | Unit job start → completion | Actual selected test step |
| --- | --- | ---: | --- |
| [#2639](https://github.com/gamesbyian/UR-Recomp/pull/2639) CI reporter plus cancellation-measurement changes | [40395290694](https://github.com/gamesbyian/UR-Recomp/actions/runs/40395290694) | **228 s** | Full dependency-free Python unit shards |
| [#2638](https://github.com/gamesbyian/UR-Recomp/pull/2638) workflow validation test/contract changes | [40395399966](https://github.com/gamesbyian/UR-Recomp/actions/runs/40395399966) | **121 s** | Full dependency-free Python unit shards |
| [#2642](https://github.com/gamesbyian/UR-Recomp/pull/2642) selector changes (not allowlisted) | [40403516182](https://github.com/gamesbyian/UR-Recomp/actions/runs/40403516182) | **178 s** | Full dependency-free Python unit shards |
| [#2643](https://github.com/gamesbyian/UR-Recomp/pull/2643) reporter + its exact unit test only | [40404426405](https://github.com/gamesbyian/UR-Recomp/actions/runs/40404426405) | **21 s** | Existing bounded operations suite; full suite skipped |

**Interpretation:** The 21-second source-verified targeted gate actually ran; it was not a simulated selector or a skipped required check. The previous three jobs had a **121–228-second observed range**. This is not equal-work A/B testing, aggregate seven-day resource accounting, or evidence of saved Windows builds. Each run's measured job wall span is an observed duration, **not** a billing receipt. Report broader speed improvements only after accumulating like-for-like samples.

The existing [manual CI runtime report](../.github/workflows/ci-runtime-report.yml) can now expose **p50 and nearest-rank p90** of legitimately timed completed runs, plus the count of completed runs whose timing is absent or reversed. [#2643](https://github.com/gamesbyian/UR-Recomp/pull/2643) corrects the former average that silently divided observed wall seconds by *all* completed runs, counting absent timing as zero-duration samples. This improves decision quality; it does not by itself make gameplay CI faster, reduce release standards or repair historical startup failures.

## 2026-10-26: PR readiness-to-merge latency, using real GitHub timeline events

**Read-only population:** 24 most recently updated, *merged* PRs from the closed-PR API snapshot at approximately 21:50 UTC, PRs #2622–#2647 plus older #2592 (selected by actual API order, not a contiguous PR-number range). For each selected PR, fetched the **individual GitHub issue timeline** (maximum 22 events observed, under the 100-event page bound), looked for a `ready_for_review` transition and used its last event timestamp when present. Otherwise used creation timestamp because no draft→ready transition appeared in that PR's observed timeline. End = actual `merged_at` timestamp. The sample contains **four explicit ready transitions** (#2629, #2609, #2619, #2622); other records use observed creation. No UI estimation or PR status-label guesswork.

| Sample (2026-10-26) | PRs | Median ready→merge | Nearest-rank p90 | Longest |
| --- | ---: | ---: | ---: | ---: |
| All selected merges | 24 | **3.9 min** | **41.1 min** | 1,285.1 min |
| Operations/CI/docs/recovery | 18 | **2.15 min** | **8.0 min** | 68.2 min |
| Player/product/QA source | 6 | **26.55 min** | **1,285.1 min** | 1,285.1 min |

**Source-checkable examples:**
- [#2629](https://github.com/gamesbyian/UR-Recomp/pull/2629): explicit `ready_for_review` **19:41:38Z**, merged **20:16:04Z**, **34.4 min**, versus **56.3 min** from original PR creation. This illustrates why draft/ready transitions must be measured.
- [#2609](https://github.com/gamesbyian/UR-Recomp/pull/2609): explicit ready **19:01:18Z**, merged **19:09:41Z**, **8.4 min** despite being created much earlier as a held draft.
- [#2619](https://github.com/gamesbyian/UR-Recomp/pull/2619): explicit ready **18:41:04Z**, merged **18:59:44Z**, **18.7 min**.
- [#2622](https://github.com/gamesbyian/UR-Recomp/pull/2622): explicit ready **18:40:35Z**, merged **18:45:09Z**, **4.6 min**.
- [#2641](https://github.com/gamesbyian/UR-Recomp/pull/2641): no ready-transition event; created **21:06:56Z**, merged **21:48:02Z**, creation-baseline **41.1 min**.
- [#2592](https://github.com/gamesbyian/UR-Recomp/pull/2592): no ready-transition event in the 16 returned timeline events; created **2026-10-25 22:28:14Z**, merged **2026-10-26 19:53:19Z**; **1,285.1 min** drives the product-sample p90. It is not evidence of 21 hours of continuous agent work or CI occupancy.

**What this does and does not prove:** This is the requested measurable *ready-PR-to-merge* latency for a bounded real sample, **not** general creation-to-merge, time to independent release acceptance, review-only delay, agent-hours or runner billing. Readiness-to-merge includes any outstanding checks, repair, scheduled-agent handoff, manual deliberation or integration dependency, and the sample is heavily weighted toward fast infra PRs opened/merged in one session. Without a comparably sampled historical cohort and stable PR mix, neither the faster operations median nor the later product median establishes a causal acceleration effect. Preserve the raw source URLs and do not attach release-gate credit.

## Measured 1000-module Python test-shard calibration (October 27 pilot)

Another exact-run inspection found Python shard tests of **114.003 / 170.714 / 194.703 / 182.033 seconds** in successful [tooling run #40599282095](https://github.com/gamesbyian/UR-Recomp/actions/runs/40599282095), despite predicted scheduler loads of approximately **147 seconds each**. The current tracked `tools/unit_test_timings.json` has timings for **114 of 1,217 discovered modules** (1,103 were unmeasured). Four-way scheduling based on unmeasured 0.3s defaults is badly under-informed. Those shard durations are observational; differences may reflect host contention and suite dependencies as well as imperfect weights.

The original full suite, `unit` required check, up-to-four-worker bound and fail/skip semantics stay unchanged. `tools/run_unit_shard.py` wraps the same discovered module population in a **single global unittest runner** while measuring per-module import plus executed test-suite time. Each full worker produces `unit-module-timings-shardN.json`, with source SHA, module census, diagnostic-only classification and explicit pass/fail. The canonical summary/exit receipts remain the authority for unit-test CI. A compressed timing-only diagnostic is also visible in the Actions job log. Timing data is **not** a gameplay, original/native or release oracle.

After a successful full run, download the four timing sidecars from the existing `ci-tooling-unit-result` artifact. Extract them together and run:

```sh
python3 tools/rebalance_unit_test_timings.py \
  --source PATH_TO_EXTRACTED_TIMINGS \
  --source-sha EXACT_GITHUB_ACTIONS_CHECKOUT_SHA \
  --shards 4 \
  --out /tmp/unit_test_timings_candidate.json
```

The calibrator refuses missing, changed-source, failed, duplicated, unknown, nonfinite, symlinked, or partial module populations; it **never silently rewrites the tracked scheduling weights**. Review candidate weights, compare before/after shard wall times over more than one successful full-suite run, and only then replace `tools/unit_test_timings.json` in a reviewed PR. A single timing sample is not a defensible performance claim. A better split can reduce the straggler tail without deleting tests, new CI jobs, extra compilers, or wider runner usage. If timing collection changes a test outcome or is slower than the savings, revert to the original `python3 -m unittest` command; retain the original log/exit report invariant.

**First measured calibration, October 28 UTC:** Full, exact-source [PR #2734 tooling run #40606670548](https://github.com/gamesbyian/UR-Recomp/actions/runs/40606670548) completed with four green unit shards: **1,441 / 1,443 / 1,515 / 1,476 executed tests** (5,875 total), and **102.619 / 148.922 / 136.951 / 152.966 seconds** of worker test execution. All 1,217 measured module timing receipts passed the same-source/full-census calibrator. Under the *same observed module costs* and original deterministic four-way partitioner, prior membership's measured module sums are **103.38 / 149.58 / 137.61 / 153.59 seconds**; reassigning that exact population by the 1,217 measured weights gives estimated **136.04 seconds per shard**, an **estimated 17.55-second (11.4%) reduction of the longest measured module-load tail**. This is a *counterfactual partition estimate*, **not an observed CI speedup**, and it ignores import-order, runner/cache/host variability. The weight-only follow-up PR uses the exact retained candidate from this successful run, not a hand-tuned score. Review next full-suite run to establish an actual observed result before making any acceleration claim.


## 2026-10-28: source-verified QA01 native C/C++ compile-cache pilot

**Measured baseline, not a claimed outcome:** Exact genuine Zoo runs [#40604157122](https://github.com/gamesbyian/UR-Recomp/actions/runs/40604157122) (sequence 12) and [#40615839010](https://github.com/gamesbyian/UR-Recomp/actions/runs/40615839010) (sequence 13) required **371 s / 349 s** in the original/native *build* job, with the build step **335 s / 306 s**. Their single Zoo *case* jobs then took 226 s / 253 s, including actual 163 s / 206 s game execution. These are completed Actions job timings, not predicted future costs. The case runners independently rehash and execute the binaries, so each newly built toolset cost dominates repeat iterations.

**Smallest change:** The existing manual-only `.github/workflows/qa01-event-campaign.yml` build job now restores a bounded **ccache** object cache, enables it only as the native Baldosa CMake C/C++ compiler launcher (not the pinned original Snes9x core or snesref), and saves it best-effort after the source-pinned original/native binaries have been built and SHA-verified. All existing ROM and input provenance checks, strict original/native comparison, case fan-out, executable digest recheck and independent review requirements are unchanged. This is a toolchain-level accelerator, **not** gameplay evidence and not a substitute for one genuine new run.

**Cache correctness and scope:** ccache keys actual preprocessed C/C++ translation-unit contents, compiler identity and compile flags, and `CCACHE_COMPILERCHECK=content` is explicit. No unsafe sloppiness mode is enabled. A changed source or different observer/patch variant must miss and recompile its affected units. The GitHub cache lineage is restricted to Ubuntu 22.04, pinned upstream Baldosa prefix `10b864b9`, a hash of related patch tools, and bounded 256 MB local storage; per-run/attempt immutable save keys allow subsequent manual runs to restore most recent objects even across docs-only `main` commits. Corrupt, failed or inaccessible cache saves/restores do not prevent experiments from compiling from source. No caches are directly published or admitted as QA results.

**Evaluation at the next *already-needed* genuine Zoo A/B run:** Compare Actions **build-step seconds** and build-job total against the two baseline runs on similar Ubuntu 22.04 hosted runners. Parse `UR_QA01_NATIVE_CCACHE_STATS_BEGIN/END` counters (hits/misses), check the *real* SHA256SUMS and continued case-source validation, and record download/cache overhead. Only claim a speedup if total end-to-end time materially improves; use the standard runner, not a speculative research replay just to populate cache. If cache overhead outweighs compiler savings, causes build/CI failure, or consumes disproportionate free GitHub cache storage, revert this scoped pilot without touching game code.


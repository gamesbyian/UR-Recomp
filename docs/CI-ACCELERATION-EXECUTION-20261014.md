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

# Hybrid agent development and cumulative research runner policy

**Account-wide runner concurrency ceiling:** 20 across the owner's repositories. This is a concurrency limit, **not an allocation, reservation or guaranteed availability**. As of 2026-10-13, frontier experiments used a fixed four-shard maximum; this change introduces a user-selected **1 / 2 / 4 frontier shard ceiling**, default **2**, while retaining the same exact case populations, full source-bound receipts, seed policy, plan identity, three-frame exact fingerprint epoch and independent release constraints.

## Working default: four agents plus bounded research

Keep four independent agents working on **Modern native player journey; original/native QA-01/07 gameplay; source-faithful graphics/QA-08/10; independent integrated release QA**. Protect CI availability for their PR checks, fresh-process integrations and source-qualified comparative experiments. A typical frontier run using two experimental shards leaves headroom *under the account-wide 20-runner ceiling* but does not actually reserve slots, and reusable jobs/build steps may temporarily consume more than two. Do not assume different repositories are idle.

Use the cumulative coordinator [`.github/workflows/qa-cumulative-research.yml`](../.github/workflows/qa-cumulative-research.yml), on the latest merged `main`, for recorded cumulative experiments. Choose `frontier_parallel=2` when agents are active, `1` when PR integration is busy, or `4` during deliberate quieter campaigns. These settings limit **simultaneous frontier experiment matrix jobs**, not the candidate build, orchestration/aggregate steps, other campaigns, other repositories, or all account activity. The coordinator still serializes campaign reservations and pushes **across all families** for scientific ledger integrity: no parallel cumulative dispatches even if runner slots are free. Direct standalone workflows lack cumulative admission. Other campaign producer matrix limits remain their own source-defined ceilings.

| Operating condition | Action | Why |
| --- | --- | --- |
| Four agents generating short feedback loops and multiple open/red PRs | Default frontier at 1 or 2 shards **only if a new question is ready**; otherwise no factory | Avoid expensive, low-actionability queues |
| One research hypothesis has passed a 100-case new-observer pilot; useful source-truth question | 1,000-case cumulative frontier at 2 shards *only if sampling more inputs could answer it* | Provides broader source-field coverage without four busy research workers |
| Little development CI activity, no urgent integration | Deliberate long producer with at most 4 frontier experiment shards | Use capacity while respecting 20 account-wide and other repos |
| Multiple PRs need merge/fail repair, or strict original/native mismatch is actionable | Protect integration and gameplay-oracle capacity; finish current run, do **not** queue further campaigns | Producing another million fingerprints won't correct an independently observed mismatch |
| Two or more cumulative dispatches desired | **Queue serially** and inspect first receipt before next; don't bypass ledger single-writer | Unique seeds, stale-read detection and durable cumulative history |

Never cancel a healthy shard merely to save a few minutes; if a priority release check is blocked, stop new dispatches and let current finite shards finish. If severe operational incidents require cancellation, the experiment must record incomplete work honestly and may consume the reserved seed window. GitHub Actions concurrency groups protect named workflows, **not a cross-repository global runner budget**. There is no background autonomous global scheduler; see automatic admission control below for the per-dispatch check.

## Automatic admission control (2026-10-14)

The coordinator's `reserve` job now runs [`tools/research_admission.py`](../tools/research_admission.py) **before** any seed is reserved. It snapshots this repository's in-progress and queued Actions jobs with a read-only token, assumes **4 runners busy in unseen repositories** (a `GITHUB_TOKEN` cannot see them) and keeps **6 runners of agent headroom**. It then decides:

| Decision | When | Effect |
| --- | --- | --- |
| `admit` | spare ≥ the lane's peak runner need | exact request |
| `admit_downsized` | frontier only; spare < requested shard parallelism | lowers `frontier_parallel` 4→2→1. Cases, seeds and `plan_sha256` stay unchanged |
| `defer` | a non-matrix job has been queued ≥ 180 s; spare < peak need; a large campaign (> 240 expected runner-minutes, e.g. 1,000+ frontier cases or a 60-trial Windows soak) while > 4 jobs are active; or a scheduled run when capacity is unobservable | **no seed window, no ledger row**. Costs about one runner-minute. Summary and `qa-cumulative-admission` artifact state the reason |

Scheduled runs keep 2 extra runners of margin. Manual dispatch keeps `admission: auto` by default. `admission: force` is the explicit operator override; it records the snapshot and admits the exact request. Matrix siblings queued behind their own `max-parallel` are reported as `matrix_throttled_jobs`, not saturation. The 2026-10-14 02:18 UTC live snapshot showed **20 active jobs** in this repository alone plus 4 genuinely queued, so both scheduled and manual `auto` correctly deferred.

Admission is a point-in-time check, not a reservation. It cannot hold capacity for later jobs in the same run, and it cannot preempt anything. Once admitted, a run is never cancelled for capacity.

**Failure-aware fair rotation.** `auto` now picks the least-recently-recorded lane, with never-run lanes first. It skips a lane whose latest receipt failed while its producer files are unchanged (`producer_digest` in the plan and record, a scheduling heuristic only). Legacy failures without a digest rank after every healthy lane. If every lane is failing unchanged, automation stops red for investigation.

**Yield-aware rotation (`auto` only; explicit dispatch is never gated).** A lane is skipped when its next automatic run cannot change a decision:
* **Repetition lanes:** the cumulative zero-failure 95% bound has met the lane's target **and** the latest positive run used the current producer digest. Starting targets: fault-recovery 1e-4, graphics 1e-4, native-2p 1e-3, Windows 5e-3 per observation.
* **Frontier:** a completed run already exists with the current producer digest. Only a changed observer, plan or execution policy earns another (100-case) run.
* **Original-native and performance:** only failure-gated, because their meaning depends on guest code outside the digest.

When only yield gates remain, `auto` defers green and lists the reasons. On 2026-10-14 this rests fault-recovery: its bound is 8.0e-6 after 373,220 journeys.

**Measured cost.** Each new ledger record carries a signed `runner_usage` receipt measured from the run's own job timings, so yield can be expressed per runner-hour. Research producers also stopped running seven unrelated product-acceptance jobs: the shared candidate's new `candidate_only` input skips them. That saves 13–16 runner-minutes and a 7-runner burst per research run (measured on runs 38446393623, 38438864232 and 38434647895). It also prevents an unrelated red product gate from blocking research.

## Measured savings (2026-10-14)

The first 100-case frontier run with both `candidate_only` and turbo (run 38506108109) used **36.1 runner-minutes in total**. The two previous 100-case runs used 56.5 and 60.4, so it was **36–40% cheaper**.
* Product-acceptance jobs fell from 14.9–15.6 minutes to 0.
* Experiment shards fell from 36.2–40.3 minutes to 31.5.
* The peak burst at start fell from 8 runners to 1 (the build).

Its four rendered-repeat guards all passed in CI. The admission cost model now uses the measured 0.32 runner-minutes per frontier case.

## Measured load profile (24 h to 2026-10-14 02:45 UTC, this repository only)

295 runs, about 748 runner-minutes. 287 were pull-request runs.
* **Bursty:** zero jobs were running **68.5%** of the time, yet the peak reached **20 simultaneous jobs**, the whole account ceiling. A point-in-time admission check therefore catches most free troughs. Fixed reservations would waste them.
* **Research share:** the cumulative coordinator used 161 runner-minutes (22%) in 4 runs.
* **Largest avoidable cost is cancelled superseded work, not research.** The Modern native heavy router lost 59 of 87 minutes to cancellation (8 of 12 runs). Tooling unit tests lost 57 minutes across 52 cancelled runs. Rule 24 in `AGENTS.md` (publish one coherent edit instead of a rapid push chain) is the lever. Owners of those workflows decide any trigger changes.

Re-measure with the jobs API before changing these reserves; other repositories on the account remain unobserved.

## Scientific dispatch policy

An experimental factory is worth a runner slot if it has a falsifiable question, a current trusted observer, a source-bound producer, a measurable next-development decision and new source cases. Use **100 cases to validate modified instrumentation**, larger batches only after a substantive source-truth signal. Keep exact normalized fingerprint novelty distinct from real original/native gameplay correctness.

The [15-frame original-source observer report](QA-FRONTIER-15-FRAME-RESULTS-20261013.md) already demonstrated 29 extra opposing-X and 5 extra rotation feature cases, plus a raw simultaneous-air witness. Two offscreen-candidate bytes stayed zero and the second-camera-enable byte stayed one; source archaeology provides better independent PPU/visibility targets than brute-force repetition. **Do not run a 10,000-case frontier now.** Prioritize actual original/native event acceptance and integrated Windows 1P/2P results/Records. The previous `original-native` cumulative invocation was recorded `incomplete_or_failed` with missing producer aggregate: inspect the failure path before spending more on that same producer.

Use the four ownership lanes in `AGENTS.md` and the live `docs/WORK-QUEUE.md`. An agent waiting for CI should switch to research, tests, proof preparation or independent tasks within their lane; never babysit queued runs. Where all safe work has exhausted, stop and let the owner provide run completion. Never modify another lane's owned guest/render/product/release authority files to make a research metric green.

## Verification of the knob

`frontier_parallel` is only scheduling policy, deliberately outside the scientific `plan_sha256`. The research plan retains the previously approved ceiling `max_parallel:4` as an **upper bound**; actual allowed experiment concurrency is constrained by the runtime workflow input. Thus toggling 1/2/4 does not silently change expected seeds, arm assignment, or the exact native-fingerprint epoch. A workflow unit contract asserts bounded choices and coordinator forwarding. A live **100-case** run on merged `main` at `frontier_parallel=2` is sufficient to validate dispatch mechanics if needed later; it will still cost genuine native experiments and should not be run solely because this documentation changed.

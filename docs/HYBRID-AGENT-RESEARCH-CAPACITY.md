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

Never cancel a healthy shard merely to save a few minutes; if a priority release check is blocked, stop new dispatches and let current finite shards finish. If severe operational incidents require cancellation, the experiment must record incomplete work honestly and may consume the reserved seed window. GitHub Actions concurrency groups protect named workflows, **not a cross-repository global runner budget**. There is no background autonomous global scheduler in this change.

## Scientific dispatch policy

An experimental factory is worth a runner slot if it has a falsifiable question, a current trusted observer, a source-bound producer, a measurable next-development decision and new source cases. Use **100 cases to validate modified instrumentation**, larger batches only after a substantive source-truth signal. Keep exact normalized fingerprint novelty distinct from real original/native gameplay correctness.

The [15-frame original-source observer report](QA-FRONTIER-15-FRAME-RESULTS-20261013.md) already demonstrated 29 extra opposing-X and 5 extra rotation feature cases, plus a raw simultaneous-air witness. Two offscreen-candidate bytes stayed zero and the second-camera-enable byte stayed one; source archaeology provides better independent PPU/visibility targets than brute-force repetition. **Do not run a 10,000-case frontier now.** Prioritize actual original/native event acceptance and integrated Windows 1P/2P results/Records. The previous `original-native` cumulative invocation was recorded `incomplete_or_failed` with missing producer aggregate: inspect the failure path before spending more on that same producer.

Use the four ownership lanes in `AGENTS.md` and the live `docs/WORK-QUEUE.md`. An agent waiting for CI should switch to research, tests, proof preparation or independent tasks within their lane; never babysit queued runs. Where all safe work has exhausted, stop and let the owner provide run completion. Never modify another lane's owned guest/render/product/release authority files to make a research metric green.

## Verification of the knob

`frontier_parallel` is only scheduling policy, deliberately outside the scientific `plan_sha256`. The research plan retains the previously approved ceiling `max_parallel:4` as an **upper bound**; actual allowed experiment concurrency is constrained by the runtime workflow input. Thus toggling 1/2/4 does not silently change expected seeds, arm assignment, or the exact native-fingerprint epoch. A workflow unit contract asserts bounded choices and coordinator forwarding. A live **100-case** run on merged `main` at `frontier_parallel=2` is sufficient to validate dispatch mechanics if needed later; it will still cost genuine native experiments and should not be run solely because this documentation changed.

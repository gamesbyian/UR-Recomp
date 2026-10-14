# Cumulative research program (seven source-bound campaigns)

**Status:** CI-only orchestration. Research observations are not gameplay-release gates and never alter `RELEASE-QUALITY-LEDGER.json`. The [single entry point](../.github/workflows/qa-cumulative-research.yml) makes every experiment leave an append-only source- and run-linked receipt; the mutable ledger lives on branch `research/qa-cumulative-ledger`, path `.github/qa-cumulative/ledger.json`, **not on `main`**. Do not delete that branch or force-push its history.

## The seven independent campaigns

| Coordinator selection | What is actually executed | What cumulative coverage means | Does not prove |
| --- | --- | --- | --- |
| `native-2p` | Original established native shared binary, seeded fresh P1/P2 inputs, identical replay and independent seat-removal checks | Unique deterministic seed windows and real guest-WRAM comparison counts on exact source/build | Strict equality to original SNES gameplay; a completed event |
| `windows` | Existing exact Windows Baldosa guest/pause/profile/recovery and ROMless launcher cohorts; fresh separate OS processes | Additional *repeated durability* samples on named exact candidate, not distinct input trajectories | Complete integrated Modern results-to-Records, physical gamepads |
| `fault-recovery` | Original production-store C09 orphan, C14/C15 receipt, QA03 midseries, real OS hard-kill and C16 storage outage oracles | Fresh 0–8 ms interprocess scheduling seeds, real source-owned fault batches on isolated roots | Device power-cuts or game-played results |
| `graphics` | New **actual native rendered frame consistency**: varied legal two-seat input to the existing race, rerun product with identical input and compare each retained framebuffer and guest-WRAM file bit for bit | New unique seeded visual-input stream; retained source-bound pixel/W RAM frame comparisons | Independent original PPU/OAM truth, correctness of HD art or physical 4K |
| `performance` | New **single-process long-horizon native guest** (over 40k additional guest frames), authentic 2P controls, periodic real Linux `/proc/PID` resident-memory and descriptor sampling | More fresh uninterrupted processes and actual measured process seconds/peak RSS/fds, not 40k fake clicks | Benchmarked 4K GPU throughput, Windows memory leaks, physical power use |
| `original-native` | Existing strict QA-01 original/native Zoo, Bowl, Switcher comparison, untouched comparator and evidence | A new **exact build/revision** scientific observation, often a strict divergence again. The original movies are fixed; a rerun on same code does **not** add new course trajectories | Release admission, source equality unless explicitly strictly accepted and independently adjudicated |
| `frontier` | 100 / 1,000 / 10,000 source-qualified real native 2P input trajectories, checkpoint fingerprints and 25-case deterministic/seat-mute interventions | Exact deduplicated normalized fingerprint identities and reproducible first-source witnesses; five-arm trial allocation | Original emulator parity, complete accepted events or semantic meaning of every new fingerprint |

For future cases not yet supported by source-owned original/native fixtures, don't count "all 45 events" just by looping over names. A strict source comparator's negative result is recorded as `strict_divergence` with **zero release credit**, even when the runner/transport reports green.

**Hybrid runner allocation:** see [four-agent and research capacity policy](HYBRID-AGENT-RESEARCH-CAPACITY.md). The frontier coordinator now exposes `frontier_parallel=1/2/4` (default `2`) to limit simultaneous experiment shards while the account's 20-runner maximum also serves other agents and repositories. It does not change scientific fingerprints or allow concurrent cumulative ledger writes. The single-writer coordinator still serializes all seven campaigns.

## How to run and continue

Use **Actions → Cumulative research campaigns (seven independent lanes) → Run workflow** on `main`. Select `auto` for the next lane in the rotation, or name a specific lane. Configure one bounded native workload per-shard budget (`15`, `60`, `120` minutes) and the Windows existing original-producer repetitions (`1`, `3`, `10`, `30`, `60`). The default is **15 minutes / 3 Windows repeats** for initial smoke. Existing standalone workflows remain available for diagnostics, but **their direct dispatches do not advance the cumulative ledger**. Always use the coordinator for cumulative testing.

**Original/native failure triage (2026-10-13):** The latest recorded original-native coordinator attempt, [38446280858](https://github.com/gamesbyian/UR-Recomp/actions/runs/38446280858), has a historical `incomplete_or_failed` record and a generic `original workflow or aggregate unavailable` reason. GitHub returned 404 for that run, its jobs and its artifacts during follow-up, so the exact failing child step could not be independently recovered. Do not treat this as a confirmed guest mismatch, or commission another long campaign based on an undifferentiated failure. Future original-native receipts now distinguish **a nonsuccess reusable job**, with its actual `needs.original-native.result`, from **a successful reusable job with a missing aggregate**, recording whether the expected aggregate was present. Neither classification fabricates the first failing child step, accepts a course, retries a consumed seed or changes prior signed ledger records. For detailed case diagnosis, examine child `plan → build → cases → aggregate` and the exact `qa01-campaign-aggregate/campaign-result.json` before choosing the smallest next experiment. **From 2026-10-14 the receipt itself preserves the diagnosis.**
* `runner_usage.failed_jobs` names each failed or cancelled child job and its first failed step. It is captured when the record is written, so it survives later deletion of the run (38446280858 later returned 404).
* A failed run's source-bound aggregate is kept as an uncredited `metrics.diagnostic`: per-case dispositions and reasons. For example, two valid strict divergences beside one producer error are no longer discarded wholesale.
* None of this counts cases or changes the disposition.

A conservative **twice-weekly Tuesday/Friday 09:17 UTC** scheduler chooses the least-recently-recorded eligible lane (failure-aware fair rotation) and passes [runner-aware admission](HYBRID-AGENT-RESEARCH-CAPACITY.md#automatic-admission-control-2026-10-14) before reserving seeds; a deferred run consumes nothing. Only one coordinator run can reserve/write at a time, across all refs, and it never cancels an in-flight experiment. Scheduled runs use the 15-minute native budget and 3-repeat Windows budget. The runner always records actual work, not an artificially slept time target. Expensive two-hour campaigns remain manual, not automatically launched every day.

Every *admitted* run (including red runs) follows **admit → reserve → exact source-owned producer → inspect aggregate → append ledger**. Deferred runs stop at admission and never touch the ledger. Reservation captures the old ledger digest, exact commit SHA and GitHub run ID; the next seed range is `50,000,000 + sequence*12,000` (8 digits, bounded at 4,084 new runs per lane). The 12k window is larger than the 3k two-seat/native case cap; different shards have separate 1,000,003 offsets. The offset modulo 12,000 is 4,003, strictly larger than the maximum 2,999-case input-index difference, so even across different coordinator runs, neither P1/P2 shard can reuse another shard's numbered seed. For cumulative fault-recovery jobs, internal micro-timing seeds use a bijective (base, suite, chunk) namespace, while the older 20261011-style seed remains reproducible. A failed run **consumes** its window and is never quietly repeated as new evidence. Legacy historical records are adopted without claiming all past seeds were disjoint: the original 15- and 120-minute native runs reused the same seed, so the 15-minute cases partly overlap the longer run.

The coordinator fetches the **source workflow's actual machine aggregate**, rejects wrong source/ROM/build identity and inconsistent counts, records only permitted positive research counts, and explicitly retains incomplete, producer-negative and false-credit assertions as **red** ledger rows. It commits a normally pushed, non-force Git revision to the evidence branch. It uploads a separate compact Actions final receipt; if the Git push fails, the workflow goes red. **Do not treat an uncommitted/failed ledger run as cumulatively recorded, and repair its push before trusting the next automatic allocation.** Never force-push, reset or rebase the evidence branch while a coordinator is active.

## Exact discovery accounting (frontier only)

Beginning with the first post-upgrade *completed* adaptive-frontier producer, the separate `frontier_exact_coverage` ledger contains the **losslessly deduplicated normalized fingerprint census and earliest run/seed/arm/shard witness**. Per-run metrics expose `exact_prior_unique_fingerprints`, `exact_new_unique_fingerprints` and `exact_post_unique_fingerprints`. Old HLL-only observations are explicitly **excluded from this new exact corpus**, not retroactively invented. Malformed, missing or contradictory source witnesses reject the run without granting novelty.

The earlier `frontier_coverage` HyperLogLog numbers remain estimates for legacy review only. A lossless 96-bit fingerprint census is still an observation of projected native WRAM fields, **never strict original/native correctness or full raw gameplay-state enumeration**. See [adaptive frontier](QA-ADAPTIVE-RESEARCH-FRONTIER.md) for limits, migration, hard capacity bound and the original-reference follow-up cycle.

**First exact frontier field result:** [2026-10-13 postmortem](QA-FRONTIER-10000-POSTMORTEM-20261013.md) documents the complete 10,000-case run, 19,978 new fingerprint identities, exact 20,179 cumulative union, five raw source-feature categories seen, three unseen, and the strategy starvation corrected in the source plan. It does not grant release credit. The recommended next run is a fresh 100-case policy smoke from merged `main`, not an automatic repeat of 10,000 inputs.

**Policy-validation run:** the [100-case 2026-10-13 experiment](https://github.com/gamesbyian/UR-Recomp/actions/runs/38438864232) validated all five strategies on the real source-bound guest, with exact cumulative normalized fingerprint union **20,379**. Its feature zeros motivate the [all-15-existing-checkpoint raw-observer follow-up](QA-FRONTIER-15-FRAME-OBSERVER-20261013.md). Future producer and coordinator receipts separately retain `full_trace_feature_counts`, `full_trace_only_feature_counts`, first source-frame witnesses and raw field-value populations. The original three-frame fingerprint corpus remains the strict comparable census; do not merge additional frame fingerprints into it silently.

## Scientific yield, escalation and stopping (2026-10-14)

[`tools/research_yield.py`](../tools/research_yield.py) derives a read-only yield view from the signed ledger. Every coordinator receipt summary now includes it. Applied to the real ledger on 2026-10-14 (12 records, 10,300 frontier cases):

* **Exact fingerprint novelty is non-saturating.** Every run produced 1.998–2.01 new fingerprints per case. Checkpoint 1740 is identical in all cases, and checkpoints 2580/3420 are unique in every case. The census restates the case count and can **never** signal progress or justify more volume. Keep it as a lossless identity index only.
* **Strategy and observer beat volume.** `both-air-raw` was **0/10,000** under the arm-starved 3-checkpoint run 38306802282. It was 1/100 in run 38446393623 after the arm fix: seed 50036056, `rotation`, frame 2580. Opposing-X incidence was 64–72% at three checkpoints but 100% at fifteen. Incidence is observer- and policy-relative, so pooled counts are not rates.
* **Four of eight feature classes carry no information** on this fixture. Two are ubiquitous (`both-moving-raw`, `split-register-nonzero` in 10,300/10,300 cases). Two are never observed (`offscreen-register-nonzero`, `split-register-changes`: per-case 95% bound < 0.0291%). The 15-frame report already explains why more inputs cannot change them.
* **Repetition lanes buy durability bounds, not states.** With zero failures, rates are bounded below: fault recovery < 0.0018% per journey (169,510), graphics < 0.0154% per frame check, native 2P < 0.40% per process, Windows < 1.9% per journey (160). Each halving of the bound costs a doubling of trials.

**Escalation rules** (`frontier_recommendation`):

| Size | Admissible only when | Never for |
| --- | --- | --- |
| 100 | an observer, arm policy or plan changed and must be validated on real native cases | repeating an unchanged plan |
| 1,000 | a *named* feature plus a *named* consumer question that current evidence cannot decide: an absence bound above the consumer threshold, or a consumer that needs a rare feature's rate in the **latest same-observer cohort** | fingerprint growth; a rare feature whose existing witness has not yet been reproduced against the original oracle |
| 10,000 | 1,000 cases in that cohort left the feature rare (≤3) or the bound still above threshold, **and** admission finds a quiet period. Run as ten 1,000-case batches | features that source analysis says the fixture cannot produce |

**Stop** when the next size cannot change a decision:
* the absence bound is already at or below the consumer threshold;
* a rare feature has a reproducible witness (hand it to the owning lane; QA-01 owns original/native adjudication);
* only fingerprints would grow.

Default today: **no frontier run is recommended**. The next useful work is reproducing witness 50036056 against the original emulator (owned by QA-01, not by more volume) and a source-qualified visibility observer (QA-08). Then a 100-case pilot of that observer.

## What to compare

For analysis, group cumulative evidence by **campaign, exact code revision and binary digest**, and then distinguish input trajectories from repeated processes. Coverage grows across revisions, but a new build requires new acceptance for that exact build. Summing Windows producer repetitions is legitimate durability evidence; calling them all "new gameplay states" is false. Reports always keep raw GitHub run ID, original aggregate SHA-256, observed trial/sample counts and zero release credit.

Research ledgers are not a substitute for the independent QA-01/08/10 acceptance authorities or the adversarial Windows release ledger. An intentionally different source revision cannot borrow a preceding binary's pass. Failures should be investigated/reproduced by their retained seed/run/source before resuming automated escalation.

## Operations and responsibility boundaries

- Keep the ledger branch under write protection against accidental force-push and deletion; its Git history is the durable audit trail. GitHub Actions `contents: write` is used **only** by the coordinator to append to this branch.
- Workloads do not modify original native guest, graphics correctness, Baldosa Modern frontend/storage implementation or QA ownership. All visual/source claims follow the existing 4:3 regression and QA-08/10 gates; the new graphic cohort checks deterministic replay only.
- Two weekly automatic dispatches, one serialized coordinator, and per-existing-shard concurrency limits avoid a runaway CI queue. Expensive launches remain deliberate and can be turned off by editing the workflow schedule.
- The standalone `qa02-native-2p-seeded-endurance`, `baldosa-windows-reliability-campaign`, `qa02-real-fault-endurance`, `qa01-event-campaign`, and `qa-cumulative-native-metrics` workflows may still be run for non-cumulative targeted investigation. Do not mix direct-run statistics with the committed cumulative totals without identifying and deduplicating them.

**Initial historical baselines adopted:** 22 + 165 original/native seed scenarios (with acknowledged overlap), 40 + 120 repeated Baldosa Windows journeys, and 169,510 production-store fault journeys. These are referenced by original GitHub run ID and SHA and carry explicit `origin: adopted`; they are never falsely attributed to newly executed coordinator work.

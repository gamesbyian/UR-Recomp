# Cumulative research program (six source-bound campaigns)

**Status:** CI-only orchestration. Research observations are not gameplay-release gates and never alter `RELEASE-QUALITY-LEDGER.json`. The [single entry point](../.github/workflows/qa-cumulative-research.yml) makes every experiment leave an append-only source- and run-linked receipt; the mutable ledger lives on branch `research/qa-cumulative-ledger`, path `.github/qa-cumulative/ledger.json`, **not on `main`**. Do not delete that branch or force-push its history.

## The six independent campaigns

| Coordinator selection | What is actually executed | What cumulative coverage means | Does not prove |
| --- | --- | --- | --- |
| `native-2p` | Original established native shared binary, seeded fresh P1/P2 inputs, identical replay and independent seat-removal checks | Unique deterministic seed windows and real guest-WRAM comparison counts on exact source/build | Strict equality to original SNES gameplay; a completed event |
| `windows` | Existing exact Windows Baldosa guest/pause/profile/recovery and ROMless launcher cohorts; fresh separate OS processes | Additional *repeated durability* samples on named exact candidate, not distinct input trajectories | Complete integrated Modern results-to-Records, physical gamepads |
| `fault-recovery` | Original production-store C09 orphan, C14/C15 receipt, QA03 midseries, real OS hard-kill and C16 storage outage oracles | Fresh 0–8 ms interprocess scheduling seeds, real source-owned fault batches on isolated roots | Device power-cuts or game-played results |
| `graphics` | New **actual native rendered frame consistency**: varied legal two-seat input to the existing race, rerun product with identical input and compare each retained framebuffer and guest-WRAM file bit for bit | New unique seeded visual-input stream; retained source-bound pixel/W RAM frame comparisons | Independent original PPU/OAM truth, correctness of HD art or physical 4K |
| `performance` | New **single-process long-horizon native guest** (over 40k additional guest frames), authentic 2P controls, periodic real Linux `/proc/PID` resident-memory and descriptor sampling | More fresh uninterrupted processes and actual measured process seconds/peak RSS/fds, not 40k fake clicks | Benchmarked 4K GPU throughput, Windows memory leaks, physical power use |
| `original-native` | Existing strict QA-01 original/native Zoo, Bowl, Switcher comparison, untouched comparator and evidence | A new **exact build/revision** scientific observation, often a strict divergence again. The original movies are fixed; a rerun on same code does **not** add new course trajectories | Release admission, source equality unless explicitly strictly accepted and independently adjudicated |

For future cases not yet supported by source-owned original/native fixtures, don't count "all 45 events" just by looping over names. A strict source comparator's negative result is recorded as `strict_divergence` with **zero release credit**, even when the runner/transport reports green.

## How to run and continue

Use **Actions → Cumulative research campaigns (six independent lanes) → Run workflow** on `main`. Select `auto` for the next lane in the rotation, or name a specific lane. Configure one bounded native workload per-shard budget (`15`, `60`, `120` minutes) and the Windows existing original-producer repetitions (`1`, `3`, `10`, `30`, `60`). The default is **15 minutes / 3 Windows repeats** for initial smoke. Existing standalone workflows remain available for diagnostics, but **their direct dispatches do not advance the cumulative ledger**. Always use the coordinator for cumulative testing.

A conservative **twice-weekly Tuesday/Friday 09:17 UTC** scheduler chooses the next lane in the six-family rotation. Only one coordinator run can reserve/write at a time, across all refs, and it never cancels an in-flight experiment. Scheduled runs use the 15-minute native budget and 3-repeat Windows budget. The runner always records actual work, not an artificially slept time target. Expensive two-hour campaigns remain manual, not automatically launched every day.

Every run (including red runs) follows **reserve → exact source-owned producer → inspect aggregate → append ledger**. Reservation captures the old ledger digest, exact commit SHA and GitHub run ID; the next seed range is `10,000,000 + sequence*10,000` (8 digits, bounded at 8,000 new runs per lane). The 10k window is larger than the 3k two-seat/native case cap; different shards have separate 1,000,003 offsets. A failed run **consumes** its window and is never quietly repeated as new evidence. Legacy historical records are adopted without claiming all past seeds were disjoint: the original 15- and 120-minute native runs reused the same seed, so the 15-minute cases partly overlap the longer run.

The coordinator fetches the **source workflow's actual machine aggregate**, rejects wrong source/ROM/build identity and inconsistent counts, records only permitted positive research counts, and explicitly retains incomplete, producer-negative and false-credit assertions as **red** ledger rows. It commits a normally pushed, non-force Git revision to the evidence branch. It uploads a separate compact Actions final receipt; if the Git push fails, the workflow goes red. **Do not treat an uncommitted/failed ledger run as cumulatively recorded, and repair its push before trusting the next automatic allocation.** Never force-push, reset or rebase the evidence branch while a coordinator is active.

## What to compare

For analysis, group cumulative evidence by **campaign, exact code revision and binary digest**, and then distinguish input trajectories from repeated processes. Coverage grows across revisions, but a new build requires new acceptance for that exact build. Summing Windows producer repetitions is legitimate durability evidence; calling them all "new gameplay states" is false. Reports always keep raw GitHub run ID, original aggregate SHA-256, observed trial/sample counts and zero release credit.

Research ledgers are not a substitute for the independent QA-01/08/10 acceptance authorities or the adversarial Windows release ledger. An intentionally different source revision cannot borrow a preceding binary's pass. Failures should be investigated/reproduced by their retained seed/run/source before resuming automated escalation.

## Operations and responsibility boundaries

- Keep the ledger branch under write protection against accidental force-push and deletion; its Git history is the durable audit trail. GitHub Actions `contents: write` is used **only** by the coordinator to append to this branch.
- Workloads do not modify original native guest, graphics correctness, Baldosa Modern frontend/storage implementation or QA ownership. All visual/source claims follow the existing 4:3 regression and QA-08/10 gates; the new graphic cohort checks deterministic replay only.
- Two weekly automatic dispatches, one serialized coordinator, and per-existing-shard concurrency limits avoid a runaway CI queue. Expensive launches remain deliberate and can be turned off by editing the workflow schedule.
- The standalone `qa02-native-2p-seeded-endurance`, `baldosa-windows-reliability-campaign`, `qa02-real-fault-endurance`, `qa01-event-campaign`, and `qa-cumulative-native-metrics` workflows may still be run for non-cumulative targeted investigation. Do not mix direct-run statistics with the committed cumulative totals without identifying and deduplicating them.

**Initial historical baselines adopted:** 22 + 165 original/native seed scenarios (with acknowledged overlap), 40 + 120 repeated Baldosa Windows journeys, and 169,510 production-store fault journeys. These are referenced by original GitHub run ID and SHA and carry explicit `origin: adopted`; they are never falsely attributed to newly executed coordinator work.

# Research findings queue: classify by consequence, not by volume

**Classification:** research triage only. It never changes the strict comparator, the [release ledger](RELEASE-QUALITY-LEDGER.json) or any implementation lane's acceptance authority. The machine-readable register is [`analysis/data/research-findings-register.json`](../analysis/data/research-findings-register.json), validated by [`tools/research_findings.py`](../tools/research_findings.py) (`--queue` prints the live table). [Cumulative research](QA-CUMULATIVE-RESEARCH.md) owns campaign mechanics; this page owns *what the outputs mean and who should act*.

## Significance classes

Ordered by decision value. A finding is triaged in this order, whatever computation produced it.

| Class | Meaning | Admission rule enforced by the validator |
| --- | --- | --- |
| `original_native_discrepancy` | Original and native differ under the same race-relative input | Needs original **and** native evidence and a declared race-relative lag |
| `source_backed_behaviour` | A state transition or behaviour confirmed by the original or by recovered source | — |
| `untested_circumstance` | A gameplay circumstance no oracle has exercised | — |
| `graphics_observation_gap` | A PPU/visibility fact current observers cannot see | — |
| `windows_durability` | A Windows durability or recovery defect, or a bound on one | — |
| `reproducible_anomaly` | Reproducible but unexplained | — |
| `method_hazard` | An experimental design error that would mislead a consumer | — |
| `fingerprint_novelty` | Native fingerprint novelty with no shown consequence | Can never be an open assignment or have an owner |

Every finding names an exact reproducer command, its source artifacts (run IDs, executable/ROM digests, census tokens), the remaining uncertainty, the owning lane and **one** resolving experiment. A closed finding records its resolution; a handoff names the receiving implementation lane.

## Race-relative alignment is mandatory for original/native replay

The ordinary 2P route enters the race on different absolute host frames in different runtimes ([staircase](TWO-PLAYER-FIXTURE-PLAN.md): Beetle 1133, Snes9x 1134, generic native 1135). Feeding identical absolute-frame input to both and comparing the same host frame therefore compares different race ticks, and the `82:A5F3` scheduler-parity gate turns that into real kinematic differences. The ordinary 2P regression already corrects this with a measured +1 shift. **Any** new original/native replay must do the same, with a lag measured *before* evaluation and never searched per case (RF-002, RF-003).

## Original-emulator cross-check of the native frontier census (2026-10-14)

[`tools/qa_frontier_original_crosscheck.py`](../tools/qa_frontier_original_crosscheck.py) turns the signed native census into original/native comparisons **without launching a native process**. For each census case it regenerates the exact controller stream from the pinned planner, shifts post-entry events by the declared lag, replays the original USA ROM in Snes9x (about 3 s per case, local or CI), and tests whether the original reaches the same 96-bit normalized fingerprint at the race-relative-equivalent frame. It also reruns the frontier's raw feature observer on the original's 15 equivalent frames, and a source-qualified opponent-offscreen observer (bank-82 sentinels `0x70/0x70` and `0x30/0x30`).

**Design, declared before evaluation.** `calibrate` measures Snes9x entry (1134) and tests each lag on the single seed-independent 1740 token: lags 0 and 2 survive, 1 does not (equal scheduler parity cannot be separated by one sample). The first 10 cases of run 38506108109 were the exploration set: L=2 agreed at 2580 and 3420 in 10/10, L=0 in 9/10, L=1 in 0/10. **L=2 was then fixed** for every other case.

| Native run (executable) | Cases | Coarse agreement | Divergent | Feature counts original vs native |
| --- | ---: | ---: | ---: | --- |
| 38506108109 (`f2ba2849…`), incl. 10 exploration | 100 | 100 | 0 | identical in every class |
| 38446393623 (`28501fa3…`), held out, incl. dual-air witness | 100 | 100 | 0 | identical, both-air 1 / 1 |
| RESULTS_PENDING | | | | |

A coarse agreement is equality of the quantized census fields (position/64 and /32, velocity/64, rotation/16, raw air, split, offscreen, race progress), **not** strict equality, event acceptance or release credit. It is nonetheless a large-population, independently-reproducible original/native comparison of random legal 2P trajectories, which the project did not have before. A divergent case would become an `original_native_discrepancy` candidate with an exact seed, arm and first divergent checkpoint.

**The dual-air witness is resolved (RF-001).** At native-equivalent 2580 the original has P1 air 1 and P2 air 2; one frame earlier P2 alone is 1; one frame later both are 0. It is a one-frame simultaneous hop that the 120-frame sampler happened to catch, reproduced by the original game. It is not a discrepancy and needs no QA-01 event work.

## Live queue

Generate with `python3 tools/research_findings.py --queue`. As of 2026-10-14:

| ID | Class | Owner | What would resolve it |
| --- | --- | --- | --- |
| RF-003 | source_backed_behaviour | research | Dense 1128–1140 entry probe of a Modern native: expect first `inRace=1` at 1136 |
| RF-004 | untested_circumstance | research | Finish the census cross-check; bisect any divergent seed densely |
| RF-005 | graphics_observation_gap | qa08-graphics | Replace the dead `$121B/$121D` predicate with the bank-82 sentinel observer, only if QA-08 names a question |
| RF-008 | reproducible_anomaly | qa01-gameplay | One single-case `qa01-event-campaign.yml` dispatch before any long original-native campaign |
| RF-002 | method_hazard | qa01-gameplay | Treat run 38509912672's same-host dual-air verdict as phase-confounded |

Closed and retired items (dual-air witness, `$0DDB`, sparse sampling, Windows and fault-recovery bounds, fingerprint census) stay in the register with their resolutions so they are not reopened by volume.

## Next experiments, in priority order

1. **Divergence hunting with original-side mutation, not native volume.** The original side costs about 3 s per case and needs no runner. Use it to search *for* disagreement: denser equivalent-frame observation (every 8 frames) and full-precision rather than quantized fields, against a locally or CI-built Modern native at the same race-relative alignment. Stop when a divergence is found (hand it to QA-01 with a bisect) or when a pre-declared population (1,000 cases) agrees.
2. **Rare-state targeting.** Seed the planner with input prefixes from the agreed original trajectories that reached rare states (the dual-air hop, opponent-offscreen sentinels) and branch from there; selection decisions are recorded, and both engines replay the same recorded inputs, so the selector never defines correctness.
3. **Regional/second-route coverage** only after a second source-qualified 2P route exists; the frontier currently varies input on one course and one mode.

No new GitHub Actions campaign is recommended by this result. The original side runs locally; a CI version would be one job per 1,000 cases with no native build, if a reviewer wants hosted provenance.

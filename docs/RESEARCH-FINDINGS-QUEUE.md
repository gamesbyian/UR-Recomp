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
| 38438864232, held out (3-frame observer) | 100 | 100 | 0 | original incidence recorded |
| 38304551380, held out (3-frame observer) | 100 | 100 | 0 | original incidence recorded |
| 38306802282 (`28501fa3…`), 10,000 cases | — | — | — | **running**; resumable journal, results to follow |

A coarse agreement is equality of the quantized census fields (position/64 and /32, velocity/64, rotation/16, raw air, split, offscreen, race progress), **not** strict equality, event acceptance or release credit. It is still a large-population, independently reproducible original/native comparison of random legal 2P trajectories, which the project did not have before. A divergent case would become an `original_native_discrepancy` candidate with an exact seed, arm and first divergent checkpoint.

**The dual-air witness is resolved (RF-001).** At native-equivalent 2580 the original has P1 air 1 and P2 air 2; one frame earlier only P2 is airborne (air 1); one frame later both are 0. It is a one-frame simultaneous hop that the 120-frame sampler happened to catch, and the original game reproduces it. It is not a discrepancy and needs no QA-01 event work.

## Exact paired original/native comparison (2026-10-14)

`paired` mode runs a real native executable beside the reference emulator. It **measures** each side's race entry (first `inRace=1`) and compares every decoded source field plus every WRAM byte at `$0200+` at native frame F against reference frame F−lag. The native side was a current-`main` Modern candidate (`fda6ace`, executable `4c1c8b56…`), built locally with the `modern-shared-native-acceptance.yml` recipe. Evidence: [`analysis/data/frontier-original-native-race-relative-20261014.json`](../analysis/data/frontier-original-native-race-relative-20261014.json).

* **Entry (RF-003, resolved):** native 1136, Snes9x 1134 and pinned Beetle-bsnes 1134 in every case. The lag of 2 is measured per case, not assumed. When a wrong lag was declared for Beetle, the tool flagged it rather than reporting a divergence.
* **Mid-race:** 26 of 26 cases (5 per arm from three held-out runs, plus the witness) show **zero** differing fields and **zero** differing semantic WRAM bytes at 30-frame spacing from 1620 to 3420. The witness was also checked at every frame from 2570 to 2590. In total 39,747 race-relative frames were compared across all paired runs.
* **Race terminal (RF-012, handed to QA-01):** a declared both-Right finish stimulus completes the ordinary 2P race in about 1,500 extra frames. In 9 of 9 seeds, state stays identical through both laps reaching 0 and through the onset of result menu `0x84`. The `0x84` phase then lasts **34 frames on Snes9x and on Beetle-bsnes, but 35 on native** (36 for seed 50024003). Every later difference follows the reference's `0x16` restoration. This is the same `Sram_RestoreDirectPage` (`83:988A`) handoff behind QA-01's open 1P Switcher strict divergence, where the original's phase is also 34 frames. It is now a 70-second deterministic 2P reproducer with two independent reference cores.

What this means for the frontier: on this route, native frontier states correspond exactly to original states for the whole race. Native fingerprint novelty here is therefore authentic original-game state novelty. But more random mid-race input will not find discrepancies. The measured discrepancy surface is the **transitions**: entry phase and the result handoff.

## Live queue

Generate with `python3 tools/research_findings.py --queue`. As of 2026-10-14:

| ID | Class | Owner | What would resolve it |
| --- | --- | --- | --- |
| RF-012 | original_native_discrepancy | qa01-gameplay | Trace native `7E:009F`/restore writers at native 5230–5234 on the 2P reproducer against the original `83:988A` opcode trace |
| RF-004 | untested_circumstance | research | Finish the 10,000-case census cross-check; bisect any divergent seed densely |
| RF-005 | graphics_observation_gap | qa08-graphics | Replace the dead `$121B/$121D` predicate with the bank-82 sentinel observer, only if QA-08 names a question |
| RF-008 | reproducible_anomaly | qa01-gameplay | One single-case `qa01-event-campaign.yml` dispatch before any long original-native campaign |
| RF-002 | method_hazard | qa01-gameplay | Treat run 38509912672's same-host dual-air verdict as phase-confounded |

Closed and retired items (dual-air witness, `$0DDB`, sparse sampling, Windows and fault-recovery bounds, fingerprint census) stay in the register with their resolutions so they are not reopened by volume.

## Next experiments, in priority order

1. **Terminal-phase population (research, local or one CI job).** Run the finish stimulus on 100 seeds with both reference cores. Record the result-phase duration distribution and its dependence on finish state (who wins, the frame margin, laps-zero parity). That turns RF-012 from "9 of 9" into a measured rate and tells QA-01 whether the extra frame tracks scheduler parity. Stop at 100: the question is the mechanism, not a tighter rate.
2. **Entry-phase invariance check (research).** Vary the pre-entry menu route timing by a few frames and confirm the measured lag stays 2. If it does not, every race-relative comparison must measure its lag per case, as `paired` already does.
3. **Rare-state branching.** Branch new inputs from agreed original trajectories that reached rare states (the dual-air hop, opponent-offscreen sentinels). Record each selection decision and replay the same recorded input on both engines, so the selector never defines correctness.
4. **Second route.** Only after a second source-qualified 2P route exists. The frontier currently varies input on one course and one mode.

No new GitHub Actions campaign is required by these results. The reference side runs in about 3 s per case and the paired side in about 30–70 s per case, locally. If hosted provenance is wanted, one manual job per 100 terminal cases, sharing a single native build, is the proportionate size.

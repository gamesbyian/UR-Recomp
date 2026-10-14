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
| 38306802282 (`28501fa3…`), 10,000 cases | 10,000 | 9,978 | 0 | 22 census-attribution-ambiguous; original 15-frame both-air 31/10,000 (native used the 3-frame observer) |
| **Total** | **10,400** | **10,378** | **0** | 22 ambiguous: the token belongs to an earlier case, consistent with the cross-shard repeats in the 10k postmortem |

A coarse agreement is equality of the quantized census fields (position/64 and /32, velocity/64, rotation/16, raw air, split, offscreen, race progress), **not** strict equality, event acceptance or release credit. It is still a large-population, independently reproducible original/native comparison of random legal 2P trajectories, which the project did not have before. A divergent case would become an `original_native_discrepancy` candidate with an exact seed, arm and first divergent checkpoint.

**The dual-air witness is resolved (RF-001).** At native-equivalent 2580 the original has P1 air 1 and P2 air 2; one frame earlier only P2 is airborne (air 1); one frame later both are 0. It is a one-frame simultaneous hop that the 120-frame sampler happened to catch, and the original game reproduces it. It is not a discrepancy and needs no QA-01 event work.

## Exact paired original/native comparison (2026-10-14)

`paired` mode runs a real native executable beside the reference emulator. It **measures** each side's race entry (first `inRace=1`) and compares every decoded source field plus every WRAM byte at `$0200+` at native frame F against reference frame F−lag. The native side was a current-`main` Modern candidate (`fda6ace`, executable `4c1c8b56…`), built locally with the `modern-shared-native-acceptance.yml` recipe. Evidence (local, **candidate** until independently re-executed with raw receipts): [`analysis/data/frontier-original-native-race-relative-20261014.json`](../analysis/data/frontier-original-native-race-relative-20261014.json).

* **Entry (RF-003, resolved):** native 1136, Snes9x 1134 and pinned Beetle-bsnes 1134 in every case. The lag of 2 is measured per case, not assumed. When a wrong lag was declared for Beetle, the tool flagged it rather than reporting a divergence.
* **Mid-race:** 26 of 26 cases (5 per arm from three held-out runs, plus the witness) show **zero** differing fields and **zero** differing semantic WRAM bytes at 30-frame spacing from 1620 to 3420. The witness was also checked at every frame from 2570 to 2590. In total 39,747 race-relative frames were compared across all paired runs.
* **Race terminal (RF-012, handed to QA-01; candidate evidence):** a declared both-Right finish stimulus completes the ordinary 2P race in about 1,500 extra frames. `7E:009F` is the DrawText cursor `wTextPos` (#1543), so its `0x84→0x16` change is a raw terminal signature, not a proven scene or menu rule. In **49 of 49 seeds** (all five arms; measured lag 2 in every one), state stays identical through both laps reaching 0. The raw `0x84` phase then lasts **34 frames on Snes9x but 35 on native** in 48 seeds (36 for 50024003); scheduler parity at onset does not predict it. Per-core boundaries differ and must stay separate. On Snes9x, onset is on the same native-indexed frame in 43 seeds and one frame earlier on native in 6, while the `0x16` restore is later on native. On Beetle-bsnes (seed 50036056), onset is native 5198 vs 5199 and both restore at 5233, giving durations 35 and 34. Decoded fields first differ only after the reference's restore. Raw semantic WRAM first differs 1–2 native frames before onset (36 seeds at two frames, 13 at one), at the `7E:2000` list and at `7E:0BDE/0BFE`; the latter offset is explained by RF-014. `83:987D Sram_RestoreDirectPage` is a downstream 207-word SRAM-to-direct-page copy, not a proven diverging decision. The causal question is the upstream caller and the actual `7E:009F` writer on each core. Gameplay significance is pending those receipts.

* **Entry lag is phase-dependent (RF-013, handed to QA-01):** delaying the whole menu route by k = 0…7 frames moves Snes9x entry by exactly k (1134…1141), but native entry by 0, 1, 3, 3, 5, 5, 6, 7. The lag is therefore 2 or 3. The census cross-check stays valid because the frontier never alters the stock prefix (k = 0, lag 2). Any other route must measure its lag per case, which `paired` does. Native seems to quantize a vblank- or fade-gated wait, the same kind of one-frame transition cost seen in RF-012.

## Lag-frame census: a common cause (RF-014, handed to QA-01)

`80:FAC9` waits for the next vblank on `$4212`. `80:FADF` then decrements direct-page `7E:00C6` modulo 32 and writes `table[$C6>>1]` (table at `80:FBAF`) to `7E:0BDE/0BFE`. Each decrement of `$C6` is therefore one completed game frame, and a host frame without one is a lag frame. [`tools/qa_lag_frame_census.py`](../tools/qa_lag_frame_census.py) counts decrements between dense dumps on every engine for the same controller stream, with no instrumentation.

| Stock 2P route, host frames 2–1126 | Game frames (`$C6` passes) | Host frames without a pass |
| --- | ---: | ---: |
| Snes9x | 801 | 323 |
| Beetle-bsnes | 802 | 322 |
| Modern native (`4c1c8b56…`) | **773** | **351** |
| Generic SNESRecomp native (no Modern patches) | **772** | **352** |

The no-input attract cycle (host 2–4002, one counter-rewrite window excluded) shows the same pattern: native **1,311** passes, Snes9x 1,326, Beetle-bsnes 1,327. A frame without a pass is a lag frame only where the game runs the wait every frame (menus, loads); races and demos don't use it.

The two independent reference cores agree within one frame. Both native builds complete 28–30 fewer game frames, so the deficit is in the shared SNESRecomp runtime or generated code, not the Modern product host. Every one of the 27 differing windows is a screen transition or menu slide (raw `7E:009F` values `0x84`, `0xD7`, `0x3D`, `0x6D`, `0x91`); in steady menus all three run one game frame per host frame. At one-frame resolution the sharpest window is the load during which `7E:009F` changes `0x84→0xD7`: all engines hold `$C6` from host 426, the reference cores resume at 436–437 and reach `0xD7` at 440, native resumes at 442 and reaches `0xD7` at 446. Native needs about 5 extra host frames for the same load. The resulting `$C6` offset (4 mod 32) is frozen during the race and explains RF-012's `$0BDE/$0BFE` offset of 8 exactly. Native losing game frames at heavy transitions is the most economical common explanation for RF-012 (longer result phase), RF-013 (later, phase-dependent entry) and the 1P result-handoff seams QA-01 is chasing. It is a hypothesis to adjudicate, not a ruling. AGENTS forbids tuning `$4212` merely to match one emulator; the question is why native spends extra host frames on the same guest work.

## Player-visible confirmation: longer black loading screens (RF-014)

[`tools/qa_blank_screen_census.py`](../tools/qa_blank_screen_census.py) dumps every frame on each engine, measures framebuffer brightness, and pairs each engine's black-screen runs. It needs no WRAM access, so it also runs on the pinned high-accuracy `bsnes-libretro` core, which exposes no system RAM. In every run below bsnes agrees exactly with Snes9x, and Beetle-bsnes agrees within one frame.

| Route | Reference black runs (bsnes) | Native | Native longer by |
| --- | --- | --- | --- |
| Stock 2P frontend, host 2–1250 | 248–276, 401–443, 988–1150 | 248–278, 404–449, 988–1151 | +2, +3, +1 |
| No-input attract cycle, host 2–4002 | 248–276, 401–443, 941–1098, 1423–1547, 3632–3762 | 248–278, 404–449, 952–1112, 1440–1564, 3649–3781 | +2, +3, +3, … +2; later loads start **17 frames late** by host 3632 |
| 2P race finish (seed 50036056), host 4700–5600 | 5109–5239 | 5109–5240 | +1 |
| Stock route, generic SNESRecomp native | 248–276, 401–443, 988–1150 | 248–278, 404–449, 988–1150 | +2, +3, 0 |

**Mechanism of the first load.** From host 248 the reference writes VRAM by CPU at 738 words per frame: unrolled `STA $2118` at `81:CD70–81:D09C` (Nitrodon bank 81). WRAM at `$0200+` stays byte-identical between native and Snes9x throughout. Native's VRAM progress falls one, then two frames behind and converges at 278. Native therefore takes about 7% more host frames (31 vs 29) for the same CPU-bound decompress-to-VRAM work. The second load starts later on native because the transition waits for a `$C6` phase that native reaches 4 frames later. The discriminating next measurement is native CPU cycles per iteration of that bank-81 writer against the hardware frame budget. This is a framework timing question (the generic build shows it too), adjudicated by QA-01.

What this means for the frontier: on this route, native frontier states correspond exactly to original states for the whole race. Native fingerprint novelty here is therefore authentic original-game state novelty. But more random mid-race input will not find discrepancies. The measured discrepancy surface is the **transitions**: entry phase and the result handoff.

## Live queue

Generate with `python3 tools/research_findings.py --queue`. As of 2026-10-14:

| ID | Class | Owner | What would resolve it |
| --- | --- | --- | --- |
| RF-014 | original_native_discrepancy | qa01-gameplay | Compare native CPU cycles per iteration of the bank-81 VRAM writer (`81:CD70–81:D09C`) in the host 248–278 load against the hardware frame budget (31 vs 29 frames, about 7%) |
| RF-012 | original_native_discrepancy | qa01-gameplay | Trace writers of `7E:2000–2009` and `7E:0BDE/0BFE` at native 5195–5198 against original 5193–5196 on the 50036056 reproducer |
| RF-013 | reproducible_anomaly | qa01-gameplay | Compare native vs original iteration counts of the entry fade wait for route delay k=1 (lag 2) against k=2 (lag 3) |
| RF-005 | graphics_observation_gap | qa08-graphics | Replace the dead `$121B/$121D` predicate with the bank-82 sentinel observer, only if QA-08 names a question |
| RF-008 | reproducible_anomaly | qa01-gameplay | One single-case `qa01-event-campaign.yml` dispatch before any long original-native campaign |
| RF-002 | method_hazard | qa01-gameplay | Keep run 38509912672 as an executed identical-input observation; read it beside the race-relative stimulus-equivalence result |

Closed and retired items (dual-air witness, `$0DDB`, sparse sampling, Windows and fault-recovery bounds, fingerprint census) stay in the register with their resolutions so they are not reopened by volume.

## Next experiments, in priority order

1. ~~Terminal-phase population~~ — done at 49 seeds: +1 frame in 48, +2 in 1, independent of arm and scheduler parity. The open question moved to the lag-frame mechanism (RF-014).
2. ~~Entry-phase invariance check~~ — done: the lag is not invariant (RF-013).
3. **Rare-state branching.** Branch new inputs from agreed original trajectories that reached rare states (the dual-air hop, opponent-offscreen sentinels). Record each selection decision and replay the same recorded input on both engines, so the selector never defines correctness.
4. **Second route.** Only after a second source-qualified 2P route exists. The frontier currently varies input on one course and one mode.

No new GitHub Actions campaign is required by these results. The reference side runs in about 3 s per case and the paired side in about 30–70 s per case, locally. If hosted provenance is wanted, one manual job per 100 terminal cases, sharing a single native build, is the proportionate size.

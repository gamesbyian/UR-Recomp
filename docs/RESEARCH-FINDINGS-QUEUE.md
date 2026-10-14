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

`80:FAC9` waits for the next vblank on `$4212`. `80:FADF` then decrements direct-page `7E:00C6` modulo 32 and writes `table[$C6>>1]` (table at `80:FBAF`) to `7E:0BDE/0BFE`. Each decrement of `$C6` is therefore one completed pass of this wait continuation. Baldosa's imported RAM map names `$C6` `wCursorAnimTimer`, so it is **not** a global simulation-frame counter: "game frames" below means vblank-wait passes, and a host frame without one is a lag frame only where the wait runs every frame (QA-01 source preflight on #1537). Races, demos, scheduler pauses and counter restores are outside that reading. [`tools/qa_lag_frame_census.py`](../tools/qa_lag_frame_census.py) counts decrements between dense dumps on every engine for the same controller stream, with no instrumentation.

| Stock 2P route, host frames 2–1126 | Vblank-wait passes (`$C6` decrements) | Host frames without a pass |
| --- | ---: | ---: |
| Snes9x | 801 | 323 |
| Beetle-bsnes | 802 | 322 |
| Modern native (`4c1c8b56…`) | **773** | **351** |
| Generic SNESRecomp native (no Modern patches) | **772** | **352** |

The no-input attract cycle (host 2–4002, one counter-rewrite window excluded) shows the same pattern: native **1,311** passes, Snes9x 1,326, Beetle-bsnes 1,327. A frame without a pass is a lag frame only where the game runs the wait every frame (menus, loads); races and demos don't use it.

The two independent reference cores agree within one frame. Both native builds complete 28–30 fewer game frames, so the deficit is in the shared SNESRecomp runtime or generated code, not the Modern product host. Every one of the 27 differing windows is a screen transition or menu slide (raw `7E:009F` values `0x84`, `0xD7`, `0x3D`, `0x6D`, `0x91`); in steady menus all three run one game frame per host frame. At one-frame resolution the sharpest window is the load during which `7E:009F` changes `0x84→0xD7`: all engines hold `$C6` from host 426, the reference cores resume at 436–437 and reach `0xD7` at 440, native resumes at 442 and reaches `0xD7` at 446. Native needs about 5 extra host frames for the same load. The resulting `$C6` offset (4 mod 32) is frozen during the race and explains RF-012's `$0BDE/$0BFE` offset of 8 exactly. Native losing game frames at heavy transitions is the most economical common explanation for RF-012 (longer result phase), RF-013 (later, phase-dependent entry) and the 1P result-handoff seams QA-01 is chasing. It is a hypothesis to adjudicate, not a ruling. AGENTS forbids tuning `$4212` merely to match one emulator; the question is why native spends extra host frames on the same guest work.

## Player-visible confirmation: longer black loading screens (RF-014)

[`tools/qa_blank_screen_census.py`](../tools/qa_blank_screen_census.py) dumps every frame on each engine, measures framebuffer brightness, and pairs each engine's black-screen runs. It needs no WRAM access, so it runs on any core, including the pinned high-accuracy `bsnes-libretro` core (which exposed no system RAM until [`tools/patches/bsnes-libretro-system-ram.patch`](../tools/patches/bsnes-libretro-system-ram.patch)). In every run below bsnes agrees exactly with Snes9x, and Beetle-bsnes agrees within one frame.

| Route | Reference black runs (bsnes) | Native | Native longer by |
| --- | --- | --- | --- |
| Stock 2P frontend, host 2–1250 | 248–276, 401–443, 988–1150 | 248–278, 404–449, 988–1151 | +2, +3, +1 |
| No-input attract cycle, host 2–4002 | 248–276, 401–443, 941–1098, 1423–1547, 3632–3762 | 248–278, 404–449, 952–1112, 1440–1564, 3649–3781 | +2, +3, +3, … +2; later loads start **17 frames late** by host 3632 |
| 2P race finish (seed 50036056), host 4700–5600 | 5109–5239 | 5109–5240 | +1 |
| Stock route, generic SNESRecomp native | 248–276, 401–443, 988–1150 | 248–278, 404–449, 988–1150 | +2, +3, 0 |

**Scope: legacy pin only, not Baldosa.** The pinned Baldosa guest (`gamesbyian/uniracers-recomp` `10b864b`, SNESRecomp fork `075fbe4`), which is being integrated into the Windows product, matches the references within one frame on all five attract-cycle loads: black runs 248–276, 401–443, 941–1097, 1422–1547 and 3632–3761, with no drift. It also completes **1,327** vblank-wait passes, the same as Beetle (Snes9x 1,326; legacy-pin native 1,311). The deficit belongs to this repository's SNESRecomp pin `cd5875c`, which is used by the current Modern build, the generic build and the frontier executable. This does **not** yet show that the shipping Windows path is free of it: by default `modern-shared-native-acceptance.yml` recompiles the Modern game against the `cd5875c` pin, and the framework identity of the canonical candidate is not disclosed there (QA-01 provenance note on #1537). Only a nominated build proven to come from the `075fbe4` fork inherits Baldosa's result. It also matters for the legacy rollback backend and for frontier research timing. QA-01's Baldosa entry lags (+2/+1/+2) need a separate explanation.

**Mechanism of the first load.** From host 248 the reference's VRAM fills by about 738 words per frame (measured VRAM progress between dumps). **The writer is not identified:** no executed-PC, `$420D`/M/X or CPU-versus-DMA receipt exists. An earlier draft named `81:CD70–81:D09C` from a static `STA $2118` search. QA-01 has since shown that routine is the race-HUD initializer (`Hud_InitRace_FastRom`, called from `82:DC1A` race setup), so it is unlikely here. The stronger static candidates are `82:B1D8`, called from `80:93FB Attract_Main` and logo setup, which writes `$2118/$2119` at `82:B1F5/B1FC`, and its `81:BB89 Decomp_ToVram` branch (#1566). WRAM at `$0200+` stays byte-identical between native and Snes9x throughout. Native's VRAM progress falls one, then two frames behind and converges at 278. Native therefore takes about 7% more host frames (31 vs 29) for the same CPU-bound decompress-to-VRAM work. The second load starts later on native because the transition waits for a `$C6` phase that native reaches 4 frames later. The discriminating next measurement is an executed-PC histogram for host 248–278 on the reference. It should carry `$420D`, M, the `$2118/$2119` write sequence, CPU cycles and vblank, compared between `cd5875c` and the `075fbe4` fork. QA-01's MEMSEL arithmetic (#1562) predicts a per-store overcharge on the old pin only if `$420D` is 0 there. This is a framework timing question (the generic build shows it too), adjudicated by QA-01.

What this means for the frontier: on this route, native frontier states correspond exactly to original states for the whole race. Native fingerprint novelty here is therefore authentic original-game state novelty. But more random mid-race input will not find discrepancies. The measured discrepancy surface is the **transitions**: entry phase and the result handoff.

## Product core: Baldosa's result phase is one frame short (RF-015, resolved 2026-10-14)

The high-accuracy bsnes core now exposes WRAM through a small accessor patch ([`tools/patches/bsnes-libretro-system-ram.patch`](../tools/patches/bsnes-libretro-system-ram.patch), applied by `bootstrap_toolchain.py`), so it can adjudicate per-frame differences. It gives the 2P `0x84` result phase **34 frames in 9 of 9 seeds**, the same as Snes9x. That settles RF-012's direction: the legacy pin (35) is long.

Baldosa, run through the research two-seat input shim with lag 0, errs the other way. All semantic WRAM stays identical through the race and result onset, but the `0x84` phase lasts **33 frames in 9 of 9 seeds**. Onset is on the same frame in 7 seeds and one frame early in 2; the restore is 1–2 frames early. The race-finish black screen lasts 129 frames on Baldosa, against 131 on bsnes and 130 on Snes9x. This has the same sign as QA-01's 1P Switcher seam (original +4665..+4698, Baldosa +4664..+4696).

Frame by frame against bsnes on seed 50036056 (host 5180–5241, both engines dumping WRAM):

| Host frame | What differs |
| --- | --- |
| 5180–5195 | nothing |
| 5196 | the sound-command queue at `7E:2000` (`wSndQueueRead`; `2002` write index, `2004` APU toggle) |
| 5197 | Baldosa decrements the `7E:00C6` vblank-wait counter one frame early (`0x1e` vs `0x1f`); `7E:0BDE/0BFE` follow |
| 5198 | Baldosa `7E:009F = 0x84` (bsnes 5199, Snes9x 5198) |
| 5199–5229 | nothing |
| 5231 | Baldosa restores `0x16` (bsnes 5233); Baldosa then runs two vblank-wait passes ahead and leaves the race screen at 5235 vs ≥ 5237 |

**Superseded reading (kept for provenance).** The table above was read as a CPU–APU handshake divergence at 5196. It is not one: **Snes9x and bsnes differ from each other in exactly that 5196/5197/5198 pattern** and both still give 34 frames, and Baldosa equals Snes9x in all semantic WRAM from 5192 through 5230. The 5196 step is a host-frame phase effect between correct implementations.

**Established cause ([QA-01 adjudication](QA01-RF015-DRAM-REFRESH-BEAM-RATE-20261014.md)).** The phase is an NMI-disabled CPU VRAM upload (`82:B1D8`) followed by the two-edge wait `80:FAC9`. Snes9x reaches the wait at V=230, just after VBlank begins, and waits a whole extra field; Baldosa reaches it at V=224 and does not. Matched upload checkpoints show a uniform 0.087% CPU-time surplus on Baldosa, from `snes_refresh_charge()` charging the 40-clock DRAM refresh once per 1364 clocks of execution (1404 of beam time). The one-line correction ([`tools/baldosa_dram_refresh_beam_rate_patch.py`](../tools/baldosa_dram_refresh_beam_rate_patch.py)) gives 34 = 34 with exact semantic-WRAM agreement through host 6400 on the RF-015 seeds, and turns the unchanged QA-01 Zoom Zoo comparison from `strict_divergence` (+5162 vs +5163) into `strict_candidate` (+5163 = +5163). Neither is an accepted event. A smaller, separate SPC-clock mechanism remains on SPC uploads (RF-016).

## Live queue

Generate with `python3 tools/research_findings.py --queue`. As of 2026-10-14 (after RF-015):

| ID | Class | Status | Owner | Finding | Resolving experiment |
| --- | --- | --- | --- | --- | --- |
| RF-012 | original_native_discrepancy | handed_off | qa01-gameplay | Legacy-pin native 2P result phase (raw 7E:009F 0x84) lasts 35 frames where the original lasts 34 (bsnes-accurate, Snes9x, Beetle) | Measure the legacy pin's arrival line at the post-load 80:FAC9 wait and matched 82:B1DD upload checkpoint drift against Snes9x (the RF-015 method). The 5196 sound-queue step is phase-sensitive between correct cores (Snes9x vs bsnes) and cannot localize a defect by itself. cd5875c carries the same refresh-rate code as Baldosa yet errs long, so its larger beam/$4212 deficit (RF-014) dominates. |
| RF-014 | original_native_discrepancy | handed_off | qa01-gameplay | Legacy-pin native (snesrecomp cd5875c) completes fewer 80:FAC9 vblank-wait passes at screen loads, so its black loading screens last 1-3 frames longer than bsnes; Baldosa does not | QA-01 / native-fidelity: executed-PC histogram with $420D, M, $2118/$2119 write sequence, CPU cycles and vblank for host 248-278 on the reference, then compare snesrecomp cd5875c against Baldosa's fork 075fbe4 (96b7e9f $4212 read-time sync, b7b4318 paced_bus) for that writer; QA-01's MEMSEL model (#1562) predicts an old-pin per-store overcharge only if $420D=0. |
| RF-016 | original_native_discrepancy | handed_off | qa01-gameplay | Baldosa runs the SPC700 at 17088 cycles per 357368-clock field (~1.02696 MHz) where Snes9x and bsnes use ~1.02528 MHz: the no-input attract SPC upload ends ~54 lines early | Disposable A/B with RTL_APU_CYCLES_PER_FRAME 17060 (32040 Hz x 32 at 357368 master clocks): if the 1097/1422 black-run boundaries and per-field stream counts match bsnes, characterise the audio-pacing consequence before any product change. |
| RF-005 | graphics_observation_gap | handed_off | qa08-graphics | $121B/$121D 'offscreen' predicate is never nonzero; bank-82 split-screen sentinels are the source-qualified culling signal | QA-08: if a culling question needs it, ask for per-frame sentinel transitions (a 100-case observer validation), not case incidence; otherwise no work. |
| RF-008 | reproducible_anomaly | handed_off | qa01-gameplay | Latest original-native coordinator attempt 38446280858 failed without a recoverable first step | One single-case qa01-event-campaign dispatch; never another long campaign before a first-failure reason exists. |
| RF-013 | reproducible_anomaly | handed_off | qa01-gameplay | Legacy-pin native race-entry lag is phase-dependent (2 or 3 frames); Baldosa enters on the same frame as the original for every route delay | QA-01: compare native and original iteration counts of the entry fade wait loop for k=1 (lag 2) and k=2 (lag 3); if the extra frame is the wait loop, test the same loop in the 0x84 phase. |
| RF-002 | method_hazard | handed_off | qa01-gameplay | Two protocols: identical absolute-host input (executed, differs at host 2580) versus race-relative stimulus equivalence (matches); same-host comparison alone cannot separate entry phase from behaviour | QA-01: keep run 38509912672 (and 38520105599) as executed identical-input observations and record the race-relative result beside them; run any further writer trace race-relatively as well. |

Closed and retired items (dual-air witness, `$0DDB`, sparse sampling, Windows and fault-recovery bounds, fingerprint census) stay in the register with their resolutions so they are not reopened by volume.

## Next experiments, in priority order

1. ~~Terminal-phase population~~ — done at 49 seeds: +1 frame in 48, +2 in 1, independent of arm and scheduler parity. The open question moved to the lag-frame mechanism (RF-014).
2. ~~Entry-phase invariance check~~ — done: the lag is not invariant (RF-013).
3. **Rare-state branching.** Branch new inputs from agreed original trajectories that reached rare states (the dual-air hop, opponent-offscreen sentinels). Record each selection decision and replay the same recorded input on both engines, so the selector never defines correctness.
4. **Second route.** Only after a second source-qualified 2P route exists. The frontier currently varies input on one course and one mode.

No new GitHub Actions campaign is required by these results. The reference side runs in about 3 s per case and the paired side in about 30–70 s per case, locally. If hosted provenance is wanted, one manual job per 100 terminal cases, sharing a single native build, is the proportionate size.

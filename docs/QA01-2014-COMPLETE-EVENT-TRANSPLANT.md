# QA-01/QA-07: completed 2014 input transplantation, bounded attempt

Status: **executable investigative producer, NOT a completed/native release witness**.
Owner: gameplay fidelity/course acceptance. The canonical **0/45 USA complete,
4/45 partial, 41/45 unverified** census and QA-01/QA-07 release ledger
remain unchanged until a reviewed run reaches genuine settled parity.

## Measured original/Baldosa Zoo result (2026-10-09)

The separate **pinned Baldosa AOT and original Snes9x** route in PR #1091 / [CI run 38003554403](https://github.com/gamesbyian/UR-Recomp/actions/runs/38003554403) has now captured the previously missing **actual matching settled result PPU text** with original 2014 controller input. Both guests have P1 laps remaining zero at result onset and print MIKE total **1:16.46**, best lap **0:25.10**, and BRONSEN total **1:20.07**, best lap **0:26.45**. Exact live decoded USA stream-2 course residency is established at seven sampled active checkpoints per guest; all 14 compared game fields match at each of those checkpoints. In-scene progress samples show lap counter **4→3→2→1**, with **0** at both result onsets, and finish-gate/checkpoint agreement. At result onset both stored player contacts are zero; at the eight-frame-later result snapshot, they differ (**P1 0/10240; P2 0/512**). Original result onset is **5163** frames after original Zoo entry versus native **5162** after native entry. No game-rule change has been made. The raw evidence and owning gate/census are in [ORIGINAL-COURSE-EVENT-CENSUS.md](ORIGINAL-COURSE-EVENT-CENSUS.md).

This closes the **result PPU identity** experiment, but retains the **one-frame phase** and **post-result contact cleanup** uncertainties; nothing has been admitted to the release denominator (**0/45 USA**). The dedicated `tools/probe_original_event_complete.py` producer below remains a separate candidate framework and has not itself earned a completed-event witness. Use the already-built route and its independently retained artifacts before scheduling costly general replays.

## Native-only one-frame input-phase experiment (2026-10-09)

Merged PR #1093 drove the **same original 2014 340-segment controller scene** through one pinned Baldosa build using explicitly tagged native input origins -1, 0 and +1 guest frame relative to independent scene entry. The **original Snes9x input phase and complete result** were held unchanged; three phase reports and the failing native checkpoint captures are retained in [analysis/data/zoo-original-baldosa-latch-phase-discriminator.json](../analysis/data/zoo-original-baldosa-latch-phase-discriminator.json), with [CI run 38004850276](https://github.com/gamesbyian/UR-Recomp/actions/runs/38004850276).

Native **phase 0** alone reproduced the complete Circuit and matching P1/P2 original result text. Each native ±1 input shift had matching initial race entry but diverged from the original at **scene-relative +604** in world position, course contact and checkpoint, lost expected lap progression (**P1 remaining 3, original 2 at +1721; remaining 3, original 1 at +4700**), and never reached the 0xBC result by +5900. No artificial completion, undocumented checkpoint patch, or rules change was introduced. The surviving one-frame result onset discrepancy **cannot be cured by simply shifting the entire native controller movie**. Inspect the native/original guest state at fixed relative frames +5158..+5173 next to decide whether that remaining delta is a host observation convention or an actual result-transition difference; only then consider the original guest code's owning result handler.

The release denominator remains **0/45 accepted USA courses**. This finding narrows a specific causal hypothesis and does not independently establish a newly accepted Race or Stunt.

## Independently observed Zoom Zoo finish-state transition (2026-10-09)

Merged #1098 / [CI 38005782923](https://github.com/gamesbyian/UR-Recomp/actions/runs/38005782923) removed the test harness result-menu `until` condition and measured **18 identical scene-relative frames +5158..+5175** across original Snes9x and Baldosa. The original game, ROM, embedded SRAM, full original controller scene and independent guest-relative race-entry calibration were retained. Native leaves active gameplay at **relative +5161**, original at **+5162**; native enters `0xBC` Circuit result at **+5162**, original at **+5163**. This is a reproduced **guest-state transition difference**, not only a one-frame diagnostic script polling offset. At +5158..+5160 the measured P1/P2 laps/checkpoint/finish/contact/race clock still agree, and **both racers have completed their laps**. Raw DP scratch bytes `0xC6/0xC8` are already one step ahead in native by +5158. Their owner/semantics remain undetermined and must not be labeled a gameplay timer from observation alone.

The originally puzzling stored contact values also reconcile: at relative +5170 Baldosa has P1 `10240` / P2 `512` while original still has `0/0`. At +5172 original has P1 `10240` / P2 `512`; by **+5173** both original/native hold **P1 `10240`, P2 `256`**. Thus eight frames after two different result onsets is not a phase-equal post-result sample. Native and original both display the same full MIKE/BRONSEN total times and best laps. This leaves a **real one-frame result-lifecycle timing discrepancy**, not a demonstrated physics or scoring fault.

Retained proof: [compact machine-readable witness](../analysis/data/zoo-original-baldosa-fixed-result-boundary.json), [raw guest WRAM and original/native PPU artifacts](https://github.com/gamesbyian/UR-Recomp/actions/runs/38005782923/artifacts/11650174888). The active bounded run was not awarded an official course pass: **0/45**. The follow-up #1103 fixed-frame replay also exposed a **real intermediate menu stage** before the final result. Original and native both have track ID **0** and menu **0x84** at +5130, +5145, +5154 and +5156; neither should be incorrectly rejected as a bad Zoo track. At +5145 all **128 KiB WRAM bytes match**, and at +5154 only one transient raw byte differs. At +5156 the two still display the same named course/menu fields, but **69 WRAM bytes differ**. The first **named state change** is at **+5157**: native has returned to track ID **1**, menu **0x16**, while original is still at **track 0, menu 0x84**. Original reaches the same pre-result state at +5158. Native then leaves the active-race flag one frame early (+5161 versus +5162), and enters result menu **0xBC** one frame early (+5162 versus +5163). This localizes the earliest *observed named* divergence to the **interstitial-to-pre-result handoff**, not the lap/physics path; it does **not** yet identify the owning instruction or prove an engine scheduling bug.

The first CI attempt [38007759861](https://github.com/gamesbyian/UR-Recomp/actions/runs/38007759861) failed because the **new analyzer incorrectly demanded track ID 1 at every sample**. The failure was an evidence-validation assumption, not a native boot, course-play or input mismatch. Its independently produced raw dumps were retained as [artifact 11652310930](https://github.com/gamesbyian/UR-Recomp/actions/runs/38007759861/artifacts/11652310930); the [compact extracted witness](../analysis/data/zoo-original-baldosa-interstitial-prelude.json) is deliberately marked **non-admitting**. #1103 now accepts only the source-observed (track, menu) staging pairs and adds finer sampling at +5110..+5157 to bracket the first raw/guest divergence. No guest or native game-rule changes. **0/45** USA release credit remains unchanged.

## Completed finer interstitial bisection (PR #1103)

The corrected same-source test [run 38008660321](https://github.com/gamesbyian/UR-Recomp/actions/runs/38008660321) **passed** in both original Snes9x and pinned Baldosa. Host log checks confirm independent scene entries **1604/1606**, and the fixed relative frame range includes +5110/+5120/+5140/+5150/+5152 through +5157. Both full 128 KiB WRAM images match at **+5155** (also +5100/+5110/+5120/+5140/+5145/+5150/+5153). At **+5156**, the **first substantial transition-prelude mismatch** comprises **69 raw WRAM bytes** even though menu=0x84, track ID 0, and all named semantic fields still agree. At **+5157**, native has advanced to menu 0x16, track ID 1, while original still displays menu 0x84, track ID 0; original advances at +5158. The native result remains at +5162 versus original +5163. Final actual PPU result labels remain identical.

The raw +5156 differences include low WRAM offsets 0x008B, 0x0187 and 0x0B90. They are **not proof of the exact owning guest instruction**, and intermittent one-byte raw differences earlier in the session should not be relabeled as proven scheduling defects. The current lowest-risk next step is to identify the instruction/frame boundary writing the 69-byte staging group from +5155 to +5156, tracing original and Baldosa around the interstitial menu-to-result-prelude handoff. The [machine-readable witness](../analysis/data/zoo-original-baldosa-interstitial-prelude.json) retains both the failed first analyzer run and successful validated follow-up; full [raw guest artifact](https://github.com/gamesbyian/UR-Recomp/actions/runs/38008660321/artifacts/11652985802). **0/45 admitted USA course pairs** until a reviewed exact candidate/fresh repeat; no guest semantics modified.

## Adjacent guest-frame memory equivalence (new bounded discriminator)

A direct, independent comparison of the *same retained* green [fixed-frame raw artifact 11652985802](https://github.com/gamesbyian/UR-Recomp/actions/runs/38008660321/artifacts/11652985802) reveals a stronger and more precise fact than the same-relative-frame disagreement alone:

- At +5155 the original Snes9x and Baldosa **128 KiB WRAM images are byte-identical**; VRAM differs in 29 bytes and CGRAM is identical.
- At **native +5156 versus original +5157**, **all 128 KiB WRAM, 64 KiB VRAM and 512 B CGRAM are byte-identical**. This is a complete **192.5 KiB triple-memory equality** at a one-frame offset, not merely a matching menu flag or race time.
- At native +5156 versus original +5156, 69 WRAM bytes differ, but **VRAM and CGRAM already match**. At native +5157 versus original +5158, only four WRAM bytes and eight CGRAM bytes differ while all VRAM matches. Subsequent result-menu and PPU text still agree at their respective one-frame-displaced onset.

Thus Baldosa has reached *exactly the original guest's next-frame bulk memory state* at the menu handoff. This is highly diagnostic of a frame-boundary/update-phase issue; it does **not**, on its own, distinguish a short-lived legitimate intermediate original state, emulator scheduling, instruction order, controller input, CPU/PPU internal state or a genuine source-level timer discrepancy. It does **not** authorize shifting original controller inputs or modifying the guest's logic to look identical. The exact guest CPU registers, executed PC sequence, PPU scanline and audio timing remain unmeasured.

`tools/baldosa_2014_zoo_phase_equivalence.py` now derives both same-frame and original-next-frame WRAM/VRAM/CGRAM SHA256 comparisons from the existing already-bounded guest dump paths. Its fail-closed branch-specific invariant asserts +5155 WRAM equality and +5156-native/+5157-original triple-memory equality, and **never promotes any course**. The original/native pinned CI job reuses its existing build and single execution; no new emulator build, extra runner or game-code modification was added. Next, if source-visible timing causality is still necessary, interrogate guest PC/CPU and NMI scheduling *at +5155 to +5157* rather than extrapolate from a raw WRAM address in isolation.

## Original guest instruction attribution at the +5156/+5157 handoff

After the verified [adjacent-frame 192.5 KiB memory-equivalence experiment](../analysis/data/zoo-original-baldosa-interstitial-prelude.json), the next uncertainty is **which original CPU instruction(s)** transition the 69-byte menu staging group and whether Baldosa's earlier postframe state is merely a different guest update observation phase. The original +5156 to +5157 changes include `7E:008B` and `7E:0187..018E`, annotated as menu sprite animation counters in Baldosa's **imported, not locally vetted**, `decomp/ram.txt`; `7E:0B90..0BFF` and `7E:0C60..0C6F` reflect sprite/cursor staging. These are leads, not verified writer PCs or authority to manipulate gameplay.

`tools/instrument_snesref_zoo_menu_writes.py` introduces a bounded **read-only** observer at Snes9x's opcode-dispatch seam, temporarily in the ignored `.tools/src/snes9x-libretro/cpuexec.cpp` copy *after* the existing pristine original/native fixed-frame comparison completes. It records guest CPU bank:PC, v-counter, measured ICPU frame, changed WRAM byte and old/new values for the 69 previously changed bytes plus menu/track/race state. The frame gate is derived from the **fresh original calibrated scene-entry frame**, not the archived movie's absolute timestamp. `tools/baldosa_zoo_opcode_writer_report.py` cross-references those exact original WRAM deltas without converting ICPU frames into supposed unmeasured game frames. A replay of the **same original emulator input and route** checks exact WRAM equality at +5155/+5156/+5157/+5158/+5163/+5175 against the uninstrumented original witness; no authentic guest changes or Baldosa edits are involved.

This is an **investigative original-only CPU writer trace**, not a completed original/Baldosa dual-PC schedule comparison, nor proof that a particular `STA` or `MVN` instruction caused the difference. The pre/post-opcode observer can attribute synchronous side effects to the invoking instruction scope; SNES DMA and interruptions require separate analysis. Keep **0/45** accepted until the next paired fresh-process semantic check. If instrumentation alters a pinned original snapshot, if the opcode scope is absent, or if source offsets drift, fail closed rather than call it a guest bug. The bounded trace reuses the same CI execution and pinned source without adding a new triggered workflow.

## Validated original source-PC ordering and host-frame caveat (merged #1109)

The disposable traced-original replay in green [run 38011250306](https://github.com/gamesbyian/UR-Recomp/actions/runs/38011250306) reproduced six selected **pristine original WRAM captures byte-for-byte** and attributed all 69 changed low-WRAM bytes from original scene-relative +5156 to +5157 to observed CPU opcode scopes. See the [compact, hash-anchored event sequence](../analysis/data/zoo-original-menu-host-order-20261009.json) and the [raw replay/trace artifact](https://github.com/gamesbyian/UR-Recomp/actions/runs/38011250306/artifacts/11653695829).

The trace log establishes **actual chronology**, not a guessed mapping of CPU and script frame labels: after original `script f=6760 dump boundary-05156`, CPU scopes **80:D32A** write the eight menu-animation frame bytes, **80:D332** changes menu animation timer `7E:008B` from 00 to 01, and **80:D348** changes menu-sprite staging `7E:0B90` from 01 to 12. These are recorded with **ICPU.Frame=6759, PPU V=230–231**; the next original script dump is **f=6761 / +5157**. **After** that dump, original CPU scope **83:988A** changes menu `7E:009F` from **0x84 to 0x16** and track `7E:00CE` from **0 to 1**, at **ICPU.Frame=6760, V=240/243**. Original `script f=6762 / +5158` then observes those changes. The same-source Baldosa guest already showed the intermediate 69-byte state at relative +5156 and menu/track return at +5157.

The externally imported symbol list places 80:D32A–D348 in the `Oam_ResetMenuSprites` neighborhood, but does not prove why 83:988A runs at that relative host frame. **A source-visible original writer is not yet evidence of a native execution defect**. Snes9x's host invokes `script_tick()` before `retro_run()`, and Baldosa invokes `TickScript()` before `RtlRunFrame()`; the CPU `ICPU.Frame` count and outer host `script f` need independent reconciliation. This ordering plus the exact adjacent-frame 192.5 KiB WRAM/VRAM/CGRAM identity strongly motivates a **guest CPU/NMI/VBlank-versus-host observation-phase comparison**, rather than modifying controller input or game logic.

**Next QA-01 discriminator:** instrument both runtimes around the now-narrow +5155..+5158 transition to record *actual* source-visible instruction sequence, NMI/VBlank phase and postframe sampling boundary, using the unchanged input and independently calibrated scene entries. Preserve reference provenance and a fresh paired rerun. Continue separately toward the first scored Bowl Stunt and non-Dragster Race. **No USA course is admitted: 0/45.**

## Why these three targets

The pinned 2014 input movie already produced **actual original Snes9x
results** for Crawler Dragster (result menu 99, frame 2874),
Zoom Zoo Circuit (BC, 8353), and Bowl Stunt (2F tally, 11915;
18 scored terminal, 11985). This is existing original evidence in
analysis/generated/result-screens-probe.json, not an invented input
policy. Zoom Zoo also has original race-entry frame 3190 and five
checkpoint/gate/lap transitions in the independent 5,000-frame trace.
Switcher, Crawler's Race B, is the nearest **non-Dragster Race** target,
but a genuine original Switcher end-to-end result must first be found
in the longer original movie. No Switcher result is assumed.

The original/native Zoo **PPU result text and course identity are now compared** in the separate PR #1091 run above. Remaining full admission requires adjudicating its result-onset phase and post-result contact discrepancy, a reviewed repeat, and extending this route to a scored Stunt and independently sourced non-Dragster Race; the dedicated producer described below is still only experimental.

## New runner

tools/probe_original_event_complete.py reuses the archived SMV
reader, original low-WRAM per-frame trace parser, genuine scene-keyed
Crawler menu navigation, original/native fresh-process wrappers,
ROM-decoded 7F course validation and PPU text decoder. It:

1. Extracts archived embedded 8 KiB SRAM (no arbitrary all-silver
   replacement) and raw recorded joypad; independently replays the source
   original movie to a bounded horizon.
2. Detects a **real** course entry and **stable** terminal result screen
   from the source WRAM trace. It reuses the stock source result analyzer's
   minimum eight consecutive guest frames, while rejecting results marked
   active-race and requiring an independently stable Bowl 2F tally before
   the settled 18 screen. This prevents a single reused DP 009F scratch
   byte or brief fake tally from being mistaken for completed gameplay.
   Zoo must still start at independently established frame **3190**.
3. Extracts exact source-original scene input, preserving SMV UID,
   CRC, reset and controller validation.
4. Boots original Snes9x and native Authentic separately via stock menus,
   measuring both entry frames, then replays identical masks shifted to
   each actual guest frame; no guest poke/freeze. Rejects changed entry
   calibration.
5. Captures motion/contact/checkpoint/gate/lap/clock/queue state
   across the scene and actual final PPU result text, including
   nonzero-scored Stunt. Zoo's known checkpoint/lap frames are sampled densely.
6. Reports first observed mismatch, wrong result menu, disagreeing
   result text/score or zero-score Stunt. It emits a candidate report only,
   and does not mutate the release evidence ledger.

Initial producer scope is Crawler Zoo/Bowl/Switcher. It does **not**
fabricate input for the other courses. After successful family routes,
extend navigation and accepted controller sequences per course.

## Execution

Requires a worktree with built snesref, pinned Snes9x libretro core,
native Authentic executable and canonical USA ROM. The source scan
defaults to 22,000 frames; SMV window limit is 24,000. Use a fresh
workspace per attempt. The native helper temporarily swaps the
executable-adjacent saves directory; do not execute multiple runs
against the same native executable concurrently.

    python3 tools/probe_original_event_complete.py \
      --case zoom-zoo --snesref <reference-driver> \
      --core <pinned-snes9x-core> \
      --native <native-authentic-executable> \
      --work-dir /tmp/qa01-zoo-complete \
      --json-out /tmp/qa01-zoo-complete-report.json

Replace zoom-zoo with bowl or switcher for other family gates.
For Bowl it demands actual 2F tally before 18 terminal and a positive
displayed score. For Switcher, failure to find a completed original
source Race B is a **blocked producer**, not an invented passed race.
Recover a longer validated source or a different independent Race B route.

Without emulator binaries:

    python3 -m unittest discover -s tests/unit \
      -p 'test_probe_original_event_complete.py'

## Admission and stop condition

A JSON with comparison.paired_event_candidate=true is still **not**
an admitted full-event release row. A reviewer must check exact
artifact SHA, reference independence, input/latch phase, authentic
guest start, checkpoint/lap order, stunt scoring, native and original
terminal text, and fresh-process repeat. Sparse sampling can miss
contact events; terminal text agreement is not an instruction-time
causality proof. If a result does not materialize, keep logs/dumps and
record the first discriminator, classifying the course partial or blocked.

The frame-2903 Dragster contact remains explicitly **causally
unresolved**. No extra archaeology or guest semantics changes are
authorized without a reproduced event discrepancy.

Next if Zoo/Bowl fail: compare source-original entry state against
independently booted reference (rider/opponent, SRAM/menu/context),
then bounded -1/0/+1 controller latch phase trials. Never attribute
a phase mismatch to guest physics by default.

### Source-state equivalence as the first likely blocker

The original Zoom Zoo/Bowl movie advanced through earlier Crawler events
before each start, whereas a fresh scripted Crawler selection may skip
those earlier in-tour outcomes and mutate opponent, retained course state,
RNG phase, score context or other guest values. Identical 8 KiB
embedded SRAM is necessary but **does not recreate the earlier
in-session history**. The new producer independently replays the 2014
original a second time to dump its exact course-loaded entry state, and
compares rider IDs, positions, live lap/checkpoint/finish state and raw
clock to both fresh guests. The report retains each mismatch under
original_source_vs_fresh_entry. **Source-to-fresh equality is diagnostic,
not a release veto:** if independently booted native and original are
equal at entry, and both actually finish with equal frames, event states
and terminal results, the fresh pairing is meaningful even if the source
SMV's earlier tour state differed. A mismatch between the two fresh
guests itself denies admission. A one-frame snapshot discrepancy may be phase rather
than gameplay causality. If this gate blocks Zoo/Bowl, preserve the
earlier original course outcomes by replaying the preceding stock
tour sequence with authentic input, then independently recalibrate.

First admit one completed Circuit, one scored 45-second Stunt and
one non-Dragster Race. Then scale input producers to the USA 45-row
census and keep complete/partial/blocked/unverified distinct.

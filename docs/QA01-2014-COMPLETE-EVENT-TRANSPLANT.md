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

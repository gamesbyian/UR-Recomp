# QA-01/QA-07: completed 2014 input transplantation, bounded attempt

Status: **executable investigative producer, NOT a completed/native release witness**.
Owner: gameplay fidelity/course acceptance. The canonical **0/45 USA complete,
4/45 partial, 41/45 unverified** census and QA-01/QA-07 release ledger
remain unchanged until a reviewed run reaches genuine settled parity.

## Measured original/Baldosa Zoo result (2026-10-09)

The separate **pinned Baldosa AOT and original Snes9x** route in PR #1091 / [CI run 38003554403](https://github.com/gamesbyian/UR-Recomp/actions/runs/38003554403) has now captured the previously missing **actual matching settled result PPU text** with original 2014 controller input. Both guests have P1 laps remaining zero at result onset and print MIKE total **1:16.46**, best lap **0:25.10**, and BRONSEN total **1:20.07**, best lap **0:26.45**. Exact live decoded USA stream-2 course residency is established at seven sampled active checkpoints per guest; all 14 compared game fields match at each of those checkpoints. In-scene progress samples show lap counter **4→3→2→1**, with **0** at both result onsets, and finish-gate/checkpoint agreement. At result onset both stored player contacts are zero; at the eight-frame-later result snapshot, they differ (**P1 0/10240; P2 0/512**). Original result onset is **5163** frames after original Zoo entry versus native **5162** after native entry. No game-rule change has been made. The raw evidence and owning gate/census are in [ORIGINAL-COURSE-EVENT-CENSUS.md](ORIGINAL-COURSE-EVENT-CENSUS.md).

This closes the **result PPU identity** experiment, but retains the **one-frame phase** and **post-result contact cleanup** uncertainties; nothing has been admitted to the release denominator (**0/45 USA**). The dedicated `tools/probe_original_event_complete.py` producer below remains a separate candidate framework and has not itself earned a completed-event witness. Use the already-built route and its independently retained artifacts before scheduling costly general replays.

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

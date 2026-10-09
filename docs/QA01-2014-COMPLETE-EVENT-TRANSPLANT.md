# QA-01/QA-07: completed 2014 input transplantation, bounded attempt

Status: **executable investigative producer, NOT a completed/native release witness**.
Owner: gameplay fidelity/course acceptance. The canonical **0/45 USA complete,
3/45 partial, 42/45 unverified** census and QA-01/QA-07 release ledger
remain unchanged until a reviewed run reaches genuine settled parity.

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

The missing proof is a correctly rebased **fresh-boot native and original**
completion of the same event, with actual terminal **time/lap/score text**
compared and course identity guarded, rather than a 64-frame entry probe.

## New runner

tools/probe_original_event_complete.py reuses the archived SMV
reader, original low-WRAM per-frame trace parser, genuine scene-keyed
Crawler menu navigation, original/native fresh-process wrappers,
ROM-decoded 7F course validation and PPU text decoder. It:

1. Extracts archived embedded 8 KiB SRAM (no arbitrary all-silver
   replacement) and raw recorded joypad; independently replays the source
   original movie to a bounded horizon.
2. Detects a **real** course entry and matching terminal menu from the
   source WRAM trace, refusing inferred frame anchors, missing results or a
   Bowl result without its preceding 2F summing screen. Zoo must still
   start at independently established frame **3190**.
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

First admit one completed Circuit, one scored 45-second Stunt and
one non-Dragster Race. Then scale input producers to the USA 45-row
census and keep complete/partial/blocked/unverified distinct.

# QA-08: isolate authentic OAM slots98/99 at 1P frame2208

**Status: native source emission accepted (run `38097914195`, artifact `11686843233`); final PPU ownership and Remastered still unapproved.** This experiment
reads the unchanged native PPU, not guest WRAM-derived synthetic pixels.

Merged #1264 (AOT `38095455347`) proved original bottom
P1 OAM slot97 emitted **0** opaque pixels at live guest2208.
Merged #1271 (AOT `38096082799`, artifact `11685889818`)
independently proved original bottom slot96 also emitted **0**.
Both source screenshots and full original 1×/4× pixel sources
remained unchanged, with full original guest CRC identity.

**Correction from actual 2026-10-11 native pixels:** The earlier claim
that the unicycles were above a 1P "split" at scanline112 was false.
The authentic 342×224 1P Original output shows the racers directly above
the colored horizontal course strip near y144. The isolated original PPU
OAM slots98 and99 actually emit at **raster y121–143** and **y120–143**
respectively, entirely in rows112–223. Those are source/image coordinates,
**not** evidence of a bottom split-screen player or of a 1P viewport
boundary at y112. "Top" in "top OAM slot98/99" was a slot name, not a
proven final on-screen viewport. Slots96/97 were authentically empty in
their separate 1P probes. Do not infer raster region or in-game player
identity from OAM slot number or begin-frame WRAM state.

## Controlled native source planes

The pinned game normally executes one genuine 1P stock route,
one Original 342×224 1× route, and one Original 1368×896
4× route (including the retained negative bottom OAM planes).
They cannot also isolate other OAM slots in the *same*
native process because the PPU exporter uses one bound OBJ source.

Two **additional read-only original-density 1P guest processes**
now capture isolated top OAM **slot98** and **slot99**
separately at the same independently proven guest frame2208.
They use the same ROM, scripted controller input, live 342-wide
course calibration, and 5,447-frame guest route; no guest writes.
Their full seven Original frame images are compared to the original
1× witness, not assumed identical merely because guest CRCs match.

`tools/check_baldosa_oneplayer_top_oam_sources.py` requires:

- **Five** complete, identical guest CRC streams (stock,
  accepted 1×, accepted 4×, isolated slot98 and isolated slot99);
- seven matching full original 1×/4× frames plus exactly
  seven original image frames each from the two probe runs,
  independently matching the uninstrumented 1× source;
- genuine PPU source alpha/bbox, PAM slot/frame/filename
  and exact native log attribution for both slots, never
  inferred source pixels from an OAM screen rectangle;
- untouched complete Original output in both probes,
  including every 342-column race pixel.

A positive top source is evidence of real emitted
original OBJ pixels, not necessarily final BG/window
pixel winners. If both top sources are also empty, investigate
other OAM, PPU background, and split-HDMA phases instead of
inventing 4× racer art. The source OAM snapshot captured at
beginning of a guest frame is not a substitute for per-scanline
HDMA-driven sprite state. Record negative findings honestly.

No `RemoveFromGame`, source sprite replacement, new art,
Remastered 342-wide authorization, Windows UI change, scoring
or beta-release acceptance is part of this experiment.


## Existing-process paired-source overlap census (candidate)

The top-slot validator now includes a **read-only, pixel-exact pair census**
under `top_pair_overlap_and_final_rgb_census` in its existing JSON report.
There is no new emulator/guest process, frame capture, workflow, OBJ deletion,
graphics asset or presentation setting. Reuse the same independently
authenticated native slot98 and slot99 342×224 RGBA PAMs and frame2208
complete Original 342×224 image; the existing five-way guest CRCs, 7-frame
Original/4× identity, slot attribution and source SHA checks still run first.

The `band_counts` field partitions raster scanlines 0–111 and 112–223 for analysis only (it does not assert a 1P viewport split), each
reporting slot98-only emission, slot99-only emission, shared emission, and
neither. For shared alpha positions it separately reports whether the two
source RGB values conflict and whether the final Original RGB matches only
slot98, only slot99, both or neither. Non-overlapping source emissions that
differ from final Original RGB are also counted. Bounded logical `[x,y]`
coordinates in `bounded_coordinate_examples` support targeted visual review
without persisting another full image or a fabricated sprite.

Two invariants make the census harder to misread:

- Unique emitted pixel coordinates are `98-only + 99-only + shared`, **not**
  the sum of the two per-slot alpha counts. That sum double-counts shared
  source pixels. Each slot's reconstructed alpha must equal its independently
  verified isolated source count.
- Matching final Original RGB is **not proof** that an emitted OBJ owned that
  pixel. A mismatch can arise from BG/window priority, another OBJ or color
  processing; it is a review candidate, not a diagnosed occlusion cause.
  Neither an exclusive emission nor matching RGB authorizes destructive
  `RemoveFromGame` or wide Remastered painting.

The synthetic regression includes both halves of scanline112, conflicting
overlaps, exclusive mismatches, coincident final/source RGB, malformed planes
and an all-transparent negative. The next native use is to apply this amended
analyzer to the retained **actual** top-slot evidence and then seek a paired
source-vs-final PPU ownership counterfactual for any disputed coordinates.
This document makes no unobserved quantitative native overlap claim.


## Observed same-native-artifact pair result

Reuse existing accepted AOT run `38097914195`, artifact `11686843233`.
The independent full Original 1P frame2208, separately isolated slot98 and
slot99 **real PPU RGBA planes**, and both corresponding untouched Original
probe captures were recovered from the artifact. Full untouched Original
capture pixels match both probes exactly; each emitted source-plane
SHA-256 matches the original native validator report.

The offline exact-byte pair census in
`analysis/data/qa08-oneplayer-top-pair-native-2208.json` found:
**slot98-only=285**, **slot99-only=293**, **source-alpha overlap=0**,
**578 distinct emitted pixels**, and **0 upper-half emitted pixels**.
All 578 source RGB values match the final Original RGB at their coordinates,
with no mismatches in this frame. The two source bboxes are [101,121,132,143]
and [36,120,71,143], so their separation is directly measurable.
This closes the **frame2208 pair-source-overlap** question without another
emulator run or duplicated native compilation.

Final BG/window or other OBJ priority ownership is **not** established by
RGB coincidence. A source pixel matching the final colour can be hidden by
another same-colour source; no full-window race coverage, removal decision,
HD replacement, 342-wide Remastered or release authorization follows.

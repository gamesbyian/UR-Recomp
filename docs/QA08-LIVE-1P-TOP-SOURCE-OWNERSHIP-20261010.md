# QA-08: identify original top-viewport unicycle source at 1P frame2208

**Status: native candidate, not yet accepted.** This experiment
reads the unchanged native PPU, not guest WRAM-derived synthetic pixels.

Merged #1264 (AOT `38095455347`) proved original bottom
P1 OAM slot97 emitted **0** opaque pixels at live guest2208.
Merged #1271 (AOT `38096082799`, artifact `11685889818`)
independently proved original bottom slot96 also emitted **0**.
Both source screenshots and full original 1×/4× pixel sources
remained unchanged, with full original guest CRC identity.

The **real image** at 1P frame2208 places both unicycles
above the blue/green split horizontal band at source scanline112.
The unicycles are in the **top viewport**, whereas previous
source-plane experiments observed bottom slots96/97.
This explains why top-source ownership needs its own test
and does not imply any CPU/PPU bug or permit HD sprite drawing.

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

The `band_counts` field distinguishes scanlines 0–111 and 112–223, each
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

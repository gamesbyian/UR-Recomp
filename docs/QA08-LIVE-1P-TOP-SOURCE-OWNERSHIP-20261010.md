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

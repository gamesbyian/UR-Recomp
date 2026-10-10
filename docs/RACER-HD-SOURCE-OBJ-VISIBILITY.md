# QA-08: do not invent riders absent from the Original PPU sprite plane

Status: concrete native 2P visual regression and conservative source-alpha
correction. This closes **source-absent viewport painting** on the
tested 256×224 scene, not full SNES foreground priority or moving-HD
shipping acceptance.

## Baldosa 342-wide single-slot source-OBJ evidence (read-only diagnostic)

The pinned SNESRecomp PPU exposes real isolated source pixels for **one exact
OAM slot** through its existing overlay capture API. The 342-wide coordinate
space spans SNES X `[-43, 299)`, centered in a physical 342×224 RGB-alpha
diagnostic raster. With `PpuSetOverlayCapture(..., flags=0)`, the OBJ slot is
*also rendered normally* into Original main/subscreen. **RemoveFromGame is
never armed by this wide probe; authored art remains gated off at width 342.**

Native QA can set `UR_RACER_HD_WIDE_SOURCE_SLOT=96|97|98|99`,
`UR_RACER_HD_WIDE_SOURCE_FRAME=1856` and
`UR_RACER_HD_WIDE_SOURCE_DIR=<existing folder>` on four separately
executed identical deterministic 2P routes. Each process emits
`ur-baldosa-ws342-obj-slotNN-frame001856.pam` with exact isolated hardware
slot alpha, native bbox and split-band source counts. Native artifact/report
`ws342_obj_slot_NN.json` preserves the image SHA256 and rejects *any*
difference between the entire probed and uninstrumented 342×224 Original
raster on shared guest frames, in addition to the independent guest CRC gate.
An empty isolated source slot is valid evidence that the PPU emitted no pixels
from it at that frame, and **must never cause a fabricated rider**.

This is an **observation-only** step toward proving individual P1/P2
ownership. Isolated OBJ emission precedes final BG/window priority and may
be fully occluded; it cannot itself authorize HD substitution, wide sprite
repositioning or foreground-overpaint. Once this evidence resolves the
occlusion/slot problem, any new wide art admission must still satisfy the
existing real-source-visible footprint rule independently per viewport and
per owner, with Original fallback for ambiguous cases.

## Original counterexample

At ordinary USA-retail 2P starting-line guest frame **1220**,
the verified Original and 4× Remastered images differ substantially:
the Original image shows a complete unicycle in the top viewport, but
**no lower racer**; the pre-fix Remastered host draws a conspicuous
lower unicycle into that previously empty portion of the scene.

The direct isolated OBJ plane fixed by #1029 is authoritative
read-only evidence of actual source sprite *emission*. On native run
`37878062421` / artifact `11593326749`, the originally opaque P7
OBJ source contained **372 alpha pixels**. The aligned independent
OBJ-only native screenshot from #1020 (run `37878148035`,
artifact `11594020402`) showed the same 372 nonbackdrop pixels
in the candidate racer footprints and **no lower-racer source**.
The original-HD raster enclosure test had previously permitted this
false lower rider because it required graphics to stay within both
registered 64×64 OAM boxes, but it never established that stock
had emitted a sprite in both boxes.

Do not infer why the Original PPU did not emit the lower sprite from
these observations alone. Possible contributors are OBJ line budgeting,
masking, HDMA OAM changes, prioritization or another unsupported
presentation mode. The concrete contract is narrower: **a host
replacement cannot draw a racer in a viewport where the source PPU
actually emitted zero racer OBJ pixels**.

## Renderer correction

The HD host already binds its source OBJ raster before invoking the
pinned PPU. The new
`racer_stock_obj_pixels_in_footprint()` inspects the resulting
256×224 ARGB32 plane inside the corresponding logical 64×64 racer
placement, including 256-line Y wrapping and scanline-112 split
ownership. After authentic PPU rendering, the host measures source alpha inside
**each active racer instance's own OAM footprint**, and paints that
instance only if its footprint contains source pixels. This is stricter
than the first per-viewport guard and avoids authorizing a disjoint
source-empty second rider using another rider's pixels.

This does not delete the Original sprite or alter the PPU's
`RemoveFromGame` policy; there were no stock sprite pixels to remove
in the absent half. It never modifies WRAM, SRAM, VRAM, OAM, palette,
guest timing, inputs or race physics. The paired replacement still
respects SNES OAM paint order within each admitted viewport.

The isolated OBJ buffer contains composited color and alpha, **not an
individual per-OAM-slot ownership mask**. The stricter check is per
racer *footprint* rather than true per-slot attribution. When two
64x64 racers overlap, either one's pixels can make both footprint
counts nonzero. Other sprites may also contribute pixels inside
the box. Per-slot visibility, sprite overlap and foreground BG/window
priority remain separate QA-08 L4 obligations.

## Native and unit acceptance

The native 2P original/HD screen comparator now takes the **exact
source PPU layer from the HD process** at frame 1220. With one or more
opaque source pixels present, it requires every HD-changed output
subpixel to remain inside a live registered OAM bounding box and
requires a completely source-empty viewport to have **zero changed
pixels**. This replaces the old unsafe assumption that both halves
must always gain HD pixels.

The first native acceptance expects nonzero source and HD changes
above the seam, and exactly zero source and zero changes below it;
the actual counts are retained in the workflow artifact. Synthetic
C++ tests cover split clip, absent lower viewport, false off-box
pixels, 256-line Y wrap and invalid geometry. Python tests deliberately
paint a fake bottom racer in an otherwise source-empty viewport and
require the strict original-vs-HD oracle to reject it.

A visually empty viewport is not proof of correct **foreground**
depth if stock OBJ alpha was emitted but BG overlays should obscure it.
Do not promote this guard into a blanket L4 priority or whole-course
visual fidelity pass. Continue the native moving-scene, 1P/VS,
single-slot ownership and 16:9 presentation counterexample campaign.

## QA-08 follow-up: same-viewport phantom-rider guard (2026-10-09)

Source-confirmed defect in the prior implementation: the renderer
accumulated all original OBJ alpha inside both registered racer rectangles
into one `source_opaque[top|bottom]` count, then used that viewport-wide
count to authorize **every** rider in that half. For spatially disjoint
footprints, one real visible racer could therefore authorize a second
source-empty HD racer. This was a distinct remaining defect even after
the already-fixed entirely empty bottom-viewport case.

The host now evaluates `racer_stock_obj_pixels_in_footprint()` separately
for each draw instance and skips an instance with zero source alpha in
its own OAM footprint. The normal full pair uses four instances (98,
99, 97, 96); diagnostic P1-only uses two (98, 97). Source diagnostic
`UR_RACER_HD_SOURCE_FOOTPRINTS` records `alpha0..alpha3` and `count=2|4`,
while the existing `UR_RACER_HD_SOURCE_OBJ` line is retained for
historical parser compatibility. The viewport counts are sums of
footprint samples, **not distinct source pixels** when rectangles
overlap, so do not use them as a unique alpha-pixel denominator.

The existing moving-source analyzer now validates that every new
per-footprint line agrees with the viewport total, rejects duplicates,
P1-only inactive-slot data and missing witnesses, and reports empty
individual footprints. Older native logs remain analyzable but cannot
prove individual rider-source gating. The synthetic C++ witness
deliberately places original pixels inside only one of two disjoint
top-viewport racers; the second footprint must report zero. This
change is **committed with unit/regression fixtures, pending fresh
native moving-scene validation on the exact PR candidate**. Do not
retroactively revise the published 87/441 or 169+902/2641 native
callback census as actual visible pixel counts. Those measurements
predate the per-footprint guard and classify presenter callbacks,
which can include a source-empty skipped instance.

Next native discriminator: capture real top/bottom per-instance alpha
for an event-aligned moving 2P interval, including disjoint and
overlapping footprints, Y-wrap and scanline-112 transitions. Compare
same-frame Original and HD at both 1x and 4x and preserve guest state.
A per-footprint hit does not identify which OAM slot emitted it;
ambiguous overlaps and BG/window/other-OBJ priority still require
a PPU-visible ownership/depth seam or a conservative pre-capture
admission policy before L4 can pass.

## Measured two-rider same-viewport ambiguity at 342 columns

The independent native CI artifact for merged #1097 (`38005764119`, source
frame **1856**) contains the genuine 342×224 final Original frame and
individually isolated PPU OBJ source for slots 96–99. It establishes an
important counterexample to admitting two painted riders from a shared
per-viewport or per-rectangle alpha count:

| Source owner | Top source alpha | Bottom source alpha | RGB matching final Original | Notes |
| --- | ---: | ---: | ---: | --- |
| Slot 98 (front top) | 321 | 0 | 321 / 321 | Stock top winning P1 at this source frame |
| Slot 99 (rear top) | 319 | 0 | 176 / 319 | 143 source samples differ from final composite |
| Slot 96 (front bottom) | 0 | 319 | 319 / 319 | Stock bottom winning P2 at this source frame |
| Slot 97 (rear bottom) | 0 | 321 | 175 / 321 | 146 source samples differ from final composite |

The two top-slot alpha footprints overlap at **157** logical pixels;
the bottom pair overlaps at another **157**. Across all four source planes,
there are 1,280 emitted alpha samples but only **966 distinct logical source
pixel coordinates**. The 143 and 146 differing rear-slot samples are strong
witnesses that painting each opaque source plane wholesale over the finished
frame would overpaint the original compositing result. Additionally, three
non-overlapping bottom slot-97 source samples differ from the main image,
consistent with further priority/occlusion or other unresolved presentation
processing. Do not assign those pixels a specific cause without a deeper
PPU-layer proof. Matching RGB can also be a coincidental palette match and
is not in itself an unambiguous pixel-ownership identifier.

The exact source-frame and full-raster hashes are retained in the #1097 CI
artifact and per-slot reports. The dedicated overlap analyzer added here
computes these counts directly from **all actual four PNG-free P7 planes**,
validates each isolated-slot report against the main PPU frame digest and
refuses the acceptance witness when the observed front-slot raster colors
diverge or overlapping rear-source pixels cease to be distinguishable. This
is a **non-destructive observation** for QA-08, never a grant to activate
`RemoveFromGame` at 342 columns. The real title's BG/window foreground
and source-visible HD pixel placement are still unverified.

## 256-wide production overlap gate and actual moving-HD coverage (2026-10-10)

Merged **#1104** addresses the concrete same-viewport slot ambiguity measured
above. When both authored racers have selected registrations, the shipping
256×224 presenter now checks the **visible 64×64 active source rectangles**
before arming destructive PPU `RemoveFromGame`. Any intersection in either
scanline-112 split viewport (including Y modulo-256 wrap) chooses the complete
Original stock raster. Nonoverlapping pairs retain the existing HD eligibility
checks. This conservative rectangle test intentionally trades away HD coverage
where individual OAM-source ownership and BG/window depth are unresolved; it
does **not** prove that even a disjoint source plane is fully front-visible.
It does not enable authored sprites at 342 logical columns.

Native acceptance run
[`38009190914`](https://github.com/gamesbyian/UR-Recomp/actions/runs/38009190914)
was green on the exact #1104 head before merge. An independent Original-A/B
and **default guarded-HD** run at source frame 1220 yielded byte-identical
256×224 stock screenshots, matching composition words, and no new guest WRAM
differences outside independently observed stock-run variability. The guarded
native script executed **1,620 frames** and recorded **102**
`overlapping-source-obj` fallback gates, with **one** HD-presented guest frame,
**frame 1139**, which is **before** the chosen moving-race window.

In the actual moving 2P interval, **1180–1620 inclusive (441 guest frames)**,
the default guarded route presented **0/441 HD frames** and **441/441 Original
frames**. Its fallback reasons were 87 overlapping-source refusals,
342 missing P1 selection/art, and 12 unavailable P2 pair selections. By
contrast, the intentionally unsafe archival authored-art route reports
**87/441 HD-presented** calls, with the existing frame-1220 source witness
showing **top OBJ alpha 372, bottom alpha 0**. Its HD callback count was never
a proof of two independently source-visible racers. The separately validated
P1-only diagnostic route can render real P1 HD while keeping P2 stock, but
does not authorize turning that experimental option into default Remastered.

**Release interpretation:** The current stock fallback is faithful and the
overlap-specific phantom/draw-over defect is contained on these tested
frames, but **shipping Remastered has zero demonstrated moving-race coverage
in this fixture**. The archival HD success counter must never be used as the
shipping numerator. It is legitimate to expose Original/Upscaled with an
explicit Remastered limitation, not to claim a working 4K HD two-racer race.
No QA-08 L4/physical-output gate is promoted by this evidence.

The native acceptance workflow now reuses
`tools/measure_racer_hd_live_draws.py` on the **default guarded** host log,
retains the production `racer-hd-production-safe-window.json` and asserts
full 441-frame presence, no armed-but-unpresented captures, and Original
presentation for every overlap-refused frame. It deliberately does **not**
assert that the HD count remains zero; successfully increasing *safe* HD
coverage should improve the measurement without weakening the pixel/guest
safety oracle. Closing this gap requires a real per-slot source/depth
discriminator or a separately accepted partial replacement seam, never
the unsafe forensic bypass.

## HD callback versus actual changed host pixels (2026-10-10)

**A counted HD callback is not necessarily a drawn HD racer.** The exact
production guarded script from green native run `38009190914` recorded
`hd/full-pair` at guest frame **1139**, before the moving race began. The
original PPU source-footprint diagnostic at that very frame reported
`alpha0=0 alpha1=0 alpha2=0 alpha3=0`. The presenter therefore skipped
all four authored drawing calls. It returned the already-scaled Original
frame, yet the old callback-only census credited one HD-presented frame.
This explains why the one supposed safe HD frame in the 1,620-frame route
was **not evidence of one changed HD sprite**.

The existing presenter now records
`UR_RACER_HD_PIXEL_CHANGE frame=N source_instances=S changed_from_underlay=B`
on each diagnostic HD presentation. This compares the **final authored host
buffer** against the same frame's incoming PPU **post-capture underlay** at
the current 1×–4× scale, over the existing active racer rectangles after all
overlapping draw writes. `S` reports source-alpha-positive
*footprints*, not verified OAM ownership. `B` is one only if at least
one final host output pixel differs from its corresponding capture-only
underlay pixel. It is an actual changed-output witness, **not** proof of correct
visibility, depth, real 4K display or complete authored artwork.

`measure_racer_hd_live_draws.py` retains its historical
`hd_drawn_guest_frames` callback counter for backwards comparison, and
now separately reports `hd_with_source_footprint_guest_frames` and
`hd_with_actual_changed_pixels_guest_frames`. New native-run reports
must include exactly one pixel-change record per HD present, including
repeated host presents for a single guest frame. Mixed missing/stale
witnesses, claimed changed pixels when no source footprint exists and
witnesses on Original fallback are rejected. Legacy logs without these
new records remain analyzable, but cannot establish changed-pixel counts.

The source-absent frame-1139 false-positive is a measurement error, not
license to admit new sprite substitutions. Existing release policy and
the 0/441 safe moving-race callback observation are unaffected. At this
writing, CI validation of the new actual-pixel witness is pending.

## Opt-in P1-only fallback when selected racer rectangles overlap (experimental)

The default production path still rejects a 256-wide full-pair HD capture
when either viewport's two large source rectangles intersect. The existing
**opt-in** `UR_RACER_HD_P1_ONLY=1` diagnostic already permits a more
restricted P1 capture when P2 has no approved authored registration. It
selectively removes **only OAM slots 97/98** (P1) while rendering original P2
slots 96/99 through the PPU. The separate strict P1-only split geometry gate
rejects a potentially visible P1 small copy, rotated sprite priority,
incompatible OBJ tile/priority, or overlapping *bottom* P2-front coverage.
Native `UR_RACER_HD_P1_NATIVE_TEST=1` verifies the untouched P2 bottom
rectangle against the same guest frame's PPU raster rather than comparing
nonaligned process screenshots.

The new bounded experiment extends this opt-in partial path to frames where
**P2 also has an authored asset but the original full-pair capture was
rejected for overlap**. It never enables this behavior without
`UR_RACER_HD_P1_ONLY=1`. It must use the P1 top and P1 bottom instances
regardless of P2's registration; drawing a P2 authored sprite while selectively
removing P1 OAM would corrupt the scene. When the strict independent P1-only
stock-P2 occlusion test rejects, the full Original frame remains intact.

An `UR_RACER_HD_P1_OVERLAP_RECOVERY` diagnostic and the existing native P2
same-frame ROI oracle will determine if this actually recovers safe changed HD
pixels in the long two-player route. A positive admission counter **alone**
will not authorize default production exposure. We still need real source
emission and original foreground/BG priority evidence for the P1-only overlay,
especially overlapping *top* P2 and 342-wide output. No QA-08 release gate
is promoted by the experimental setting.

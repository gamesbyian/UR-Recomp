# QA-08: do not invent riders absent from the Original PPU sprite plane

Status: concrete native 2P visual regression and conservative source-alpha
correction. This closes **source-absent viewport painting** on the
tested 256×224 scene, not full SNES foreground priority or moving-HD
shipping acceptance.

## Baldosa 342-wide single-slot source-OBJ evidence (read-only diagnostic)

The pinned SNESRecomp PPU exposes real isolated source pixels for **one exact
OAM slot** through its existing overlay capture API. The 342-wide coordinate
space spans SNES X \`[-43, 299)\`, centered in a physical 342×224 RGB-alpha
diagnostic raster. With \`PpuSetOverlayCapture(..., flags=0)\`, the OBJ slot is
*also rendered normally* into Original main/subscreen. **RemoveFromGame is
never armed by this wide probe; authored art remains gated off at width 342.**

Native QA can set \`UR_RACER_HD_WIDE_SOURCE_SLOT=96|97|98|99\`,
\`UR_RACER_HD_WIDE_SOURCE_FRAME=1856\` and
\`UR_RACER_HD_WIDE_SOURCE_DIR=<existing folder>\` on four separately
executed identical deterministic 2P routes. Each process emits
\`ur-baldosa-ws342-obj-slotNN-frame001856.pam\` with exact isolated hardware
slot alpha, native bbox and split-band source counts. Native artifact/report
\`ws342_obj_slot_NN.json\` preserves the image SHA256 and rejects *any*
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

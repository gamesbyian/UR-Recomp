# QA-08: do not invent riders absent from the Original PPU sprite plane

Status: concrete native 2P visual regression and conservative source-alpha
correction. This closes **source-absent viewport painting** on the
tested 256×224 scene, not full SNES foreground priority or moving-HD
shipping acceptance.

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
ownership. The host determines per-viewport source presence **after
authentic PPU rendering** and only paints authored HD assets where at
least one source OBJ pixel exists in that viewport.

This does not delete the Original sprite or alter the PPU's
`RemoveFromGame` policy; there were no stock sprite pixels to remove
in the absent half. It never modifies WRAM, SRAM, VRAM, OAM, palette,
guest timing, inputs or race physics. The paired replacement still
respects SNES OAM paint order within each admitted viewport.

The check is intentionally **per viewport**, not per rider slot:
the current isolated OBJ buffer contains composited color and alpha,
not an individual per-OAM-slot ownership mask. A visible racer in one
viewport therefore establishes only that some registered racer OBJ
source was emitted in that half. Per-slot visual completeness, other
sprites' occlusion and foreground BG/window priority remain separate
QA-08 L4 obligations.

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

# QA-08: source-proven native PPU journal tag to framebuffer row

**Scope: pinned native renderer only.** This recovers the exact native
**whole-line replay** mapping by following source code, without claiming
physical SNES hardware timing, original-emulator parity or an observed
per-pixel PPU layer owner.

## Reconstructed chain (no inferred offset)

The native 2P PPU's pinned code is
`baldosa/snesrecomp@075fbe4c8e0d97b0013be541795c39cb644a9709`.

1. `runner/src/snes/ppu.c` `raster_key` starts the field at
   `V=225`; saved register writes occur in key order
   **225..261, then 0..224**. `ppu_rasterFieldBoundary` snapshots
   the next field when the beam crosses V=225.
2. `runner/src/beam_frame_driver.c`,
   `snes_beam_frame_driver_draw_ppu_frame`, loops
   **`line=1..224`**. On each iteration it executes
   `ppu_rasterApplyLine(g_ppu, line - 1)`, then
   `ppu_runLine(g_ppu, line)`. A tagged register write
   at **V=N** can therefore affect this native renderer's
   whole-line draw for **line N+1**.
3. `ppu.c` `PpuDrawWholeLine` writes to
   `ppu->renderBuffer + (y-1) * renderPitch`, with
   `y=line` from that call. The physical row in the
   native source buffer is consequently **`rowY=N`**
   for visible journal tags **N=0..223**. This is an
   *exact static renderer mapping*, not an empirical alignment
   against the final SDL / displayed monitor image.
4. A write at raw tag 225..261 precedes all visible lines
   in that field. Same-tag multiple writes apply in journal
   order before the line is rendered. Tag **224** is outside
   the 224 source rows even though the debug journal includes it.

## What this permits and does not

The source path now permits matching reconstructed **native
per-tag register-state hypotheses** to **native PPU framebuffer row
indices** without an invented `+1`, `-1` or split-screen offset.
This specifically narrows how to investigate the previously observed
red5 +13 source/finished-output differences around upper source rows
47–52 and lower rows 159–164 in authentic guest2208 2P. Both viewports
share the same source-space vertical coordinate system in the 342x224
logical renderer; do not add 112 when interpreting the register tag
*again*. Preserve the distinct measured source-pair displacement
`(-13,+112)`, which is a sprite-registration fact, not a PPU
timing offset.

This is **not** proof of an equivalent physical console's
intra-scanline effects. The beam-driver source explicitly approximates
writes made partway through a line as affecting the line represented
by its integer tag. Actual display screenshots additionally require
pitch, crop and output-scaling provenance; the accepted 342x224
Original CRC/SHA route is the independent evidence authority for
those bytes. Neither fixed-colour arithmetic, object math eligibility,
window masks, subscreen sources, OAM sprite rip nor contested pixel
ownership follows from the tag-to-row equality by itself.

## Colour-math source conditions for the next authenticated native capture

The same pinned `ppu.h` defines:
- `PPU_mathEnabled = CGADSUB & 0x3f`; OBJ corresponds to
  **layer 4 / bit `0x10`** in the native renderer's per-layer math gate.
- `PPU_halfColor` uses CGADSUB bit `0x40`;
  `PPU_subtractColor` uses `0x80`.
- `PPU_addSubscreen` uses CGWSEL bit `0x02`;
  the window math eligibility tests `CGWSEL >>4 & 3`.
- `COLDATA` uses independent red/green/blue write selectors
  `0x20/0x40/0x80`, updating the low five data bits in each channel.

With the proposed read-only PPU field baseline export in
[#1421](https://github.com/gamesbyian/UR-Recomp/pull/1421),
the existing strict 2P journal should provide real register values
for all those hypotheses at native tags 47–52 and 159–164.
**Necessary register conditions are not sufficient to attribute
the final +13 red5 pixels to fixed-colour addition.** Per-source palette,
source priority, subscreen fallback, math/window gating and the
independent source-deletion counterfactual must still be reconciled
before changing presentation pixels. Do not enable the owner-vetoed
procedural HD racer or relax 256x224 / 7:6 / 4x Original / actual
widescreen-world constraints.

No new guest process, CI factory, ROM extract, artwork or gameplay
change was used to establish the source mapping.

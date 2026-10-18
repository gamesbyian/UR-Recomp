# QA08: original 2014 Snes9x medal active sprite painter source (one-shot)
18 October 2026 | **read-only authentic original PPU research, unmerged source experiment**

## Why this is the next causally relevant experiment

The SHA-bound current/native RF017 Win32 capture independently establishes
19/19 effective native medal OBJ zbuffer words from the *actual* last
nontransparent SNESRecomp physical 4bpp tile writer, plus six BG1 controls.
This permanent source evidence is merged in [#1835](https://github.com/gamesbyian/UR-Recomp/pull/1835)
commit `93dc3b7b5ceddcde09ff0cbaaa706eebedb5959f`.
The 2014 Snes9x original/natively composited 263-frame result image still
has 890,205 RGB5 errors in the wider census. Source capture [#1788]
independently found full original 544-byte OAM input packets two native
host fields earlier, but **neither this DMA producer phase nor a 2014
field-end OAM snapshot establishes the actually painted sprite at a
particular original scanline.** Fixing an imagined medal tile or moving
frame labels without that missing source would be unjustified.

## Actual original source and scientific contract

The original/real reference is the **pinned Snes9x libretro core**
from `snes9xgit/snes9x` at exact full SHA
`1bcc369e89f08243e0a462882fb1f3e42e51de3a`,
with the existing reproducible debug-export patch and original
`gamesbyian/uniracers-recomp` snesref host
`10b864b9d14a7b7416dd909eb7b054c88faef101`.
The original 2014 USA ROM SHA256 is
`859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`.
The authentic separate `tests/input/qa08-original-medal-source-2014.script`
matches SHA256
`bddfb15fedbaba3fcb0e95e628f11e1506fd210d93f4be67c6e9855c705dd3db`,
exactly matching the archived original original-Snesref-2014 movie
from the independently certified palette-source ZIP. The script is
unchanged and reaches `script f=5484 quit`; no turbo directive,
random input, inserted frame, guest memory poke or modified action.

The original Snes9x source performs actual `DrawOBJS` 4bpp tile
calls at `gfx.cpp` before BG priority resolution. Temporary patches
only bracket **two preexisting calls** (`DrawTile` and
`DrawClippedTile`) with direct host `GFX.DB`/16-bit RGB
screen reads at sample (x,y), selected actual OAM slot, original
tile argument, line and sprite palette/priority. Both original tile
calls still execute exactly once, in their existing order. No second
software rasterizer is installed. It retains true before/after depth,
16-bit colour, and whether an original draw visibly changed either.
A tile *call* is only a candidate: a transparent source pixel or
already-higher BG/depth may prevent output. Same-colour sprite writes
can be invisible to a before/after comparison. Record all candidates
in exact source order; do not label candidates as actual winners absent
source evidence.

Select only original reference `ICPU.Frame=4028..4036` and
`4172..4180`, and the already fixed medal raster coordinates:
(207,91), (205,115), (205,139), (225,96), (225,120).
Observe only the **main-screen** source draw path, not subscreen
guesses. These are Snes9x-original **frame labels**, not assumed
corresponding native host clock, and must be explicitly compared
against original source callback registration before any cross-emulator
conclusion. The Windows source probe used actual native raster_y, not
the Snes9x internal tile row Y, which remains an explicit source field.

## Decision gates

- If an actual original painter candidate and host framebuffer/PPU
  depth coincide, derive the original OAM slot/tile source there.
  Independently re-check whether any BG later owns the pixel; a
  tile call alone is not a visible winner.
- If original raster calls yield different OAM/tile candidates than
  current/native winners, test actual original/native producer
  chronology and NMI execution with CPU owner, **without** changing
  renderer tile, frame shift or CPU clock based solely on correlation.
- If original draws do not reach the selected coordinates or
  callbacks fail to align with the source image, report
  **NOT ADJUDICATED**, never fabricate frame parity.
- The execution is one source-bound original USA run. Retain only
  the original captured tile-call stderr log, actual pinned core
  SHA, original `end.info.json` and exact route exit. No ROM,
  profile or SRAM is exported.

This diagnostic PR will be **closed unmerged** when qualified; unique
research/negative findings can transfer in a separate docs-only
source evidence PR. Production #1780, Modern #1713, accepted CPU/APU
source phase, 3840×2160, 7:6, new HD racer artwork and independent
release ledger remain untouched and explicitly **HOLD**.

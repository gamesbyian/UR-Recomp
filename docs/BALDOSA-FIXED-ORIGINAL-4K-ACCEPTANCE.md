# QA-08: fixed 256-wide Original physical 4K acceptance

The verified wide 342×224 native SDL2 3840×2160 capture at guest frame
1856 **does not** prove the separate fixed Original 256×224 case,
including stock title/menus, authentic 7:6 pixel aspect, full 224-line
frame height and 480-pixel matte borders.

A later complete fixed-output native physical gate must compare:

1. A native **256×224 source PPU frame** from an independent stock
   input/guest run, captured without changing guest state
2. A separately executed **1024×896 Original fallback** from the
   existing Baldosa 4× exact-nearest presenter, same input/frame
3. A third independent native **3840×2160 physical SDL drawable**,
   with the existing exact Original viewport [480,0,2880,2160] and
   stock black side mattes

The existing `check_baldosa_physical_4k_capture.py` already supports
both logical widths, SDL2 16.16 fixed-point sampling, exact output
RGB/opaque alpha and all physical pixels. Its fixed 256 case has
**synthetic test coverage only**, not yet live host evidence.

The native Baldosa bridge now has one opt-in read-only source capture
at `UR_BALDOSA_FIXED_ORIGINAL_SOURCE_FRAME=400`, enabled only with
`UR_BALDOSA_HD=1` and an isolated
`UR_BALDOSA_HD_CAPTURE_DIR`. It writes
`ur-baldosa-original-source-000400.pam` straight from the native
256×224 Original field **before** running the 4× host compositor and
logs `UR_BALDOSA_FIXED_ORIGINAL_SOURCE`. No fake downsampling from the
4× fallback is permitted for this independent logical witness.
No normal render mode changes, guest WRAM updates, authored art,
unsafe overlap bypass or PPU source suppression are involved.

The existing accepted 4× fallback run already independently saved
`ur-baldosa-fallback-000400.pam` (plus frames 640, 880, 1120,
1360, 1600), with exact Original 1024×896 frame contents and
unchanged guest CRCs.

**Next native execution** should route a stock 1× fixed source at
guest frame 400, reuse the existing 4× fallback snapshot, then run
an independent 4× 3840×2160 SDL output capture at that same frame,
with no HD art or widened-world flags. Require identical full guest
CRC streams across all processes and strict all-pixel output parity.
The exact matte alpha behaviour is not currently established and
must not be faked or tolerated.

Until that native run succeeds, only the live **342-wide world 4K**
output is accepted. Fixed 256-wide output and Windows physical 4K
are explicitly separate pending gates.

## Native fixed-width three-process QA run added

The existing Baldosa AOT workflow now separately executes an
unmodified native 256×224 source at guest frame **400**, compares
the full guest CRC stream with its earlier genuine 1024×896 Original
4× fallback, and captures a third real 3840×2160 SDL surface from
a fresh process on the already-established virtual 4K display.
The same all-pixel physical oracle checks the entire 2880×2160
active viewport plus both opaque-black 480-pixel side mattes.

No capture is synthesized from another input, and any difference
in source, 4× fallback, guest state, physical pixel or matte must
fail CI. The original 342-wide physical acceptance remains intact.

**The new fixed-width path remains pending until its native AOT run
passes.** It does not establish Windows physical output or physical
monitor scanout.

# QA-08: source OAM on-screen eligibility for missing 1P authored art

**Status: native candidate, not yet accepted.** This is read-only PPU/OAM
geometry research. It does not grant Remastered art, OAM erasure or
Windows-release permission.

## Measured starting point

Merged #1231, exact native AOT run `38091207834`, artifact
`11684526840`, proved seven identical 1x/4x genuine 342-wide Original
1P frames, including clearly racing frame 2208. In 3,430 authentic
post-race-milestone guest-state observations, 3,355 had no registered
authored asset, 17 had existing art but unmatched composition and 58
selected registered art. The two `0A4B` fingerprints account for
**1,521** missing-art samples, roughly 45.3%. But that is not proof
that the source game's P1 unicycle is on screen in those frames.

## Exact extension to the already scheduled 1P guest process

The existing opt-in `UR_RACER_HD_1P_STATE_TRACE=1` now also decodes the
native PPU's actual P1 top/bottom split source OAM slots **98 / 97**
and stock P2 slots **99 / 96** at the same guest simulation frame,
*before* graphics-geometry fallback and before any source OBJ
removal. No new emulator process, guest ROM/CPU/WRAM write, art
source, compositor or second capture pipeline is introduced.

For each of the 3,451 bounded trace frames, it records the signed
9-bit source X, wrapped 8-bit Y, original tile bank/OBSEL,
whether a 64x64 Original OBJ rectangle can intersect each stock
top/bottom (scanline 112) viewport, and whether the existing
conservative P1-only/P2-front admission guard would permit the
source layout.

`tools/check_baldosa_1p_oam_art_visibility.py` fails closed unless
EVERY native semantic observation has exactly one matching genuine
OAM observation, all original/host **5,447 CRCs** match, the source
script entered the original 1P race and reached the expected end,
the native P1 original OAM rectangle is consistent with SNES
signed-X and 256-line Y wrap, and bank/OBSEL/priority assertions do
not contradict the source guard. The new report intersects
actual missing-art and authored-but-unregistered states with:
 
- original screen rectangle potentially on-screen, from P1 OAM;
- the source tile-bank and original graphics mode;
- the existing conservative P2-front safety guard;
- explicit counts of source-bank-unproven or off-screen
  original P1 OAM rectangles.

A high-frequency pose with no source OAM on-screen becomes a
**poor art candidate**, not an invitation to generate an invisible
sprite. A high-frequency source-geometry candidate becomes a
**priority for original-PPU isolated-OBJ alpha and final-composite
review**, not automatic HD authorization.

## Hard evidentiary limits

A source OAM rectangle crossing a screen region is an upper bound,
not proof any opaque racer pixel was emitted. The original BG/window
priority and 342-wide camera-shifted replacement coordinates remain
unproven. The source alpha and P2 foreground attribution also need
independent per-slot native image witnesses. Do not change source
OBJs, game physics, historic art, 1P/2P fallback, output sizing,
Windows Modern UI, or the Remastered release gate to satisfy this test.

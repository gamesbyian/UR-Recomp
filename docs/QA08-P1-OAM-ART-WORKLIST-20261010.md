# QA-08: source OAM on-screen eligibility for missing 1P authored art

**Status: accepted bounded native read-only OAM geometry census.** Merged #1255; exact AOT run `38094430121`, artifact `11684953572`, all five CI workflows successful. This establishes candidate screen geometry and conservative original P1/P2 source guards, **not source OBJ alpha, final BG/window priority, HD sprite erasure, or Windows beta admission**.

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

## Exact native outcome: first useful artwork shortlist

The independent native PPU and source WRAM census matched **all
5,447 guest CRC frames** and exactly **3,430 post-milestone source
states**. Source OAM geometry and the original tile/OBSEL bank
classified the 3,355 missing-art observations:

| Source-registered classification | Guest observations |
| --- | ---: |
| Missing authored asset with plausible on-screen original racer OAM | **1,844** |
| Missing authored asset with absent/non-racer screen OAM | **1,511** |
| Existing authored asset but unmatched runtime composition; eligible OAM | 17 |
| Existing authored selected pose; eligible OAM | 58 |

The decisive source observation is `0A4B`, previously the
largest raw missing-art semantic:

| Semantic | Eligible source-OAM / total observations |
| --- | ---: |
| `08D5` | **526 / 526** |
| `0895` | **515 / 515** |
| `0855` | **511 / 511** |
| `0A4B` | **10 / 1,521** |

Original P1 screen bank/geometry is still valid at native frame
**3639**, but **3640** changes from the active large-racer
`OBSEL=83` / tile `00` into a non-racer
small-sprite `OBSEL=00` scene. Later `0A4B`
is held while the actual PPU uses `OBSEL=63`,
top slot98 tile `E6/EA` and bottom slot97 tile
`CE/C8`. A source semantic left unchanged in WRAM
is **not** proof that the original rider should still be drawn.
This is a genuine source-based eligibility distinction, not a
guess based on animation timing.

The art-authoring priority is therefore the rapidly cycling
`08D5 / 0855 / 0895` family, with its exact
observed companion compositions; these three IDs account for
**1,552 eligible moving-race guest observations**. They are
*plausible original OAM screen candidates*, not yet
isolated opaque source pixels. The next narrow experiment
[#1264](https://github.com/gamesbyian/UR-Recomp/pull/1264)
targets the already accepted native 1P guest frame **2208**
(`0895`) and the original **slot97** pre-BG/window
isolated-OBJ plane using the *existing 4× guest process*.
Only a source-plane and final-composite ownership review may
authorize corresponding authored 4× artwork/replacement.

The exact per-frame geometry worklist and confidence limitations
are in `ws342_live_1p_oam_visibility_worklist.json` in
artifact `11684953572`. Preserve these derived findings
for the technical reference, but retain the original full
native artifact as the strongest source while available.

## Hard evidentiary limits

A source OAM rectangle crossing a screen region is an upper bound,
not proof any opaque racer pixel was emitted. The original BG/window
priority and 342-wide camera-shifted replacement coordinates remain
unproven. The source alpha and P2 foreground attribution also need
independent per-slot native image witnesses. Do not change source
OBJs, game physics, historic art, 1P/2P fallback, output sizing,
Windows Modern UI, or the Remastered release gate to satisfy this test.

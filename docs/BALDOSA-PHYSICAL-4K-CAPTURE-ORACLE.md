# QA-08: actual physical 3840×2160 Original-output capture gate

## Verified 4K SDL framebuffer and remaining platform limits

The pinned Baldosa route has proved genuine **342×224** source-wide
world pixels from a +48 backing margin and 43 visible pixels on each side,
then **1368×896** exact 4× nearest-density Original presentation.
**Native pinned Baldosa SDL2 software 3840×2160 drawable output is now
pixel-exact for frame 1856, as recorded below.** Neither source nor
4× density captures alone provided this credit. The pure
widescreen_output_composition contract separately resolves 7:6
Original pixel aspect (and widened 512/513 horizontal fit) into a 16:9
target. Layout geometry is not an actual host screenshot.

The new tools/check_baldosa_physical_4k_capture.py verifies **three
independently captured images of the exact same simulation frame**:

1. The native PPU's 256×224 fixed or genuine 342×224 widened RGBA image.
2. Its actual native 4× RGBA output, 1024×896 or 1368×896 respectively,
   requiring every single exact 4×4 source-pixel block.
3. A **real 3840×2160 desktop/SDL drawable screenshot** with no overlay,
   linear filtering, CRT simulation or color processing.

All three must be exact eight-bit RGBA PAM images with the guest frame
number embedded in each filename. The final capture is compared across
every pixel against the original full-height source projected through
the actual pinned SDL2 software renderer's **16.16 fixed-point nearest**
texture sampling and the accepted Original pixel aspect.
The full 342-wide world must occupy all 3840×2160 pixels, including both
widened world margins and the split-screen seam. Fixed 256-wide Original
must remain centered at x=480, width=2880, preserving all 224 rows, with
opaque black side mattes. The first mismatched physical pixel and same-frame
input digests are reported to distinguish a bad source from output scaling.

Example after independently capturing an actual physical 4K window:

    python3 tools/check_baldosa_physical_4k_capture.py \
      --source captures/ur-baldosa-ws342-001872.pam \
      --density-4x captures-4x/ur-baldosa-ws342-001872.pam \
      --physical-4k captured-window/ur-baldosa-output-001872.pam \
      --frame 1872 \
      --out reports/baldosa-physical-4k-frame1872.json

**The third file is now produced by the pinned Baldosa AOT native CI.**
It is read back from the real 3840×2160 SDL virtual-display drawable,
never synthesized from its 342×224 or 1368×896 sources. Synthetic
unit tests alone still give **zero** real host acceptance.

## Strict scope and integration order

- Exact Original nearest filtering only. UI overlays, CRT effects,
  bilinear sampling, color correction, or alternate GPU presentation
  need separately specified oracles, not relaxed tolerances here.
- This script cannot request 4K display modes, create SDL textures,
  take real screenshots, verify host frame timing, exercise monitor
  refresh or prove 4K hardware scanout. It can only verify independently
  supplied pixel evidence.
- Current widened native source contains stock Original OAM riders because
  safe Remastered per-slot OBJ attribution, final depth and BG/window
  priority remain incomplete. Exact Original output does not establish
  correctly composited HD riders or complete-event gameplay fidelity.
- The pinned Linux Baldosa SDL2/Xvfb 4K drawable proof now exists.
  **Windows physical 4K host, other graphics backends, physical monitor
  scanout and true frame-timing/latency are not established**. Retain
  the original output viewport ownership and separate acceptance gates.

## Baldosa desktop viewport binding (native SDL witness completed)

The native Baldosa 342-wide adapter now assigns the desktop host's
`compute_viewport` callback to the *existing* first-party Original-mode
7:6 pixel-aspect policy. Its source dimensions are checked against either
logical or exact 1x–4x density output. A calibrated 342x224 scene maps
to [0,0,3840,2160] in a 3840x2160 drawable using the existing 512/513
fit; a complete 256x224 Original scene remains centered at
[480,0,2880,2160] with matte side margins. Unsupported +24 experiments,
invalid geometry or a stale wide admission leave host viewport unchanged.
A compiled native bridge test checks these coordinates and density cases.

The hook alone is only static geometry, but the pinned SDL2 native
frame-1856 result below now **independently exercised it on real
3840×2160 virtual-display output**. A fixed 256-wide physical capture
still needs independent acceptance; the fixed viewport has unit proof.

## Real native SDL 4K output execution and accepted artifact

The pinned Baldosa AOT acceptance now stages the separately merged,
opt-in SDL2 renderer readback for its **disposable** framework checkout
before the normal 342-wide world/4× host rebuild. Routine baseline,
1P, 2P, VS and per-slot PPU jobs do not request a physical capture.

After first recording original guest-frame **1856** at genuine native
342×224 (1×) and 1368×896 (4×) in two independent processes, it starts
a separate Xvfb **3840×2160** display and an isolated Baldosa configuration
with `WindowSize=3840x2160`, `OutputMethod=SDL-Software`,
`LinearFiltering=0`, and `Fullscreen=0`. The same unchanged native
2P route renders the real SDL drawable, with exactly one full-frame
`SDL_RenderReadPixels` readback before `SDL_RenderPresent`.
The explicit frame/file arguments are `1856` and
`ur-baldosa-output-001856.pam`.

The workflow requires the complete stock guest CRC sequence, an
authenticated 3840×2160 SDL readback log, and pixel-exact verification
by `check_baldosa_physical_4k_capture.py` against the independent
same-guest-frame source and 4× captures. The full physical RGBA file,
native log and machine-readable report are retained as CI artifacts.

**Accepted:** [Baldosa AOT run 38075396346](https://github.com/gamesbyian/UR-Recomp/actions/runs/38075396346),
from merged [PR #1178](https://github.com/gamesbyian/UR-Recomp/pull/1178)
(commit `e1e2668ed22bb5c4c92a720d81858a243702a496`), passed the
full-frame native 4K oracle with the three real same-guest-frame inputs.
The native log contains:

`UR_BALDOSA_PHYSICAL_4K_SOURCE_PARITY PASS frame=1856 logical=[342, 224] density=[1368, 896] physical=[3840, 2160] viewport=[0, 0, 3840, 2160]`

The retained GitHub Actions artifact `11678860795` contains the
**33,177,671-byte full 3840×2160 RGBA PAM**
`ur-baldosa-output-001856.pam`, native log and machine-readable
`ws342_physical_4k_frame1856.json` report with
`status=exact-native-capture-pixel-parity`.
All **8,294,400 output pixels** matched the accepted genuine Original
source/4× density presentation through the SDL2 sampling contract,
including both wide margins and the two-player split seam.
The complete native guest CRC sequence matched stock.

The report preserves exact uncompressed RGBA pixel SHA256 digests:

| Real captured raster | SHA256 of RGBA data |
|---|---|
| 342×224 Original | `0e956fac212cb7413a32ee2a0de318540e58cfd5f2b7610472c2573ab6719dd9` |
| 1368×896 Original 4× | `2c61d698f6922a2724acf550c6a42e185c0f3e1824db824a0aa741a9f06a6535` |
| 3840×2160 SDL readback | `aaa75568a62855325cc7e2dd4df2a0bf8a4f1cda8f40332fed321e3baf6e311b` |

**Scope:** Native Linux SDL2 software on an Xvfb virtual display, one
complete Original two-player frame. This is **not** Windows product
validation, physical monitor scanout, arbitrary-frame/renderer equivalence,
accurate HD rider replacement or original-emulator complete-event parity.

## Physical SDL alpha normalization, not colour tolerance

The first actual **3840×2160 SDL readback** in native run
[38074405401](https://github.com/gamesbyian/UR-Recomp/actions/runs/38074405401)
successfully produced its full-size PAM and preserved the original guest
CRC stream. The first strict comparison revealed a specific output-domain
difference at screen pixel `(0,0)`: the source PPU wrote
`RGB=84a5a5 alpha=00`, while SDL's explicitly OPAQUE presentation
texture correctly returned `RGB=84a5a5 alpha=ff`. The older checker
incorrectly equated the PPU's unused alpha byte with final SDL
pixel opacity.

The physical oracle now requires an **opaque 255 alpha for every
displayed pixel**, while continuing to compare **every RGB pixel
exactly** against independent 1× and 4× original source frames.
The logical-vs-4× source-pixel check retains its original strict RGBA
identity, including the zero-alpha PPU source. No colour tolerance,
rescaling or synthetic 4K source generation is introduced. Unit
regression reproduces the observed zero-alpha source/full-opacity
display case and rejects an improperly transparent output pixel.

That initial mismatch was corrected before the later **successful**
independent native run identified above. The oracle still rejects
any incorrectly transparent physical pixel.

## Exact SDL2 software sampling and diagnostic OSD exclusion

A complete offline examination of the **actual failed first-run**
4K artifact (`11677683656`) isolated the next two mismatches
*after* normalizing SDL's opaque alpha:

- **17,048** colour differences from the oracle's ideal floating-point
  1× center-of-texel mapping instead matched the real SDL2 software
  raster's **16.16 fixed-point nearest stepping** from the 1368×896
  fourfold presentation texture. That precise mapping agreed across
  every pixel outside the on-screen OSD; no arbitrary tolerance is used
- **3,567** changed pixels formed a native turbo/FPS OSD rectangle
  at `x=6..128`, `y=5..33` on the completed 4K SDL surface.
  The new disposable host patch suppresses the title-independent
  OSD **only when the explicit source-to-physical capture frame and
  filename both match**, and calls `snes_osd_present_done()`.
  All other frames preserve ordinary OSD behaviour

The 4K oracle now calculates the exact host's 16.16 fixed-step
nearest sampling from the validated *actual 4× native texture* and
continues to enforce pixel-exact RGB and opaque-alpha output on
**every one of 8,294,400 physical pixels**. It never ignores the
OSD rectangle, nor grants colour tolerance or source-art admission.
The independent native follow-up **passed** that complete strict oracle.
Future alternate renderers, different frames, 1P/VS geometry and Windows
backend outputs must satisfy their own full-pixel capture gates.

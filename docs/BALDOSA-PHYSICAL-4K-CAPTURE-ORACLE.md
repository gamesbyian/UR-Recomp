# QA-08: actual physical 3840×2160 Original-output capture gate

## Measured prerequisite versus missing final measurement

The pinned Baldosa route has proved genuine **342×224** source-wide
world pixels from a +48 backing margin and 43 visible pixels on each side,
then **1368×896** exact 4× nearest-density Original presentation. Neither
source nor density capture establishes physical **3840×2160** output.
The pure widescreen_output_composition contract separately resolves 7:6
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
every pixel against the original full-height source projected with
center-of-texel nearest sampling and the accepted Original pixel aspect.
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

**The third file is not produced by current native CI.** It must come from
a real 3840×2160 drawable, never from resizing the other two inputs.
Synthetic unit tests make artificial 4K buffers only to verify this
checker; a green unit test gives **zero actual 4K host acceptance**.

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
- Once one pinned Windows/Baldosa host can capture a genuine 3840×2160
  drawable, reuse its existing native workflow to provide the matching
  logical, 4× density and physical screenshots and call this checker.
  Do not add another source renderer or replace existing output viewport
  or display-resolution ownership.

## Baldosa desktop viewport binding (still awaiting physical witness)

The native Baldosa 342-wide adapter now assigns the desktop host's
`compute_viewport` callback to the *existing* first-party Original-mode
7:6 pixel-aspect policy. Its source dimensions are checked against either
logical or exact 1x–4x density output. A calibrated 342x224 scene maps
to [0,0,3840,2160] in a 3840x2160 drawable using the existing 512/513
fit; a complete 256x224 Original scene remains centered at
[480,0,2880,2160] with matte side margins. Unsupported +24 experiments,
invalid geometry or a stale wide admission leave host viewport unchanged.
A compiled native bridge test checks these coordinates and density cases.

This is a real host integration hook, **not** a real 4K screenshot or
native display acceptance. The independent physical drawable capture
and unchanged guest/PPU semantics remain required.

## Real native SDL 4K output execution candidate

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

**This is an acceptance *attempt*, not an established 4K result.**
A wrong output drawable, missing actual readback, one mismatched RGBA
pixel, time-bound failure or source divergence must fail CI. Any failure
is a real output integration finding to investigate, never a reason to
substitute a synthetically resized image or declare physical scanout.

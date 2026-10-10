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

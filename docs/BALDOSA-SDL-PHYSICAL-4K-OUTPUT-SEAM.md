# QA-08: physical SDL output readback seam

Status: opt-in native **instrumentation only**. No physical 4K accepted yet.

The pinned Baldosa SDL2 host's stock `SNESRECOMP_SCREENSHOT` reads the
raw SNES presentation texture, not the *actual* SDL-rendered drawable after
viewports, aspect correction or letterboxing. The existing strict oracle in
`tools/check_baldosa_physical_4k_capture.py` requires a separately captured
**3840×2160 drawable** from the completed real SDL renderer.

`tools/baldosa_sdl_physical_4k_capture_spike.py --framework baldosa/snesrecomp`
stages one strictly anchored modification in the **disposable Baldosa
framework checkout**. It adds a one-time SDL2 `SDL_RenderReadPixels` call
after the native host has actually drawn its Original 7:6 viewport texture
but before `SDL_RenderPresent`. The opt-in needs both:

- `UR_BALDOSA_PHYSICAL_4K_CAPTURE_FRAME=1872`: exact guest frame index
  already recorded by the source-world/density capture oracles
- `UR_BALDOSA_PHYSICAL_4K_CAPTURE_FILE=/absolute/native/ur-baldosa-output-001872.pam`

It must see an actual **3840×2160 renderer drawable**; a 1368×896
scaled texture, smaller SDL window, or screenshot from the root X display
fails the geometry gate. It saves the SDL's true ARGB8888 pixels as RGBA
PAM without synthesizing, cropping or nearest-scaling a source image.

The staging script is fail-closed on an unknown host render boundary,
idempotent on a known patched host, and is never linked to the product
Windows host or the authoritative guest implementation. Source pins and
toolchain patch manifest remain unchanged. Linux SDL2/Xvfb can provide a
test drawable, but a CI native route must explicitly set 3840×2160 SDL
output, disable linear filtering/OSD/CRT, and obtain same-frame genuine
source 1×/4× PAMs to run the existing full-output oracle.

**No release credit** for this capture seam until a real native route
writes the file and passes the pixel-exact 3840×2160 oracle. Even a
successful SDL readback is not physical monitor scanout or HD OBJ proof.

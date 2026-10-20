#!/usr/bin/env python3
"""Opt-in final-SDL-drawable readback for Modern acceptance, disposable host only.

Stages in a *cloned* pinned Baldosa framework runner; never patches repository
game code or the shipping user's executable. Screenshot pixels are captured
after SDL_RenderCopy/texture composition and before SDL_RenderPresent. This is
independent of the guest logical framebuffer. SDL2 path only; no silent SDL3
fallback. Reuses the pinning pattern of baldosa_sdl_physical_4k_capture_spike.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from baldosa_sdl_physical_4k_capture_spike import ANCHOR

MARK = "UR_MODERN_UI_SDL_DRAWABLE_CAPTURE"
START = "static void SdlRenderer_EndDraw(void)"
STOP = "static void SdlRenderer_Reconfigure(void)"

# Env-gated and write-once. Draw ordinal is the actual SDL presentation call,
# NOT emulated guest frame: the frontend may hold the latter completely still.
# Output P7 is *raw observed SDL pixels*, not a resized source-frame PNG.
INSTRUMENT = r"""/* UR_MODERN_UI_SDL_DRAWABLE_CAPTURE: QA-only, never a release feature.
 * Draw index counts actual SDL EndDraw calls even while guest frames are
 * paused. Explicit one-shot, output-size-checked SDL2 readback. An opt-in
 * fixture can convert the exact P7 bytes to lossless PNG independently. */
#if !SNESRECOMP_SDL3
static void UrQaModernReadDrawable(void) {
  static unsigned present_calls = 0;
  static int completed = 0;
  ++present_calls;
  if (completed) return;
  const char *target = getenv("UR_MODERN_VISUAL_SDL_CAPTURE_DRAW");
  const char *output = getenv("UR_MODERN_VISUAL_SDL_CAPTURE_FILE");
  const char *width_env = getenv("UR_MODERN_VISUAL_SDL_CAPTURE_EXPECT_WIDTH");
  const char *height_env = getenv("UR_MODERN_VISUAL_SDL_CAPTURE_EXPECT_HEIGHT");
  if (!target || !*target || !output || !*output ||
      !width_env || !*width_env || !height_env || !*height_env)
    return;
  char *end_t = NULL, *end_w = NULL, *end_h = NULL;
  unsigned long frame = strtoul(target, &end_t, 10);
  unsigned long expected_w = strtoul(width_env, &end_w, 10);
  unsigned long expected_h = strtoul(height_env, &end_h, 10);
  if (end_t == target || *end_t || target[0] == '-' ||
      end_w == width_env || *end_w || width_env[0] == '-' ||
      end_h == height_env || *end_h || height_env[0] == '-' ||
      frame < 1 || frame > 120000 ||
      expected_w < 320 || expected_w > 3840 ||
      expected_h < 224 || expected_h > 2160)
    return;
  if (present_calls != frame) return;
  completed = 1;
  int w = 0, h = 0;
  if (!snesrecomp_sdl_get_render_output_size(g_renderer, &w, &h) ||
      w != (int)expected_w || h != (int)expected_h) {
    fprintf(stderr, "UR_MODERN_VISUAL_SDL_CAPTURE refused=output-size"
            " draw=%u observed=%dx%d requested=%lux%lu\n",
            present_calls, w, h, expected_w, expected_h);
    return;
  }
  /* Bounds above cap decoded bytes at 3840*2160*4. */
  const size_t pitch = (size_t)w * 4u;
  uint8_t *rgba = (uint8_t *)malloc(pitch * (size_t)h);
  if (!rgba) {
    fprintf(stderr, "UR_MODERN_VISUAL_SDL_CAPTURE refused=allocation\n");
    return;
  }
  if (SDL_RenderReadPixels(g_renderer, NULL, SDL_PIXELFORMAT_ARGB8888,
                           rgba, (int)pitch) != 0) {
    fprintf(stderr, "UR_MODERN_VISUAL_SDL_CAPTURE refused=readback"
            " sdl_error=%s\n", SDL_GetError());
    free(rgba);
    return;
  }
  /* Do not silently overwrite another capture from the same user run. */
  FILE *existing = fopen(output, "rb");
  if (existing) {
    fclose(existing);
    fprintf(stderr, "UR_MODERN_VISUAL_SDL_CAPTURE refused=exists\n");
    free(rgba);
    return;
  }
  FILE *file = fopen(output, "wb");
  int ok = file != NULL;
  if (ok) ok = fprintf(file, "P7\nWIDTH %d\nHEIGHT %d\nDEPTH 4\n"
                       "MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n",
                       w, h) > 0;
  uint8_t *row = (uint8_t *)malloc(pitch);
  if (!row) ok = 0;
  for (int y = 0; ok && y < h; ++y) {
    const uint8_t *source = rgba + (size_t)y * pitch;
    for (int x = 0; x < w; ++x) {
      uint32_t pixel = 0;
      memcpy(&pixel, source + (size_t)x * 4u, 4u);
      row[x * 4 + 0] = (uint8_t)((pixel >> 16) & 255u);
      row[x * 4 + 1] = (uint8_t)((pixel >> 8) & 255u);
      row[x * 4 + 2] = (uint8_t)(pixel & 255u);
      row[x * 4 + 3] = (uint8_t)((pixel >> 24) & 255u);
    }
    if (fwrite(row, 1, pitch, file) != pitch) ok = 0;
  }
  free(row);
  if (file && fclose(file) != 0) ok = 0;
  if (!ok && file) remove(output);
  free(rgba);
  fprintf(stderr, "UR_MODERN_VISUAL_SDL_CAPTURE status=%s"
          " draw=%u guest_frame=%u output=%dx%d source=SDL_RenderReadPixels\n",
          ok ? "saved" : "failed", present_calls, g_present_frame, w, h);
}
#endif
"""

REPLACEMENT = """  snesrecomp_sdl_render_texture(g_renderer, g_texture, &g_sdl_renderer_rect,
                                &g_sdl_present_rect);
#if !SNESRECOMP_SDL3
  UrQaModernReadDrawable();
#endif
  SDL_RenderPresent(g_renderer);
"""


def patch_host(source: str) -> str:
    """Fail closed if the pinned host renderer or ABI is no longer exact."""
    if MARK in source:
        if source.count(MARK) != 1 or REPLACEMENT not in source:
            raise ValueError("partial/duplicate Modern SDL diagnostic")
        return source
    if source.count(ANCHOR) != 1 or source.count(START) != 1 or source.count(STOP) != 1:
        raise ValueError("pinned native SDL renderer drifted")
    lo, anchor, hi = source.index(START), source.index(ANCHOR), source.index(STOP)
    if not lo < anchor < hi:
        raise ValueError("capture anchor outside pinned native SDL EndDraw")
    return (source[:lo] + INSTRUMENT + "\n" + source[lo:])
        .replace(ANCHOR, REPLACEMENT, 1)


def stage(framework: Path) -> bool:
    root = framework.resolve()
    target = root / "runner/src/desktop/host_main.c"
    if target.is_symlink() or not target.is_file():
        raise ValueError("missing/redirected disposable framework SDL host")
    original = target.read_text(encoding="utf-8")
    patched = patch_host(original)
    if patched != original:
        target.write_text(patched, encoding="utf-8")
    return patched != original


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--framework", required=True, type=Path,
                   help="Cloned pinned baldosa/snesrecomp root, not project root")
    options = p.parse_args()
    changed = stage(options.framework)
    print("UR_MODERN_VISUAL_SDL_DIAGNOSTIC_STAGE changed=" + str(int(changed)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Stage an opt-in *real SDL drawable* 4K capture in a disposable Baldosa host.

The pinned SDL2 host already presents a 342x224 Original logical texture using
the title's compute_viewport callback. Its normal SCREENSHOT is a source/HD
texture dump, never the actual SDL output. This tiny diagnostic reads the
COMPLETE 3840x2160 SDL renderer output immediately before SDL_RenderPresent.

This edits only a disposable framework checkout; no ROM, generated guest C,
project toolchain patch pin, live Modern frontend or shipping host changes.
An exact pinned host source anchor and mutually explicit frame/file knobs are
required. The adapter is inert unless all opt-in conditions are met.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_BALDOSA_REAL_SDL_OUTPUT_4K_CAPTURE"
OSD_ANCHOR = """static void ComposeOsd(uint8 *dst, int pitch, int dst_w, int dst_h, int scale_div) {
  const uint32_t *px = NULL;"""
OSD_REPLACEMENT = """static void ComposeOsd(uint8 *dst, int pitch, int dst_w, int dst_h, int scale_div) {
  /* QA-08: the one explicit physical source-to-drawable validation frame
   * must contain ONLY the Original game picture. Suppress the turbo/FPS
   * OSD on this exact frame, not by tolerating a rectangle in the oracle.
   * Never change routine presentation or a missing/unmatched capture. */
  const char *ur4k_file = getenv("UR_BALDOSA_PHYSICAL_4K_CAPTURE_FILE");
  const char *ur4k_frame = getenv("UR_BALDOSA_PHYSICAL_4K_CAPTURE_FRAME");
  if (ur4k_file && *ur4k_file && ur4k_frame && *ur4k_frame) {
    char *ur4k_end = NULL;
    unsigned long ur4k_target = strtoul(ur4k_frame, &ur4k_end, 10);
    if (ur4k_end != ur4k_frame && *ur4k_end == '\\0' &&
        ur4k_target == g_present_frame) {
      snes_osd_present_done();
      return;
    }
  }
  const uint32_t *px = NULL;"""
ANCHOR = """  snesrecomp_sdl_render_texture(g_renderer, g_texture, &g_sdl_renderer_rect,
                                &g_sdl_present_rect);
  SDL_RenderPresent(g_renderer);
"""
IMPLEMENTATION = r"""/* UR_BALDOSA_REAL_SDL_OUTPUT_4K_CAPTURE: disposable SDL2 diagnostic.
 * This is a pixel readback from the REAL completed 3840x2160 renderer, not a
 * synthetic upscale of SNES PPU, a 4x texture dump, or an Xvfb root window.
 * Opt-in and exact guest-frame identity are mandatory. */
#if !SNESRECOMP_SDL3
static void UrBaldosaReadActual4kDrawable(void) {
  static int done;
  if (done) return;
  const char *path = getenv("UR_BALDOSA_PHYSICAL_4K_CAPTURE_FILE");
  const char *frame_env = getenv("UR_BALDOSA_PHYSICAL_4K_CAPTURE_FRAME");
  if (!path || !*path || !frame_env || !*frame_env) return;
  char *end = NULL;
  unsigned long target = strtoul(frame_env, &end, 10);
  if (end == frame_env || *end != '\0' || target != g_present_frame) return;
  int w = 0, h = 0;
  if (!snesrecomp_sdl_get_render_output_size(g_renderer, &w, &h) ||
      w != 3840 || h != 2160) {
    fprintf(stderr, "UR_BALDOSA_PHYSICAL_4K_CAPTURE_REJECT frame=%u"
            " reason=not-real-4k-drawable output=%dx%d\n",
            g_present_frame, w, h);
    done = 1;
    return;
  }
  const size_t pitch = (size_t)w * 4u;
  const size_t bytes = pitch * (size_t)h;
  uint8_t *pixels = (uint8_t *)malloc(bytes);
  if (!pixels) {
    fprintf(stderr, "UR_BALDOSA_PHYSICAL_4K_CAPTURE_REJECT frame=%u"
            " reason=allocation\n", g_present_frame);
    done = 1;
    return;
  }
  /* SDL reads the *composited* target, including the original title's
   * viewport and any physical letterboxing, but excluding window borders. */
  if (SDL_RenderReadPixels(g_renderer, NULL, SDL_PIXELFORMAT_ARGB8888,
                           pixels, (int)pitch) != 0) {
    fprintf(stderr, "UR_BALDOSA_PHYSICAL_4K_CAPTURE_REJECT frame=%u"
            " reason=readpixels error=%s\n",
            g_present_frame, SDL_GetError());
    free(pixels);
    done = 1;
    return;
  }
  FILE *out = fopen(path, "wb");
  int ok = out != NULL;
  if (ok) ok = fprintf(out,
      "P7\nWIDTH 3840\nHEIGHT 2160\nDEPTH 4\nMAXVAL 255\n"
      "TUPLTYPE RGB_ALPHA\nENDHDR\n") > 0;
  /* Raw SDL2 pixels are ARGB8888 in native host endian. Serialize RGBA
   * explicitly, one genuine output pixel at a time, never interpolate. */
  uint8_t row[3840 * 4];
  for (int y = 0; ok && y < h; ++y) {
    const uint8_t *source = pixels + (size_t)y * pitch;
    for (int x = 0; x < w; ++x) {
      uint32_t p = 0;
      memcpy(&p, source + (size_t)x * 4u, 4);
      row[x * 4 + 0] = (uint8_t)((p >> 16) & 255);
      row[x * 4 + 1] = (uint8_t)((p >> 8) & 255);
      row[x * 4 + 2] = (uint8_t)(p & 255);
      row[x * 4 + 3] = (uint8_t)((p >> 24) & 255);
    }
    if (fwrite(row, 1, pitch, out) != pitch) ok = 0;
  }
  if (out && fclose(out) != 0) ok = 0;
  if (!ok) remove(path);
  free(pixels);
  fprintf(stderr, "UR_BALDOSA_PHYSICAL_4K_CAPTURE frame=%u"
          " output=%dx%d source=SDL_RenderReadPixels status=%s\n",
          g_present_frame, w, h, ok ? "saved" : "failed");
  done = 1;
}
#endif
"""


def patch_host(source: str) -> str:
    if MARK in source:
        if source.count(MARK) != 1:
            raise ValueError("Capture marker repeated in pinned host")
        return source
    if source.count(ANCHOR) != 1 or source.count(OSD_ANCHOR) != 1:
        raise ValueError("Pinned SDL renderer/OSD ABI drift: no unique boundaries")
    first = source.index("static void SdlRenderer_EndDraw(void)")
    last = source.index("static void SdlRenderer_Reconfigure(void)", first)
    if not (first < source.index(ANCHOR) < last):
        raise ValueError("Native SDL present callback is not the one expected")
    # One exact host OSD frame is suppressed in the already-created
    # physical witness. All other SDL playback keeps its stock overlays.
    source = source.replace(OSD_ANCHOR, OSD_REPLACEMENT, 1)
    # The helper must be declared above the function that calls it.
    first = source.index("static void SdlRenderer_EndDraw(void)")
    source = source[:first] + IMPLEMENTATION + "\n" + source[first:]
    return source.replace(
        ANCHOR,
        """  snesrecomp_sdl_render_texture(g_renderer, g_texture, &g_sdl_renderer_rect,
                                &g_sdl_present_rect);
#if !SNESRECOMP_SDL3
  UrBaldosaReadActual4kDrawable();
#endif
  SDL_RenderPresent(g_renderer);
""",
        1,
    )


def stage(framework: Path) -> bool:
    target = framework / "runner/src/desktop/host_main.c"
    before = target.read_text(encoding="utf-8")
    after = patch_host(before)
    if after != before:
        target.write_text(after, encoding="utf-8")
    return before != after


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--framework", type=Path, required=True)
    a = p.parse_args()
    changed = stage(a.framework.resolve())
    print("UR_BALDOSA_PHYSICAL_4K_SDL_CAPTURE_STAGE changed=" + str(int(changed)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

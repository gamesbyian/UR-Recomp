#!/usr/bin/env python3
"""Opt-in consecutive SDL drawable recorder for an isolated pinned Baldosa checkout.

Injects a bounded recorder immediately before the existing SDL_RenderPresent.
Frames are actual host drawable readbacks, not reconstructed or interpolated.
Never patch shipping sources or the authoritative guest. Requires FFmpeg at run time.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_CONTINUOUS_NATIVE_SDL_CAPTURE_V1"
ANCHOR = """  snesrecomp_sdl_render_texture(g_renderer, g_texture, &g_sdl_renderer_rect,
                                &g_sdl_present_rect);
  SDL_RenderPresent(g_renderer);
"""
CODE = r"""
/* UR_CONTINUOUS_NATIVE_SDL_CAPTURE_V1: disposable SDL2 readback observer.
 * Raw BGRA8888 frames go to an FFmpeg lossless stream, with one sidecar
 * record for EACH host-presented guest-frame ID. No frame is invented. */
#if !SNESRECOMP_SDL3
static void UrContinuousNativeCapture(void) {
  static int initialized = 0, failed = 0, captured = 0;
  static unsigned long start = 0, count = 0, previous = 0;
  static int width = 0, height = 0;
  static FILE *pipe = NULL, *index = NULL;
  if (failed) return;
  if (!initialized) {
    initialized = 1;
    const char *begin = getenv("UR_NATIVE_VIDEO_START");
    const char *length = getenv("UR_NATIVE_VIDEO_COUNT");
    const char *target = getenv("UR_NATIVE_VIDEO_OUTPUT");
    if (!begin && !length && !target) return;
    if (!begin || !length || !target) { failed = 1; return; }
    char *e1 = NULL, *e2 = NULL;
    start = strtoul(begin, &e1, 10);
    count = strtoul(length, &e2, 10);
    if (!*begin || !*length || *e1 || *e2 || count < 600 ||
        count > 1200 || start < 1990) {
      fprintf(stderr, "UR_NATIVE_VIDEO_REJECT invalid frame window\n");
      failed = 1; return;
    }
    /* The target becomes a shell argument in popen: permit only a narrow,
     * relative, shell-inert filename alphabet. */
    size_t n = strlen(target);
    if (!n || n > 160 || target[0] == '-' || target[0] == '.' ||
        strchr(target, '/') || strchr(target, '\\')) {
      fprintf(stderr, "UR_NATIVE_VIDEO_REJECT unsafe output filename\n");
      failed = 1; return;
    }
    for (size_t i = 0; i < n; ++i) {
      char c = target[i];
      if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
            (c >= '0' && c <= '9') || c == '-' || c == '_' || c == '.')) {
        failed = 1; return;
      }
    }
    if (!snesrecomp_sdl_get_render_output_size(g_renderer, &width, &height) ||
        width < 342 || height < 224 || width > 3840 || height > 2160) {
      fprintf(stderr, "UR_NATIVE_VIDEO_REJECT drawable size %dx%d\n", width, height);
      failed = 1; return;
    }
    char sidecar[240], cmd[1024];
    snprintf(sidecar, sizeof(sidecar), "%s.frames.tsv", target);
    index = fopen(sidecar, "wb");
    if (!index) { failed = 1; return; }
    fprintf(index, "ordinal\\tguest_frame\\twidth\\theight\n");
    snprintf(cmd, sizeof(cmd), "ffmpeg -nostdin -hide_banner -loglevel error "
             "-y -f rawvideo -pix_fmt bgra -s %dx%d -r 60 -i pipe:0 "
             "-an -c:v ffv1 -level 3 -slicecrc 1 '%s' ",
             width, height, target);
    pipe = popen(cmd, "w");
    if (!pipe) { fclose(index); failed = 1; return; }
    fprintf(stderr, "UR_NATIVE_VIDEO_BEGIN start=%lu count=%lu drawable=%dx%d\n",
            start, count, width, height);
  }
  if (!pipe || g_present_frame < start || captured >= (int)count) return;
  unsigned long frame = g_present_frame;
  if ((captured && frame != previous + 1) || frame != start + (unsigned long)captured) {
    fprintf(stderr, "UR_NATIVE_VIDEO_REJECT discontinuity expected=%lu actual=%lu\n",
            start + (unsigned long)captured, frame);
    failed = 1;
  }
  size_t bytes = (size_t)width * (size_t)height * 4;
  uint8_t *buffer = failed ? NULL : (uint8_t *)malloc(bytes);
  if (!buffer) failed = 1;
  if (!failed && SDL_RenderReadPixels(g_renderer, NULL, SDL_PIXELFORMAT_ARGB8888,
                                      buffer, width * 4) != 0) failed = 1;
  if (!failed && fwrite(buffer, 1, bytes, pipe) != bytes) failed = 1;
  free(buffer);
  if (!failed) {
    fprintf(index, "%d\\t%lu\\t%d\\t%d\n", captured, frame, width, height);
    previous = frame;
    ++captured;
  }
  if (failed || captured == (int)count) {
    int rc = pclose(pipe);
    pipe = NULL;
    if (fclose(index) != 0) failed = 1;
    index = NULL;
    fprintf(stderr, "UR_NATIVE_VIDEO_END actual=%d expected=%lu last=%lu "
                    "ffmpeg_status=%d status=%s\n", captured, count, previous,
                    rc, (!failed && rc == 0) ? "complete" : "REJECT");
    if (rc != 0 || failed) {
      /* Leave incomplete evidence for diagnosis; validator must reject it. */
      failed = 1;
    }
  }
}
#endif
"""


def patch(source: str) -> str:
    if MARK in source:
        if source.count(MARK) != 1:
            raise ValueError("Duplicate recorder patch")
        return source
    if source.count(ANCHOR) != 1:
        raise ValueError("Pinned SDL2 present anchor changed")
    before = source.index("static void SdlRenderer_EndDraw(void)")
    after = source.index("static void SdlRenderer_Reconfigure(void)", before)
    pos = source.index(ANCHOR)
    if not before < pos < after:
        raise ValueError("Anchor outside SDL EndDraw")
    source = source[:before] + CODE + "\n" + source[before:]
    return source.replace(ANCHOR, ANCHOR.replace(
        "  SDL_RenderPresent(g_renderer);",
        "#if !SNESRECOMP_SDL3\n  UrContinuousNativeCapture();\n#endif\n"
        "  SDL_RenderPresent(g_renderer);"), 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework", type=Path, required=True)
    args = parser.parse_args()
    target = args.framework / "runner/src/desktop/host_main.c"
    original = target.read_text()
    modified = patch(original)
    if original != modified:
        target.write_text(modified)
    print(f"Native SDL recording hook staged: {original != modified}")


if __name__ == "__main__":
    main()

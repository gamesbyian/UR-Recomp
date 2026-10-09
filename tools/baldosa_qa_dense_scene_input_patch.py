#!/usr/bin/env python3
"""Ephemeral per-frame controller file shim for pinned Baldosa AOT **test checkout**.

The upstream `press` script command forces one released frame after each
hold, so it CANNOT reproduce a frame-dense historical movie by chaining
presses. This opt-in host input override is inserted into a disposable pinned
framework checkout in CI only. Never patch the project production submodule.
No guest memory writes, no changes to gameplay/PPU/saves.
"""
from __future__ import annotations
import argparse
from pathlib import Path

DECL = r"""
/* UR QA ONLY: deterministic per-frame scene input in a disposable build.
 * Format: absolute_guest_frame:duration:12-bit_hex_mask. All gaps idle.
 * Unset UR_QA_SCENE_INPUT_FILE leaves normal host input unchanged. */
typedef struct {
  uint32 start, end, mask;
} UrQaSceneInput;
static UrQaSceneInput g_ur_qa_scene[4096];
static unsigned g_ur_qa_count;
static uint32 g_ur_qa_first, g_ur_qa_last;
static int g_ur_qa_checked;

static uint32 UrQaSceneInputAt(uint32 frame) {
  if (!g_ur_qa_checked) {
    g_ur_qa_checked = 1;
    const char *path = getenv("UR_QA_SCENE_INPUT_FILE");
    if (path && *path) {
      FILE *f = fopen(path, "r");
      if (!f) { fprintf(stderr, "UR QA scene input missing: %s\n", path); exit(4); }
      char line[256];
      unsigned line_number = 0;
      uint32 prev_end = 0;
      while (fgets(line, sizeof(line), f)) {
        line_number++;
        if (line[0] == '#' || line[0] == '\n' || line[0] == '\r') continue;
        unsigned a = 0, duration = 0, mask = 0;
        char extra;
        int parsed = sscanf(line, " %u:%u:%x %c",
                            &a, &duration, &mask, &extra);
        if (parsed != 3 || duration == 0 || a < prev_end ||
            duration > 0xffffffffu - a || mask == 0 || mask > 0x0fffu ||
            g_ur_qa_count >= sizeof(g_ur_qa_scene)/sizeof(g_ur_qa_scene[0])) {
          fprintf(stderr, "UR QA invalid scene input %s:%u\n", path, line_number);
          fclose(f);
          exit(4);
        }
        UrQaSceneInput *event = &g_ur_qa_scene[g_ur_qa_count++];
        event->start = a;
        event->end = a + duration;
        event->mask = mask;
        prev_end = event->end;
        if (g_ur_qa_count == 1) g_ur_qa_first = a;
        g_ur_qa_last = event->end;
      }
      fclose(f);
      if (!g_ur_qa_count) {
        fprintf(stderr, "UR QA scene file contained no input: %s\n", path);
        exit(4);
      }
      fprintf(stderr, "UR QA dense input: %u original events, first=%u last=%u\n",
              g_ur_qa_count, g_ur_qa_first, g_ur_qa_last);
    }
  }
  if (!g_ur_qa_count || frame < g_ur_qa_first || frame >= g_ur_qa_last)
    return 0xffffffffu;
  for (unsigned i = 0; i < g_ur_qa_count; i++) {
    UrQaSceneInput *event = &g_ur_qa_scene[i];
    if (frame < event->start) return 0;
    if (frame < event->end) return event->mask;
  }
  return 0;
}

"""

MARKER_DECL = "static uint32 TickScript(void) {\n"
MARKER_INPUT = ("    inputs |= debug_server_get_controller_inputs();\n"
                "    double profile_start = ProfileStart();\n")
REPLACE_INPUT = (
    "    inputs |= debug_server_get_controller_inputs();\n"
    "    /* QA-only movie mask becomes authoritative ONLY inside its absolute\n"
    "     * scene window; all earlier frontend/menu input stays unchanged. */\n"
    "    const uint32 ur_qa_mask = UrQaSceneInputAt((uint32)snes_frame_counter);\n"
    "    if (ur_qa_mask != 0xffffffffu)\n"
    "      inputs = (inputs & ~0x0fffu) | ur_qa_mask;\n"
    "    double profile_start = ProfileStart();\n"
)


def patch(source: str) -> str:
    if (source.count(MARKER_DECL) != 1 or source.count(MARKER_INPUT) != 1
            or "UrQaSceneInputAt" in source):
        raise ValueError("pinned Baldosa input boundary absent or already patched")
    return (source.replace(MARKER_DECL, DECL + MARKER_DECL, 1)
            .replace(MARKER_INPUT, REPLACE_INPUT, 1))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", type=Path, required=True)
    args = ap.parse_args()
    host = args.host
    old = host.read_text(encoding="utf-8")
    host.write_text(patch(old), encoding="utf-8")
    print("QA-only dense scene-input shim installed into disposable Baldosa host")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

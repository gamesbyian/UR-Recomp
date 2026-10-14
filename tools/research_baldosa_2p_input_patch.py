#!/usr/bin/env python3
"""Research-only two-seat controller-stream shim for a DISPOSABLE Baldosa build.

QA-01's ``baldosa_qa_dense_scene_input_patch.py`` replays one-seat movies.
Race-relative original/native research needs the repository's ordinary
two-seat stream format (``tests/input/*.input``: ``start:duration:p1[:p2]``,
12-bit hex masks), which the pinned Baldosa host cannot read. This installs
an equivalent shim into a throwaway checkout of
``gamesbyian/uniracers-recomp``; it is an alternative to, never combined
with, the QA-01 patch, and never touches a production submodule.

Inside the stream's [first, last) frame window the stream becomes the
authoritative state of both seats (gaps are idle); outside it host input is
unchanged. No guest memory writes, no gameplay, PPU or save changes.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ENV = "UR_RESEARCH_2P_INPUT_FILE"

DECL = r"""
/* UR RESEARCH ONLY: two-seat controller stream in a disposable build.
 * Format: absolute_frame:duration:p1_hex[:p2_hex]; '#' comments; gaps idle.
 * Unset UR_RESEARCH_2P_INPUT_FILE leaves normal host input unchanged. */
typedef struct { uint32 start, end, mask; } UrResearch2pInput;
static UrResearch2pInput g_ur_r2p[8192];
static unsigned g_ur_r2p_count;
static uint32 g_ur_r2p_first, g_ur_r2p_last;
static int g_ur_r2p_checked;

static uint32 UrResearch2pInputAt(uint32 frame) {
  if (!g_ur_r2p_checked) {
    g_ur_r2p_checked = 1;
    const char *path = getenv("UR_RESEARCH_2P_INPUT_FILE");
    if (path && *path) {
      FILE *f = fopen(path, "r");
      if (!f) { fprintf(stderr, "UR research 2P input missing: %s\n", path); exit(4); }
      char line[256];
      unsigned line_number = 0;
      uint32 prev_end = 0;
      while (fgets(line, sizeof(line), f)) {
        line_number++;
        char *hash = strchr(line, '#');
        if (hash) *hash = 0;
        unsigned a = 0, duration = 0, p1 = 0, p2 = 0;
        char extra;
        int parsed = sscanf(line, " %u:%u:%x:%x %c", &a, &duration, &p1, &p2, &extra);
        if (parsed <= 0) continue;
        if (parsed == 3) p2 = 0;
        if ((parsed != 3 && parsed != 4) || duration == 0 || a < prev_end ||
            duration > 0xffffffffu - a || p1 > 0x0fffu || p2 > 0x0fffu ||
            g_ur_r2p_count >= sizeof(g_ur_r2p) / sizeof(g_ur_r2p[0])) {
          fprintf(stderr, "UR research 2P input invalid %s:%u\n", path, line_number);
          fclose(f);
          exit(4);
        }
        UrResearch2pInput *event = &g_ur_r2p[g_ur_r2p_count++];
        event->start = a;
        event->end = a + duration;
        event->mask = p1 | (p2 << 12);
        prev_end = event->end;
        if (g_ur_r2p_count == 1) g_ur_r2p_first = a;
        g_ur_r2p_last = event->end;
      }
      fclose(f);
      if (!g_ur_r2p_count) {
        fprintf(stderr, "UR research 2P input contained no events: %s\n", path);
        exit(4);
      }
      fprintf(stderr, "UR research 2P input: %u events, first=%u last=%u\n",
              g_ur_r2p_count, g_ur_r2p_first, g_ur_r2p_last);
    }
  }
  if (!g_ur_r2p_count || frame < g_ur_r2p_first || frame >= g_ur_r2p_last)
    return 0xffffffffu;
  for (unsigned i = 0; i < g_ur_r2p_count; i++) {
    if (frame < g_ur_r2p[i].start) return 0;
    if (frame < g_ur_r2p[i].end) return g_ur_r2p[i].mask;
  }
  return 0;
}

"""

MARKER_DECL = "static uint32 TickScript(void) {\n"
MARKER_INPUT = ("    inputs |= debug_server_get_controller_inputs();\n"
                "    double profile_start = ProfileStart();\n")
REPLACE_INPUT = (
    "    inputs |= debug_server_get_controller_inputs();\n"
    "    /* Research-only two-seat stream is authoritative only inside its\n"
    "     * own frame window; host input elsewhere is unchanged. */\n"
    "    const uint32 ur_r2p_mask = UrResearch2pInputAt((uint32)snes_frame_counter);\n"
    "    if (ur_r2p_mask != 0xffffffffu)\n"
    "      inputs = (inputs & ~0xffffffu) | ur_r2p_mask;\n"
    "    double profile_start = ProfileStart();\n"
)


def patch(source: str) -> str:
    if (source.count(MARKER_DECL) != 1 or source.count(MARKER_INPUT) != 1
            or "UrResearch2pInputAt" in source or "UrQaSceneInputAt" in source):
        raise ValueError("pinned Baldosa input boundary absent, or a shim is already installed")
    return (source.replace(MARKER_DECL, DECL + MARKER_DECL, 1)
            .replace(MARKER_INPUT, REPLACE_INPUT, 1))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", type=Path, required=True,
                    help="snesrecomp/runner/src/desktop/host_main.c of a disposable checkout")
    args = ap.parse_args()
    args.host.write_text(patch(args.host.read_text(encoding="utf-8")), encoding="utf-8")
    print("research-only two-seat input shim installed into disposable Baldosa host")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

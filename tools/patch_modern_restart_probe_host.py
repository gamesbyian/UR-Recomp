#!/usr/bin/env python3
"""Inject a diagnostic-only race-restart snapshot probe into a generated host."""

from __future__ import annotations

import argparse
from pathlib import Path


INCLUDE_ANCHOR = '#include "snesrecomp_rom_identity.h"  /* generated from rom_identity.txt */\n'
HOST_ANCHOR = "static const SnesDesktopHostGame kGameHost = {\n"
FIELD_ANCHOR = '    .game_info           = &kGameInfo,\n'

PROBE = r'''
#include "common_rtl.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { kUrRestartProbeCap = 2 * 1024 * 1024, kUrRestartProbeWindow = 60 };

static uint8_t *g_ur_restart_anchor;
static size_t g_ur_restart_anchor_len;
static uint8_t *g_ur_restart_expected;
static size_t g_ur_restart_expected_len;
static unsigned g_ur_restart_probe_count;
static int g_ur_restart_probe_phase;
static int g_ur_restart_prev_in_race;

static int UrRestartProbeSave(uint8_t *dst, size_t *len) {
    const size_t n = RtlSaveSnapshotToMemory(dst, kUrRestartProbeCap);
    if (!n) return 0;
    *len = n;
    return 1;
}

static void UrRestartProbeAfterRunFrame(const SnesDesktopHostFrameStats *stats) {
    const int in_race = g_ram[0x0313] == 1;

    if (g_ur_restart_probe_phase == 0 && in_race && !g_ur_restart_prev_in_race) {
        g_ur_restart_anchor = (uint8_t *)malloc(kUrRestartProbeCap);
        g_ur_restart_expected = (uint8_t *)malloc(kUrRestartProbeCap);
        if (!g_ur_restart_anchor || !g_ur_restart_expected ||
            !UrRestartProbeSave(g_ur_restart_anchor, &g_ur_restart_anchor_len)) {
            fprintf(stderr, "UR_RESTART_PROBE FAIL capture\n");
            g_ur_restart_probe_phase = 4;
        } else {
            fprintf(stderr,
                    "UR_RESTART_PROBE captured=1 frame=%u bytes=%zu\n",
                    stats ? stats->frame : 0u,
                    g_ur_restart_anchor_len);
            g_ur_restart_probe_count = 0;
            g_ur_restart_probe_phase = 1;
        }
    } else if (g_ur_restart_probe_phase == 1) {
        if (++g_ur_restart_probe_count == kUrRestartProbeWindow) {
            if (!UrRestartProbeSave(
                    g_ur_restart_expected, &g_ur_restart_expected_len)) {
                fprintf(stderr, "UR_RESTART_PROBE FAIL expected-capture\\n");
                g_ur_restart_probe_phase = 4;
            } else if (!RtlLoadSnapshotFromMemory(
                           g_ur_restart_anchor, g_ur_restart_anchor_len)) {
                fprintf(stderr, "UR_RESTART_PROBE FAIL restore-refused\\n");
                g_ur_restart_probe_phase = 4;
            } else {
                uint8_t *immediate = (uint8_t *)malloc(kUrRestartProbeCap);
                size_t immediate_len = 0;
                const int immediate_ok =
                    immediate &&
                    UrRestartProbeSave(immediate, &immediate_len) &&
                    immediate_len == g_ur_restart_anchor_len &&
                    memcmp(immediate, g_ur_restart_anchor, immediate_len) == 0;
                free(immediate);
                if (!immediate_ok) {
                    fprintf(stderr,
                            "UR_RESTART_PROBE FAIL immediate-restore-mismatch\\n");
                    g_ur_restart_probe_phase = 4;
                } else {
                    fprintf(stderr, "UR_RESTART_PROBE immediate_equal=1\\n");
                    g_ur_restart_probe_count = 0;
                    g_ur_restart_probe_phase = 3;
                }
            }
        }
    } else if (g_ur_restart_probe_phase == 3) {
        if (++g_ur_restart_probe_count == kUrRestartProbeWindow) {
            uint8_t *actual = (uint8_t *)malloc(kUrRestartProbeCap);
            size_t actual_len = 0;
            const int ok =
                actual &&
                UrRestartProbeSave(actual, &actual_len) &&
                actual_len == g_ur_restart_expected_len &&
                memcmp(actual, g_ur_restart_expected, actual_len) == 0;
            fprintf(stderr,
                    "UR_RESTART_PROBE %s replay_equal=%d window=%u\n",
                    ok ? "PASS" : "FAIL",
                    ok ? 1 : 0,
                    (unsigned)kUrRestartProbeWindow);
            free(actual);
            g_ur_restart_probe_phase = 4;
        }
    }

    g_ur_restart_prev_in_race = in_race;
}
'''


def patch_text(source: str) -> str:
    if "UR_RESTART_PROBE captured=1" in source:
        return source
    if INCLUDE_ANCHOR not in source:
        raise ValueError("generated host include anchor not found")
    if HOST_ANCHOR not in source:
        raise ValueError("generated host struct anchor not found")
    if FIELD_ANCHOR not in source:
        raise ValueError("generated host game_info field not found")

    source = source.replace(INCLUDE_ANCHOR, INCLUDE_ANCHOR + PROBE + "\n", 1)
    source = source.replace(
        FIELD_ANCHOR,
        FIELD_ANCHOR
        + "    .before_run_frame    = &UrRestartProbeBeforeRunFrame,\n"
        + "    .after_run_frame     = &UrRestartProbeAfterRunFrame,\n",
        1,
    )
    return source


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("main_c", type=Path)
    args = parser.parse_args()

    original = args.main_c.read_text(encoding="utf-8")
    patched = patch_text(original)
    args.main_c.write_text(patched, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

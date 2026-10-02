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
#include "netplay/snes_state_digest.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { kUrRestartProbeWindow = 60 };

static size_t g_ur_restart_probe_cap;
static uint8_t *g_ur_restart_anchor;
static size_t g_ur_restart_anchor_len;
static SnesStateDigestParts g_ur_restart_anchor_digest;
static SnesStateDigestParts g_ur_restart_expected_digest;
static unsigned g_ur_restart_probe_count;
static int g_ur_restart_probe_phase;
static int g_ur_restart_prev_in_race;

static int UrRestartProbeSave(uint8_t *dst, size_t *len) {
    if (!g_ur_restart_probe_cap) return 0;
    const size_t n =
        RtlRollbackSaveToMemory(dst, g_ur_restart_probe_cap);
    if (!n) return 0;
    *len = n;
    return 1;
}

static void UrRestartProbeAfterRunFrame(const SnesDesktopHostFrameStats *stats) {
    const int in_race = g_ram[0x0313] == 1;

    if (g_ur_restart_probe_phase == 0 && in_race && !g_ur_restart_prev_in_race) {
        g_ur_restart_probe_cap = RtlRollbackSnapshotBound();
        g_ur_restart_anchor = (uint8_t *)malloc(g_ur_restart_probe_cap);
        if (!g_ur_restart_probe_cap ||
            !g_ur_restart_anchor ||
            !UrRestartProbeSave(g_ur_restart_anchor, &g_ur_restart_anchor_len)) {
            fprintf(stderr, "UR_RESTART_PROBE FAIL capture\n");
            g_ur_restart_probe_phase = 4;
        } else {
            snes_state_digest_parts(&g_ur_restart_anchor_digest);
            fprintf(stderr,
                    "UR_RESTART_PROBE captured=1 frame=%u bytes=%zu digest=%08x\n",
                    stats ? stats->frame : 0u,
                    g_ur_restart_anchor_len,
                    (unsigned)g_ur_restart_anchor_digest.master);
            g_ur_restart_probe_count = 0;
            g_ur_restart_probe_phase = 1;
        }
    } else if (g_ur_restart_probe_phase == 1) {
        if (++g_ur_restart_probe_count == kUrRestartProbeWindow) {
            snes_state_digest_parts(&g_ur_restart_expected_digest);
            if (!RtlRollbackLoadFromMemory(
                    g_ur_restart_anchor, g_ur_restart_anchor_len)) {
                fprintf(stderr, "UR_RESTART_PROBE FAIL restore-refused\n");
                g_ur_restart_probe_phase = 4;
            } else {
                SnesStateDigestParts immediate;
                snes_state_digest_parts(&immediate);
                if (immediate.master != g_ur_restart_anchor_digest.master) {
                    const uint32_t part = snes_state_digest_first_diff(
                        &g_ur_restart_anchor_digest, &immediate);
                    fprintf(stderr,
                            "UR_RESTART_PROBE FAIL immediate-digest-mismatch "
                            "part=%s expected=%08x actual=%08x\n",
                            snes_state_digest_part_name(part),
                            (unsigned)g_ur_restart_anchor_digest.master,
                            (unsigned)immediate.master);
                    g_ur_restart_probe_phase = 4;
                } else {
                    fprintf(stderr,
                            "UR_RESTART_PROBE immediate_equal=1 digest=%08x\n",
                            (unsigned)immediate.master);
                    g_ur_restart_probe_count = 0;
                    g_ur_restart_probe_phase = 3;
                }
            }
        }
    } else if (g_ur_restart_probe_phase == 3) {
        if (++g_ur_restart_probe_count == kUrRestartProbeWindow) {
            SnesStateDigestParts actual;
            snes_state_digest_parts(&actual);
            const int ok =
                actual.master == g_ur_restart_expected_digest.master;
            if (!ok) {
                const uint32_t part = snes_state_digest_first_diff(
                    &g_ur_restart_expected_digest, &actual);
                fprintf(stderr,
                        "UR_RESTART_PROBE FAIL replay_equal=0 window=%u "
                        "part=%s expected=%08x actual=%08x\n",
                        (unsigned)kUrRestartProbeWindow,
                        snes_state_digest_part_name(part),
                        (unsigned)g_ur_restart_expected_digest.master,
                        (unsigned)actual.master);
            } else {
                fprintf(stderr,
                        "UR_RESTART_PROBE PASS replay_equal=1 window=%u "
                        "digest=%08x\n",
                        (unsigned)kUrRestartProbeWindow,
                        (unsigned)actual.master);
            }
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

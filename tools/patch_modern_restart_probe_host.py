#!/usr/bin/env python3
"""Inject the modern-product Restart Race acceptance into a generated host."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INCLUDE_ANCHOR = '#include "snesrecomp_rom_identity.h"  /* generated from rom_identity.txt */\n'
HOST_ANCHOR = "static const SnesDesktopHostGame kGameHost = {\n"
FIELD_ANCHOR = '    .game_info           = &kGameInfo,\n'

PROBE = r'''
#include "common_rtl.h"
#include "modern_session_c_api.h"
#include "netplay/snes_state_digest.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { kUrRestartProbeWindow = 60 };

static UrModernSession *g_ur_restart_session;
static SnesStateDigestParts g_ur_restart_anchor_digest;
static SnesStateDigestParts g_ur_restart_expected_digest;
static uint8_t *g_ur_restart_anchor_sram;
static size_t g_ur_restart_anchor_sram_len;
static unsigned g_ur_restart_probe_count;
static int g_ur_restart_probe_phase;
static int g_ur_restart_prev_in_race;

static size_t UrRestartSave(void *dst, size_t capacity) {
    return RtlRollbackSaveToMemory(dst, capacity);
}

static bool UrRestartLoad(const void *src, size_t size) {
    return RtlRollbackLoadFromMemory(src, size);
}

static void UrRestartTimingLock(int active) {
    RtlSetRewindAudioTimingLock(active != 0);
}

static void UrRestartReconcilePresentation(void) {
    RtlAudioSetFastForward(true);
    RtlAudioSetFastForward(false);
}

static int UrRestartSramMatchesAnchor(void) {
    if (!g_ur_restart_anchor_sram || g_ur_restart_anchor_sram_len == 0)
        return g_sram_size == 0;
    return g_sram &&
           (size_t)g_sram_size == g_ur_restart_anchor_sram_len &&
           memcmp(g_sram, g_ur_restart_anchor_sram,
                  g_ur_restart_anchor_sram_len) == 0;
}

static int UrRestartEnsureSession(void) {
    if (g_ur_restart_session)
        return 1;
    const size_t cap = RtlRollbackSnapshotBound();
    if (!cap)
        return 0;
    g_ur_restart_session = ur_modern_session_create(
        1,
        cap,
        &UrRestartSave,
        &UrRestartLoad,
        NULL,
        NULL,
        &UrRestartTimingLock,
        &UrRestartReconcilePresentation);
    return g_ur_restart_session != NULL;
}

static int UrRestartCaptureOracle(const SnesDesktopHostFrameStats *stats) {
    if (!UrRestartEnsureSession())
        return 0;
    if (!ur_modern_session_restart_available(g_ur_restart_session))
        return 0;

    snes_state_digest_parts(&g_ur_restart_anchor_digest);
    if (g_sram_size > 0) {
        g_ur_restart_anchor_sram_len = (size_t)g_sram_size;
        g_ur_restart_anchor_sram =
            (uint8_t *)malloc(g_ur_restart_anchor_sram_len);
        if (!g_ur_restart_anchor_sram)
            return 0;
        memcpy(g_ur_restart_anchor_sram, g_sram,
               g_ur_restart_anchor_sram_len);
    }

    fprintf(stderr,
            "UR_RESTART_PROBE captured=1 frame=%u digest=%08x command_path=armed\n",
            stats ? stats->frame : 0u,
            (unsigned)g_ur_restart_anchor_digest.master);
    return 1;
}

static int UrRestartRequestAndValidateImmediate(const char *label) {
    const UrModernSessionResult result =
        ur_modern_session_restart_race(g_ur_restart_session);
    if (result != UR_MODERN_SESSION_APPLIED) {
        fprintf(stderr,
                "UR_RESTART_PROBE FAIL %s-dispatch result=%d\n",
                label,
                (int)result);
        return 0;
    }

    SnesStateDigestParts immediate;
    snes_state_digest_parts(&immediate);
    if (immediate.master != g_ur_restart_anchor_digest.master) {
        const uint32_t part = snes_state_digest_first_diff(
            &g_ur_restart_anchor_digest, &immediate);
        fprintf(stderr,
                "UR_RESTART_PROBE FAIL %s-immediate-digest part=%s "
                "expected=%08x actual=%08x\n",
                label,
                snes_state_digest_part_name(part),
                (unsigned)g_ur_restart_anchor_digest.master,
                (unsigned)immediate.master);
        return 0;
    }
    if (!UrRestartSramMatchesAnchor()) {
        fprintf(stderr, "UR_RESTART_PROBE FAIL %s-sram-mutated\n", label);
        return 0;
    }

    fprintf(stderr,
            "UR_RESTART_PROBE %s_applied=1 immediate_equal=1 "
            "sram_progression_unchanged=1 digest=%08x\n",
            label,
            (unsigned)immediate.master);
    return 1;
}

static int UrRestartReplayMatchesExpected(const char *label) {
    SnesStateDigestParts actual;
    snes_state_digest_parts(&actual);
    if (actual.master != g_ur_restart_expected_digest.master) {
        const uint32_t part = snes_state_digest_first_diff(
            &g_ur_restart_expected_digest, &actual);
        fprintf(stderr,
                "UR_RESTART_PROBE FAIL %s-replay window=%u part=%s "
                "expected=%08x actual=%08x\n",
                label,
                (unsigned)kUrRestartProbeWindow,
                snes_state_digest_part_name(part),
                (unsigned)g_ur_restart_expected_digest.master,
                (unsigned)actual.master);
        return 0;
    }
    return 1;
}

static void UrRestartProbeAfterRunFrame(const SnesDesktopHostFrameStats *stats) {
    const int in_race = g_ram[0x0313] == 1;

    if (!UrRestartEnsureSession()) {
        fprintf(stderr, "UR_RESTART_PROBE FAIL session-create\n");
        g_ur_restart_probe_phase = 9;
        return;
    }

    ur_modern_session_observe_race_active(g_ur_restart_session, in_race);

    if (g_ur_restart_probe_phase == 0 &&
        in_race && !g_ur_restart_prev_in_race) {
        if (!UrRestartCaptureOracle(stats)) {
            fprintf(stderr, "UR_RESTART_PROBE FAIL capture\n");
            g_ur_restart_probe_phase = 9;
        } else {
            g_ur_restart_probe_count = 0;
            g_ur_restart_probe_phase = 1;
        }
    } else if (g_ur_restart_probe_phase == 1) {
        if (++g_ur_restart_probe_count == kUrRestartProbeWindow) {
            snes_state_digest_parts(&g_ur_restart_expected_digest);
            if (!UrRestartRequestAndValidateImmediate("restart1")) {
                g_ur_restart_probe_phase = 9;
            } else {
                g_ur_restart_probe_count = 0;
                g_ur_restart_probe_phase = 2;
            }
        }
    } else if (g_ur_restart_probe_phase == 2) {
        if (++g_ur_restart_probe_count == kUrRestartProbeWindow) {
            if (!UrRestartReplayMatchesExpected("restart1")) {
                g_ur_restart_probe_phase = 9;
            } else if (!UrRestartRequestAndValidateImmediate("restart2")) {
                g_ur_restart_probe_phase = 9;
            } else {
                g_ur_restart_probe_count = 0;
                g_ur_restart_probe_phase = 3;
            }
        }
    } else if (g_ur_restart_probe_phase == 3) {
        if (++g_ur_restart_probe_count == kUrRestartProbeWindow) {
            if (!UrRestartReplayMatchesExpected("restart2")) {
                g_ur_restart_probe_phase = 9;
            } else {
                fprintf(stderr,
                        "UR_RESTART_PROBE PASS command_dispatch=1 "
                        "repeated_restart_equal=1 window=%u\n",
                        (unsigned)kUrRestartProbeWindow);
                g_ur_restart_probe_phase = 9;
            }
        }
    }

    g_ur_restart_prev_in_race = in_race;
}
'''


def patch_text(source: str) -> str:
    if "UR_RESTART_PROBE PASS command_dispatch=1" in source:
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


def patch_cmake_text(source: str, product_root: Path = ROOT) -> str:
    marker = "# UR_RESTART_PRODUCT_INTEGRATION"
    if marker in source:
        return source

    match = re.search(r"add_executable\(([^\s\)]+)", source)
    if not match:
        raise ValueError("generated CMake target anchor not found")

    target = match.group(1)
    product_dir = (product_root / "native" / "product").as_posix()
    sources = [
        "session_control.cpp",
        "session_runtime_adapter.cpp",
        "race_restart_anchor.cpp",
        "race_restart_lifecycle.cpp",
        "modern_session_runtime.cpp",
        "modern_session_c_api.cpp",
    ]
    source_lines = "\n".join(
        f'    "{product_dir}/{name}"' for name in sources
    )
    return (
        source.rstrip()
        + "\n\n"
        + marker
        + "\n"
        + f'target_include_directories({target} PRIVATE "{product_dir}")\n'
        + f"target_sources({target} PRIVATE\n"
        + source_lines
        + "\n"
        + '    "${SNESRECOMP_ROOT}/runner/src/netplay/snes_state_digest.c"\n'
        + ")\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("main_c", type=Path)
    parser.add_argument("--cmake", type=Path)
    args = parser.parse_args()

    original = args.main_c.read_text(encoding="utf-8")
    patched = patch_text(original)
    args.main_c.write_text(patched, encoding="utf-8")

    if args.cmake is not None:
        cmake_original = args.cmake.read_text(encoding="utf-8")
        cmake_patched = patch_cmake_text(cmake_original)
        args.cmake.write_text(cmake_patched, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Inject modern-product Restart Race acceptance into a generated host."""

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
#include "desktop/host_main.h"
#include "desktop/config.h"
#include "desktop/sdl_compat.h"
#include "snes_overlay_draw.h"
#include "modern_session_c_api.h"
#include "modern_pause_menu.h"
#include "uniracers_restart_policy.h"
#include "netplay/snes_state_digest.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { kUrRestartProbeWindow = 60 };

static UrModernSession *g_ur_restart_session;
static SnesStateDigestParts g_ur_restart_anchor_digest;
static SnesStateDigestParts g_ur_restart_expected_digest;
static unsigned g_ur_restart_probe_count;
static int g_ur_restart_probe_phase;
static int g_ur_restart_prev_in_race;
static int g_ur_restart_results_mode = -1;
static UrUniracersRestartPolicyState g_ur_restart_title_policy;
static UrUniracersRestartSurface g_ur_restart_surface;
static int g_ur_session_key_selftest_done;
static int g_ur_session_overlay_selftest_pending;
static int g_ur_session_gamepad_selftest_done;
static UrModernPauseMenu g_ur_pause_menu;
static uint8_t *g_ur_restart_before_sram;
static size_t g_ur_restart_before_sram_len;

static size_t UrRestartSave(void *dst, size_t capacity) {
    return RtlRollbackSaveToMemory(dst, capacity);
}

static bool UrRestartLoad(const void *src, size_t size) {
    return ur_modern_session_load_preserving_persistent_bytes(
        &RtlRollbackLoadFromMemory,
        src,
        size,
        g_sram,
        g_sram_size > 0 ? (size_t)g_sram_size : 0u);
}

static void UrRestartTimingLock(int active) {
    RtlSetRewindAudioTimingLock(active != 0);
}

static void UrRestartReconcilePresentation(void) {
    RtlAudioSetFastForward(true);
    RtlAudioSetFastForward(false);
}

static int UrRestartResultsMode(void) {
    if (g_ur_restart_results_mode < 0) {
        const char *mode = getenv("UR_RESTART_PROBE_MODE");
        g_ur_restart_results_mode =
            mode && strcmp(mode, "results") == 0 ? 1 : 0;
    }
    return g_ur_restart_results_mode;
}

static int UrRestartCopyCurrentSram(void) {
    free(g_ur_restart_before_sram);
    g_ur_restart_before_sram = NULL;
    g_ur_restart_before_sram_len =
        g_sram_size > 0 ? (size_t)g_sram_size : 0u;
    if (g_ur_restart_before_sram_len == 0)
        return 1;
    if (!g_sram)
        return 0;
    g_ur_restart_before_sram =
        (uint8_t *)malloc(g_ur_restart_before_sram_len);
    if (!g_ur_restart_before_sram)
        return 0;
    memcpy(g_ur_restart_before_sram, g_sram,
           g_ur_restart_before_sram_len);
    return 1;
}

static int UrRestartSramStillMatchesPreRequest(void) {
    if (g_ur_restart_before_sram_len == 0)
        return g_sram_size == 0;
    return g_sram &&
           (size_t)g_sram_size == g_ur_restart_before_sram_len &&
           memcmp(g_sram, g_ur_restart_before_sram,
                  g_ur_restart_before_sram_len) == 0;
}

static int UrRestartNonCartEqualsAnchor(
    const SnesStateDigestParts *actual) {
    return actual->cpu == g_ur_restart_anchor_digest.cpu &&
           actual->wram == g_ur_restart_anchor_digest.wram &&
           actual->apu == g_ur_restart_anchor_digest.apu &&
           actual->ppu == g_ur_restart_anchor_digest.ppu &&
           actual->dma == g_ur_restart_anchor_digest.dma;
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
        &snesrecomp_desktop_set_paused,
        &snesrecomp_desktop_is_paused,
        &UrRestartTimingLock,
        &UrRestartReconcilePresentation);
    return g_ur_restart_session != NULL;
}

static int UrModernSystemKeyDown(int key, int mod, int repeat) {
    if (repeat || !UrRestartEnsureSession())
        return 0;

    UrModernSessionKey semantic;
    if (key == SDLK_ESCAPE) {
        semantic = UR_MODERN_SESSION_KEY_ESCAPE;
    } else if ((key == SDLK_RETURN || key == SDLK_KP_ENTER) &&
               ur_modern_session_is_paused(g_ur_restart_session)) {
        semantic = UR_MODERN_SESSION_KEY_ACCEPT;
    } else if (key == SDLK_r && (mod & KMOD_CTRL) &&
               ur_modern_session_restart_available(g_ur_restart_session)) {
        semantic = UR_MODERN_SESSION_KEY_RESTART;
    } else {
        return 0;
    }

    const UrModernSessionResult result =
        ur_modern_session_handle_key(g_ur_restart_session, semantic);
    fprintf(stderr,
            "UR_SESSION_KEY key=%d semantic=%d result=%d paused=%d restart=%d\n",
            key,
            (int)semantic,
            (int)result,
            ur_modern_session_is_paused(g_ur_restart_session),
            ur_modern_session_restart_available(g_ur_restart_session));
    return 1;
}

static int UrModernSystemGamepadButton(int button, int pressed) {
    if (!UrRestartEnsureSession())
        return 0;

    const int paused = ur_modern_session_is_paused(g_ur_restart_session);
    if (!pressed)
        return paused ? 1 : 0;

    if (button == kGamepadBtn_Start) {
        const UrModernSessionResult result =
            ur_modern_session_handle_key(
                g_ur_restart_session, UR_MODERN_SESSION_KEY_ESCAPE);
        if (ur_modern_session_is_paused(g_ur_restart_session))
            ur_modern_pause_menu_reset(&g_ur_pause_menu);
        return result == UR_MODERN_SESSION_APPLIED ||
               result == UR_MODERN_SESSION_NO_OP;
    }

    if (!paused)
        return 0;

    const int restart =
        ur_modern_session_restart_available(g_ur_restart_session);
    if (button == kGamepadBtn_DpadUp) {
        ur_modern_pause_menu_move(&g_ur_pause_menu, -1, restart);
    } else if (button == kGamepadBtn_DpadDown) {
        ur_modern_pause_menu_move(&g_ur_pause_menu, 1, restart);
    } else if (button == kGamepadBtn_A) {
        const UrModernPauseItem item =
            ur_modern_pause_menu_selected(&g_ur_pause_menu, restart);
        if (item == UR_MODERN_PAUSE_RESTART) {
            (void)ur_modern_session_handle_key(
                g_ur_restart_session, UR_MODERN_SESSION_KEY_RESTART);
        } else {
            (void)ur_modern_session_handle_key(
                g_ur_restart_session, UR_MODERN_SESSION_KEY_ACCEPT);
        }
    } else if (button == kGamepadBtn_B) {
        (void)ur_modern_session_handle_key(
            g_ur_restart_session, UR_MODERN_SESSION_KEY_ACCEPT);
    }
    return 1;
}

static int UrSessionKeySelftest(void) {
    if (g_ur_session_key_selftest_done)
        return 1;
    if (!UrModernSystemKeyDown(SDLK_ESCAPE, 0, 0) ||
        !ur_modern_session_is_paused(g_ur_restart_session)) {
        fprintf(stderr, "UR_SESSION_KEY FAIL pause-dispatch\n");
        return 0;
    }
    /* Leave the host paused until the post-compose overlay has actually
     * rendered once. The overlay callback resumes it, proving both hooks are
     * on the real desktop presentation path. */
    g_ur_session_key_selftest_done = 1;
    g_ur_session_overlay_selftest_pending = 1;
    return 1;
}

static void UrModernSystemOverlay(
    uint8_t *dst,
    size_t pitch,
    int width,
    int height) {
    if (!dst || pitch < 4 || width <= 0 || height <= 0 ||
        !UrRestartEnsureSession()) {
        return;
    }

    const int paused =
        ur_modern_session_is_paused(g_ur_restart_session);
    const int results =
        g_ur_restart_surface == UR_UNIRACERS_RESTART_RESULTS;
    const int restart =
        ur_modern_session_restart_available(g_ur_restart_session);
    if (!paused && !results && !g_ur_session_overlay_selftest_pending)
        return;

    uint32_t *pixels = (uint32_t *)dst;
    const int stride = (int)(pitch / 4u);
    const int panel_w = width < 220 ? width - 16 : 212;
    const int panel_h = paused ? 54 : 30;
    const int x = (width - panel_w) / 2;
    const int y = paused ? (height - panel_h) / 2 : height - panel_h - 8;

    snes_ovl_fill_rect(
        pixels, stride, height, x, y, panel_w, panel_h, 0xE0202020u);
    snes_ovl_stroke_rect(
        pixels, stride, height, x, y, panel_w, panel_h, 0xFFF0F0F0u);

    if (paused) {
        ur_modern_pause_menu_move(&g_ur_pause_menu, 0, restart);
        const UrModernPauseItem selected =
            ur_modern_pause_menu_selected(&g_ur_pause_menu, restart);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + 7,
            "PAUSED", 0xFFFFFFFFu, 1);
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + 22,
            selected == UR_MODERN_PAUSE_RESUME ? "> RESUME" : "  RESUME",
            0xFFFFFFFFu, 1);
        if (restart) {
            snes_ovl_draw_text(
                pixels, stride, height, x + 8, y + 37,
                selected == UR_MODERN_PAUSE_RESTART
                    ? "> RESTART" : "  RESTART",
                0xFFFFFFFFu, 1);
        }
    } else if (results && restart) {
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + 11,
            "CTRL+R  RETRY", 0xFFFFFFFFu, 1);
    }

    if (g_ur_session_overlay_selftest_pending) {
        g_ur_session_overlay_selftest_pending = 0;
        if (!paused ||
            !UrModernSystemKeyDown(SDLK_RETURN, 0, 0) ||
            ur_modern_session_is_paused(g_ur_restart_session)) {
            fprintf(stderr, "UR_SESSION_OVERLAY FAIL resume-after-present\n");
            return;
        }
        fprintf(stderr,
                "UR_SESSION_KEY PASS pause_resume_host_gate=1\n"
                "UR_SESSION_OVERLAY PASS paused_panel_presented=1\n");
    }
}

static UrUniracersRestartSurface UrRestartObserveTitleLifecycle(void) {
    const uint8_t race = g_ram[0x0313];
    const uint8_t menu = g_ram[0x009F];
    const UrUniracersRestartDecision decision =
        ur_uniracers_restart_policy_observe(
            &g_ur_restart_title_policy, race, menu);
    const UrUniracersRestartSurface surface = decision.surface;
    g_ur_restart_surface = surface;

    if (surface == UR_UNIRACERS_RESTART_ACTIVE_RACE) {
        ur_modern_session_observe_race_active(g_ur_restart_session, 1);
    } else {
        ur_modern_session_observe_race_active(g_ur_restart_session, 0);
        if (decision.retire_attempt) {
            ur_modern_session_retire_race_attempt(g_ur_restart_session);
        }
    }
    return surface;
}

static int UrRestartSurfaceAllowsCommand(
    UrUniracersRestartSurface surface) {
    return (surface == UR_UNIRACERS_RESTART_ACTIVE_RACE ||
            surface == UR_UNIRACERS_RESTART_RESULTS) &&
           ur_modern_session_restart_available(g_ur_restart_session);
}

static int UrRestartCaptureOracle(const SnesDesktopHostFrameStats *stats) {
    if (!UrRestartEnsureSession())
        return 0;
    if (!ur_modern_session_restart_available(g_ur_restart_session))
        return 0;

    snes_state_digest_parts(&g_ur_restart_anchor_digest);
    if (!g_ur_session_gamepad_selftest_done) {
        ur_modern_pause_menu_reset(&g_ur_pause_menu);
        if (!UrModernSystemGamepadButton(kGamepadBtn_Start, 1) ||
            !ur_modern_session_is_paused(g_ur_restart_session) ||
            !UrModernSystemGamepadButton(kGamepadBtn_DpadDown, 1) ||
            ur_modern_pause_menu_selected(
                &g_ur_pause_menu, 1) != UR_MODERN_PAUSE_RESTART ||
            !UrModernSystemGamepadButton(kGamepadBtn_B, 1) ||
            ur_modern_session_is_paused(g_ur_restart_session)) {
            fprintf(stderr, "UR_SESSION_GAMEPAD FAIL navigation\n");
            return 0;
        }
        g_ur_session_gamepad_selftest_done = 1;
        fprintf(stderr,
                "UR_SESSION_GAMEPAD PASS start_nav_cancel=1 restart_item=1\n");
    }
    fprintf(stderr,
            "UR_RESTART_PROBE captured=1 frame=%u digest=%08x command_path=armed\n",
            stats ? stats->frame : 0u,
            (unsigned)g_ur_restart_anchor_digest.master);
    return 1;
}

static int UrRestartRequestAndValidateImmediate(
    const char *label,
    int preserve_newer_cart) {
    SnesStateDigestParts before;
    snes_state_digest_parts(&before);
    if (!UrRestartCopyCurrentSram()) {
        fprintf(stderr, "UR_RESTART_PROBE FAIL %s-sram-copy\n", label);
        return 0;
    }

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

    if (preserve_newer_cart) {
        if (!UrRestartNonCartEqualsAnchor(&immediate) ||
            immediate.cart != before.cart) {
            fprintf(stderr,
                    "UR_RESTART_PROBE FAIL %s-results-immediate "
                    "noncart_anchor_equal=%d cart_preserved=%d\n",
                    label,
                    UrRestartNonCartEqualsAnchor(&immediate),
                    immediate.cart == before.cart);
            return 0;
        }
    } else if (immediate.master != g_ur_restart_anchor_digest.master) {
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

    if (!UrRestartSramStillMatchesPreRequest()) {
        fprintf(stderr, "UR_RESTART_PROBE FAIL %s-sram-mutated\n", label);
        return 0;
    }

    fprintf(stderr,
            "UR_RESTART_PROBE %s_applied=1 immediate_equal=1 "
            "sram_progression_unchanged=1 persistent_cart_preserved=1 "
            "digest=%08x\n",
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

static void UrRestartProbeMidRace(
    const SnesDesktopHostFrameStats *stats,
    UrUniracersRestartSurface surface) {
    const int in_race = surface == UR_UNIRACERS_RESTART_ACTIVE_RACE;

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
            if (!UrRestartSurfaceAllowsCommand(surface) ||
                !UrRestartRequestAndValidateImmediate("restart1", 0)) {
                g_ur_restart_probe_phase = 9;
            } else {
                g_ur_restart_probe_count = 0;
                g_ur_restart_probe_phase = 2;
            }
        }
    } else if (g_ur_restart_probe_phase == 2) {
        if (++g_ur_restart_probe_count == kUrRestartProbeWindow) {
            if (!UrRestartReplayMatchesExpected("restart1") ||
                !UrRestartSurfaceAllowsCommand(surface) ||
                !UrRestartRequestAndValidateImmediate("restart2", 0)) {
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

static void UrRestartProbeResults(
    const SnesDesktopHostFrameStats *stats,
    UrUniracersRestartSurface surface) {
    const int in_race = surface == UR_UNIRACERS_RESTART_ACTIVE_RACE;

    if (g_ur_restart_probe_phase == 0 &&
        in_race && !g_ur_restart_prev_in_race) {
        if (!UrRestartCaptureOracle(stats)) {
            fprintf(stderr, "UR_RESTART_PROBE FAIL capture\n");
            g_ur_restart_probe_phase = 19;
        } else {
            g_ur_restart_probe_phase = 10;
        }
    } else if (g_ur_restart_probe_phase == 10 &&
               surface == UR_UNIRACERS_RESTART_RESULTS) {
        /* Leave one completed stock results frame visible to the input/script
         * consumer before performing the host-owned Retry. */
        g_ur_restart_probe_phase = 20;
    } else if (g_ur_restart_probe_phase == 20) {
        if (!UrRestartSurfaceAllowsCommand(surface)) {
            fprintf(stderr,
                    "UR_RESTART_PROBE FAIL results-restart-not-supported\n");
            g_ur_restart_probe_phase = 19;
        } else if (!UrRestartRequestAndValidateImmediate(
                       "results_restart1", 1)) {
            g_ur_restart_probe_phase = 19;
        } else {
            g_ur_restart_probe_count = 0;
            g_ur_restart_probe_phase = 11;
        }
    } else if (g_ur_restart_probe_phase == 11) {
        if (++g_ur_restart_probe_count == kUrRestartProbeWindow) {
            snes_state_digest_parts(&g_ur_restart_expected_digest);
            if (!UrRestartSurfaceAllowsCommand(surface) ||
                !UrRestartRequestAndValidateImmediate(
                    "results_restart2", 1)) {
                g_ur_restart_probe_phase = 19;
            } else {
                g_ur_restart_probe_count = 0;
                g_ur_restart_probe_phase = 12;
            }
        }
    } else if (g_ur_restart_probe_phase == 12) {
        if (++g_ur_restart_probe_count == kUrRestartProbeWindow) {
            if (!UrRestartReplayMatchesExpected("results_restart2")) {
                g_ur_restart_probe_phase = 19;
            } else {
                fprintf(stderr,
                        "UR_RESTART_RESULTS PASS results_surface=1 "
                        "persistent_sram_preserved=1 repeated_restart_equal=1 "
                        "window=%u\n",
                        (unsigned)kUrRestartProbeWindow);
                g_ur_restart_probe_phase = 19;
            }
        }
    }

    g_ur_restart_prev_in_race = in_race;
}

static void UrRestartProbeAfterRunFrame(const SnesDesktopHostFrameStats *stats) {
    if (!UrRestartEnsureSession()) {
        fprintf(stderr, "UR_RESTART_PROBE FAIL session-create\n");
        g_ur_restart_probe_phase = 99;
        return;
    }

    if (!UrSessionKeySelftest()) {
        g_ur_restart_probe_phase = 99;
        return;
    }

    const UrUniracersRestartSurface surface =
        UrRestartObserveTitleLifecycle();

    if (UrRestartResultsMode()) {
        UrRestartProbeResults(stats, surface);
    } else {
        UrRestartProbeMidRace(stats, surface);
    }
}
'''


def patch_text(source: str) -> str:
    if "UR_RESTART_RESULTS PASS results_surface=1" in source:
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
        + "    .after_run_frame     = &UrRestartProbeAfterRunFrame,\n"
        + "    .system_key_down     = &UrModernSystemKeyDown,\n"
        + "    .system_gamepad_button = &UrModernSystemGamepadButton,\n"
        + "    .system_overlay      = &UrModernSystemOverlay,\n",
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
    title_dir = (product_root / "native" / "title").as_posix()
    product_sources = [
        "session_control.cpp",
        "session_runtime_adapter.cpp",
        "race_restart_anchor.cpp",
        "race_restart_lifecycle.cpp",
        "modern_session_runtime.cpp",
        "modern_session_c_api.cpp",
        "modern_pause_menu.cpp",
    ]
    source_lines = "\n".join(
        f'    "{product_dir}/{name}"' for name in product_sources
    )
    return (
        source.rstrip()
        + "\n\n"
        + marker
        + "\n"
        + f'target_include_directories({target} PRIVATE "{product_dir}" "{title_dir}")\n'
        + f"target_sources({target} PRIVATE\n"
        + source_lines
        + "\n"
        + f'    "{title_dir}/uniracers_restart_policy.cpp"\n'
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

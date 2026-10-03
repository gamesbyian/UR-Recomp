#include "uniracers_modern_host.h"

#include "common_rtl.h"
#include "desktop/config.h"
#include "desktop/host_main.h"
#include "desktop/sdl_compat.h"
#include "modern_pause_input.h"
#include "modern_pause_menu.h"
#include "modern_session_c_api.h"
#include "snes_overlay_draw.h"
#include "uniracers_restart_policy.h"

#include <cstdlib>
#include <cstring>

namespace {

UrModernSession* g_session;
UrModernPauseMenu g_pause_menu;
UrUniracersRestartPolicyState g_title_policy;
UrUniracersRestartSurface g_surface = UR_UNIRACERS_RESTART_UNSUPPORTED;

bool modern_mode() {
    const char* mode = std::getenv("UR_EXECUTION_MODE");
    return !(mode && std::strcmp(mode, "authentic") == 0);
}

std::size_t save_snapshot(void* dst, std::size_t capacity) {
    return RtlRollbackSaveToMemory(dst, capacity);
}

bool load_snapshot(const void* src, std::size_t size) {
    return ur_modern_session_load_preserving_persistent_bytes(
        &RtlRollbackLoadFromMemory,
        src,
        size,
        g_sram,
        g_sram_size > 0 ? static_cast<std::size_t>(g_sram_size) : 0u);
}

void set_timing_lock(int active) {
    RtlSetRewindAudioTimingLock(active != 0);
}

void reconcile_presentation() {
    RtlAudioSetFastForward(true);
    RtlAudioSetFastForward(false);
}

bool ensure_session() {
    if (g_session) return true;
    const std::size_t capacity = RtlRollbackSnapshotBound();
    if (!capacity) return false;

    g_session = ur_modern_session_create(
        modern_mode() ? 1 : 0,
        capacity,
        &save_snapshot,
        &load_snapshot,
        &snesrecomp_desktop_set_paused,
        &snesrecomp_desktop_is_paused,
        &set_timing_lock,
        &reconcile_presentation);
    ur_modern_pause_menu_reset(&g_pause_menu);
    ur_uniracers_restart_policy_reset(&g_title_policy);
    return g_session != nullptr;
}

bool restart_surface() {
    return g_surface == UR_UNIRACERS_RESTART_ACTIVE_RACE ||
           g_surface == UR_UNIRACERS_RESTART_RESULTS;
}

bool paused() {
    return g_session && ur_modern_session_is_paused(g_session);
}

bool dispatch(UrModernPauseAction action) {
    if (!ensure_session()) return false;
    const UrModernSessionResult result =
        ur_modern_pause_handle_action(g_session, &g_pause_menu, action);
    return result == UR_MODERN_SESSION_APPLIED ||
           result == UR_MODERN_SESSION_NO_OP;
}

}  // namespace

extern "C" void ur_uniracers_modern_after_run_frame(
    const SnesDesktopHostFrameStats*) {
    if (!ensure_session()) return;

    const UrUniracersRestartDecision decision =
        ur_uniracers_restart_policy_observe(
            &g_title_policy,
            g_ram[0x0313],
            g_ram[0x009F]);
    g_surface = decision.surface;

    if (g_surface == UR_UNIRACERS_RESTART_ACTIVE_RACE) {
        ur_modern_session_observe_race_active(g_session, 1);
    } else {
        ur_modern_session_observe_race_active(g_session, 0);
        if (decision.retire_attempt) {
            ur_modern_session_retire_race_attempt(g_session);
        }
    }
}

extern "C" int ur_uniracers_modern_system_key_down(
    int key,
    int mod,
    int repeat) {
    if (repeat || !ensure_session()) return 0;

    if (key == SDLK_ESCAPE) {
        if (!paused() && !restart_surface()) return 0;
        return dispatch(UR_MODERN_PAUSE_TOGGLE) ? 1 : 0;
    }
    if (paused() && key == SDLK_UP) {
        return dispatch(UR_MODERN_PAUSE_PREVIOUS) ? 1 : 0;
    }
    if (paused() && key == SDLK_DOWN) {
        return dispatch(UR_MODERN_PAUSE_NEXT) ? 1 : 0;
    }
    if (paused() && (key == SDLK_RETURN || key == SDLK_KP_ENTER)) {
        return dispatch(UR_MODERN_PAUSE_ACTIVATE) ? 1 : 0;
    }
    if (key == SDLK_r && (mod & KMOD_CTRL) &&
        restart_surface() &&
        ur_modern_session_restart_available(g_session)) {
        return dispatch(UR_MODERN_PAUSE_RESTART_HOTKEY) ? 1 : 0;
    }
    return 0;
}

extern "C" int ur_uniracers_modern_system_gamepad_button(
    int button,
    int pressed) {
    if (!ensure_session()) return 0;

    if (!pressed) {
        return paused() ? 1 : 0;
    }

    if (button == kGamepadBtn_Start) {
        if (!paused() && !restart_surface()) return 0;
        return dispatch(UR_MODERN_PAUSE_TOGGLE) ? 1 : 0;
    }
    if (!paused()) return 0;

    if (button == kGamepadBtn_DpadUp) {
        return dispatch(UR_MODERN_PAUSE_PREVIOUS) ? 1 : 0;
    }
    if (button == kGamepadBtn_DpadDown) {
        return dispatch(UR_MODERN_PAUSE_NEXT) ? 1 : 0;
    }
    if (button == kGamepadBtn_A) {
        return dispatch(UR_MODERN_PAUSE_ACTIVATE) ? 1 : 0;
    }
    if (button == kGamepadBtn_B) {
        return dispatch(UR_MODERN_PAUSE_CANCEL) ? 1 : 0;
    }
    return 0;
}

extern "C" void ur_uniracers_modern_system_overlay(
    uint8_t* dst,
    size_t pitch,
    int width,
    int height) {
    if (!ensure_session() || !dst || pitch < 4 || width <= 0 || height <= 0) {
        return;
    }

    const int is_paused = paused() ? 1 : 0;
    const int results = g_surface == UR_UNIRACERS_RESTART_RESULTS;
    const int restart = ur_modern_session_restart_available(g_session);
    if (!is_paused && !(results && restart)) return;

    uint32_t* pixels = reinterpret_cast<uint32_t*>(dst);
    const int stride = static_cast<int>(pitch / 4u);
    const int panel_w = width < 220 ? width - 16 : 212;
    const int panel_h = is_paused ? 54 : 30;
    const int x = (width - panel_w) / 2;
    const int y = is_paused ? (height - panel_h) / 2 : height - panel_h - 8;

    snes_ovl_fill_rect(
        pixels, stride, height, x, y, panel_w, panel_h, 0xE0202020u);
    snes_ovl_stroke_rect(
        pixels, stride, height, x, y, panel_w, panel_h, 0xFFF0F0F0u);

    if (is_paused) {
        ur_modern_pause_menu_move(&g_pause_menu, 0, restart);
        const UrModernPauseItem selected =
            ur_modern_pause_menu_selected(&g_pause_menu, restart);
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
    } else {
        snes_ovl_draw_text(
            pixels, stride, height, x + 8, y + 11,
            "START / CTRL+R  RETRY", 0xFFFFFFFFu, 1);
    }
}

/* Baldosa native execution lifecycle witness over the existing observer.
 *
 * In ordinary play this adds only the observer forward and a cheap inert
 * SDL event-loop tick. A bounded, explicit environment test exercises the
 * REAL host pause/guest freeze/audio pause path without a synthetic guest
 * step or made-up event completion.
 */
#include <cstddef>
#include <cstdint>
#include <cerrno>
#include <climits>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

#include "modern_session_c_api.h"
#include "baldosa_physical_pause_input.hpp"
#include "modern_pause_input.h"
#include "modern_pause_overlay_presenter.hpp"

extern "C" {
#include "desktop/config.h"
#include "desktop/sdl_compat.h"
#include "snes_overlay_draw.h"
}

extern "C" {
#include "host_main.h"
#include "common_rtl.h"
extern std::uint8_t g_ram[0x20000];
void ur_baldosa_product_guest_restarted(void);
int ur_baldosa_product_set_paused(int paused);
int snesrecomp_desktop_product_is_paused(void);
unsigned snesrecomp_desktop_product_pause_presentations(void);
int ur_baldosa_modern_root_key(int key, int pressed);
int ur_baldosa_modern_root_gamepad(int player, int button, int pressed);
void ur_baldosa_modern_root_after_run_frame(unsigned frame);
void ur_baldosa_guest_snapshot_after_run_frame(
    const SnesDesktopHostFrameStats* stats);
}

namespace {
bool g_smoke_initialized;
bool g_smoke_enabled;
UrModernSession* g_modern_session;
bool g_native_live_race;
UrModernPauseMenu g_native_pause_menu{};
bool g_pause_navigation_keys[3]{};
bool g_pause_navigation_pad[4]{};
bool g_pause_panel_logged;
unsigned g_pause_panel_paints;
bool g_pause_panel_nav_smoke;
bool g_pause_panel_nav_verified;
ur::product::BaldosaPhysicalPauseInput g_keyboard_pause;
ur::product::BaldosaPhysicalPauseInput g_p1_gamepad_pause;
ur::product::BaldosaPhysicalPauseInput g_keyboard_restart;
bool g_restart_same_frame_checked;
bool g_delayed_restart_enabled;
bool g_native_anchor_captured;
bool g_delayed_restart_verified;
unsigned g_native_anchor_frame;
std::uint8_t g_native_anchor_ram[0x20000];
std::vector<std::uint8_t> g_paused_persistent_bytes;

// Deliberately opt-in while the native Baldosa executable lacks the visible
// established Modern pause/root surfaces. Authentic remains untouched.
bool physical_modern_enabled() {
    static const bool enabled = [] {
        const char* opt = std::getenv("UR_BALDOSA_MODERN_INPUT");
        const char* mode = std::getenv("UR_EXECUTION_MODE");
        return opt && std::strcmp(opt, "1") == 0 &&
               !(mode && std::strcmp(mode, "authentic") == 0);
    }();
    return enabled;
}

bool acknowledged_guest_pause(void*, int paused) {
    return ur_baldosa_product_set_paused(paused) != 0;
}

std::size_t save_native_guest(void* bytes, std::size_t capacity) {
    return RtlRollbackSaveToMemory(bytes, capacity);
}

bool restore_native_guest_preserving_sram(const void* bytes, std::size_t size) {
    return ur_modern_session_load_preserving_persistent_bytes(
        &RtlRollbackLoadFromMemory, bytes, size, g_sram,
        g_sram_size > 0 ? static_cast<std::size_t>(g_sram_size) : 0u);
}

void reconcile_after_native_restart() {
    // This is the existing Modern host's post-restore audio reconciliation
    // and the already merged two-seat human input release latch. A paused
    // Restart never gives a held physical Start back to the guest.
    ur_baldosa_product_guest_restarted();
    RtlAudioSetFastForward(true);
    RtlAudioSetFastForward(false);
}

// One physical, edge-triggered menu navigation gesture. The guest owns
// every key outside an acknowledged native pause, including its key-up.
bool pause_navigation_edge(int pressed, bool& holding,
                           UrModernPauseAction action) {
    if (!pressed) {
        if (!holding) return false;
        holding = false;
        return true;
    }
    if (!g_modern_session ||
        !ur_modern_session_is_paused(g_modern_session))
        return false;
    if (holding) return true;
    holding = true;
    const auto result = ur_modern_pause_handle_action(
        g_modern_session, &g_native_pause_menu, action);
    std::fprintf(stderr,
        "UR_BALDOSA_NATIVE_PAUSE_MENU action=%d selected=%d result=%d paused=%d\n",
        static_cast<int>(action),
        g_native_pause_menu.selected, static_cast<int>(result),
        ur_modern_session_is_paused(g_modern_session));
    return true;
}

void reset_native_pause_menu_on_open() {
    if (g_modern_session && ur_modern_session_is_paused(g_modern_session)) {
        ur_modern_pause_menu_reset(&g_native_pause_menu);
        g_pause_panel_logged = false;
    }
}

void create_modern_session() {
    if (g_modern_session) return;
    const UrModernNativeSessionHooks hooks{
        nullptr, &acknowledged_guest_pause, nullptr, nullptr, nullptr};
    const auto capacity = RtlRollbackSnapshotBound();
    g_modern_session = capacity
        ? ur_modern_session_create_native_with_snapshot(
              1, &hooks, capacity, &save_native_guest,
              &restore_native_guest_preserving_sram,
              &reconcile_after_native_restart)
        : ur_modern_session_create_native(1, &hooks);
    if (!g_modern_session) {
        std::fprintf(stderr, "UR_BALDOSA_NATIVE_PAUSE FAIL=modern_session_create\n");
        std::abort();
    }
}
bool g_armed;
bool g_resumed;
unsigned g_guest_frame;
unsigned g_frozen_ticks;
unsigned g_pause_at_frame = 120;
bool g_require_race;
bool g_physical_smoke;
std::uint8_t g_frozen_ram[0x20000];

// Use the real Baldosa SDL event pump in this explicit bounded acceptance.
// Queued synthetic keys exercise host dispatch, NOT physical hardware QA.
void queue_key_edge(int key) {
    SDL_Event event{};
    event.type = SDL_KEYDOWN;
#if SNESRECOMP_SDL3
    event.key.key = key;
#else
    event.key.keysym.sym = key;
#endif
    if (SDL_PushEvent(&event) != 1) {
        std::fprintf(stderr, "UR_BALDOSA_NATIVE_PAUSE FAIL=keydown_not_queued\n");
        std::abort();
    }
    event.type = SDL_KEYUP;
    if (SDL_PushEvent(&event) != 1) {
        std::fprintf(stderr, "UR_BALDOSA_NATIVE_PAUSE FAIL=keyup_not_queued\n");
        std::abort();
    }
}

void queue_escape_edge() { queue_key_edge(SDLK_ESCAPE); }
void queue_restart_edge() { queue_key_edge(SDLK_r); }

bool smoke_enabled() {
    if (!g_smoke_initialized) {
        const char* env = std::getenv("UR_BALDOSA_PAUSE_SMOKE");
        g_smoke_enabled = env && std::strcmp(env, "1") == 0;
        if (g_smoke_enabled) {
            const char* frame = std::getenv("UR_BALDOSA_PAUSE_SMOKE_AT_FRAME");
            if (frame && frame[0]) {
                errno = 0;
                char* end = nullptr;
                const unsigned long n = std::strtoul(frame, &end, 10);
                if (errno != 0 || !end || end == frame || *end != '\0' ||
                    n == 0 || n > UINT_MAX) {
                    std::fprintf(stderr,
                        "UR_BALDOSA_NATIVE_PAUSE FAIL=invalid_test_frame\n");
                    std::abort();
                }
                g_pause_at_frame = static_cast<unsigned>(n);
            }
            const char* require = std::getenv("UR_BALDOSA_PAUSE_REQUIRE_RACE");
            g_require_race = require && std::strcmp(require, "1") == 0;
            const char* physical = std::getenv("UR_BALDOSA_PHYSICAL_PAUSE_SMOKE");
            g_physical_smoke = physical && std::strcmp(physical, "1") == 0;
            const char* nav = std::getenv("UR_BALDOSA_PAUSE_PANEL_NAV_SMOKE");
            g_pause_panel_nav_smoke = nav && std::strcmp(nav, "1") == 0;
            const char* delayed = std::getenv("UR_BALDOSA_DELAYED_RESTART_SMOKE");
            g_delayed_restart_enabled =
                delayed && std::strcmp(delayed, "1") == 0;
        }
        g_smoke_initialized = true;
    }
    return g_smoke_enabled;
}
void require(bool ok, const char* why) {
    if (!ok) {
        std::fprintf(stderr, "UR_BALDOSA_NATIVE_PAUSE FAIL=%s\n", why);
        std::fflush(stderr);
        std::abort();
    }
}
} // namespace

// Called from the ORIGINAL Baldosa SDL keyboard/gamepad processing after the
// host's physical mapping, not from a script/debug controller word. Only P1
// Escape/Start while actually racing belongs to this narrow Modern pause
// bridge; all ordinary profile/stock/menu controls retain guest authority.
extern "C" int ur_baldosa_product_system_key(int key, int pressed) {
    if (ur_baldosa_modern_root_key(key, pressed)) return 1;
    if (!physical_modern_enabled() ||
        (smoke_enabled() && !g_physical_smoke)) return 0;
    int nav = -1;
    switch (key) {
    case SDLK_UP: nav = 0; break;
    case SDLK_DOWN: nav = 1; break;
    case SDLK_RETURN: nav = 2; break;
    default: break;
    }
    if (nav >= 0 && pause_navigation_edge(
            pressed, g_pause_navigation_keys[nav],
            nav == 0 ? UR_MODERN_PAUSE_PREVIOUS :
            nav == 1 ? UR_MODERN_PAUSE_NEXT :
                       UR_MODERN_PAUSE_ACTIVATE)) return 1;
    if (key == SDLK_r) {
        // R is a Modern Restart command only inside an acknowledged host
        // pause. Normal stock racing and menu navigation retain the key.
        if (!g_modern_session ||
            (!ur_modern_session_is_paused(g_modern_session) &&
             !g_keyboard_restart.holding())) return 0;
        const bool used = g_keyboard_restart.on_button(
            pressed, false, g_modern_session, UR_MODERN_SESSION_KEY_RESTART);
        if (used && pressed && std::getenv("UR_BALDOSA_MODERN_INPUT_DIAGNOSTICS"))
            std::fprintf(stderr,
                "UR_BALDOSA_MODERN_INPUT key=restart status=%d paused=%d\n",
                static_cast<int>(g_keyboard_restart.last_result()),
                ur_modern_session_is_paused(g_modern_session));
        return used ? 1 : 0;
    }
    if (key != SDLK_ESCAPE) return 0;
    if (pressed && g_native_live_race && !g_modern_session)
        create_modern_session();
    const bool used = g_keyboard_pause.on_button(
        pressed, g_native_live_race, g_modern_session);
    if (used && pressed &&
        g_keyboard_pause.last_result() == UR_MODERN_SESSION_APPLIED)
        reset_native_pause_menu_on_open();
    if (used && pressed && std::getenv("UR_BALDOSA_MODERN_INPUT_DIAGNOSTICS")) {
        std::fprintf(stderr, "UR_BALDOSA_MODERN_INPUT key=escape action=%d paused=%d\n",
                     static_cast<int>(g_keyboard_pause.last_result()),
                     ur_modern_session_is_paused(g_modern_session));
    }
    return used ? 1 : 0;
}

extern "C" int ur_baldosa_product_system_gamepad(
    int player, int button, int pressed) {
    if (ur_baldosa_modern_root_gamepad(player, button, pressed)) return 1;
    if (!physical_modern_enabled() ||
        (smoke_enabled() && !g_physical_smoke) || player != 0) return 0;
    int nav = -1;
    switch (button) {
    case kGamepadBtn_DpadUp: nav = 0; break;
    case kGamepadBtn_DpadDown: nav = 1; break;
    case kGamepadBtn_A: nav = 2; break;
    case kGamepadBtn_B: nav = 3; break;
    default: break;
    }
    if (nav >= 0 && pause_navigation_edge(
            pressed, g_pause_navigation_pad[nav],
            nav == 0 ? UR_MODERN_PAUSE_PREVIOUS :
            nav == 1 ? UR_MODERN_PAUSE_NEXT :
            nav == 2 ? UR_MODERN_PAUSE_ACTIVATE :
                       UR_MODERN_PAUSE_CANCEL)) return 1;
    if (button != kGamepadBtn_Start) return 0;
    if (pressed && g_native_live_race && !g_modern_session)
        create_modern_session();
    const bool used = g_p1_gamepad_pause.on_button(
        pressed, g_native_live_race, g_modern_session);
    if (used && pressed &&
        g_p1_gamepad_pause.last_result() == UR_MODERN_SESSION_APPLIED)
        reset_native_pause_menu_on_open();
    if (used && pressed && std::getenv("UR_BALDOSA_MODERN_INPUT_DIAGNOSTICS")) {
        std::fprintf(stderr, "UR_BALDOSA_MODERN_INPUT pad=p1_start action=%d paused=%d\n",
                     static_cast<int>(g_p1_gamepad_pause.last_result()),
                     ur_modern_session_is_paused(g_modern_session));
    }
    return used ? 1 : 0;
}

// Called solely by Baldosa's ORIGINAL frozen-frame renderer after it copies
// the last raster. This operates on host pixels; no guest draw/step or SRAM.
extern "C" int ur_baldosa_product_pause_draw(
    std::uint8_t* pixels, std::size_t pitch, int width, int height) {
    if (!physical_modern_enabled() || !g_modern_session ||
        !ur_modern_session_is_paused(g_modern_session) ||
        !pixels || width <= 0 || height <= 0 ||
        pitch < static_cast<std::size_t>(width) * 4 ||
        pitch % 4 != 0)
        return 0;
    const ur::product::ModernRootOverlayPainter paint{
        &snes_ovl_fill_rect, &snes_ovl_stroke_rect, &snes_ovl_draw_text};
    if (!ur::product::render_native_modern_pause_overlay(
            paint, reinterpret_cast<std::uint32_t*>(pixels),
            static_cast<int>(pitch / 4), width, height, g_native_pause_menu,
            ur_modern_session_restart_available(g_modern_session) != 0))
        return 0;
    ++g_pause_panel_paints;
    if (!g_pause_panel_logged) {
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PAUSE PANEL_RENDERED=1 pixels=%dx%d "
            "renderer=shared guest_steps=0\n", width, height);
        g_pause_panel_logged = true;
    }
    return 1;
}

extern "C" void ur_baldosa_product_after_run_frame(
    const SnesDesktopHostFrameStats* stats) {
    // Existing verified two-seat guest observer remains intact.
    ur_baldosa_guest_snapshot_after_run_frame(stats);
    if (stats) ur_baldosa_modern_root_after_run_frame(stats->frame);
    // A rollback can rewind the guest's own snes_frame_counter, which the
    // stock framedump uses as its filename. A deterministic replay can
    // overwrite earlier frame_NNN.json files with their identical CRCs.
    // Record a separate APPEND-ONLY host-frame witness, measured after each
    // genuine RtlRunFrame, to distinguish a real rewind from frame filenames.
    const char* host_trace = std::getenv("UR_BALDOSA_RESTART_FRAME_TRACE");
    if (stats && host_trace && std::strcmp(host_trace, "1") == 0 &&
        stats->frame >= 1948 && stats->frame <= 1970) {
        std::uint32_t hash = 2166136261u; // full 128 KiB WRAM, FNV-1a
        for (const std::uint8_t byte : g_ram) {
            hash ^= byte;
            hash *= 16777619u;
        }
        std::fprintf(stderr,
            "UR_BALDOSA_HOST_FRAME_CRC host=%u guest=%d hash=%08x\n",
            stats->frame, snes_frame_counter, static_cast<unsigned>(hash));
        std::fflush(stderr);
    }
    if (stats) {
        g_native_live_race = g_ram[0x0313] == 0x01;
        // Create at the FIRST observed authentic racing frame, not at the
        // first human pause. That gives Restart a real immutable race anchor.
        if (physical_modern_enabled() && g_native_live_race &&
            !g_modern_session) create_modern_session();
        if (g_modern_session)
            ur_modern_session_observe_race_active(
                g_modern_session, g_native_live_race ? 1 : 0);

        if (smoke_enabled() && g_delayed_restart_enabled &&
            g_native_live_race && !g_native_anchor_captured) {
            require(g_modern_session &&
                        ur_modern_session_restart_available(g_modern_session),
                    "delayed_restart_anchor_unavailable");
            g_native_anchor_captured = true;
            g_native_anchor_frame = stats->frame;
            std::memcpy(g_native_anchor_ram, g_ram, sizeof(g_native_anchor_ram));
        }

        // Explicit test-only, real same-boundary native rollback round trip.
        // It must leave guest WRAM, persistent SRAM and all future 2P frame
        // CRCs unchanged; the user-facing, multi-frame Retry still needs QA.
        if (!g_restart_same_frame_checked && g_native_live_race &&
            std::getenv("UR_BALDOSA_RESTART_SAME_FRAME_SMOKE") &&
            std::strcmp(std::getenv("UR_BALDOSA_RESTART_SAME_FRAME_SMOKE"), "1") == 0) {
            g_restart_same_frame_checked = true;
            require(g_modern_session &&
                    ur_modern_session_restart_available(g_modern_session),
                    "native_restart_anchor_missing");
            std::uint8_t before_ram[0x20000];
            std::memcpy(before_ram, g_ram, sizeof(before_ram));
            require(g_sram != nullptr && g_sram_size > 0,
                    "native_restart_sram_unavailable");
            const std::vector<std::uint8_t> preserved(
                g_sram, g_sram + static_cast<std::size_t>(g_sram_size));
            require(ur_modern_session_restart_race(g_modern_session) ==
                        UR_MODERN_SESSION_APPLIED,
                    "native_rollback_restore_rejected");
            require(std::memcmp(g_ram, before_ram, sizeof(before_ram)) == 0,
                    "native_rollback_wram_changed");
            require(std::memcmp(g_sram, preserved.data(), preserved.size()) == 0,
                    "native_rollback_sram_changed");
            std::fprintf(stderr,
                "UR_BALDOSA_NATIVE_RESTART SAME_FRAME guest=%u sram_equal=1 wram_equal=1\n",
                stats->frame);
            std::fflush(stderr);
        }
    }
    if (!smoke_enabled()) return;
    require(stats != nullptr, "missing_frame_statistics");

    if (g_resumed && stats->frame == g_guest_frame + 1) {
        require(g_frozen_ticks >= 24, "insufficient_frozen_event_pumps");
        require(snesrecomp_desktop_product_is_paused() == 0,
                "guest_not_resumed_after_event");
        if (g_delayed_restart_enabled)
            require(g_delayed_restart_verified,
                    "delayed_restart_missing_acknowledgement");
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PAUSE RESUMED previous_guest=%u "
            "new_guest=%u frozen_pumps=%u\n",
            g_guest_frame, stats->frame, g_frozen_ticks);
        std::fflush(stderr);
        // Only one synthetic acceptance pause per process; no player data
        // or host controls are modified once the observation is complete.
        g_resumed = false;
        // Keep the real Modern session and immutable race anchor alive for
        // Retry after the smoke; only guest completion/front-end owns retirement.
    }

    // Explicit test frame only. Require the actual source guest's in-race
    // byte, shared with Modern's existing title-state observer, when enabled.
    // A script advancing frames without entering a race cannot pass the gate.
    if (!g_armed && stats->frame == g_pause_at_frame) {
        const bool live_race = g_ram[0x0313] == 0x01;
        if (g_require_race)
            require(live_race, "expected_live_race_state");
        if (g_delayed_restart_enabled) {
            require(g_physical_smoke, "delayed_restart_needs_sdl_input");
            require(g_native_anchor_captured &&
                        g_native_anchor_frame + 12 < stats->frame,
                    "delayed_restart_insufficient_real_guest_frames");
            require(std::memcmp(
                        g_native_anchor_ram, g_ram, sizeof(g_native_anchor_ram)) != 0,
                    "delayed_restart_guest_has_not_advanced");
            require(g_sram && g_sram_size > 0, "delayed_restart_missing_sram");
            g_paused_persistent_bytes.assign(
                g_sram, g_sram + static_cast<std::size_t>(g_sram_size));
        }
        g_armed = true;
        g_guest_frame = stats->frame;
        std::memcpy(g_frozen_ram, g_ram, sizeof(g_frozen_ram));
        if (g_physical_smoke) {
            require(physical_modern_enabled(), "physical_modern_mode_disabled");
            queue_escape_edge();  // next normal SDL event pump opens pause
        } else {
            create_modern_session();
            require(ur_modern_session_pause(g_modern_session) ==
                        UR_MODERN_SESSION_APPLIED,
                    "modern_pause_was_not_acknowledged");
            require(snesrecomp_desktop_product_is_paused() != 0,
                    "host_not_actually_paused");
        }
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PAUSE ARMED guest=%u live_race=%u modern_session=1 physical_sdl=%u\n",
            g_guest_frame, live_race ? 1U : 0U, g_physical_smoke ? 1U : 0U);
        std::fflush(stderr);
    }
}

extern "C" void ur_baldosa_product_host_tick(void) {
    if (!smoke_enabled() || !g_armed || g_resumed ||
        g_frozen_ticks >= 24) return;
    require(snesrecomp_desktop_product_is_paused() != 0,
            "host_exited_pause_without_permission");
    if (g_physical_smoke) {
        require(g_modern_session &&
                    ur_modern_session_is_paused(g_modern_session),
                "physical_sdl_did_not_reach_modern_session");
    }
    if (g_delayed_restart_enabled && g_frozen_ticks >= 8) {
        // At the eighth frozen pump the host queued an actual SDL 'R'
        // press/release; this is checked on the ninth pump after the SDL
        // dispatcher has handled it. No guest frames run during Restart.
        require(g_keyboard_restart.last_result() == UR_MODERN_SESSION_APPLIED &&
                    !g_keyboard_restart.holding() &&
                    ur_modern_session_is_paused(g_modern_session),
                "delayed_restart_did_not_reach_modern_native_session");
        require(std::memcmp(
                    g_ram, g_native_anchor_ram, sizeof(g_native_anchor_ram)) == 0,
                "delayed_restart_wram_did_not_rewind_to_race_anchor");
        require(g_sram &&
                    static_cast<std::size_t>(g_sram_size) ==
                        g_paused_persistent_bytes.size() &&
                    std::memcmp(g_sram, g_paused_persistent_bytes.data(),
                                g_paused_persistent_bytes.size()) == 0,
                "delayed_restart_did_not_preserve_persistent_sram");
        if (!g_delayed_restart_verified) {
            g_delayed_restart_verified = true;
            std::fprintf(stderr,
                "UR_BALDOSA_NATIVE_RESTART DELAYED anchor_guest=%u "
                "request_guest=%u paused=1 sram_equal=1 wram_rewound=1\n",
                g_native_anchor_frame, g_guest_frame);
            std::fflush(stderr);
        }
    } else {
        require(std::memcmp(g_ram, g_frozen_ram, sizeof(g_frozen_ram)) == 0,
                "guest_wram_advanced_during_pause");
    }
    ++g_frozen_ticks;
    if (g_physical_smoke && g_pause_panel_nav_smoke) {
        // Test-only queued physical SDL key edges: Down then Up must
        // navigate the existing Modern model while the original guest stays
        // frozen. Never feed them into the guest controller word.
        if (g_frozen_ticks == 2) queue_key_edge(SDLK_DOWN);
        if (g_frozen_ticks == 4) {
            require(g_native_pause_menu.selected == UR_MODERN_PAUSE_RESTART,
                    "physical_down_did_not_select_restart");
            queue_key_edge(SDLK_UP);
        }
        if (g_frozen_ticks >= 6 && !g_pause_panel_nav_verified) {
            require(g_native_pause_menu.selected == UR_MODERN_PAUSE_RESUME &&
                    g_pause_panel_paints >= 4,
                    "native_paused_panel_navigation_or_paint_failed");
            g_pause_panel_nav_verified = true;
            std::fprintf(stderr,
                "UR_BALDOSA_NATIVE_PAUSE_MENU NAV=1 down_up=1 "
                "selected=0 guest_steps=0\n");
            std::fflush(stderr);
        }
    }
    if (g_delayed_restart_enabled && g_frozen_ticks == 8)
        queue_restart_edge(); // SDL processes this BEFORE the next host tick
    if (g_frozen_ticks == 24) {
        // The host's real frozen compositor must keep the window visibly
        // alive during the entire native-pause interval. Presentations run
        // without a guest frame and without executing draw_ppu_frame().
        const unsigned frozen_presentations =
            snesrecomp_desktop_product_pause_presentations();
        require(frozen_presentations >= 23u,
                "native_pause_did_not_present_frozen_raster");
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PAUSE FROZEN_PRESENT guest=%u present_count=%u "
            "no_guest_steps=1\n", g_guest_frame, frozen_presentations);
        std::fflush(stderr);
        if (g_physical_smoke) {
            // A second physical SDL edge, not a direct lifecycle call, resumes.
            // If the host fails to dispatch it, the guest remains frozen and
            // the existing bounded native route fails closed.
            queue_escape_edge();
        } else {
            require(ur_modern_session_resume(g_modern_session) ==
                        UR_MODERN_SESSION_APPLIED,
                    "modern_resume_was_not_acknowledged");
            require(snesrecomp_desktop_product_is_paused() == 0,
                    "host_still_paused_after_resume");
            ur_modern_session_destroy(g_modern_session);
            g_modern_session = nullptr;
        }
        g_resumed = true;
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PAUSE RELEASED guest=%u frozen_pumps=%u physical_sdl=%u\n",
            g_guest_frame, g_frozen_ticks, g_physical_smoke ? 1U : 0U);
        std::fflush(stderr);
    }
}

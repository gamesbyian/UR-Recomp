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

#include "modern_session_c_api.h"
#include "baldosa_physical_pause_input.hpp"

extern "C" {
#include "desktop/config.h"
#include "desktop/sdl_compat.h"
}

extern "C" {
#include "host_main.h"
extern std::uint8_t g_ram[0x20000];
int ur_baldosa_product_set_paused(int paused);
int snesrecomp_desktop_product_is_paused(void);
void ur_baldosa_guest_snapshot_after_run_frame(
    const SnesDesktopHostFrameStats* stats);
}

namespace {
bool g_smoke_initialized;
bool g_smoke_enabled;
UrModernSession* g_modern_session;
bool g_native_live_race;
ur::product::BaldosaPhysicalPauseInput g_keyboard_pause;
ur::product::BaldosaPhysicalPauseInput g_p1_gamepad_pause;

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

void create_modern_session() {
    if (g_modern_session) return;
    // Reuse Modern's real command/phase policy even in the existing bounded
    // 2P native guest pause witness. This is not a new menu or second host.
    const UrModernNativeSessionHooks hooks{
        nullptr, &acknowledged_guest_pause, nullptr, nullptr, nullptr};
    g_modern_session = ur_modern_session_create_native(1, &hooks);
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
std::uint8_t g_frozen_ram[0x20000];

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
    if (!physical_modern_enabled() || smoke_enabled() ||
        key != SDLK_ESCAPE) return 0;
    if (pressed && g_native_live_race && !g_modern_session)
        create_modern_session();
    const bool used = g_keyboard_pause.on_button(
        pressed, g_native_live_race, g_modern_session);
    if (used && pressed && std::getenv("UR_BALDOSA_MODERN_INPUT_DIAGNOSTICS")) {
        std::fprintf(stderr, "UR_BALDOSA_MODERN_INPUT key=escape action=%d paused=%d\\n",
                     static_cast<int>(g_keyboard_pause.last_result()),
                     ur_modern_session_is_paused(g_modern_session));
    }
    return used ? 1 : 0;
}

extern "C" int ur_baldosa_product_system_gamepad(
    int player, int button, int pressed) {
    if (!physical_modern_enabled() || smoke_enabled() ||
        player != 0 || button != kGamepadBtn_Start) return 0;
    if (pressed && g_native_live_race && !g_modern_session)
        create_modern_session();
    const bool used = g_p1_gamepad_pause.on_button(
        pressed, g_native_live_race, g_modern_session);
    if (used && pressed && std::getenv("UR_BALDOSA_MODERN_INPUT_DIAGNOSTICS")) {
        std::fprintf(stderr, "UR_BALDOSA_MODERN_INPUT pad=p1_start action=%d paused=%d\\n",
                     static_cast<int>(g_p1_gamepad_pause.last_result()),
                     ur_modern_session_is_paused(g_modern_session));
    }
    return used ? 1 : 0;
}

extern "C" void ur_baldosa_product_after_run_frame(
    const SnesDesktopHostFrameStats* stats) {
    // Existing verified two-seat guest observer remains intact.
    ur_baldosa_guest_snapshot_after_run_frame(stats);
    if (stats) {
        g_native_live_race = g_ram[0x0313] == 0x01;
        if (g_modern_session)
            ur_modern_session_observe_race_active(
                g_modern_session, g_native_live_race ? 1 : 0);
    }
    if (!smoke_enabled()) return;
    require(stats != nullptr, "missing_frame_statistics");

    if (g_resumed && stats->frame == g_guest_frame + 1) {
        require(g_frozen_ticks >= 24, "insufficient_frozen_event_pumps");
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PAUSE RESUMED previous_guest=%u "
            "new_guest=%u frozen_pumps=%u\n",
            g_guest_frame, stats->frame, g_frozen_ticks);
        std::fflush(stderr);
        // Only one synthetic acceptance pause per process; no player data
        // or host controls are modified once the observation is complete.
        g_resumed = false;
    }

    // Explicit test frame only. Require the actual source guest's in-race
    // byte, shared with Modern's existing title-state observer, when enabled.
    // A script advancing frames without entering a race cannot pass the gate.
    if (!g_armed && stats->frame == g_pause_at_frame) {
        const bool live_race = g_ram[0x0313] == 0x01;
        if (g_require_race)
            require(live_race, "expected_live_race_state");
        g_armed = true;
        g_guest_frame = stats->frame;
        std::memcpy(g_frozen_ram, g_ram, sizeof(g_frozen_ram));
        create_modern_session();
        require(ur_modern_session_pause(g_modern_session) ==
                    UR_MODERN_SESSION_APPLIED,
                "modern_pause_was_not_acknowledged");
        require(snesrecomp_desktop_product_is_paused() != 0,
                "host_not_actually_paused");
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PAUSE ARMED guest=%u live_race=%u modern_session=1\n",
            g_guest_frame, live_race ? 1U : 0U);
        std::fflush(stderr);
    }
}

extern "C" void ur_baldosa_product_host_tick(void) {
    if (!smoke_enabled() || !g_armed || g_resumed ||
        g_frozen_ticks >= 24) return;
    require(snesrecomp_desktop_product_is_paused() != 0,
            "host_exited_pause_without_permission");
    require(std::memcmp(g_ram, g_frozen_ram, sizeof(g_frozen_ram)) == 0,
            "guest_wram_advanced_during_pause");
    ++g_frozen_ticks;
    if (g_frozen_ticks == 24) {
        require(ur_modern_session_resume(g_modern_session) ==
                    UR_MODERN_SESSION_APPLIED,
                "modern_resume_was_not_acknowledged");
        require(snesrecomp_desktop_product_is_paused() == 0,
                "host_still_paused_after_resume");
        g_resumed = true;
        ur_modern_session_destroy(g_modern_session);
        g_modern_session = nullptr;
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PAUSE RELEASED guest=%u frozen_pumps=%u\n",
            g_guest_frame, g_frozen_ticks);
        std::fflush(stderr);
    }
}

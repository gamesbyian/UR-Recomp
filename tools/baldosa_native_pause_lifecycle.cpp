/* Baldosa native execution lifecycle witness over the existing observer.
 *
 * In ordinary play this adds only the observer forward and a cheap inert
 * SDL event-loop tick. A bounded, explicit environment test exercises the
 * REAL host pause/guest freeze/audio pause path without a synthetic guest
 * step or made-up event completion.
 */
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

extern "C" {
#include "host_main.h"
extern std::uint8_t g_ram[0x20000];
int snesrecomp_desktop_product_set_paused(int paused);
int snesrecomp_desktop_product_is_paused(void);
void ur_baldosa_guest_snapshot_after_run_frame(
    const SnesDesktopHostFrameStats* stats);
}

namespace {
bool g_smoke_initialized;
bool g_smoke_enabled;
bool g_armed;
bool g_resumed;
unsigned g_guest_frame;
unsigned g_frozen_ticks;
std::uint8_t g_frozen_ram[0x20000];

bool smoke_enabled() {
    if (!g_smoke_initialized) {
        const char* env = std::getenv("UR_BALDOSA_PAUSE_SMOKE");
        g_smoke_enabled = env && std::strcmp(env, "1") == 0;
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

extern "C" void ur_baldosa_product_after_run_frame(
    const SnesDesktopHostFrameStats* stats) {
    // Existing verified two-seat guest observer remains intact.
    ur_baldosa_guest_snapshot_after_run_frame(stats);
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

    // Frame 120 precedes the 2P route's confirmed gameplay. Its identity
    // is for the isolated smoke exercise, NEVER course/event acceptance.
    if (!g_armed && stats->frame == 120) {
        g_armed = true;
        g_guest_frame = stats->frame;
        std::memcpy(g_frozen_ram, g_ram, sizeof(g_frozen_ram));
        require(snesrecomp_desktop_product_set_paused(1) != 0,
                "pause_was_not_acknowledged");
        require(snesrecomp_desktop_product_is_paused() != 0,
                "host_not_actually_paused");
        std::fprintf(stderr, "UR_BALDOSA_NATIVE_PAUSE ARMED guest=%u\n",
                     g_guest_frame);
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
        require(snesrecomp_desktop_product_set_paused(0) != 0,
                "resume_was_not_acknowledged");
        require(snesrecomp_desktop_product_is_paused() == 0,
                "host_still_paused_after_resume");
        g_resumed = true;
        std::fprintf(stderr,
            "UR_BALDOSA_NATIVE_PAUSE RELEASED guest=%u frozen_pumps=%u\n",
            g_guest_frame, g_frozen_ticks);
        std::fflush(stderr);
    }
}

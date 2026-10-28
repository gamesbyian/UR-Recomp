/* Native mapped-human-word seam in the pinned Baldosa SnesDesktopHostGame.
 * No gameplay, profile, SRAM, records or renderer ownership is transferred.
 * The pinned host supplies mapped human words BEFORE scripts/debug are merged. An
 * eventual Modern host must call focus/reset only at authoritative boundaries.
 */
#include "baldosa_execution_backend.hpp"
#include "quick_practice_input_mask.hpp"

#include <cstdint>
#include <cstdio>
#include <cstdlib>

// Read-only source-owned race flag: only a genuine in-progress demo may
// consume a P1 physical Start. Never write stock guest RAM.
extern "C" std::uint8_t g_ram[0x20000];

namespace {
ur::product::BaldosaGuestInputAuthority g_input;
std::uint16_t g_pending_stock_menu_mask;
unsigned g_host_owned_samples = 0;
bool g_attract_p1_physical_start_held = false;
}

// Only our existing host-owned stock-route may submit a discrete P1 input
// edge. The source-owned human filter remains first, before any script/debug
// words; no direct WRAM/ROM writes or synthetic result authority.
extern "C" int ur_baldosa_product_queue_stock_menu_input(std::uint16_t mask) {
    if (!g_input.host_owns_input() || g_pending_stock_menu_mask ||
        !ur::product::quick_practice_runner_mask_is_discrete_menu_input(mask))
        return 0;
    g_pending_stock_menu_mask = mask;
    return 1;
}

// Called ONLY from the native P1 Start down/up callback. It is intentionally
// distinct from the scripted discrete stock-menu input API: no A/keyboard/P2
// wake may masquerade as Start. The down state follows actual held duration.
extern "C" void ur_baldosa_product_attract_p1_start_event(int pressed) {
    if (!pressed) {
        g_attract_p1_physical_start_held = false;
    } else if (g_input.host_owns_input() && g_ram[0x0313u] == 1u) {
        g_attract_p1_physical_start_held = true;
    }
}

extern "C" void ur_baldosa_product_cancel_stock_menu_input(void) {
    g_pending_stock_menu_mask = 0;
}

extern "C" std::uint32_t ur_baldosa_product_filter_human_frame_inputs(
    std::uint32_t word, unsigned frame) {
    const bool host_owned = g_input.host_owns_input();
    const std::uint32_t queued = g_pending_stock_menu_mask;
    const std::uint32_t filtered = g_input.filter(word);
    // One frame, exact original runner button bit; never leak a held menu A
    // into the first playable frame after the route releases host focus.
    // SNES 12-bit Start is 0x0008, not 0x0100 (stock-menu Accept).
    // The real P1 physical/SDL Start edge can reach the ORIGINAL running demo,
    // but never its menu, another player's word or any non-host-owned state.
    // No fixed-length synthetic press, no RAM/menu rewrites and no bypass
    // of the existing physical release latch on subsequent focus handoff.
    const std::uint32_t live_demo_start =
        host_owned && g_attract_p1_physical_start_held &&
        g_ram[0x0313u] == 1u ? 0x0008u : 0u;
    const std::uint32_t accepted =
        filtered | static_cast<std::uint32_t>(g_pending_stock_menu_mask) |
        live_demo_start;
    g_pending_stock_menu_mask = 0;
    // Opt-in real mapped-human-word witness. Modern-owned physical buttons
    // must be masked while presence bits survive. Count actual filter calls.
    if (host_owned) {
        ++g_host_owned_samples;
        if (std::getenv("UR_BALDOSA_PRODUCT_INPUT_ISOLATION_DIAGNOSTICS") &&
            (g_host_owned_samples % 180u == 0u ||
             // After the 900-frame idle, sample bounded live navigation
             // even when Modern consumes every SDL button before this seam.
             (g_host_owned_samples > 900u &&
              g_host_owned_samples <= 1080u &&
              g_host_owned_samples % 30u == 0u) ||
             (word & 0x00ffffffu) != 0u ||
             // Read-only actual mapped-human-word sample around the
             // stock-attract seat-2 SDL B edge, never a guest write.
             (frame >= 1642u && frame <= 1646u &&
              std::getenv("UR_BALDOSA_MODERN_TITLE_ATTRACT_PROBE")))) {
            std::fprintf(stderr,
                "UR_BALDOSA_PRODUCT_INPUT_ISOLATION sample=%u frame=%u "
                "incoming=%08x guest=%08x queued=%04x host_owns=1\n",
                g_host_owned_samples, frame, static_cast<unsigned>(word),
                static_cast<unsigned>(accepted), static_cast<unsigned>(queued));
        }
    }
    if (std::getenv("UR_BALDOSA_PRODUCT_INPUT_DIAGNOSTICS") &&
        (frame == 0 || frame == 119 || frame == 479)) {
        std::fprintf(stderr,
            "UR_BALDOSA_PRODUCT_INPUT frame=%u incoming=%08x guest=%08x "
            "host_owns=%d\n", frame, static_cast<unsigned>(word),
            static_cast<unsigned>(accepted), g_input.host_owns_input() ? 1 : 0);
    }
    return accepted;
}

// Called only by a future Modern host's modal/focus owner. This function
// does not pause emulation. Pausing requires the framework's genuine host
// execution hold before returning success from the product lifecycle hook.
extern "C" void ur_baldosa_product_set_host_focus(int owned) {
    if (!owned) {
        g_pending_stock_menu_mask = 0;
        g_attract_p1_physical_start_held = false;
    }
    if (owned && !g_input.host_owns_input()) g_host_owned_samples = 0;
    g_input.host_focus(owned != 0);
}

extern "C" void ur_baldosa_product_guest_restarted(void) {
    // A Modern Restart is legal while the acknowledged native guest is
    // paused. Reset physical latches, but keep host input ownership through
    // that transaction; dropping focus here can leak held Start on resume.
    const bool was_host_owned = g_input.host_owns_input();
    g_input.reset();
    g_pending_stock_menu_mask = 0;
    g_attract_p1_physical_start_held = false;
    if (was_host_owned) g_input.host_focus(true);
}

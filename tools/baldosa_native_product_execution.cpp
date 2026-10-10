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

namespace {
ur::product::BaldosaGuestInputAuthority g_input;
std::uint16_t g_pending_stock_menu_mask;
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

extern "C" std::uint32_t ur_baldosa_product_filter_human_frame_inputs(
    std::uint32_t word, unsigned frame) {
    const std::uint32_t filtered = g_input.filter(word);
    // One frame, exact original runner button bit; never leak a held menu A
    // into the first playable frame after the route releases host focus.
    const std::uint32_t accepted =
        filtered | static_cast<std::uint32_t>(g_pending_stock_menu_mask);
    g_pending_stock_menu_mask = 0;
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
    if (!owned) g_pending_stock_menu_mask = 0;
    g_input.host_focus(owned != 0);
}

extern "C" void ur_baldosa_product_guest_restarted(void) {
    // A Modern Restart is legal while the acknowledged native guest is
    // paused. Reset physical latches, but keep host input ownership through
    // that transaction; dropping focus here can leak held Start on resume.
    const bool was_host_owned = g_input.host_owns_input();
    g_input.reset();
    g_pending_stock_menu_mask = 0;
    if (was_host_owned) g_input.host_focus(true);
}

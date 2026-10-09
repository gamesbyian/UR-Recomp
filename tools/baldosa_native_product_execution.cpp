/* Native mapped-human-word seam in the pinned Baldosa SnesDesktopHostGame.
 * No gameplay, profile, SRAM, records or renderer ownership is transferred.
 * The pinned host supplies mapped human words BEFORE scripts/debug are merged. An
 * eventual Modern host must call focus/reset only at authoritative boundaries.
 */
#include "baldosa_execution_backend.hpp"

#include <cstdint>
#include <cstdio>
#include <cstdlib>

namespace {
ur::product::BaldosaGuestInputAuthority g_input;
}

extern "C" std::uint32_t ur_baldosa_product_filter_human_frame_inputs(
    std::uint32_t word, unsigned frame) {
    const std::uint32_t accepted = g_input.filter(word);
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
    g_input.host_focus(owned != 0);
}

extern "C" void ur_baldosa_product_guest_restarted(void) {
    g_input.reset();
}

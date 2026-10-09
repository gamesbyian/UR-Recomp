/* Experiment-only adapter: bridge Baldosa's compiled guest WRAM to
 * UR-Recomp's existing source-visible racer semantics. Pure observation.
 * Exactly the same compiled game controls and state remain authoritative. */
#include "racer_guest_snapshot.hpp"

#include <cstdint>
#include <cstdio>

extern "C" {
#include "desktop/host_main.h"
extern std::uint8_t g_ram[];

void ur_baldosa_racer_snapshot_after_frame(const SnesDesktopHostFrameStats* stats)
{
    if (stats == nullptr || stats->frame == 0 || stats->frame % 600 != 0) {
        return;
    }
    const auto snapshot = ur::presentation::read_racer_guest_snapshot(
        g_ram, ur::presentation::RacerGuestAddresses::wram_size);
    if (!snapshot) {
        std::fprintf(stderr, "UR_BALDOSA_BRIDGE frame=%u invalid_wram\n",
                     stats->frame);
        return;
    }
    std::fprintf(stderr,
                 "UR_BALDOSA_BRIDGE frame=%u p1_frame=%04x p2_frame=%04x "
                 "p1_selector=%04x p2_selector=%04x\n",
                 stats->frame,
                 static_cast<unsigned>(snapshot->p1_semantic_frame_id),
                 static_cast<unsigned>(snapshot->p2_semantic_frame_id),
                 static_cast<unsigned>(snapshot->composition.p1_selector),
                 static_cast<unsigned>(snapshot->composition.p2_selector));
}
}  // extern "C"

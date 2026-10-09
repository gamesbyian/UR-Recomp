/* Read-only guest-state adapter. Validates reuse of UR-Recomp racer presentation
 * against Baldosa's compiled game without adopting a second guest authority. */
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>

extern "C" {
#include "host_main.h"
extern std::uint8_t g_ram[0x20000];
}
#include "racer_guest_snapshot.hpp"

extern "C" void ur_baldosa_guest_snapshot_after_run_frame(
    const SnesDesktopHostFrameStats *stats)
{
    using namespace ur::presentation;
    if (!stats)
        std::abort();
    const auto snapshot = read_racer_guest_snapshot(g_ram, 0x20000);
    if (!snapshot)
        std::abort();
    /* Real UR-Recomp Original fallback decision, not a stand-in or invented
     * semantic mapping. Both player slots share one coherent guest frame. */
    const auto p1 = select_racer_presentation_from_wram(
        GraphicsPack::Original, g_ram, 0x20000, 1);
    const auto p2 = select_racer_presentation_from_wram(
        GraphicsPack::Original, g_ram, 0x20000, 2);
    if (p1.selected_pack != GraphicsPack::Original ||
        p2.selected_pack != GraphicsPack::Original)
        std::abort();

    if (stats->frame == 1 || stats->frame == 120 || stats->frame == 480)
        std::fprintf(stderr,
            "UR_BALDOSA_GUEST_SNAPSHOT frame=%u "
            "p1=0x%04x p2=0x%04x\n",
            stats->frame,
            static_cast<unsigned>(snapshot->p1_semantic_frame_id),
            static_cast<unsigned>(snapshot->p2_semantic_frame_id));
}

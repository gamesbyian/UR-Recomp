// Synthetic TEST-ONLY source-paced C++ motion oracle consumed by an
// independent Python verifier. These rows are NOT true native host captures
// or SDL-presented frames. The actual shipping engine is not instantiated.
#include "modern_menu_motion.hpp"

#include <cstdint>
#include <cstdio>
#include <cstring>

int main(int argc, char** argv) {
    const bool wide = argc == 2 &&
        std::strcmp(argv[1], "--wide") == 0;
    if (argc > 2 || (argc == 2 && !wide)) return 2;
    const int width = wide ? 342 : 256;
    const int root_x = wide ? 11 : 8;
    const int root_w = wide ? 320 : 240;

    ur::product::ModernMenuMotionState state{};
    unsigned selection = 0;
    for (unsigned i = 0; i < 48; ++i) {
        // Real UI semantics would be driven by controller navigation;
        // here they are deterministic synthetic edges testing the model.
        switch (i) {
        case 1: selection = 1; break;
        case 4: selection = 0; break;
        case 6: selection = 1; break;
        case 8: selection = 3; break; // discontinuous skip snaps
        case 10: selection = 2; break;
        case 12: selection = 1; break;
        case 33: selection = 2; break;
        case 37: selection = 1; break;
        default: break;
        }
        const bool reduced = i >= 25 && i < 29;
        const std::uint64_t tick = 14u + i;
        const auto pose = ur::product::advance_modern_menu_motion(
            state,
            {tick, static_cast<std::uint8_t>(selection), true, reduced});
        if (!pose.visible || pose.selection != selection) return 3;
        std::printf(
            "UR_MODERN_MENU_MOTION_CAPTURE ordinal=%u tick60=%llu "
            "selection=%u spin=%d offset=%d entrance=%d reduced=%u "
            "root_x=%d root_w=%d surface_w=%d surface_h=224 painted=1\n",
            i, static_cast<unsigned long long>(tick), selection,
            pose.cursor_spin_phase, pose.cursor_remainder_px,
            pose.entrance_distance_px, reduced ? 1u : 0u,
            root_x, root_w, width);
    }
    return 0;
}

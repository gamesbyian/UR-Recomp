// Prints the C++ results of the layout formulas mirrored in
// tools/qa_modern_visual_diagnostics.py for a grid of inputs, so a unit test
// can prove the two implementations never drift.
#include "native/product/modern_ui_access.hpp"

#include <cstdio>

using namespace ur::product;

int main() {
    const int canvases[][2] = {{256, 224}, {342, 224}, {64, 64}, {63, 200},
                               {200, 63}, {16384, 224}, {16385, 224}, {100, 300}};
    for (const auto& c : canvases) {
        const auto t = modern_ui_title_safe(c[0], c[1]);
        const auto a = modern_ui_action_safe(c[0], c[1]);
        std::printf("safe %d %d title %d %d %d %d action %d %d %d %d\n", c[0], c[1],
                    t.x, t.y, t.width, t.height, a.x, a.y, a.width, a.height);
    }
    const int outputs[][2] = {{1280, 720}, {1920, 1080}, {3840, 2160}, {1024, 768},
                              {640, 480}, {800, 600}, {342, 224}, {341, 224},
                              {300, 700}, {16384, 16384}, {16385, 2000}, {512, 448}};
    for (const auto& lc : {canvases[0], canvases[1]})
        for (const auto& o : outputs) {
            const auto s = modern_ui_integer_scale(lc[0], lc[1], o[0], o[1]);
            std::printf("scale %d %d %d %d factor %d vp %d %d %d %d\n", lc[0], lc[1],
                        o[0], o[1], s.factor, s.viewport.x, s.viewport.y,
                        s.viewport.width, s.viewport.height);
        }
    return 0;
}

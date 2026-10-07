#include "modern_pad_glyphs.hpp"

#include <array>
#include <cassert>
#include <string>

namespace {

constexpr int kControlsBase = 100;

// SNESRecomp's default P1 map (kDefaultGamepadCmds): controls Up..R come
// from DpadUp, DpadDown, DpadLeft, DpadRight, Back, Start, B, A, Y, X, L1, R1.
constexpr std::array<int, 12> kDefaultButtons = {
    11, 12, 13, 14, 4, 6, 1, 0, 3, 2, 9, 10,
};

int default_map(int button) {
    for (int control = 0; control < 12; ++control) {
        if (kDefaultButtons[static_cast<std::size_t>(control)] == button) {
            return kControlsBase + control;
        }
    }
    return 0;
}

}  // namespace

int main() {
    using ur::product::modern_pad_glyph_for_control;
    auto glyph = [](int control, auto map) {
        return modern_pad_glyph_for_control(control, kControlsBase, map);
    };

    // Positional default: SNES B (jump) is the south button, printed "A".
    assert(glyph(7, default_map) == "A");
    assert(glyph(6, default_map) == "B");
    assert(glyph(8, default_map) == "Y");
    assert(glyph(9, default_map) == "X");
    assert(glyph(10, default_map) == "LB");
    assert(glyph(11, default_map) == "RB");
    assert(glyph(2, default_map) == "LEFT");
    assert(glyph(3, default_map) == "RIGHT");
    assert(glyph(5, default_map) == "START");
    assert(glyph(4, default_map) == "BACK");

    // A remap is followed: SNES B moved to the right trigger.
    auto remapped = [](int button) {
        if (button == 16) return kControlsBase + 7;
        if (button == 0) return 0;
        return default_map(button);
    };
    assert(glyph(7, remapped) == "RT");

    // Unbound and out-of-range controls read NONE.
    auto empty = [](int) { return 0; };
    assert(glyph(7, empty) == "NONE");
    assert(glyph(12, default_map) == "NONE");
    assert(glyph(-1, default_map) == "NONE");
    return 0;
}

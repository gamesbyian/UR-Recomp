#include "modern_controls_presenter.hpp"

#include <array>
#include <cassert>
#include <string_view>

using namespace ur::product;

int main() {
    const std::array<std::string_view, 12> keys{
        "Z", "X", "A", "S", "Q", "W",
        "ENTER", "RSHIFT", "UP", "DOWN", "LEFT", "",
    };

    ModernControlsRebindState state;
    state.selected = ModernControlBinding::Right;

    auto view = present_modern_controls(state, keys);
    assert(view.rows.size() == 12);
    assert(view.rows[0].control_label == "A");
    assert(view.rows[0].key_label == "Z");
    assert(!view.rows[0].selected);
    assert(view.rows[11].control_label == "RIGHT");
    assert(view.rows[11].key_label == "NONE");
    assert(view.rows[11].selected);
    assert(!view.rows[11].capturing);
    // Default glyphs are the positional pad buttons that produce SNES A/B/X/Y.
    assert(view.instruction == "B/ENTER SET  A/ESC BACK");
    assert(view.instruction_detail == "Y/DEL CLEAR  X/R RESET");
    // Both lines fit the narrowest pause-family panel (24 cells).
    assert(view.instruction.size() <= 24u);
    assert(view.instruction_detail.size() <= 24u);

    state.capturing = true;
    view = present_modern_controls(state, keys);
    assert(view.rows[11].capturing);
    assert(view.instruction == "PRESS A KEY");
    assert(view.instruction_detail == "ESC / A CANCEL");

    // Hints follow the live map rather than the SNES letters.
    ur::product::ModernControlsPadGlyphs remapped;
    remapped.confirm = "RT";
    remapped.back = "LT";
    state.capturing = false;
    view = present_modern_controls(state, keys, remapped);
    // Width is the host's job: it fits every Controls line to the panel.
    assert(view.instruction == "RT/ENTER SET  LT/ESC BACK");

    return 0;
}

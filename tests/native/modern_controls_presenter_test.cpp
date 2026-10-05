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
    assert(view.instruction.find("ENTER REBIND") != std::string::npos);

    state.capturing = true;
    view = present_modern_controls(state, keys);
    assert(view.rows[11].capturing);
    assert(view.instruction == "PRESS A KEY   ESC CANCEL");

    return 0;
}

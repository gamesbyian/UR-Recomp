#pragma once

#include "modern_controls_rebind.hpp"

#include <array>
#include <string>
#include <string_view>

namespace ur::product {

struct ModernControlsBindingRow {
    ModernControlBinding binding = ModernControlBinding::A;
    std::string control_label;
    std::string key_label;
    bool selected = false;
    bool capturing = false;
};

struct ModernControlsPresentation {
    std::array<ModernControlsBindingRow, 12> rows{};
    // Two short lines, each no wider than the narrowest pause-family panel
    // (24 cells). Keyboard keys and the mapped SNES buttons share a line.
    std::string instruction;
    std::string instruction_detail;
};

// Physical pad glyphs for the controls the panel reacts to (SNES A confirm,
// SNES B back, SNES X clear, SNES Y reset), read from the live GamepadMap.
struct ModernControlsPadGlyphs {
    std::string confirm = "B";
    std::string back = "A";
    std::string clear = "Y";
    std::string reset = "X";
};

ModernControlsPresentation present_modern_controls(
    const ModernControlsRebindState& state,
    const std::array<std::string_view, 12>& key_labels,
    const ModernControlsPadGlyphs& pad = {});

}  // namespace ur::product

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
    std::string instruction;
};

ModernControlsPresentation present_modern_controls(
    const ModernControlsRebindState& state,
    const std::array<std::string_view, 12>& key_labels);

}  // namespace ur::product

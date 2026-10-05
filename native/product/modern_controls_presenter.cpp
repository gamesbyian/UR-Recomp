#include "modern_controls_presenter.hpp"

namespace ur::product {

ModernControlsPresentation present_modern_controls(
    const ModernControlsRebindState& state,
    const std::array<std::string_view, 12>& key_labels) {
    ModernControlsPresentation out;

    for (int i = 0; i < modern_control_binding_count(); ++i) {
        const auto binding = static_cast<ModernControlBinding>(i);
        auto& row = out.rows[static_cast<std::size_t>(i)];
        row.binding = binding;
        row.control_label = modern_control_binding_name(binding);
        row.key_label =
            key_labels[static_cast<std::size_t>(i)].empty()
                ? "NONE"
                : std::string(key_labels[static_cast<std::size_t>(i)]);
        row.selected = binding == state.selected;
        row.capturing = row.selected && state.capturing;
    }

    out.instruction = state.capturing
        ? "PRESS A KEY   ESC CANCEL"
        : "ENTER REBIND   DELETE CLEAR   R RESET   ESC BACK";
    return out;
}

}  // namespace ur::product

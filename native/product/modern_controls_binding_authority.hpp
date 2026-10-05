#pragma once

#include "modern_controls_rebind.hpp"

#include <functional>

namespace ur::product {

struct ModernControlsBindingAuthority {
    std::function<void(int button, int key_scancode)> set_button;
    std::function<void()> reset_player;
    std::function<void()> save;
};

bool apply_modern_controls_command(
    const ModernControlsCommand& command,
    const ModernControlsBindingAuthority& authority);

}  // namespace ur::product

#pragma once

#include "host_product_state.hpp"

namespace ur::product {

constexpr bool should_pause_on_focus_loss(
    ExecutionMode mode,
    const HostSettings& settings,
    bool focused,
    bool already_paused) noexcept {
    return policy_for(mode).host_settings &&
           settings.pause_on_focus_loss &&
           !focused &&
           !already_paused;
}

}  // namespace ur::product

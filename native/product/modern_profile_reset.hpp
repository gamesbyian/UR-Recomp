#pragma once

#include "host_product_state.hpp"

#include <cstdint>

namespace ur::product {

enum class ModernProfileResetPhase : std::uint8_t {
    Idle = 0,
    Confirming = 1,
};

struct ModernProfileResetState {
    ModernProfileResetPhase phase = ModernProfileResetPhase::Idle;
};

enum class ModernProfileResetAction : std::uint8_t {
    None = 0,
    Execute = 1,
};

constexpr std::uint32_t modern_profile_admin_filter_human_input(
    ExecutionMode mode,
    bool settled_main_menu,
    std::uint32_t inputs) noexcept {
    constexpr std::uint32_t kP1L = 1u << 10;
    constexpr std::uint32_t kP1R = 1u << 11;
    if (mode == ExecutionMode::Modern && settled_main_menu) {
        return inputs & ~(kP1L | kP1R);
    }
    return inputs;
}

constexpr bool modern_profile_reset_can_open(
    ExecutionMode mode,
    bool active_profile_authoritative,
    bool selected_profile_is_active) noexcept {
    return mode == ExecutionMode::Modern &&
           active_profile_authoritative &&
           selected_profile_is_active;
}

constexpr ModernProfileResetState modern_profile_reset_open(
    ExecutionMode mode,
    bool active_profile_authoritative,
    bool selected_profile_is_active) noexcept {
    return modern_profile_reset_can_open(
               mode,
               active_profile_authoritative,
               selected_profile_is_active)
        ? ModernProfileResetState{ModernProfileResetPhase::Confirming}
        : ModernProfileResetState{};
}

constexpr bool modern_profile_reset_confirming(
    ModernProfileResetState state) noexcept {
    return state.phase == ModernProfileResetPhase::Confirming;
}

constexpr ModernProfileResetState modern_profile_reset_cancel(
    ModernProfileResetState) noexcept {
    return {};
}

struct ModernProfileResetDecision {
    ModernProfileResetState state{};
    ModernProfileResetAction action = ModernProfileResetAction::None;
};

constexpr ModernProfileResetDecision modern_profile_reset_confirm(
    ModernProfileResetState state,
    ExecutionMode mode,
    bool active_profile_authoritative,
    bool selected_profile_is_active) noexcept {
    if (!modern_profile_reset_confirming(state) ||
        !modern_profile_reset_can_open(
            mode,
            active_profile_authoritative,
            selected_profile_is_active)) {
        return {{}, ModernProfileResetAction::None};
    }
    return {{}, ModernProfileResetAction::Execute};
}

}  // namespace ur::product

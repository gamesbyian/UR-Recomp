#pragma once

#include "session_control.hpp"

#include <cstdint>

namespace ur::product {

enum class RuntimeDispatchStatus : std::uint8_t {
    Applied = 0,
    UnsupportedAction = 1,
    MissingHook = 2,
};

struct PauseRuntimeHooks {
    void (*set_paused)(int paused) = nullptr;
    int (*is_paused)(void) = nullptr;
};

RuntimeDispatchStatus dispatch_runtime_action(
    RuntimeAction action,
    const PauseRuntimeHooks& hooks) noexcept;

}  // namespace ur::product

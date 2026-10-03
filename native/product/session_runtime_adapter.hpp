#pragma once

#include "session_control.hpp"

#include <cstdint>

namespace ur::product {

class RaceRestartLifecycle;

enum class RuntimeDispatchStatus : std::uint8_t {
    Applied = 0,
    UnsupportedAction = 1,
    MissingHook = 2,
    RejectedByRuntime = 3,
};

struct SessionRuntimeHooks {
    void (*set_paused)(int paused) = nullptr;
    int (*is_paused)(void) = nullptr;
    bool (*restart_race)(void) = nullptr;
    void (*set_rewind_audio_timing_lock)(int active) = nullptr;
    void (*reconcile_after_restart)(void) = nullptr;
};

RuntimeDispatchStatus dispatch_runtime_action(
    RuntimeAction action,
    const SessionRuntimeHooks& hooks,
    RaceRestartLifecycle* restart_lifecycle = nullptr) noexcept;

}  // namespace ur::product

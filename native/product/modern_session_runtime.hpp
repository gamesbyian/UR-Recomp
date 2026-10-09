#pragma once

#include "race_restart_lifecycle.hpp"
#include "session_control.hpp"
#include "session_runtime_adapter.hpp"

#include <cstdint>

namespace ur::product {

struct ModernSessionDispatchResult {
    SessionRequestStatus request_status = SessionRequestStatus::RejectedByPolicy;
    RuntimeDispatchStatus dispatch_status = RuntimeDispatchStatus::UnsupportedAction;
    bool dispatched = false;

    bool applied() const noexcept {
        return request_status == SessionRequestStatus::Accepted &&
               dispatched &&
               dispatch_status == RuntimeDispatchStatus::Applied;
    }
};

class ModernSessionRuntime {
public:
    ModernSessionRuntime(
        ExecutionMode mode,
        RaceRestartLifecycle& restart_lifecycle,
        SessionRuntimeHooks hooks = {}) noexcept
        : control_(mode),
          restart_lifecycle_(restart_lifecycle),
          hooks_(hooks) {}

    ExecutionMode mode() const noexcept { return control_.mode(); }
    SessionPhase phase() const noexcept { return control_.phase(); }
    bool restart_available() const noexcept {
        return control_.mode() == ExecutionMode::Modern &&
               (hooks_.native_restart_available
                    ? hooks_.native_restart_available(hooks_.native_context)
                    : restart_lifecycle_.restart_available());
    }

    RestartLifecycleEvent observe_race_active(bool active);
    RestartLifecycleEvent retire_race_attempt() noexcept;
    ModernSessionDispatchResult request(SessionCommand command) noexcept;

private:
    SessionControl control_;
    RaceRestartLifecycle& restart_lifecycle_;
    SessionRuntimeHooks hooks_;
};

}  // namespace ur::product

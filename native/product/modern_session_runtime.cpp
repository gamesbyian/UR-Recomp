#include "modern_session_runtime.hpp"

namespace ur::product {

RestartLifecycleEvent ModernSessionRuntime::observe_race_active(bool active) {
    if (control_.mode() != ExecutionMode::Modern) {
        return RestartLifecycleEvent::None;
    }
    return restart_lifecycle_.observe_race_active(active);
}

RestartLifecycleEvent ModernSessionRuntime::retire_race_attempt() noexcept {
    if (control_.mode() != ExecutionMode::Modern) {
        return RestartLifecycleEvent::None;
    }
    return restart_lifecycle_.retire_attempt();
}

ModernSessionDispatchResult ModernSessionRuntime::request(
    SessionCommand command) noexcept {
    const SessionRequestResult requested = control_.request(command);
    ModernSessionDispatchResult result{};
    result.request_status = requested.status;

    if (!requested.accepted()) {
        return result;
    }

    const auto action = control_.take_pending_action();
    if (!action) {
        result.dispatch_status = RuntimeDispatchStatus::RejectedByRuntime;
        return result;
    }

    result.dispatched = true;
    result.dispatch_status = dispatch_runtime_action(
        *action,
        hooks_,
        &restart_lifecycle_);
    return result;
}

}  // namespace ur::product

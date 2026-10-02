#include "session_runtime_adapter.hpp"

namespace ur::product {

RuntimeDispatchStatus dispatch_runtime_action(
    RuntimeAction action,
    const SessionRuntimeHooks& hooks) noexcept {
    switch (action) {
    case RuntimeAction::SuspendGuest:
        if (!hooks.set_paused) {
            return RuntimeDispatchStatus::MissingHook;
        }
        hooks.set_paused(1);
        return RuntimeDispatchStatus::Applied;

    case RuntimeAction::ResumeGuest:
        if (!hooks.set_paused) {
            return RuntimeDispatchStatus::MissingHook;
        }
        hooks.set_paused(0);
        return RuntimeDispatchStatus::Applied;

    case RuntimeAction::RestartRace:
        if (!hooks.restart_race) {
            return RuntimeDispatchStatus::MissingHook;
        }
        return hooks.restart_race()
            ? RuntimeDispatchStatus::Applied
            : RuntimeDispatchStatus::RejectedByRuntime;

    case RuntimeAction::ExitToFrontend:
        return RuntimeDispatchStatus::UnsupportedAction;
    }

    return RuntimeDispatchStatus::UnsupportedAction;
}

}  // namespace ur::product

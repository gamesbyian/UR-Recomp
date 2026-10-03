#include "session_runtime_adapter.hpp"

#include "race_restart_lifecycle.hpp"

namespace ur::product {

RuntimeDispatchStatus dispatch_runtime_action(
    RuntimeAction action,
    const SessionRuntimeHooks& hooks,
    RaceRestartLifecycle* restart_lifecycle) noexcept {
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
        if (restart_lifecycle) {
            switch (restart_lifecycle->restart()) {
            case RestartAnchorRestoreStatus::Restored:
                return RuntimeDispatchStatus::Applied;
            case RestartAnchorRestoreStatus::MissingHook:
                return RuntimeDispatchStatus::MissingHook;
            case RestartAnchorRestoreStatus::NoAnchor:
            case RestartAnchorRestoreStatus::RestoreFailed:
                return RuntimeDispatchStatus::RejectedByRuntime;
            }
        }
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

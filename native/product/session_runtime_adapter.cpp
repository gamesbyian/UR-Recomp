#include "session_runtime_adapter.hpp"

#include "race_restart_lifecycle.hpp"

namespace ur::product {

RuntimeDispatchStatus dispatch_runtime_action(
    RuntimeAction action,
    const SessionRuntimeHooks& hooks,
    RaceRestartLifecycle* restart_lifecycle) noexcept {
    switch (action) {
    case RuntimeAction::SuspendGuest:
        if (hooks.native_set_paused) {
            return hooks.native_set_paused(hooks.native_context, 1)
                ? RuntimeDispatchStatus::Applied
                : RuntimeDispatchStatus::RejectedByRuntime;
        }
        if (!hooks.set_paused) {
            return RuntimeDispatchStatus::MissingHook;
        }
        hooks.set_paused(1);
        return RuntimeDispatchStatus::Applied;

    case RuntimeAction::ResumeGuest:
        if (hooks.native_set_paused) {
            return hooks.native_set_paused(hooks.native_context, 0)
                ? RuntimeDispatchStatus::Applied
                : RuntimeDispatchStatus::RejectedByRuntime;
        }
        if (!hooks.set_paused) {
            return RuntimeDispatchStatus::MissingHook;
        }
        hooks.set_paused(0);
        return RuntimeDispatchStatus::Applied;

    case RuntimeAction::RestartRace:
        if (hooks.native_restart_race) {
            return hooks.native_restart_race(hooks.native_context)
                ? RuntimeDispatchStatus::Applied
                : RuntimeDispatchStatus::RejectedByRuntime;
        }
        if (restart_lifecycle) {
            switch (restart_lifecycle->restart()) {
            case RestartAnchorRestoreStatus::Restored:
                if (hooks.reconcile_after_restart) {
                    hooks.reconcile_after_restart();
                }
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
        if (hooks.native_exit_to_frontend) {
            // The native guest must acknowledge the complete transition,
            // including any unpause. No legacy void call can certify it.
            return hooks.native_exit_to_frontend(hooks.native_context)
                ? RuntimeDispatchStatus::Applied
                : RuntimeDispatchStatus::RejectedByRuntime;
        }
        if (!hooks.exit_to_frontend || !hooks.set_paused) {
            return RuntimeDispatchStatus::MissingHook;
        }
        if (!hooks.exit_to_frontend()) {
            return RuntimeDispatchStatus::RejectedByRuntime;
        }
        hooks.set_paused(0);
        return RuntimeDispatchStatus::Applied;
    }

    return RuntimeDispatchStatus::UnsupportedAction;
}

}  // namespace ur::product

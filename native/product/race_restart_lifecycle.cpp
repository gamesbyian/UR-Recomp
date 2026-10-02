#include "race_restart_lifecycle.hpp"

namespace ur::product {

RestartLifecycleEvent RaceRestartLifecycle::observe_race_active(bool active) {
    const bool entering_race = active && !race_active_;
    race_active_ = active;

    if (!entering_race) {
        return RestartLifecycleEvent::None;
    }

    // A newly entered race supersedes any prior attempt. Keep the previous
    // anchor through results/frontend transitions so Retry remains available
    // until the next actual race begins.
    anchor_.clear();
    return anchor_.capture() == RestartAnchorCaptureStatus::Captured
        ? RestartLifecycleEvent::AnchorCaptured
        : RestartLifecycleEvent::AnchorCaptureFailed;
}

}  // namespace ur::product

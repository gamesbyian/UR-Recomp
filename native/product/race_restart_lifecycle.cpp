#include "race_restart_lifecycle.hpp"

namespace ur::product {

RestartLifecycleEvent RaceRestartLifecycle::observe_race_active(bool active) {
    const bool entering_race = active && !race_active_;
    race_active_ = active;

    if (!entering_race) {
        return RestartLifecycleEvent::None;
    }

    // A newly entered race supersedes any prior attempt. Keep the previous
    // anchor through results so Retry remains available until a confirmed
    // course/frontend transition retires the attempt or the next race begins.
    anchor_.clear();
    return anchor_.capture() == RestartAnchorCaptureStatus::Captured
        ? RestartLifecycleEvent::AnchorCaptured
        : RestartLifecycleEvent::AnchorCaptureFailed;
}

RestartAnchorRestoreStatus RaceRestartLifecycle::restart() {
    const auto status = anchor_.restart();
    if (status == RestartAnchorRestoreStatus::Restored) {
        // The restored snapshot is the active-race anchor. Mark that lifecycle
        // state immediately so the next observed active frame is not mistaken
        // for a new attempt and cannot replace the immutable restart point.
        race_active_ = true;
    }
    return status;
}

RestartLifecycleEvent RaceRestartLifecycle::retire_attempt() noexcept {
    const bool had_attempt = race_active_ || anchor_.armed();
    race_active_ = false;
    anchor_.clear();
    return had_attempt
        ? RestartLifecycleEvent::AnchorRetired
        : RestartLifecycleEvent::None;
}

}  // namespace ur::product

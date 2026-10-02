#include "race_restart_anchor.hpp"

namespace ur::product {

RaceRestartAnchor::RaceRestartAnchor(
    SnapshotRuntimeHooks hooks,
    std::size_t capacity)
    : hooks_(hooks), capacity_(capacity) {}

RestartAnchorCaptureStatus RaceRestartAnchor::capture() {
    if (armed()) {
        return RestartAnchorCaptureStatus::AlreadyArmed;
    }
    if (!hooks_.save_snapshot || capacity_ == 0) {
        return RestartAnchorCaptureStatus::MissingHook;
    }

    std::vector<std::uint8_t> candidate(capacity_);
    const std::size_t size = hooks_.save_snapshot(candidate.data(), candidate.size());
    if (size == 0 || size > candidate.size()) {
        return RestartAnchorCaptureStatus::CaptureFailed;
    }

    candidate.resize(size);
    snapshot_.swap(candidate);
    return RestartAnchorCaptureStatus::Captured;
}

RestartAnchorRestoreStatus RaceRestartAnchor::restart() {
    if (!armed()) {
        return RestartAnchorRestoreStatus::NoAnchor;
    }
    if (!hooks_.load_snapshot) {
        return RestartAnchorRestoreStatus::MissingHook;
    }
    if (!hooks_.load_snapshot(snapshot_.data(), snapshot_.size())) {
        return RestartAnchorRestoreStatus::RestoreFailed;
    }
    return RestartAnchorRestoreStatus::Restored;
}

void RaceRestartAnchor::clear() noexcept {
    snapshot_.clear();
    snapshot_.shrink_to_fit();
}

}  // namespace ur::product

#pragma once

#include "race_restart_anchor.hpp"

#include <cstdint>

namespace ur::product {

enum class RestartLifecycleEvent : std::uint8_t {
    None = 0,
    AnchorCaptured = 1,
    AnchorCaptureFailed = 2,
};

class RaceRestartLifecycle {
public:
    explicit RaceRestartLifecycle(RaceRestartAnchor& anchor) noexcept
        : anchor_(anchor) {}

    RestartLifecycleEvent observe_race_active(bool active);
    RestartAnchorRestoreStatus restart() { return anchor_.restart(); }

    bool race_active() const noexcept { return race_active_; }
    bool restart_available() const noexcept { return anchor_.armed(); }

private:
    RaceRestartAnchor& anchor_;
    bool race_active_ = false;
};

}  // namespace ur::product

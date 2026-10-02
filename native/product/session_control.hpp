#pragma once

#include "host_product_state.hpp"

#include <cstdint>
#include <optional>

namespace ur::product {

enum class SessionPhase : std::uint8_t {
    Running = 0,
    Paused = 1,
};

enum class SessionCommand : std::uint8_t {
    Pause = 0,
    Resume = 1,
    RestartRace = 2,
    ExitToFrontend = 3,
};

enum class SessionRequestStatus : std::uint8_t {
    Accepted = 0,
    RejectedByPolicy = 1,
    NoOp = 2,
    Busy = 3,
};

enum class RuntimeAction : std::uint8_t {
    SuspendGuest = 0,
    ResumeGuest = 1,
    RestartRace = 2,
    ExitToFrontend = 3,
};

struct SessionRequestResult {
    SessionRequestStatus status;
    std::optional<RuntimeAction> action;

    bool accepted() const noexcept {
        return status == SessionRequestStatus::Accepted;
    }
};

class SessionControl {
public:
    explicit SessionControl(ExecutionMode mode) noexcept : mode_(mode) {}

    ExecutionMode mode() const noexcept { return mode_; }
    SessionPhase phase() const noexcept { return phase_; }
    bool has_pending_action() const noexcept { return pending_action_.has_value(); }

    SessionRequestResult request(SessionCommand command) noexcept;
    std::optional<RuntimeAction> take_pending_action() noexcept;

private:
    ExecutionMode mode_;
    SessionPhase phase_ = SessionPhase::Running;
    std::optional<RuntimeAction> pending_action_;
};

}  // namespace ur::product

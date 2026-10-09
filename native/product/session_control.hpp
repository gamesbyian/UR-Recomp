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
    void reconcile_failed_runtime_action(SessionPhase before) noexcept {
        // Request policy is optimistic; an unacknowledged native pause or
        // resume must not silently change Modern's authoritative UI phase.
        phase_ = before;
        pending_action_.reset();
    }
    void reconcile_frontend_return() noexcept {
        phase_ = SessionPhase::Running;
        pending_action_.reset();
    }

private:
    ExecutionMode mode_;
    SessionPhase phase_ = SessionPhase::Running;
    std::optional<RuntimeAction> pending_action_;
};

}  // namespace ur::product

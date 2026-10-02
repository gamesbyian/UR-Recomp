#include "session_control.hpp"

namespace ur::product {

SessionRequestResult SessionControl::request(SessionCommand command) noexcept {
    if (!policy_for(mode_).modern_commands) {
        return {SessionRequestStatus::RejectedByPolicy, std::nullopt};
    }

    if (pending_action_) {
        return {SessionRequestStatus::Busy, std::nullopt};
    }

    switch (command) {
    case SessionCommand::Pause:
        if (phase_ == SessionPhase::Paused) {
            return {SessionRequestStatus::NoOp, std::nullopt};
        }
        phase_ = SessionPhase::Paused;
        pending_action_ = RuntimeAction::SuspendGuest;
        break;

    case SessionCommand::Resume:
        if (phase_ == SessionPhase::Running) {
            return {SessionRequestStatus::NoOp, std::nullopt};
        }
        phase_ = SessionPhase::Running;
        pending_action_ = RuntimeAction::ResumeGuest;
        break;

    case SessionCommand::RestartRace:
        pending_action_ = RuntimeAction::RestartRace;
        break;

    case SessionCommand::ExitToFrontend:
        pending_action_ = RuntimeAction::ExitToFrontend;
        break;
    }

    return {SessionRequestStatus::Accepted, pending_action_};
}

std::optional<RuntimeAction> SessionControl::take_pending_action() noexcept {
    auto action = pending_action_;
    pending_action_.reset();
    return action;
}

}  // namespace ur::product

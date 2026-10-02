#include "session_control.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    {
        SessionControl authentic{ExecutionMode::Authentic};
        assert(authentic.phase() == SessionPhase::Running);
        for (const auto command : {
                 SessionCommand::Pause,
                 SessionCommand::Resume,
                 SessionCommand::RestartRace,
                 SessionCommand::ExitToFrontend,
             }) {
            const auto result = authentic.request(command);
            assert(result.status == SessionRequestStatus::RejectedByPolicy);
            assert(!result.action);
            assert(!authentic.has_pending_action());
            assert(authentic.phase() == SessionPhase::Running);
        }
    }

    {
        SessionControl modern{ExecutionMode::Modern};

        const auto redundant_resume = modern.request(SessionCommand::Resume);
        assert(redundant_resume.status == SessionRequestStatus::NoOp);
        assert(!redundant_resume.action);

        const auto pause = modern.request(SessionCommand::Pause);
        assert(pause.accepted());
        assert(pause.action == RuntimeAction::SuspendGuest);
        assert(modern.phase() == SessionPhase::Paused);
        assert(modern.has_pending_action());

        const auto busy_restart = modern.request(SessionCommand::RestartRace);
        assert(busy_restart.status == SessionRequestStatus::Busy);
        assert(!busy_restart.action);

        assert(modern.take_pending_action() == RuntimeAction::SuspendGuest);
        assert(!modern.has_pending_action());

        const auto redundant_pause = modern.request(SessionCommand::Pause);
        assert(redundant_pause.status == SessionRequestStatus::NoOp);

        const auto restart = modern.request(SessionCommand::RestartRace);
        assert(restart.accepted());
        assert(restart.action == RuntimeAction::RestartRace);
        assert(modern.phase() == SessionPhase::Paused);
        assert(modern.take_pending_action() == RuntimeAction::RestartRace);

        const auto resume = modern.request(SessionCommand::Resume);
        assert(resume.accepted());
        assert(resume.action == RuntimeAction::ResumeGuest);
        assert(modern.phase() == SessionPhase::Running);
        assert(modern.take_pending_action() == RuntimeAction::ResumeGuest);

        const auto exit = modern.request(SessionCommand::ExitToFrontend);
        assert(exit.accepted());
        assert(exit.action == RuntimeAction::ExitToFrontend);
        assert(modern.phase() == SessionPhase::Running);
        assert(modern.take_pending_action() == RuntimeAction::ExitToFrontend);
        assert(!modern.take_pending_action());
    }

    return 0;
}

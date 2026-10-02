#include "session_runtime_adapter.hpp"

#include <cassert>

using namespace ur::product;

namespace {

int paused = 0;
bool restart_result = true;
unsigned restart_calls = 0;

void set_paused(int value) {
    paused = value ? 1 : 0;
}

int is_paused() {
    return paused;
}

bool restart_race() {
    ++restart_calls;
    return restart_result;
}

}  // namespace

int main() {
    const SessionRuntimeHooks hooks{&set_paused, &is_paused, &restart_race};

    paused = 0;
    assert(dispatch_runtime_action(RuntimeAction::SuspendGuest, hooks) ==
           RuntimeDispatchStatus::Applied);
    assert(paused == 1);
    assert(hooks.is_paused() == 1);

    assert(dispatch_runtime_action(RuntimeAction::ResumeGuest, hooks) ==
           RuntimeDispatchStatus::Applied);
    assert(paused == 0);
    assert(hooks.is_paused() == 0);

    restart_result = true;
    assert(dispatch_runtime_action(RuntimeAction::RestartRace, hooks) ==
           RuntimeDispatchStatus::Applied);
    assert(restart_calls == 1);

    restart_result = false;
    assert(dispatch_runtime_action(RuntimeAction::RestartRace, hooks) ==
           RuntimeDispatchStatus::RejectedByRuntime);
    assert(restart_calls == 2);

    assert(dispatch_runtime_action(RuntimeAction::ExitToFrontend, hooks) ==
           RuntimeDispatchStatus::UnsupportedAction);
    assert(paused == 0);

    SessionRuntimeHooks missing{};
    assert(dispatch_runtime_action(RuntimeAction::SuspendGuest, missing) ==
           RuntimeDispatchStatus::MissingHook);
    assert(dispatch_runtime_action(RuntimeAction::ResumeGuest, missing) ==
           RuntimeDispatchStatus::MissingHook);
    assert(dispatch_runtime_action(RuntimeAction::RestartRace, missing) ==
           RuntimeDispatchStatus::MissingHook);

    return 0;
}

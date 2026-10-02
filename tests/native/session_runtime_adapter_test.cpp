#include "session_runtime_adapter.hpp"

#include <cassert>

using namespace ur::product;

namespace {

int paused = 0;

void set_paused(int value) {
    paused = value ? 1 : 0;
}

int is_paused() {
    return paused;
}

}  // namespace

int main() {
    const PauseRuntimeHooks hooks{&set_paused, &is_paused};

    paused = 0;
    assert(dispatch_runtime_action(RuntimeAction::SuspendGuest, hooks) ==
           RuntimeDispatchStatus::Applied);
    assert(paused == 1);
    assert(hooks.is_paused() == 1);

    assert(dispatch_runtime_action(RuntimeAction::ResumeGuest, hooks) ==
           RuntimeDispatchStatus::Applied);
    assert(paused == 0);
    assert(hooks.is_paused() == 0);

    assert(dispatch_runtime_action(RuntimeAction::RestartRace, hooks) ==
           RuntimeDispatchStatus::UnsupportedAction);
    assert(paused == 0);

    assert(dispatch_runtime_action(RuntimeAction::ExitToFrontend, hooks) ==
           RuntimeDispatchStatus::UnsupportedAction);
    assert(paused == 0);

    PauseRuntimeHooks missing{};
    assert(dispatch_runtime_action(RuntimeAction::SuspendGuest, missing) ==
           RuntimeDispatchStatus::MissingHook);
    assert(dispatch_runtime_action(RuntimeAction::ResumeGuest, missing) ==
           RuntimeDispatchStatus::MissingHook);

    return 0;
}

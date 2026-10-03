#include "focus_pause_policy.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    HostSettings settings;

    assert(should_pause_on_focus_loss(
        ExecutionMode::Modern, settings, false, false));
    assert(!should_pause_on_focus_loss(
        ExecutionMode::Modern, settings, true, false));
    assert(!should_pause_on_focus_loss(
        ExecutionMode::Modern, settings, false, true));

    settings.pause_on_focus_loss = false;
    assert(!should_pause_on_focus_loss(
        ExecutionMode::Modern, settings, false, false));

    settings.pause_on_focus_loss = true;
    assert(!should_pause_on_focus_loss(
        ExecutionMode::Authentic, settings, false, false));

    return 0;
}

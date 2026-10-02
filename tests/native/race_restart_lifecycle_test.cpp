#include "race_restart_lifecycle.hpp"

#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <vector>

using namespace ur::product;

namespace {

std::vector<std::uint8_t> machine;
unsigned saves = 0;
unsigned loads = 0;

std::size_t save_snapshot(void* dst, std::size_t capacity) {
    ++saves;
    if (machine.empty() || capacity < machine.size()) {
        return 0;
    }
    std::copy(machine.begin(), machine.end(), static_cast<std::uint8_t*>(dst));
    return machine.size();
}

bool load_snapshot(const void* src, std::size_t size) {
    ++loads;
    const auto* bytes = static_cast<const std::uint8_t*>(src);
    machine.assign(bytes, bytes + size);
    return true;
}

}  // namespace

int main() {
    RaceRestartAnchor anchor{{&save_snapshot, &load_snapshot}, 64};
    RaceRestartLifecycle lifecycle{anchor};

    // Frontend/pre-race observation does not create an anchor.
    machine = {1};
    assert(lifecycle.observe_race_active(false) == RestartLifecycleEvent::None);
    assert(!lifecycle.restart_available());
    assert(saves == 0);

    // First completed active-race observation captures exactly once.
    machine = {1, 2, 3};
    assert(lifecycle.observe_race_active(true) ==
           RestartLifecycleEvent::AnchorCaptured);
    assert(lifecycle.race_active());
    assert(lifecycle.restart_available());
    assert(saves == 1);

    machine = {9, 9};
    assert(lifecycle.observe_race_active(true) == RestartLifecycleEvent::None);
    assert(saves == 1);

    // Leaving gameplay does not discard the just-finished attempt. This keeps
    // a Results-screen Retry action meaningful.
    assert(lifecycle.observe_race_active(false) == RestartLifecycleEvent::None);
    assert(!lifecycle.race_active());
    assert(lifecycle.restart_available());
    assert(lifecycle.restart() == RestartAnchorRestoreStatus::Restored);
    assert((machine == std::vector<std::uint8_t>{1, 2, 3}));
    assert(loads == 1);

    // The next actual race entry replaces the prior attempt atomically.
    machine = {4, 5, 6, 7};
    assert(lifecycle.observe_race_active(true) ==
           RestartLifecycleEvent::AnchorCaptured);
    assert(saves == 2);
    machine = {0};
    assert(lifecycle.restart() == RestartAnchorRestoreStatus::Restored);
    assert((machine == std::vector<std::uint8_t>{4, 5, 6, 7}));

    // Failed capture of a new race does not leave the stale prior race
    // restartable under the new session.
    lifecycle.observe_race_active(false);
    machine.clear();
    assert(lifecycle.observe_race_active(true) ==
           RestartLifecycleEvent::AnchorCaptureFailed);
    assert(!lifecycle.restart_available());
    assert(lifecycle.restart() == RestartAnchorRestoreStatus::NoAnchor);

    return 0;
}

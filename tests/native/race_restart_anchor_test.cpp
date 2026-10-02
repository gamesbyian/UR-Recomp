#include "race_restart_anchor.hpp"

#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <vector>

using namespace ur::product;

namespace {

std::vector<std::uint8_t> machine{1, 2, 3, 4, 5};
bool refuse_save = false;
bool refuse_load = false;
unsigned save_calls = 0;
unsigned load_calls = 0;

std::size_t save_snapshot(void* data, std::size_t capacity) {
    ++save_calls;
    if (refuse_save || capacity < machine.size()) {
        return 0;
    }
    std::copy(machine.begin(), machine.end(), static_cast<std::uint8_t*>(data));
    return machine.size();
}

bool load_snapshot(const void* data, std::size_t size) {
    ++load_calls;
    if (refuse_load) {
        return false;
    }
    const auto* bytes = static_cast<const std::uint8_t*>(data);
    machine.assign(bytes, bytes + size);
    return true;
}

}  // namespace

int main() {
    RaceRestartAnchor anchor{{&save_snapshot, &load_snapshot}, 64};

    assert(!anchor.armed());
    assert(anchor.restart() == RestartAnchorRestoreStatus::NoAnchor);

    assert(anchor.capture() == RestartAnchorCaptureStatus::Captured);
    assert(anchor.armed());
    assert(anchor.snapshot_size() == 5);
    assert(save_calls == 1);

    // A race anchor is immutable until the lifecycle owner explicitly clears it.
    machine = {9, 9, 9};
    assert(anchor.capture() == RestartAnchorCaptureStatus::AlreadyArmed);
    assert(save_calls == 1);

    assert(anchor.restart() == RestartAnchorRestoreStatus::Restored);
    assert((machine == std::vector<std::uint8_t>{1, 2, 3, 4, 5}));
    assert(load_calls == 1);

    // A failed restore keeps the exact anchor available for a later retry.
    machine = {7, 7};
    refuse_load = true;
    assert(anchor.restart() == RestartAnchorRestoreStatus::RestoreFailed);
    assert(anchor.armed());
    assert((machine == std::vector<std::uint8_t>{7, 7}));
    refuse_load = false;
    assert(anchor.restart() == RestartAnchorRestoreStatus::Restored);
    assert((machine == std::vector<std::uint8_t>{1, 2, 3, 4, 5}));

    anchor.clear();
    assert(!anchor.armed());
    machine = {6, 5, 4};
    assert(anchor.capture() == RestartAnchorCaptureStatus::Captured);
    assert(anchor.snapshot_size() == 3);

    RaceRestartAnchor missing{{nullptr, nullptr}, 64};
    assert(missing.capture() == RestartAnchorCaptureStatus::MissingHook);

    RaceRestartAnchor too_small{{&save_snapshot, &load_snapshot}, 1};
    assert(too_small.capture() == RestartAnchorCaptureStatus::CaptureFailed);
    assert(!too_small.armed());

    refuse_save = true;
    RaceRestartAnchor refused{{&save_snapshot, &load_snapshot}, 64};
    assert(refused.capture() == RestartAnchorCaptureStatus::CaptureFailed);
    assert(!refused.armed());

    return 0;
}

#include "modern_session_runtime.hpp"

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
int host_paused = 0;

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

void set_paused(int paused) {
    host_paused = paused ? 1 : 0;
}

int is_paused() {
    return host_paused;
}

void reset_fixture() {
    machine.clear();
    saves = 0;
    loads = 0;
    host_paused = 0;
}

}  // namespace

int main() {
    {
        reset_fixture();
        RaceRestartAnchor anchor{{&save_snapshot, &load_snapshot}, 64};
        RaceRestartLifecycle lifecycle{anchor};
        ModernSessionRuntime authentic{
            ExecutionMode::Authentic,
            lifecycle,
            {&set_paused, &is_paused, nullptr}};

        machine = {1, 2, 3};
        assert(authentic.observe_race_active(true) == RestartLifecycleEvent::None);
        assert(!authentic.restart_available());
        assert(saves == 0);

        const auto restart = authentic.request(SessionCommand::RestartRace);
        assert(restart.request_status == SessionRequestStatus::RejectedByPolicy);
        assert(!restart.dispatched);
        assert(loads == 0);
    }

    {
        reset_fixture();
        RaceRestartAnchor anchor{{&save_snapshot, &load_snapshot}, 64};
        RaceRestartLifecycle lifecycle{anchor};
        ModernSessionRuntime modern{
            ExecutionMode::Modern,
            lifecycle,
            {&set_paused, &is_paused, nullptr}};

        // Before an active-race anchor exists, the typed command reaches the
        // runtime adapter and fails closed at the real lifecycle restore.
        const auto early = modern.request(SessionCommand::RestartRace);
        assert(early.request_status == SessionRequestStatus::Accepted);
        assert(early.dispatched);
        assert(early.dispatch_status == RuntimeDispatchStatus::RejectedByRuntime);
        assert(loads == 0);

        // Entering a supported active race establishes one immutable anchor.
        machine = {1, 2, 3, 4};
        assert(modern.observe_race_active(true) ==
               RestartLifecycleEvent::AnchorCaptured);
        assert(modern.restart_available());
        assert(saves == 1);

        machine = {9, 9, 9};
        assert(modern.observe_race_active(true) == RestartLifecycleEvent::None);
        assert(saves == 1);

        // Restart travels SessionControl -> RuntimeAction -> adapter ->
        // validated lifecycle -> exact snapshot restore.
        const auto restart = modern.request(SessionCommand::RestartRace);
        assert(restart.applied());
        assert((machine == std::vector<std::uint8_t>{1, 2, 3, 4}));
        assert(loads == 1);

        // Repeated restart reuses the exact same anchor.
        machine = {8, 7, 6};
        const auto repeated = modern.request(SessionCommand::RestartRace);
        assert(repeated.applied());
        assert((machine == std::vector<std::uint8_t>{1, 2, 3, 4}));
        assert(loads == 2);
        assert(saves == 1);

        // Results/post-race keeps Retry available.
        assert(modern.observe_race_active(false) == RestartLifecycleEvent::None);
        assert(modern.restart_available());
        machine = {5};
        assert(modern.request(SessionCommand::RestartRace).applied());
        assert((machine == std::vector<std::uint8_t>{1, 2, 3, 4}));

        // Host pause state is independent of the restored guest snapshot.
        assert(modern.request(SessionCommand::Pause).applied());
        assert(host_paused == 1);
        machine = {4};
        assert(modern.request(SessionCommand::RestartRace).applied());
        assert(host_paused == 1);
        assert(modern.phase() == SessionPhase::Paused);
        assert((machine == std::vector<std::uint8_t>{1, 2, 3, 4}));
        assert(modern.request(SessionCommand::Resume).applied());
        assert(host_paused == 0);

        // A confirmed course/frontend transition retires stale Retry state.
        assert(modern.retire_race_attempt() ==
               RestartLifecycleEvent::AnchorRetired);
        assert(!modern.restart_available());
        machine = {7};
        const auto retired = modern.request(SessionCommand::RestartRace);
        assert(retired.dispatch_status == RuntimeDispatchStatus::RejectedByRuntime);
        assert((machine == std::vector<std::uint8_t>{7}));

        // The next actual race establishes a fresh anchor.
        machine = {10, 11};
        assert(modern.observe_race_active(true) ==
               RestartLifecycleEvent::AnchorCaptured);
        assert(saves == 2);
        machine = {0};
        assert(modern.request(SessionCommand::RestartRace).applied());
        assert((machine == std::vector<std::uint8_t>{10, 11}));
    }

    return 0;
}

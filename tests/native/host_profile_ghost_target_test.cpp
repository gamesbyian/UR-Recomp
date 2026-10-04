#include "host_profile_ghost_target.hpp"

#include <array>
#include <cassert>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <string>

using namespace ur::product;

namespace {

std::string read_all(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    return std::string(
        std::istreambuf_iterator<char>(in),
        std::istreambuf_iterator<char>());
}

HostProfileState fixture() {
    HostProfileState state;
    state.profile_id = "profile.alpha";
    state.autosave_generation = 41;
    state.ghost_target = CompletedRunGhostTarget::Off;

    std::array<std::uint8_t, kStockSramBytes> sram{};
    sram[0] = 0x12;
    sram[1234] = 0x34;
    sram.back() = 0x56;
    state.stock_sram = sram;

    HostTourContinuation continuation;
    continuation.rider_index = 3;
    continuation.tour_row = 4;
    continuation.medal_value = 1;
    continuation.qualified = {1, 0, 1, 0, 0};
    state.tour_continuation = continuation;
    return state;
}

}  // namespace

int main(int argc, char** argv) {
    assert(argc == 2);
    const std::string path = argv[1];
    std::remove(path.c_str());

    HostProfileState state = fixture();
    const HostProfileState before = state;

    assert(update_host_profile_ghost_target(
               ExecutionMode::Authentic,
               path,
               true,
               state,
               CompletedRunGhostTarget::PersonalBest) ==
           HostProfileGhostTargetUpdateStatus::RejectedByPolicy);
    assert(state == before);
    assert(read_all(path).empty());

    assert(update_host_profile_ghost_target(
               ExecutionMode::Modern,
               path,
               false,
               state,
               CompletedRunGhostTarget::PersonalBest) ==
           HostProfileGhostTargetUpdateStatus::ReadOnly);
    assert(state == before);
    assert(read_all(path).empty());

    assert(update_host_profile_ghost_target(
               ExecutionMode::Modern,
               path,
               true,
               state,
               CompletedRunGhostTarget::PersonalBest) ==
           HostProfileGhostTargetUpdateStatus::Saved);
    assert(state.ghost_target == CompletedRunGhostTarget::PersonalBest);
    assert(state.autosave_generation == before.autosave_generation);
    assert(state.stock_sram == before.stock_sram);
    assert(state.tour_continuation == before.tour_continuation);

    const auto loaded = load_host_profile_state_file(
        ExecutionMode::Modern, path, state.profile_id);
    assert(loaded.loaded());
    assert(loaded.state->ghost_target == CompletedRunGhostTarget::PersonalBest);
    assert(loaded.state->autosave_generation == before.autosave_generation);
    assert(loaded.state->stock_sram == before.stock_sram);
    assert(loaded.state->tour_continuation == before.tour_continuation);

    const std::string persisted = read_all(path);
    assert(update_host_profile_ghost_target(
               ExecutionMode::Modern,
               path,
               true,
               state,
               CompletedRunGhostTarget::PersonalBest) ==
           HostProfileGhostTargetUpdateStatus::Unchanged);
    assert(read_all(path) == persisted);

    const HostProfileState saved = state;
    assert(update_host_profile_ghost_target(
               ExecutionMode::Modern,
               path + "/missing/profile.txt",
               true,
               state,
               CompletedRunGhostTarget::Previous) ==
           HostProfileGhostTargetUpdateStatus::SaveFailed);
    assert(state == saved);

    return 0;
}

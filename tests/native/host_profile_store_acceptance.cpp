#include "host_profile_store.hpp"

#include <array>
#include <cassert>
#include <cstdio>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>

using namespace ur::product;

namespace {

std::array<std::uint8_t, kStockSramBytes> fixture() {
    std::array<std::uint8_t, kStockSramBytes> data{};
    for (std::size_t i = 0; i < data.size(); ++i) {
        data[i] = static_cast<std::uint8_t>((i * 29u + 7u) & 0xffu);
    }
    return data;
}

std::string read_all(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    return std::string(
        std::istreambuf_iterator<char>(in),
        std::istreambuf_iterator<char>());
}

void save_case(const std::string& path) {
    HostProfileState state;
    state.profile_id = "profile.alpha";
    const auto data = fixture();
    assert(capture_stock_sram_for_profile(
               ExecutionMode::Modern,
               state,
               data.data(),
               data.size()) == HostProfileTransferStatus::Applied);
    state.ghost_target = CompletedRunGhostTarget::PersonalBest;
    assert(save_host_profile_state_file(
               ExecutionMode::Modern,
               path,
               state) == HostProfileSaveStatus::Saved);
    std::cout << "PROFILE_ACCEPTANCE saved generation="
              << state.autosave_generation << "\n";
}

void load_case(const std::string& path) {
    const auto loaded = load_host_profile_state_file(
        ExecutionMode::Modern, path, "profile.alpha");
    assert(loaded.loaded());
    assert(host_profile_resolve_writable(HostProfileResolveStatus::Loaded));
    assert(loaded.state->autosave_generation == 1);
    assert(loaded.state->ghost_target == CompletedRunGhostTarget::PersonalBest);

    std::array<std::uint8_t, kStockSramBytes> restored{};
    assert(restore_stock_sram_from_profile(
               ExecutionMode::Modern,
               *loaded.state,
               restored.data(),
               restored.size()) == HostProfileTransferStatus::Applied);
    assert(restored == fixture());
    std::cout << "PROFILE_ACCEPTANCE fresh_process_load_ok ghost_target=personal-best\n";
}

void legacy_host_default_case(const std::string& path) {
    std::remove(path.c_str());
    const auto legacy_host = decode_host_product_state(
        "UR-HOST-STATE/1\n"
        "profile=profile.alpha\n"
        "pause_on_focus_loss=1\n"
        "vibration_enabled=1\n");
    assert(legacy_host);
    assert(legacy_host.state->active_profile_id);
    assert(*legacy_host.state->active_profile_id == "profile.alpha");

    const auto resolved = resolve_host_profile_state_file(
        ExecutionMode::Modern,
        path,
        *legacy_host.state->active_profile_id);
    assert(resolved);
    assert(resolved.status == HostProfileResolveStatus::DefaultedMissing);
    assert(!host_profile_resolve_writable(resolved.status));
    assert(resolved.state->profile_id == "profile.alpha");
    assert(resolved.state->autosave_generation == 0);
    assert(!resolved.state->stock_sram);
    assert(resolved.state->ghost_target == CompletedRunGhostTarget::Off);
    std::cout << "PROFILE_ACCEPTANCE legacy_host_defaulted ghost_target=off\n";
}

void malformed_case(const std::string& path) {
    {
        std::ofstream out(path, std::ios::binary | std::ios::trunc);
        out << "UR-HOST-PROFILE/1\n"
               "profile=profile.alpha\n"
               "generation=nope\n"
               "stock_sram=1234\n";
    }
    const std::string before = read_all(path);
    const auto resolved = resolve_host_profile_state_file(
        ExecutionMode::Modern, path, "profile.alpha");
    assert(resolved);
    assert(resolved.status == HostProfileResolveStatus::DefaultedMalformed);
    assert(!host_profile_resolve_writable(resolved.status));
    assert(resolved.state->profile_id == "profile.alpha");
    assert(resolved.state->autosave_generation == 0);
    assert(!resolved.state->stock_sram);
    assert(!resolved.error.empty());
    assert(read_all(path) == before);
    std::cout << "PROFILE_ACCEPTANCE malformed_defaulted_preserved\n";
}

void authentic_case(const std::string& path) {
    const std::string before = read_all(path);
    const auto resolved = resolve_host_profile_state_file(
        ExecutionMode::Authentic, path, "profile.alpha");
    assert(!resolved);
    assert(resolved.status == HostProfileResolveStatus::RejectedByPolicy);
    assert(!host_profile_resolve_writable(resolved.status));
    assert(!host_profile_resolve_writable(HostProfileResolveStatus::IoError));

    HostProfileState state;
    state.profile_id = "profile.alpha";
    const auto data = fixture();
    assert(capture_stock_sram_for_profile(
               ExecutionMode::Authentic,
               state,
               data.data(),
               data.size()) == HostProfileTransferStatus::RejectedByPolicy);
    assert(save_host_profile_state_file(
               ExecutionMode::Authentic,
               path,
               state) == HostProfileSaveStatus::Rejected);
    assert(read_all(path) == before);
    std::cout << "PROFILE_ACCEPTANCE authentic_inert\n";
}

}  // namespace

int main(int argc, char** argv) {
    assert(argc == 3);
    const std::string mode = argv[1];
    const std::string path = argv[2];

    if (mode == "save") {
        save_case(path);
    } else if (mode == "load") {
        load_case(path);
    } else if (mode == "legacy-host-default") {
        legacy_host_default_case(path);
    } else if (mode == "malformed") {
        malformed_case(path);
    } else if (mode == "authentic") {
        authentic_case(path);
    } else {
        return 2;
    }
    return 0;
}

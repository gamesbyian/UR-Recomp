#include "host_profile_store.hpp"

#include <array>
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iostream>
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

void save_case(const std::string& path) {
    HostProfileState state;
    state.profile_id = "profile.alpha";
    const auto data = fixture();
    assert(capture_stock_sram_for_profile(
               ExecutionMode::Modern,
               state,
               data.data(),
               data.size()) == HostProfileTransferStatus::Applied);
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
    assert(!loaded.migrated);
    assert(loaded.state->autosave_generation == 1);

    std::array<std::uint8_t, kStockSramBytes> restored{};
    assert(restore_stock_sram_from_profile(
               ExecutionMode::Modern,
               *loaded.state,
               restored.data(),
               restored.size()) == HostProfileTransferStatus::Applied);
    assert(restored == fixture());
    std::cout << "PROFILE_ACCEPTANCE fresh_process_load_ok\n";
}

void old_case(const std::string& path) {
    HostProfileState legacy;
    legacy.profile_id = "profile.alpha";
    legacy.stock_sram = fixture();
    std::string encoded = encode_host_profile_state(legacy);
    const auto header_end = encoded.find('\n');
    const auto generation = encoded.find("generation=");
    const auto generation_end = encoded.find('\n', generation);
    encoded.replace(0, header_end, "UR-HOST-PROFILE/0");
    encoded.erase(generation, generation_end - generation + 1);

    {
        std::ofstream out(path, std::ios::binary | std::ios::trunc);
        out << encoded;
    }

    const auto loaded = load_host_profile_state_file(
        ExecutionMode::Modern, path, "profile.alpha");
    assert(loaded.loaded());
    assert(loaded.migrated);
    assert(loaded.state->autosave_generation == 0);
    assert(loaded.state->stock_sram == legacy.stock_sram);
    std::cout << "PROFILE_ACCEPTANCE old_state_migrated\n";
}

void malformed_case(const std::string& path) {
    {
        std::ofstream out(path, std::ios::binary | std::ios::trunc);
        out << "UR-HOST-PROFILE/1\n"
               "profile=profile.alpha\n"
               "generation=nope\n"
               "stock_sram=1234\n";
    }
    const auto loaded = load_host_profile_state_file(
        ExecutionMode::Modern, path, "profile.alpha");
    assert(loaded.status == HostProfileLoadStatus::Rejected);
    assert(!loaded.state);
    std::cout << "PROFILE_ACCEPTANCE malformed_rejected\n";
}

void authentic_case(const std::string& path) {
    const auto loaded = load_host_profile_state_file(
        ExecutionMode::Authentic, path, "profile.alpha");
    assert(loaded.status == HostProfileLoadStatus::Rejected);
    assert(!loaded.state);

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
    } else if (mode == "old") {
        old_case(path);
    } else if (mode == "malformed") {
        malformed_case(path);
    } else if (mode == "authentic") {
        authentic_case(path);
    } else {
        return 2;
    }
    return 0;
}

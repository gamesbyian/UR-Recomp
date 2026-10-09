// QA-02: real production host-store writer/reader exercised by separate processes.
// The Python driver owns process concurrency and fresh-process recovery.
#include "host_product_store.hpp"
#include "host_profile_store.hpp"
#include "host_profile_catalog.hpp"
#include "local_tournament_atomic_replace.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <thread>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

using namespace ur::product;

namespace {
HostProfileState profile(unsigned value) {
    HostProfileState state;
    state.profile_id = "qa-profile";
    state.autosave_generation = 100u + value;
    std::array<std::uint8_t, kStockSramBytes> sram{};
    sram.fill(static_cast<std::uint8_t>(value));
    state.stock_sram = sram;
    return state;
}

void terminate_before_publish() { std::_Exit(77); }
bool fail_before_durable_stage(std::FILE*) { return false; }

int write_one(const std::string& family, const std::string& path,
              unsigned value) {
    if (family == "profile") {
        return save_host_profile_state_file(
            ExecutionMode::Modern, path, profile(value)) ==
            HostProfileSaveStatus::Saved ? 0 : 3;
    }
    if (family == "host") {
        HostProductState state;
        state.active_profile_id = "racer-" + std::to_string(value);
        return save_host_product_state_file(path, state) ==
            HostProductSaveStatus::Saved ? 0 : 3;
    }
    if (family == "catalog") {
        const std::vector<HostProfileCatalogEntry> entries{
            {"racer", {"RACER", static_cast<std::uint8_t>(value)}}};
        return save_host_profile_catalog_file(path, entries) ? 0 : 3;
    }
    return 2;
}

int read_one(const std::string& family, const std::string& path) {
    if (family == "profile") {
        const auto loaded = load_host_profile_state_file(
            ExecutionMode::Modern, path, "qa-profile");
        if (!loaded.loaded() || !loaded.state->stock_sram) return 4;
        const unsigned value = loaded.state->stock_sram->at(0);
        if (!std::all_of(loaded.state->stock_sram->begin(),
                         loaded.state->stock_sram->end(),
                         [value](auto n) { return n == value; }) ||
            loaded.state->autosave_generation != 100u + value) return 5;
        std::cout << value << "\n";
        return 0;
    }
    if (family == "host") {
        const auto loaded = load_host_product_state_file(path);
        if (!loaded.loaded() || !loaded.state->active_profile_id) return 4;
        const auto& id = *loaded.state->active_profile_id;
        if (id.rfind("racer-", 0) != 0) return 5;
        std::cout << id.substr(6) << "\n";
        return 0;
    }
    if (family == "catalog") {
        const auto loaded = load_host_profile_catalog_file(path);
        if (!loaded || loaded->size() != 1 ||
            (*loaded)[0].profile_id != "racer" ||
            (*loaded)[0].identity.name != "RACER") return 4;
        std::cout << static_cast<unsigned>((*loaded)[0].identity.rider_index)
                  << "\n";
        return 0;
    }
    return 2;
}
} // namespace

int main(int argc, char** argv) {
    if (argc != 5 && argc != 6) return 2;
    const std::string family(argv[1]), action(argv[2]), path(argv[3]);
    const unsigned value = static_cast<unsigned>(std::strtoul(argv[4], nullptr, 10));
    if (value > 15) return 2;
    if (family == "profile" && action == "cas-create") {
        const auto status = save_host_profile_state_file_if_current(
            ExecutionMode::Modern, path, std::nullopt, profile(value));
        return status == HostProfileSaveStatus::Saved ? 0 :
               status == HostProfileSaveStatus::Conflict ? 6 : 7;
    }
    if (family == "profile" && action == "cas-rollback") {
        const auto loaded = load_host_profile_state_file(
            ExecutionMode::Modern, path, "qa-profile");
        if (!loaded.loaded()) return 4;
        const auto intermediate = profile(value);
        if (save_host_profile_state_file_if_current(
                ExecutionMode::Modern, path, *loaded.state, intermediate) !=
            HostProfileSaveStatus::Saved) return 7;
        if (argc == 6 && std::string(argv[5]) == "interleave") {
            const auto winner = profile(value + 1u);
            if (save_host_profile_state_file_if_current(
                    ExecutionMode::Modern, path, intermediate, winner) !=
                HostProfileSaveStatus::Saved) return 8;
            return save_host_profile_state_file_if_current(
                ExecutionMode::Modern, path, intermediate, *loaded.state) ==
                HostProfileSaveStatus::Conflict ? 0 : 9;
        }
        return save_host_profile_state_file_if_current(
            ExecutionMode::Modern, path, intermediate, *loaded.state) ==
            HostProfileSaveStatus::Saved ? 0 : 9;
    }
    if (family == "profile" && action == "cas-contend" && argc == 6) {
        const auto loaded = load_host_profile_state_file(
            ExecutionMode::Modern, path, "qa-profile");
        if (!loaded.loaded()) return 4;
        const std::filesystem::path synchronization(argv[5]);
        const auto ready = synchronization /
            ("ready-" + std::to_string(value));
        {
            std::ofstream marker(ready);
            if (!marker) return 7;
        }
        bool released = false;
        for (unsigned n = 0; n < 10000; ++n) {
            if (std::filesystem::exists(synchronization / "go")) {
                released = true;
                break;
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
        if (!released) return 8;
        const auto status = save_host_profile_state_file_if_current(
            ExecutionMode::Modern, path, *loaded.state, profile(value));
        return status == HostProfileSaveStatus::Saved ? 0 :
               status == HostProfileSaveStatus::Conflict ? 6 : 9;
    }
    if (action == "write") return write_one(family, path, value);
    if (action == "read") return read_one(family, path);
    if (action == "syncfail" && family == "profile") {
        const auto result = write_host_replace_staged(
            path, encode_host_profile_state(profile(value)), "urprofile",
            nullptr, &fail_before_durable_stage);
        return result ? 8 : 0;
    }
    if (action == "crash" && family == "profile") {
        (void)write_host_replace_staged(
            path, encode_host_profile_state(profile(value)), "urprofile",
            &terminate_before_publish);
        return 8; // callback must terminate the process
    }
    return 2;
}

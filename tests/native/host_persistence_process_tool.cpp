// QA-02: real production host-store writer/reader exercised by separate processes.
// The Python driver owns process concurrency and fresh-process recovery.
#include "host_product_store.hpp"
#include "host_profile_store.hpp"
#include "host_profile_catalog.hpp"
#include "local_tournament_atomic_replace.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
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
    if (argc != 5) return 2;
    const std::string family(argv[1]), action(argv[2]), path(argv[3]);
    const unsigned value = static_cast<unsigned>(std::strtoul(argv[4], nullptr, 10));
    if (value > 15) return 2;
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

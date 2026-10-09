// QA-02: real production host-store writer/reader exercised by separate processes.
// The Python driver owns process concurrency and fresh-process recovery.
#include "host_product_store.hpp"
#include "host_profile_store.hpp"
#include "host_profile_catalog.hpp"
#include "local_tournament_atomic_replace.hpp"
#include "local_tournament_launch_path_lock.hpp"

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

HostProfileState initial_unregistered_profile(unsigned value) {
    auto state = profile(value);
    state.racer_identity = HostRacerIdentity{"QA Racer", 2u};
    return state;
}

void terminate_before_publish() { std::_Exit(77); }
void terminate_after_publish() { std::_Exit(79); }
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

    // C04: exact selector-versus-framework-SRAM authority cut. Existing
    // production typed host/profile stores and staged-file primitive perform
    // real filesystem writes; separate executable invocations simulate the
    // framework save as the distinct second artifact. No new data schema.
    if (family == "host" && action.rfind("c04-", 0) == 0) {
        namespace fs = std::filesystem;
        const fs::path root(path);
        const auto host_path = (root / "host-state.txt").string();
        const auto racer_a = root / "racer-1";
        const auto racer_b = root / "racer-2";
        const auto a_sram = racer_a / "save.srm";
        const auto b_sram = racer_b / "save.srm";
        const auto b_profile_path = (racer_b / "host-profile.txt").string();
        auto saved_sram = [](const fs::path& p, unsigned expected) {
            std::ifstream input(p, std::ios::binary);
            std::string bytes(
                static_cast<std::size_t>(kStockSramBytes), '\0');
            input.read(bytes.data(), static_cast<std::streamsize>(bytes.size()));
            return input.gcount() == static_cast<std::streamsize>(bytes.size()) &&
                input.peek() == std::char_traits<char>::eof() &&
                std::all_of(bytes.begin(), bytes.end(), [&](char c) {
                    return static_cast<unsigned char>(c) == expected;
                });
        };
        if (action == "c04-seed") {
            std::error_code ec;
            fs::create_directories(racer_a, ec);
            if (ec) return 9;
            fs::create_directories(racer_b, ec);
            if (ec) return 9;
            HostProductState initial;
            initial.active_profile_id = "racer-1";
            auto prior_profile = profile(2);
            prior_profile.profile_id = "racer-1";
            auto target_profile = profile(9);
            target_profile.profile_id = "racer-2";
            if (save_host_product_state_file(host_path, initial) !=
                    HostProductSaveStatus::Saved ||
                save_host_profile_state_file(
                    ExecutionMode::Modern,
                    (racer_a / "host-profile.txt").string(),
                    prior_profile) != HostProfileSaveStatus::Saved ||
                save_host_profile_state_file(
                    ExecutionMode::Modern, b_profile_path, target_profile) !=
                    HostProfileSaveStatus::Saved ||
                !write_host_replace_staged(
                    a_sram.string(), std::string(kStockSramBytes, '\x02'),
                    "ursram") ||
                !write_host_replace_staged(
                    b_sram.string(), std::string(kStockSramBytes, '\x03'),
                    "ursram")) return 9;
            return 0;
        }
        const auto old = load_host_product_state_file(host_path);
        const auto b_profile = load_host_profile_state_file(
            ExecutionMode::Modern, b_profile_path, "racer-2");
        if (!old.loaded() || !old.state->active_profile_id ||
            !b_profile.loaded() || !b_profile.state->stock_sram ||
            !saved_sram(a_sram, 2)) return 7;
        const auto target_bytes = std::string(
            b_profile.state->stock_sram->begin(),
            b_profile.state->stock_sram->end());
        if (action == "c04-stage-fail") {
            const auto staged = write_host_replace_staged(
                b_sram.string(), target_bytes, "ursram",
                nullptr, &fail_before_durable_stage);
            return !staged && *old.state->active_profile_id == "racer-1" &&
                saved_sram(b_sram, 3) ? 0 : 9;
        }
        if (action == "c04-kill-before-target-publication") {
            auto exit_before = []() { std::_Exit(84); };
            (void)write_host_replace_staged(
                b_sram.string(), target_bytes, "ursram",
                exit_before);
            return 9;
        }
        if (action == "c04-kill-after-target-publication") {
            auto exit_after = []() { std::_Exit(82); };
            (void)write_host_replace_staged(
                b_sram.string(), target_bytes, "ursram",
                nullptr, nullptr, exit_after);
            return 9;
        }
        if (action == "c04-verify-uncommitted") {
            return *old.state->active_profile_id == "racer-1" &&
                saved_sram(b_sram, 3) ? 0 : 9;
        }
        if (action == "c04-verify-precommit") {
            return *old.state->active_profile_id == "racer-1" &&
                saved_sram(b_sram, 9) ? 0 : 9;
        }
        if (action == "c04-commit-selector") {
            if (!saved_sram(b_sram, 9) ||
                *old.state->active_profile_id != "racer-1") return 9;
            auto selected = *old.state;
            selected.active_profile_id = "racer-2";
            if (save_host_product_state_file_if_current(
                    host_path, *old.state, selected) !=
                HostProductSaveStatus::Saved) return 9;
            std::_Exit(83); // power-off boundary: global pointer committed
        }
        if (action == "c04-verify-postcommit") {
            return *old.state->active_profile_id == "racer-2" &&
                saved_sram(b_sram, 9) ? 0 : 9;
        }
        return 2;
    }
    if (family == "host" && action == "cas-create") {
        HostProductState next;
        next.active_profile_id = "racer-" + std::to_string(value);
        const auto status =
            save_host_product_state_file_if_current(path, std::nullopt, next);
        return status == HostProductSaveStatus::Saved ? 0 :
               status == HostProductSaveStatus::Conflict ? 6 : 9;
    }
    if (family == "host" && action == "cas-rollback") {
        const auto loaded = load_host_product_state_file(path);
        if (!loaded.loaded()) return 4;
        auto intermediate = *loaded.state;
        intermediate.active_profile_id = "racer-" + std::to_string(value);
        if (save_host_product_state_file_if_current(
                path, *loaded.state, intermediate) !=
            HostProductSaveStatus::Saved) return 7;
        if (argc == 6 && std::string(argv[5]) == "interleave") {
            auto winner = intermediate;
            winner.active_profile_id = "racer-" +
                std::to_string(value + 1u);
            if (save_host_product_state_file_if_current(
                    path, intermediate, winner) !=
                HostProductSaveStatus::Saved) return 8;
            return save_host_product_state_file_if_current(
                path, intermediate, *loaded.state) ==
                HostProductSaveStatus::Conflict ? 0 : 9;
        }
        return save_host_product_state_file_if_current(
            path, intermediate, *loaded.state) ==
            HostProductSaveStatus::Saved ? 0 : 9;
    }
    if (family == "host" && action == "cas-contend" && argc == 6) {
        const auto loaded = load_host_product_state_file(path);
        if (!loaded.loaded()) return 4;
        auto next = *loaded.state;
        next.active_profile_id = "racer-" + std::to_string(value);
        const std::filesystem::path synchronization(argv[5]);
        {
            std::ofstream marker(
                synchronization / ("ready-" + std::to_string(value)));
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
        const auto status = save_host_product_state_file_if_current(
            path, *loaded.state, next);
        return status == HostProductSaveStatus::Saved ? 0 :
               status == HostProductSaveStatus::Conflict ? 6 : 9;
    }
    if (family == "profile" && action == "orphan-crash-after-publish") {
        const std::filesystem::path root(path);
        std::error_code ec;
        std::filesystem::create_directories(root, ec);
        if (ec) return 9;
        const auto profile_path = (root / "host-profile.txt").string();
        TournamentLaunchPathLock lock(profile_path);
        if (!lock.acquired() ||
            load_host_profile_state_file(
                ExecutionMode::Modern, profile_path, "qa-profile").status !=
                HostProfileLoadStatus::Missing) return 9;
        (void)write_host_replace_staged(
            profile_path,
            encode_host_profile_state(initial_unregistered_profile(value)),
            "urprofile", nullptr, nullptr, &terminate_after_publish);
        return 8; // the injection callback must kill this process
    }
    if (family == "profile" && action == "orphan-crash") {
        const std::filesystem::path root(path);
        std::error_code ec;
        std::filesystem::create_directories(root, ec);
        if (ec) return 9;
        const auto profile_path = (root / "host-profile.txt").string();
        const auto status = save_host_profile_state_file_if_current(
            ExecutionMode::Modern, profile_path, std::nullopt,
            initial_unregistered_profile(value));
        if (status != HostProfileSaveStatus::Saved) return 9;
        // Same first-phase production CAS, no catalog row: sudden death at
        // the boundary after a completed profile publication.
        std::_Exit(78);
    }
    if (family == "profile" && action == "orphan-claim" && argc == 6) {
        const std::string profile_path =
            (std::filesystem::path(path) / "host-profile.txt").string();
        TournamentLaunchPathLock lock(profile_path);
        if (!lock.acquired()) return 9;
        if (!pristine_unregistered_profile_creation_root(path)) return 6;
        const auto loaded = load_host_profile_state_file(
            ExecutionMode::Modern, profile_path, "qa-profile");
        if (!loaded.loaded() || !(*loaded.state == initial_unregistered_profile(value))) return 6;

        const std::string catalog_path(argv[5]);
        const auto current = load_host_profile_catalog_file(catalog_path);
        if (!current) return 9;
        for (const auto& entry : *current) {
            if (entry.profile_id == "qa-profile") return 6;
        }
        auto next = *current;
        next.push_back({"qa-profile", {"QA Racer", 2u}});
        const auto published = save_host_profile_catalog_file_if_current(
            catalog_path, *current, next);
        return published == HostProfileCatalogSaveStatus::Saved ? 0 :
               published == HostProfileCatalogSaveStatus::Conflict ? 6 : 9;
    }
    if (family == "profile" && action == "root-pristine") {
        if (!pristine_unregistered_profile_creation_root(path)) return 6;
        const auto loaded = load_host_profile_state_file(
            ExecutionMode::Modern,
            (std::filesystem::path(path) / "host-profile.txt").string(),
            "qa-profile");
        return loaded.loaded() && *loaded.state == initial_unregistered_profile(value) ? 0 : 6;
    }
    if (family == "profile" && action == "root-reusable") {
        return reusable_aborted_profile_creation_root(path) ? 0 : 6;
    }
    if (family == "catalog" && action == "cas-roster-read") {
        const auto catalog = load_host_profile_catalog_file(path);
        if (!catalog || catalog->empty()) return 4;
        std::cout << catalog->size();
        for (const auto& entry : *catalog) {
            std::cout << " " << entry.profile_id;
        }
        std::cout << "\n";
        return 0;
    }
    if (family == "catalog" && action == "cas-roster-contend" &&
        argc == 6) {
        const auto current = load_host_profile_catalog_file(path);
        if (!current) return 4;
        auto next = *current;
        next.push_back({
            "racer-" + std::to_string(value),
            {"RACER", static_cast<std::uint8_t>(value)}
        });
        const std::filesystem::path synchronization(argv[5]);
        {
            std::ofstream marker(
                synchronization / ("ready-" + std::to_string(value)));
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
        const auto result = save_host_profile_catalog_file_if_current(
            path, *current, next);
        return result == HostProfileCatalogSaveStatus::Saved ? 0 :
               result == HostProfileCatalogSaveStatus::Conflict ? 6 : 9;
    }
    if (family == "profile" && action == "cas-delete") {
        const auto prior = load_host_profile_state_file(
            ExecutionMode::Modern, path, "qa-profile");
        if (!prior.loaded()) return 4;
        return remove_host_profile_state_file_if_current(
            ExecutionMode::Modern, path, *prior.state) ==
            HostProfileSaveStatus::Saved ? 0 : 9;
    }
    if (family == "profile" && action == "cas-delete-stale") {
        const auto prior = load_host_profile_state_file(
            ExecutionMode::Modern, path, "qa-profile");
        if (!prior.loaded()) return 4;
        // Another owner saves newer valid bytes between this process's
        // catalog-registration attempt and its stale cleanup decision.
        if (save_host_profile_state_file_if_current(
                ExecutionMode::Modern, path, *prior.state,
                profile(value)) != HostProfileSaveStatus::Saved) return 8;
        return remove_host_profile_state_file_if_current(
            ExecutionMode::Modern, path, *prior.state) ==
            HostProfileSaveStatus::Conflict ? 0 : 9;
    }
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

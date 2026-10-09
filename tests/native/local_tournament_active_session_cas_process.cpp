#include "local_tournament_session_store.hpp"

#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <thread>
#include <vector>

using namespace ur::product;
namespace fs = std::filesystem;

namespace {
std::optional<LocalTournamentSessionDefinition> build(const std::string& instance) {
    const std::vector<HostProfileCatalogEntry> catalog{
        {"alpha", {"MIKE", 0}}, {"beta", {"ANDREW", 1}}};
    return make_local_tournament_session_definition(
        instance, {"alpha", "beta"}, catalog, {"course:01"}, 1);
}
}

int main(int argc, char** argv) {
    if (argc != 5) return 2;
    const std::string mode(argv[1]), file(argv[2]), instance(argv[3]);
    const fs::path barrier(argv[4]);
    const auto next = build(instance);
    if (!next) return 3;
    if (mode == "seed") {
        return save_local_tournament_session_definition_if_current(
            file, std::nullopt, *next) ==
            LocalTournamentSessionFileStatus::Saved ? 0 : 4;
    }
    if (mode == "verify") {
        const auto loaded = load_historical_local_tournament_session_definition(file);
        if (!loaded.loaded()) return 5;
        const auto& saved = loaded.session->instance_id;
        if (saved != std::string(32, 'b') &&
            saved != std::string(32, 'c')) return 6;
        std::cout << saved << "\n";
        return 0;
    }
    if (mode != "contend") return 2;
    const auto previous = load_historical_local_tournament_session_definition(file);
    if (!previous.loaded()) return 5;
    {
        std::ofstream ready(barrier /
            ("ready-" + instance.substr(0, 1)));
        if (!ready) return 8;
    }
    bool started = false;
    for (unsigned i = 0; i < 10000; ++i) {
        if (fs::exists(barrier / "go")) {
            started = true;
            break;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    if (!started) return 9;
    const auto result = save_local_tournament_session_definition_if_current(
        file, *previous.session, *next);
    if (result == LocalTournamentSessionFileStatus::Saved) return 0;
    if (result == LocalTournamentSessionFileStatus::Conflict) return 6;
    return 7;
}

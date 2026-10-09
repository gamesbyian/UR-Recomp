// QA-02 C12: real coordinator creation contended by separate OS processes.
// No arbitrary staging clone or store-only simulation: each process calls
// the exact production event-archive and active-pointer creation workflow.
#include "local_tournament_session_coordinator.hpp"

#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <string>
#include <thread>
#include <vector>

using namespace ur::product;
namespace fs = std::filesystem;

namespace {
void require(bool ok, const char* detail) {
    if (!ok) {
        std::fprintf(stderr, "QA02_C12_FAIL %s\n", detail);
        std::exit(13);
    }
}
std::vector<HostProfileCatalogEntry> catalog() {
    return {{"alpha", {"MIKE", 0}},
            {"beta", {"ANDREW", 1}},
            {"gamma", {"ANNA", 2}}};
}
LocalTournamentCoordinatorPaths paths(const fs::path& root) {
    return {(root / "local-tournaments").string(),
            (root / "multiplayer-runs").string()};
}
}

int main(int argc, char** argv) {
    if (argc != 4) return 2;
    const std::string action(argv[1]);
    const fs::path root(argv[2]);
    const std::string id(argv[3]);
    const auto layout = paths(root);
    if (action == "contend") {
        require(local_tournament_valid_instance_token(id),
                "valid independent instance identity");
        const fs::path barrier = root / "barrier";
        const fs::path marker = barrier / ("ready-" + id);
        {
            std::ofstream ready(marker, std::ios::binary);
            require(bool(ready), "write synchronization marker");
        }
        bool started = false;
        for (unsigned i = 0; i < 10000; ++i) {
            if (fs::exists(barrier / "go")) {
                started = true;
                break;
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
        require(started, "barrier was not released");
        const bool full_roster = id.front() == 'c';
        const auto created = create_local_tournament_coordinator(
            layout, id,
            full_roster ? std::vector<std::string>{"alpha", "beta", "gamma"}
                        : std::vector<std::string>{"alpha", "beta"},
            catalog(),
            full_roster ? std::vector<std::string>{"course:01", "course:04"}
                        : std::vector<std::string>{"course:01"});
        if (created.usable() &&
            created.status == LocalTournamentCoordinatorStatus::Created) {
            std::puts("QA02_C12_CREATED");
            return 0;
        }
        if (created.status == LocalTournamentCoordinatorStatus::AlreadyExists) {
            std::puts("QA02_C12_CONFLICT");
            return 6;
        }
        std::fprintf(stderr, "QA02_C12_UNEXPECTED %s\n",
                     created.detail.c_str());
        return 14;
    }
    if (action == "verify") {
        const auto restored = restore_local_tournament_coordinator(
            layout, catalog());
        require(restored.usable(), "restore one canonical active winner");
        const auto& winner = restored.session->definition;
        require(winner.instance_id == std::string(32, 'b') ||
                winner.instance_id == std::string(32, 'c'),
                "only one of two explicitly competing event IDs can win");
        const auto active = load_historical_local_tournament_session_definition(
            (fs::path(layout.tournaments_root) / "active.urtournament").string());
        require(active.loaded(), "full active event file survives");
        require(encode_local_tournament_session_definition(*active.session) ==
                encode_local_tournament_session_definition(winner),
                "fresh restorer matches current active canonical bytes");
        require(!restored.session->launch.pending,
                "racing creators cannot invent guest launch");
        for (const auto& result : restored.session->results.results) {
            require(!result, "neither creator may award any fixture");
        }
        const auto history = load_completed_local_tournament_history(layout);
        require(history.scanned && !history.truncated &&
                history.completed.empty(),
                "inactive orphan plan never masquerades as completed event");
        std::size_t archives = 0;
        for (const auto& entry : fs::directory_iterator(layout.tournaments_root)) {
            if (!entry.is_directory()) continue;
            const auto dir_id = entry.path().filename().string();
            if (!local_tournament_valid_instance_token(dir_id)) continue;
            const auto file = load_historical_local_tournament_session_definition(
                (entry.path() / "session.urtournament").string());
            require(file.loaded() && file.session->instance_id == dir_id,
                    "every contended archive keeps its own identity");
            ++archives;
        }
        require(archives >= 1 && archives <= 2,
                "winner plus at most one abandoned archive");
        std::puts("QA02_C12_SINGLE_ACTIVE_NO_CREDIT");
        return 0;
    }
    return 2;
}

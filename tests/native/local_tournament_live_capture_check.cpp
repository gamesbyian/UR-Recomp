#include "local_tournament_session_coordinator.hpp"

#include <cstdio>
#include <filesystem>
#include <string>
#include <vector>

using namespace ur::product;
namespace fs = std::filesystem;

// Fresh process checker: this does NOT fabricate a result or infer tournament
// membership from all ordinary Records. The production host must already have
// persisted the exact fixture receipt during its genuine stock 2P capture.
int main(int argc, char** argv) {
    if (argc != 3) {
        std::fprintf(stderr,
            "usage: tournament-live-check <user-root> <multiplayer-run-dir>\n");
        return 2;
    }
    const fs::path tournament_root = fs::path(argv[1]) / "local-tournaments";
    const std::vector<HostProfileCatalogEntry> catalog{
        {"join.alpha", {"MIKE", 0}},
        {"join.bravo", {"ANDREW", 1}},
    };
    const LocalTournamentCoordinatorPaths paths{
        tournament_root.string(), argv[2],
    };
    const auto restored = restore_local_tournament_coordinator(paths, catalog);
    if (!restored.usable() ||
        restored.session->definition.instance_id !=
            "0123456789abcdef0123456789abcdef" ||
        restored.session->results.fixtures.size() != 1 ||
        !local_tournament_coordinator_complete(*restored.session) ||
        local_tournament_next_unplayed_fixture(*restored.session)) {
        std::fprintf(stderr,
            "UR_LOCAL_TOURNAMENT_NATIVE_CHECK FAILED: no complete verified fixture\n");
        return 1;
    }
    const auto& fixture = restored.session->results.fixtures[0];
    if (fixture.course_id != "course:01" ||
        !restored.session->results.results[0] ||
        restored.session->results.results[0]->run_artifact_checksum.empty()) {
        std::fprintf(stderr,
            "UR_LOCAL_TOURNAMENT_NATIVE_CHECK FAILED: unexpected saved fixture\n");
        return 1;
    }
    const auto standings = local_tournament_standings(restored.session->results);
    if (standings.size() != 2) return 1;
    const auto* first = standings[0].profile_id == "join.alpha"
        ? &standings[0] : &standings[1];
    const auto* second = standings[0].profile_id == "join.bravo"
        ? &standings[0] : &standings[1];
    if (first->profile_id != "join.alpha" ||
        second->profile_id != "join.bravo" ||
        first->played != 1 || first->wins != 1 ||
        first->points != 3 || first->rank != 1 ||
        second->played != 1 || second->losses != 1 ||
        second->points != 0 || second->rank != 2) {
        std::fprintf(stderr,
            "UR_LOCAL_TOURNAMENT_NATIVE_CHECK FAILED: result or standings mismatch\n");
        return 1;
    }
    std::printf(
        "UR_LOCAL_TOURNAMENT_NATIVE_CHECK PASS instance=%s fixture=0 course=%s alpha_points=%zu bravo_points=%zu\n",
        restored.session->definition.instance_id.c_str(),
        fixture.course_id.c_str(), first->points, second->points);
    return 0;
}

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
    if (argc != 3 && argc != 4) {
        std::fprintf(stderr,
            "usage: tournament-live-check <user-root> <multiplayer-run-dir> [minted]\n");
        return 2;
    }
    // "minted": the event was created from the player-facing panel, so its
    // identity must be an OS-minted 32-hex token, never the fixed ID the
    // env-armed acceptance route uses.
    const bool minted = argc == 4 && std::string(argv[3]) == "minted";
    if (argc == 4 && !minted) return 2;
    constexpr const char* kFixedAcceptanceId =
        "0123456789abcdef0123456789abcdef";
    const fs::path tournament_root = fs::path(argv[1]) / "local-tournaments";
    const std::vector<HostProfileCatalogEntry> catalog{
        {"join.alpha", {"MIKE", 0}},
        {"join.bravo", {"ANDREW", 1}},
    };
    const LocalTournamentCoordinatorPaths paths{
        tournament_root.string(), argv[2],
    };
    const auto restored = restore_local_tournament_coordinator(paths, catalog);
    const auto valid_minted_id = [](const std::string& id) {
        if (id.size() != 32) return false;
        for (const char ch : id) {
            if (!((ch >= '0' && ch <= '9') || (ch >= 'a' && ch <= 'f'))) {
                return false;
            }
        }
        return true;
    };
    if (!restored.usable() ||
        (minted
            ? (!valid_minted_id(restored.session->definition.instance_id) ||
               restored.session->definition.instance_id == kFixedAcceptanceId)
            : restored.session->definition.instance_id != kFixedAcceptanceId) ||
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

#include "local_tournament_session_store.hpp"

#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

using namespace ur::product;
namespace fs = std::filesystem;

void require(bool ok, const char* message) {
    if (!ok) {
        std::fprintf(stderr, "FAIL: %s\n", message);
        std::exit(1);
    }
}

std::string read_bytes(const fs::path& path) {
    std::ifstream in(path, std::ios::binary);
    return {std::istreambuf_iterator<char>(in),
            std::istreambuf_iterator<char>()};
}

void put_bytes(const fs::path& path, const std::string& content) {
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    out.write(content.data(), static_cast<std::streamsize>(content.size()));
    require(bool(out), "test fixture writes");
}

int main() {
    const std::vector<HostProfileCatalogEntry> catalog{
        {"alice", {}}, {"bob", {}}, {"carol", {}}, {"other", {}},
    };
    const std::string id = "0123456789abcdef0123456789abcdef";
    const auto session = make_local_tournament_session_definition(
        id, {"alice", "bob", "carol"}, catalog,
        {"course:01", "course:04"});
    require(bool(session), "explicit catalog-authorized session");
    require(session->empty_schedule.fixtures.size() == 3,
            "canonical odd-roster round robin");
    const std::string canonical =
        encode_local_tournament_session_definition(*session);
    require(canonical.rfind("UR-LOCAL-TOURNAMENT-SESSION/1\n", 0) == 0,
            "canonical session magic");
    const auto decoded = decode_local_tournament_session_definition(
        canonical, catalog);
    require(bool(decoded) && decoded->instance_id == id &&
            decoded->empty_schedule.fixtures.size() == 3 &&
            encode_local_tournament_session_definition(*decoded) == canonical,
            "session reload reconstitutes identical fixture schedule");
    require(!decoded->empty_schedule.results[0],
            "session never stores invented result cells");

    require(!make_local_tournament_session_definition(
        id, {"alice", "intruder"}, catalog, {"course:01"}),
        "selected entrant must appear in authoritative catalog");
    require(!make_local_tournament_session_definition(
        id, {"alice", "ALICE"}, catalog, {"course:01"}),
        "Windows-equivalent profile cannot occupy distinct entries");
    require(!make_local_tournament_session_definition(
        id, {"alice", "bob"}, catalog, {"course:02"}),
        "non-Race course cannot become tournament fixture");
    require(!make_local_tournament_session_definition(
        id, {"alice", "bob"}, catalog, {"course:01", "course:01"}),
        "duplicate course pool rejected");
    require(!make_local_tournament_session_definition(
        "not-an-instance", {"alice", "bob"}, catalog, {"course:01"}),
        "instance token cannot derive from arbitrary names");
    require(!decode_local_tournament_session_definition(
        canonical, {catalog[0], catalog[1]}),
        "deleted roster profile prevents session restore");
    std::string changed = canonical;
    changed[changed.find("course:04")] = 'x';
    require(!decode_local_tournament_session_definition(changed, catalog),
            "mutated course invalidates canonical payload");
    changed = canonical + "\n";
    require(!decode_local_tournament_session_definition(changed, catalog),
            "extra trailing bytes rejected");
    changed = canonical;
    changed.replace(0, 2, "xx");
    require(!decode_local_tournament_session_definition(changed, catalog),
            "unknown version rejected");

    auto finished = *session;
    finished.empty_schedule.results[0] = LocalTournamentRecordedResult{
        "1111111111111111", ur::title::OrdinaryTwoPlayerRaceOutcome::Draw, false};
    require(encode_local_tournament_session_definition(finished).empty(),
            "completed results cannot be smuggled into immutable session");
    auto drifted = *session;
    drifted.empty_schedule.fixtures[0].course_id = "course:39";
    require(encode_local_tournament_session_definition(drifted).empty(),
            "authored fixture drift rejected");

    const auto unique =
        std::chrono::steady_clock::now().time_since_epoch().count();
    const fs::path root = fs::temp_directory_path() /
        ("ur-local-tournament-session-" + std::to_string(unique));
    require(fs::create_directory(root), "test directory");
    const fs::path path = root / "active.urtournament";
    using S = LocalTournamentSessionFileStatus;
    require(load_local_tournament_session_definition(
        path.string(), catalog).status == S::Missing,
        "unstarted session remains absent, not implicit");
    require(save_local_tournament_session_definition(
        path.string(), *session) == S::Saved,
        "session published through same-directory replacement");
    require(read_bytes(path) == canonical && !fs::exists(path.string() + ".tmp"),
            "disk bytes exactly canonical and no temporary residue");
    const auto fresh = load_local_tournament_session_definition(
        path.string(), catalog);
    require(fresh.loaded() &&
            fresh.session->instance_id == id &&
            fresh.session->empty_schedule.fixtures.size() == 3,
            "fresh filesystem load reconstructs active fixture plan");
    require(load_local_tournament_session_definition(
        path.string(), {catalog[0],catalog[1]}).status == S::Rejected,
        "fresh load refuses missing roster member");
    require(save_local_tournament_session_definition(
        path.string(), finished) == S::Rejected &&
        read_bytes(path) == canonical,
        "invalid replacement leaves previous session intact");
    put_bytes(path, canonical.substr(0, canonical.size() - 1));
    require(load_local_tournament_session_definition(
        path.string(), catalog).status == S::Rejected,
        "truncation rejected");
    put_bytes(path, std::string(4097, 'x'));
    require(load_local_tournament_session_definition(
        path.string(), catalog).status == S::Rejected,
        "oversized disk input bounded before allocation");
    require(save_local_tournament_session_definition(
        path.string(), *session) == S::Saved,
        "canonical session can replace a damaged disk payload");
    require(read_bytes(path) == canonical, "repaired session byte exact");

    fs::remove_all(root);
    std::puts("local_tournament_session_store_test: ok");
    return 0;
}

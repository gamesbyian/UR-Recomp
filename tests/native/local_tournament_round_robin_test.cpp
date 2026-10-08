#include "local_tournament_round_robin.hpp"

#include <cstdio>
#include <cstdlib>
#include <set>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

using namespace ur::product;
using Outcome = ur::title::OrdinaryTwoPlayerRaceOutcome;

namespace {

void require(bool ok, const char* message) {
    if (!ok) {
        std::fprintf(stderr, "FAIL: %s\n", message);
        std::exit(1);
    }
}

StoredMultiplayerMatch admitted(
    const LocalTournamentState& state,
    std::size_t fixture_index,
    const std::string& checksum,
    Outcome outcome,
    bool reverse = false) {
    const auto& fixture = state.fixtures.at(fixture_index);
    StoredMultiplayerMatch stored;
    stored.run_path = checksum + ".urrun";
    stored.run.provenance.mode = "race-2p";
    stored.run.provenance.course_id = fixture.course_id;
    stored.match.schema_version = kMultiplayerMatchRecordSchemaVersion;
    stored.match.run_artifact_checksum = checksum;
    stored.match.context.course_id = fixture.course_id;
    const auto p1 = reverse ? fixture.player2 : fixture.player1;
    const auto p2 = reverse ? fixture.player1 : fixture.player2;
    stored.match.context.match.player1.profile_id = state.entrants.at(p1);
    stored.match.context.match.player2.profile_id = state.entrants.at(p2);
    stored.match.context.match.result.outcome = outcome;
    return stored;
}

std::size_t pair_fixture(
    const LocalTournamentState& t,
    std::size_t first,
    std::size_t second) {
    for (std::size_t i = 0; i < t.fixtures.size(); ++i) {
        const auto& f = t.fixtures[i];
        if ((f.player1 == first && f.player2 == second) ||
            (f.player1 == second && f.player2 == first)) {
            return i;
        }
    }
    require(false, "missing expected fixture");
    return 0;
}

const LocalTournamentStanding& find_row(
    const std::vector<LocalTournamentStanding>& rows,
    std::string_view id) {
    for (const auto& row : rows) {
        if (local_tournament_storage_key(row.profile_id) ==
            local_tournament_storage_key(id)) return row;
    }
    require(false, "missing standings entrant");
    return rows.front();
}

} // namespace

int main() {
    require(local_tournament_ordinary_race_course("course:01"),
            "first ordinary race");
    require(local_tournament_ordinary_race_course("course:04"),
            "second ordinary race");
    require(local_tournament_ordinary_race_course("course:39"),
            "last ordinary race in ordinary tours");
    for (const auto* bad : {"course:00", "course:02", "course:40",
                            "course:41", "course:45", "course:1",
                            "course:001", "track:01", "course:0a"}) {
        require(!local_tournament_ordinary_race_course(bad),
                "reject non-canonical/non-race/secret course");
    }
    require(!make_local_round_robin({}, {"course:01"}),
            "no entrants rejected");
    require(!make_local_round_robin({"alice"}, {"course:01"}),
            "single participant rejected");
    require(!make_local_round_robin({"alice", "ALICE"}, {"course:01"}),
            "case-insensitive duplicate profile rejected");
    require(!make_local_round_robin({"alice", ""}, {"course:01"}),
            "blank profile rejected");
    require(!make_local_round_robin({"alice", "bob"}, {}),
            "no courses rejected");
    require(!make_local_round_robin({"alice", "bob"}, {"course:01", "course:01"}),
            "duplicate course rejected");
    require(!make_local_round_robin({"alice", "bob"}, {"course:02"}),
            "non-Race course rejected");
    require(!make_local_round_robin(
        {"a","b","c","d","e","f","g","h","i"}, {"course:01"}),
        "oversized tournament rejected");

    // Even entrant count: each unordered pair once, every round contains
    // exactly one fixture for every entrant, one of two validated Race courses.
    auto even = make_local_round_robin(
        {"alice", "bob", "charlie", "dana"}, {"course:01", "course:04"});
    require(bool(even), "even schedule created");
    require(even->fixtures.size() == 6 && even->results.size() == 6,
            "four entrants form six fixtures");
    std::set<std::pair<std::size_t, std::size_t>> pairs;
    for (std::size_t round = 1; round <= 3; ++round) {
        std::set<std::size_t> seen;
        for (const auto& fixture : even->fixtures) {
            if (fixture.round != round) continue;
            require(seen.insert(fixture.player1).second &&
                    seen.insert(fixture.player2).second,
                    "no participant plays twice in same round");
            const auto key = std::minmax(fixture.player1, fixture.player2);
            require(pairs.insert(key).second, "pair appears only once");
            require(fixture.course_id == "course:01" ||
                    fixture.course_id == "course:04",
                    "round fixture from validated pool");
        }
        require(seen.size() == 4, "all even entrants play each round");
    }
    require(pairs.size() == 6, "every pair appears exactly once");
    require(local_tournament_standings(*even).size() == 4,
            "empty tournament still displays four entrants");
    require(local_tournament_standings(*even)[0].rank == 1 &&
            local_tournament_standings(*even)[3].rank == 1,
            "equal unplayed points share rank");

    // Odd entrants: exactly one bye per round, all unordered pairs scheduled.
    auto odd = make_local_round_robin(
        {"ALICE", "bob", "cAROL"}, {"course:01"});
    require(bool(odd), "odd schedule created");
    require(odd->fixtures.size() == 3, "three entrant single round robin");
    for (std::size_t round = 1; round <= 3; ++round) {
        std::size_t in_round = 0;
        for (const auto& fixture : odd->fixtures) {
            if (fixture.round == round) ++in_round;
        }
        require(in_round == 1, "exactly one fixture and one bye each round");
    }

    const auto ab = pair_fixture(*odd, 0, 1);
    const auto ac = pair_fixture(*odd, 0, 2);
    const auto bc = pair_fixture(*odd, 1, 2);

    // ALICE beats bob with reversed source seats to verify that the
    // standings normalize the authoritative P1/P2 winner to fixture seats.
    auto game_ab = admitted(*odd, ab, "checksum-ab", Outcome::Player1Win, true);
    // In reversed seats, P1 is bob, so Player2Win means ALICE wins.
    game_ab.match.context.match.result.outcome = Outcome::Player2Win;
    require(record_local_tournament_result(*odd, ab, game_ab) ==
                LocalTournamentRecordStatus::Applied,
            "reversed-seat admitted pair recorded");
    require(record_local_tournament_result(*odd, ab, game_ab) ==
                LocalTournamentRecordStatus::AlreadyRecorded,
            "same fixture cannot be overwritten");

    // The same completed run must never be counted for two fixtures.
    auto dup = admitted(*odd, ac, "checksum-ab", Outcome::Player1Win);
    require(record_local_tournament_result(*odd, ac, dup) ==
                LocalTournamentRecordStatus::DuplicateArtifact,
            "duplicate run checksum cannot count twice");
    require(!odd->results[ac], "rejected result leaves state unchanged");

    auto wrong_mode = admitted(*odd, ac, "checksum-ac", Outcome::Draw);
    wrong_mode.run.provenance.mode = "race-1p";
    require(record_local_tournament_result(*odd, ac, wrong_mode) ==
                LocalTournamentRecordStatus::EvidenceNotAdmitted,
            "one player run has no tournament authority");
    auto wrong_course = admitted(*odd, ac, "checksum-ac", Outcome::Draw);
    wrong_course.match.context.course_id = "course:04";
    require(record_local_tournament_result(*odd, ac, wrong_course) ==
                LocalTournamentRecordStatus::CourseMismatch,
            "wrong course not silently projected into fixture");
    auto wrong_profile = admitted(*odd, ac, "checksum-ac", Outcome::Draw);
    wrong_profile.match.context.match.player2.profile_id = "outsider";
    require(record_local_tournament_result(*odd, ac, wrong_profile) ==
                LocalTournamentRecordStatus::ParticipantsMismatch,
            "unrelated participant rejected");
    auto missing_path = admitted(*odd, ac, "checksum-ac", Outcome::Draw);
    missing_path.run_path.clear();
    require(record_local_tournament_result(*odd, ac, missing_path) ==
                LocalTournamentRecordStatus::EvidenceNotAdmitted,
            "unidentified run not admitted");
    auto invalid_outcome = admitted(*odd, ac, "checksum-ac",
                                   static_cast<Outcome>(255));
    require(record_local_tournament_result(*odd, ac, invalid_outcome) ==
                LocalTournamentRecordStatus::EvidenceNotAdmitted,
            "unsupported outcome rejected");
    require(!odd->results[ac], "all rejected attempts preserve empty slot");

    // CAROL beats ALICE, and bob draws with CAROL.
    auto game_ac = admitted(*odd, ac, "checksum-ac", Outcome::Draw);
    const bool carol_is_p1 = odd->fixtures[ac].player1 == 2;
    game_ac.match.context.match.result.outcome =
        carol_is_p1 ? Outcome::Player1Win : Outcome::Player2Win;
    require(record_local_tournament_result(*odd, ac, game_ac) ==
                LocalTournamentRecordStatus::Applied,
            "CAROL beats ALICE from authoritative result");
    auto game_bc = admitted(*odd, bc, "checksum-bc", Outcome::Draw);
    require(record_local_tournament_result(*odd, bc, game_bc) ==
                LocalTournamentRecordStatus::Applied,
            "draw recorded");
    const auto standings = local_tournament_standings(*odd);
    require(standings.size() == 3, "three standings rows");
    const auto& alice = find_row(standings, "alice");
    const auto& bob = find_row(standings, "BOB");
    const auto& carol = find_row(standings, "carol");
    require(alice.played == 2 && alice.wins == 1 &&
            alice.losses == 1 && alice.points == 3,
            "ALICE one win and one loss, three points");
    require(bob.played == 2 && bob.draws == 1 &&
            bob.losses == 1 && bob.points == 1,
            "bob draw plus loss, one point");
    require(carol.played == 2 && carol.wins == 1 &&
            carol.draws == 1 && carol.points == 4,
            "CAROL win plus draw, four points");
    require(standings.front().profile_id == "cAROL" &&
            standings.front().rank == 1,
            "points rank winner");
    require(record_local_tournament_result(*odd, 999, game_ab) ==
                LocalTournamentRecordStatus::InvalidFixture,
            "out of range fixture rejected");
    std::puts("local_tournament_round_robin_test: ok");
    return 0;
}

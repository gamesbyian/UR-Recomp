#include "local_tournament_fixture_launch_codec.hpp"

#include <cstdlib>
#include <cstdio>
#include <string>
#include <vector>

using namespace ur::product;
using Outcome = ur::title::OrdinaryTwoPlayerRaceOutcome;
using Status = LocalTournamentLaunchStatus;

static void require(bool condition, const char* message) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", message);
        std::exit(1);
    }
}

static constexpr const char* instance_a =
    "0123456789abcdef0123456789abcdef";
static constexpr const char* instance_b =
    "abcdef0123456789abcdef0123456789";
static constexpr const char* attempt_a =
    "11111111111111111111111111111111";
static constexpr const char* attempt_b =
    "22222222222222222222222222222222";

static std::size_t fixture_for(
    const LocalTournamentState& tour, std::size_t a, std::size_t b) {
    for (std::size_t i = 0; i < tour.fixtures.size(); ++i) {
        const auto& f = tour.fixtures[i];
        if ((f.player1 == a && f.player2 == b) ||
            (f.player1 == b && f.player2 == a)) return i;
    }
    require(false, "fixture missing");
    return 0;
}

static StoredMultiplayerMatch match_for(
    const LocalTournamentState& tour, std::size_t index,
    std::string checksum = "0011223344556677", bool reversed = false) {
    const auto& fixture = tour.fixtures.at(index);
    StoredMultiplayerMatch m;
    m.run_path = "run.urrun";
    m.run.provenance.mode = "race-2p";
    m.run.provenance.course_id = fixture.course_id;
    m.match.schema_version = kMultiplayerMatchRecordSchemaVersion;
    m.match.run_artifact_checksum = std::move(checksum);
    m.match.context.course_id = fixture.course_id;
    m.match.context.match.player1.profile_id =
        tour.entrants[reversed ? fixture.player2 : fixture.player1];
    m.match.context.match.player2.profile_id =
        tour.entrants[reversed ? fixture.player1 : fixture.player2];
    m.match.context.match.result.outcome = Outcome::Player1Win;
    return m;
}

int main() {
    const auto original = make_local_round_robin(
        {"ALICE", "bOb", "Carol"}, {"course:01", "course:04"});
    require(bool(original), "three-profile tournament admitted");
    const std::size_t ab = fixture_for(*original, 0, 1);
    const std::size_t ac = fixture_for(*original, 0, 2);
    const auto candidate = match_for(*original, ab);
    auto tournament = *original;
    LocalTournamentLaunchState launch;

    require(!local_tournament_valid_instance_token("not-an-instance"),
            "reject non-canonical instance ID");
    require(!local_tournament_valid_instance_token(
                "ABCDEF0123456789ABCDEF0123456789"),
            "reject upper-case instance ID");
    require(local_tournament_valid_instance_token(instance_a),
            "accept canonical 32-character identifier");
    require(local_tournament_arm_fixture(
            launch, tournament, instance_a, instance_a, ab) ==
            Status::InvalidInstance,
            "instance and attempt must be different");
    require(local_tournament_arm_fixture(
            launch, tournament, "not-canonical", attempt_a, ab) ==
            Status::InvalidInstance,
            "tournament must have canonical instance identity");
    require(local_tournament_arm_fixture(
            launch, tournament, instance_a, attempt_a, 999) ==
            Status::InvalidFixture,
            "reject unknown fixture before guest routing");
    require(!launch.pending, "all invalid arms remain inert");

    require(local_tournament_arm_fixture(
            launch, tournament, instance_a, attempt_a, ab) ==
            Status::Armed,
            "launch explicitly armed");
    const auto pending = *launch.pending;
    require(pending.fixture_index == ab &&
            pending.round == tournament.fixtures[ab].round &&
            pending.course_id == tournament.fixtures[ab].course_id &&
            pending.first_profile_key ==
                local_tournament_storage_key(
                    tournament.entrants[tournament.fixtures[ab].player1]) &&
            pending.second_profile_key ==
                local_tournament_storage_key(
                    tournament.entrants[tournament.fixtures[ab].player2]),
            "launch snapshots immutable selected fixture authority");
    require(local_tournament_arm_fixture(
            launch, tournament, instance_a, attempt_b, ac) ==
            Status::AlreadyArmed,
            "cannot supersede active fixture without cancellation");

    require(local_tournament_commit_live_result(
            launch, tournament, instance_a, attempt_b, candidate) ==
            Status::StaleAttempt,
            "unrelated live capture attempt has no authority");
    require(local_tournament_commit_live_result(
            launch, tournament, instance_b, attempt_a, candidate) ==
            Status::StaleTournament,
            "unrelated tournament instance has no authority");
    require(local_tournament_cancel_launch(
            launch, instance_a, attempt_b) == Status::StaleAttempt,
            "stale caller cannot cancel active attempt");
    require(!tournament.results[ab] && launch.pending.has_value(),
            "invalid context never changes result or pending launch");

    auto wrong_mode = candidate;
    wrong_mode.run.provenance.mode = "race-1p";
    require(local_tournament_commit_live_result(
            launch, tournament, instance_a, attempt_a, wrong_mode) ==
            Status::MatchRejected,
            "1P run cannot become tournament result");
    auto wrong_course = candidate;
    wrong_course.match.context.course_id = "course:39";
    require(local_tournament_commit_live_result(
            launch, tournament, instance_a, attempt_a, wrong_course) ==
            Status::MatchRejected,
            "course mismatch does not attach another race");
    auto wrong_profiles = candidate;
    wrong_profiles.match.context.match.player2.profile_id = "not-entrant";
    require(local_tournament_commit_live_result(
            launch, tournament, instance_a, attempt_a, wrong_profiles) ==
            Status::MatchRejected,
            "unknown participant cannot attach");
    require(!tournament.results[ab] && launch.pending.has_value(),
            "bad match never mutates launch or standings");

    // Even matching participants/course are insufficient when the durable
    // capture attempt ID does not match the *launched* attempt.
    require(local_tournament_commit_live_result(
            launch, tournament, instance_a, attempt_b, candidate) ==
            Status::StaleAttempt,
            "historical matching pair cannot be inferred by coincidence");

    // A changed schedule must invalidate an outstanding launch, not silently
    // reassign it to the same index with a different course or roster.
    auto drifted = tournament;
    drifted.fixtures[ab].course_id =
        drifted.fixtures[ab].course_id == "course:01"
            ? "course:04" : "course:01";
    require(local_tournament_commit_live_result(
            launch, drifted, instance_a, attempt_a, candidate) ==
            Status::StaleFixture,
            "modified fixture cannot inherit old live attempt");
    drifted = tournament;
    drifted.entrants[tournament.fixtures[ab].player1] = "MALLORY";
    require(local_tournament_commit_live_result(
            launch, drifted, instance_a, attempt_a, candidate) ==
            Status::StaleFixture,
            "modified roster cannot inherit old live attempt");

    const auto reversed = match_for(tournament, ab, "aabbccddeeff0011", true);
    require(local_tournament_commit_live_result(
            launch, tournament, instance_a, attempt_a, reversed) ==
            Status::Recorded,
            "explicit live pair with reversed seats records");
    require(!launch.pending && tournament.results[ab] &&
            tournament.results[ab]->seats_swapped,
            "commit retires attempt and preserves source seat orientation");
    require(local_tournament_commit_live_result(
            launch, tournament, instance_a, attempt_a, reversed) ==
            Status::NoActiveFixture,
            "replay of consumed attempt cannot record twice");

    require(local_tournament_arm_fixture(
            launch, tournament, instance_a, attempt_b, ab) ==
            Status::AlreadyCompleted,
            "completed fixture cannot relaunch");
    require(local_tournament_arm_fixture(
            launch, tournament, instance_a, attempt_b, ac) ==
            Status::Armed,
            "different unfinished fixture can launch");
    require(local_tournament_cancel_launch(
            launch, instance_b, attempt_b) == Status::StaleTournament,
            "unrelated instance cannot cancel a live fixture");
    require(local_tournament_cancel_launch(
            launch, instance_a, attempt_b) == Status::Cancelled,
            "explicit abort retires exact in-flight fixture");
    require(!launch.pending && !tournament.results[ac],
            "abort never fabricates a result");
    require(local_tournament_commit_live_result(
            launch, tournament, instance_a, attempt_b,
            match_for(tournament, ac, "1010101010101010")) ==
            Status::NoActiveFixture,
            "cancelled attempt cannot admit late result");

    // A new attempt can proceed after cancellation, but a stale capture
    // carrying the old ID cannot hijack it.
    require(local_tournament_arm_fixture(
            launch, tournament, instance_a, attempt_a, ac) ==
            Status::Armed,
            "new explicit attempt admitted after abort");
    const auto ac_match = match_for(tournament, ac, "1010101010101010");
    require(local_tournament_commit_live_result(
            launch, tournament, instance_a, attempt_b, ac_match) ==
            Status::StaleAttempt,
            "old capture ID cannot complete new attempt");
    require(local_tournament_commit_live_result(
            launch, tournament, instance_a, attempt_a, ac_match) ==
            Status::Recorded,
            "new capture ID completes correct fixture");

    // A canonical bounded checkpoint can be round-tripped in a new process,
    // but cannot be admitted without the matching active tournament schedule.
    LocalTournamentLaunchState saved;
    require(local_tournament_arm_fixture(
            saved, *original, instance_a, attempt_b, ab) ==
            Status::Armed,
            "fresh pending fixture for durable checkpoint");
    const std::string serialized =
        encode_local_tournament_pending_fixture(*saved.pending);
    require(!serialized.empty() &&
            serialized.size() < kLocalTournamentLaunchMaxBytes,
            "bounded canonical launch checkpoint");
    const auto decoded = decode_local_tournament_pending_fixture(serialized);
    require(decoded && decoded->attempt_id == attempt_b &&
            decoded->course_id == original->fixtures[ab].course_id,
            "strict checkpoint decoder preserves selected fixture");
    LocalTournamentLaunchState restored;
    require(!local_tournament_restore_pending_fixture(
            restored, *original, instance_b, serialized),
            "wrong active tournament cannot restore checkpoint");
    require(!restored.pending, "rejected restore does not mutate owner");
    auto wrong_schedule = *original;
    wrong_schedule.fixtures[ab].round += 1;
    require(!local_tournament_restore_pending_fixture(
            restored, wrong_schedule, instance_a, serialized),
            "new schedule does not inherit stale pending fixture");
    require(!local_tournament_restore_pending_fixture(
            restored, tournament, instance_a, serialized),
            "completed fixture cannot restore pending launch");
    require(local_tournament_restore_pending_fixture(
            restored, *original, instance_a, serialized),
            "exact active fixture can restore pending launch");
    require(!local_tournament_restore_pending_fixture(
            restored, *original, instance_a, serialized),
            "replay cannot overwrite already-restored launch");
    require(local_tournament_cancel_launch(
            restored, instance_a, attempt_b) == Status::Cancelled,
            "restored attempt still has exact cancellation semantics");

    auto reseal = [](std::string altered) {
        const auto cut = altered.rfind("checksum ");
        require(cut != std::string::npos, "fixture checksum field");
        return altered.substr(0, cut) + "checksum " +
            local_tournament_launch_hex64(
                local_tournament_launch_fnv64(
                    std::string_view(altered).substr(0, cut))) + "\n";
    };
    auto tampered = serialized;
    tampered[0] = 'X';
    require(!decode_local_tournament_pending_fixture(tampered),
            "tampered codec magic rejected");
    tampered = serialized;
    tampered.replace(tampered.find("course:"), 9, "course:39");
    require(!decode_local_tournament_pending_fixture(tampered),
            "tampered course rejected by checksum");
    require(bool(decode_local_tournament_pending_fixture(reseal(tampered))),
            "checksum is corruption detection, not an authorization seal");
    // A canonical different course may decode, but cannot restore under the
    // authoritative saved fixture. Never claim the checksum is a signature.
    auto forged = decode_local_tournament_pending_fixture(reseal(tampered));
    if (forged) {
        LocalTournamentLaunchState no_restore;
        require(!local_tournament_restore_pending_fixture(
                no_restore, *original, instance_a, reseal(tampered)),
                "resealed drifted course cannot be restored");
    }
    tampered = serialized;
    tampered.erase(tampered.size() - 1);
    require(!decode_local_tournament_pending_fixture(tampered),
            "missing trailing newline rejected");
    require(!decode_local_tournament_pending_fixture(
            serialized + "extra\\n"), "trailing lines rejected");
    require(!decode_local_tournament_pending_fixture(
            std::string(kLocalTournamentLaunchMaxBytes + 1u, 'x')),
            "oversize checkpoint rejected");
    const auto original_fixture = std::to_string(ab);
    const std::string fixture_field = "fixture " + original_fixture + "\n";
    tampered = serialized;
    const auto field_pos = tampered.find(fixture_field);
    require(field_pos != std::string::npos, "fixture field found");
    tampered.replace(field_pos, fixture_field.size(),
                    "fixture 0" + original_fixture + "\n");
    require(!decode_local_tournament_pending_fixture(reseal(tampered)),
            "noncanonical leading-zero integer rejected");
    tampered = serialized;
    const auto first_pos = tampered.find("first ");
    require(first_pos != std::string::npos, "first profile field found");
    tampered[first_pos + 6] = 'G';
    require(!decode_local_tournament_pending_fixture(reseal(tampered)),
            "invalid hex profile ID rejected");

    std::puts("local_tournament_fixture_launch_test: ok");
}

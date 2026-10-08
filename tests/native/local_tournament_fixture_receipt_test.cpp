#include "local_tournament_fixture_receipt.hpp"

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

using namespace ur::product;
using Outcome = ur::title::OrdinaryTwoPlayerRaceOutcome;

void check(bool pass, const char* why) {
    if (!pass) {
        std::fprintf(stderr, "FAIL: %s\n", why);
        std::exit(1);
    }
}

StoredMultiplayerMatch accepted(
    const LocalTournamentState& t,
    std::size_t fixture,
    Outcome outcome) {
    const auto& f = t.fixtures.at(fixture);
    StoredMultiplayerMatch result;
    result.run_path = "confirmed.urrun";
    result.run.provenance.mode = "race-2p";
    result.run.provenance.course_id = f.course_id;
    result.match.schema_version = kMultiplayerMatchRecordSchemaVersion;
    result.match.run_artifact_checksum = "0123456789abcdef";
    result.match.context.course_id = f.course_id;
    result.match.context.match.player1.profile_id = t.entrants[f.player1];
    result.match.context.match.player2.profile_id = t.entrants[f.player2];
    result.match.context.match.result.outcome = outcome;
    return result;
}

int main() {
    const std::string id = "0123456789abcdef0123456789abcdef";
    auto plan = make_local_round_robin(
        {"ALICE", "bob", "CAROL"}, {"course:01", "course:04"});
    check(bool(plan), "tournament plan exists");
    auto stored = accepted(*plan, 0, Outcome::Player1Win);
    check(!make_local_tournament_receipt(*plan, id, 0, stored),
          "uncommitted fixture cannot fabricate receipt");
    check(record_local_tournament_result(*plan, 0, stored) ==
              LocalTournamentRecordStatus::Applied,
          "source pair must first be explicitly committed to active fixture");

    const auto receipt = make_local_tournament_receipt(*plan, id, 0, stored);
    check(bool(receipt), "committed fixture can produce receipt");
    check(receipt->source_p1_profile ==
              local_tournament_storage_key(stored.match.context.match.player1.profile_id),
          "source profile canonicalized to storage identity");
    const auto bytes = encode_local_tournament_receipt(*receipt);
    check(!bytes.empty(), "receipt encodes");
    check(bytes.find("UR-LOCAL-TOURNAMENT-FIXTURE/1\n") == 0,
          "receipt has strict independent v1 magic");
    check(bytes.find("run_checksum 0123456789abcdef\n") != std::string::npos,
          "run binding carried");
    check(bytes.find("\nchecksum ") != std::string::npos,
          "receipt tamper detection present");
    const auto decoded = decode_local_tournament_receipt(bytes);
    check(bool(decoded), "canonical receipt round trips");
    check(encode_local_tournament_receipt(*decoded) == bytes,
          "canonical re-encoding preserves exact bytes");
    check(local_tournament_receipt_matches(
              *decoded, *plan, id, stored),
          "receipt matches explicit active fixture and bound pair");

    auto uncommitted_copy = *plan;
    uncommitted_copy.results.assign(plan->results.size(), std::nullopt);
    check(local_tournament_receipt_matches(
              *decoded, uncommitted_copy, id, stored),
          "fresh-process restore validates before applying standings");
    check(!local_tournament_receipt_matches(
              *decoded, *plan, "ffffffffffffffffffffffffffffffff", stored),
          "another tournament instance cannot claim same fixture");
    auto wrong_run = stored;
    wrong_run.match.run_artifact_checksum = "fedcba9876543210";
    check(!local_tournament_receipt_matches(*decoded, *plan, id, wrong_run),
          "run checksum mismatch rejected");
    auto wrong_course = stored;
    wrong_course.match.context.course_id = "course:04";
    check(!local_tournament_receipt_matches(*decoded, *plan, id, wrong_course),
          "course mismatch rejected");
    auto wrong_participant = stored;
    wrong_participant.match.context.match.player1.profile_id = "outsider";
    check(!local_tournament_receipt_matches(
              *decoded, *plan, id, wrong_participant),
          "participant mismatch rejected");
    auto wrong_outcome = stored;
    wrong_outcome.match.context.match.result.outcome = Outcome::Player2Win;
    check(!local_tournament_receipt_matches(*decoded, *plan, id, wrong_outcome),
          "different authoritative outcome rejected");
    auto wrong_mode = stored;
    wrong_mode.run.provenance.mode = "race-1p";
    check(!local_tournament_receipt_matches(*decoded, *plan, id, wrong_mode),
          "one-player artifacts have no fixture binding authority");
    auto altered_plan = *plan;
    altered_plan.fixtures[0].course_id = "course:04";
    check(!local_tournament_receipt_matches(
              *decoded, altered_plan, id, stored),
          "modified schedule rejected");

    auto malformed_id = *receipt;
    malformed_id.tournament_id = "bad id";
    check(encode_local_tournament_receipt(malformed_id).empty(),
          "invalid instance key refused");
    auto malformed_checksum = *receipt;
    malformed_checksum.run_checksum = "garbage";
    check(encode_local_tournament_receipt(malformed_checksum).empty(),
          "noncanonical run checksum refused");
    auto same_participant = *receipt;
    same_participant.source_p2_profile = same_participant.source_p1_profile;
    check(encode_local_tournament_receipt(same_participant).empty(),
          "identical seat identities rejected");

    auto tamper = [&](const std::string& from, const std::string& to) {
        std::string changed = bytes;
        const auto i = changed.find(from);
        check(i != std::string::npos, "tamper target present");
        changed.replace(i, from.size(), to);
        check(!decode_local_tournament_receipt(changed),
              "tampered receipt fails decoding");
    };
    tamper("fixture 0\n", "fixture 1\n");
    tamper("outcome p1\n", "outcome p2\n");
    tamper("swapped 0\n", "swapped 1\n");
    tamper("run_checksum 0123456789abcdef", "run_checksum 0123456789abcdee");
    tamper("course ", "wrong  ");
    tamper("tournament ", "tournamentx ");
    check(!decode_local_tournament_receipt(bytes + "extra"),
          "trailing bytes rejected");
    check(!decode_local_tournament_receipt(bytes.substr(0, bytes.size() - 1)),
          "missing final newline rejected");
    check(!decode_local_tournament_receipt(std::string(2049, 'x')),
          "oversized receipt rejected");
    check(!decode_local_tournament_receipt(""),
          "empty receipt rejected");

    // A valid but newly re-signed receipt for another fixture must still
    // fail the authenticated source-pair/schedule projection.
    auto wrong_fixture_receipt = *receipt;
    wrong_fixture_receipt.fixture_index = 1;
    const auto other_bytes = encode_local_tournament_receipt(wrong_fixture_receipt);
    check(!other_bytes.empty() && decode_local_tournament_receipt(other_bytes),
          "syntactically valid alternate receipt");
    check(!local_tournament_receipt_matches(
              *decode_local_tournament_receipt(other_bytes),
              *plan, id, stored),
          "changed fixture index cannot hijack a completed match");

    std::puts("local_tournament_fixture_receipt_test: ok");
    return 0;
}

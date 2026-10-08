#include "local_tournament_receipt_restore.hpp"

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

using namespace ur::product;
using Outcome = ur::title::OrdinaryTwoPlayerRaceOutcome;

namespace {

void check(bool ok, const char* reason) {
    if (!ok) {
        std::fprintf(stderr, "FAIL: %s\n", reason);
        std::exit(1);
    }
}

StoredMultiplayerMatch admitted(
    const LocalTournamentState& plan,
    std::size_t fixture_index,
    std::string checksum,
    Outcome outcome,
    bool swapped = false) {
    const auto& f = plan.fixtures.at(fixture_index);
    StoredMultiplayerMatch stored;
    stored.run_path = checksum + ".urrun";
    stored.run.provenance.mode = "race-2p";
    stored.run.provenance.course_id = f.course_id;
    stored.match.schema_version = kMultiplayerMatchRecordSchemaVersion;
    stored.match.run_artifact_checksum = std::move(checksum);
    stored.match.context.course_id = f.course_id;
    stored.match.context.match.player1.profile_id =
        plan.entrants[swapped ? f.player2 : f.player1];
    stored.match.context.match.player2.profile_id =
        plan.entrants[swapped ? f.player1 : f.player2];
    stored.match.context.match.result.outcome = outcome;
    return stored;
}

LocalTournamentReceiptEvidence seal(
    const LocalTournamentState& empty,
    std::string_view instance,
    std::size_t index,
    const StoredMultiplayerMatch& pair) {
    auto started = empty;
    check(record_local_tournament_result(started, index, pair) ==
        LocalTournamentRecordStatus::Applied, "explicit fixture admission");
    const auto receipt =
        make_local_tournament_receipt(started, instance, index, pair);
    check(bool(receipt), "fixture receipt sealed after explicit admission");
    auto encoded = encode_local_tournament_receipt(*receipt);
    check(!encoded.empty(), "receipt encoded");
    return {std::move(encoded), pair};
}

void rejected(
    const LocalTournamentState& plan,
    std::string_view id,
    const std::vector<LocalTournamentReceiptEvidence>& receipts,
    LocalTournamentRestoreStatus status,
    const char* why) {
    const auto result = restore_local_tournament_receipts(plan, id, receipts);
    check(!result.restored() && !result.state && result.status == status, why);
}

} // namespace

int main() {
    constexpr auto kWin1 = Outcome::Player1Win;
    constexpr auto kWin2 = Outcome::Player2Win;
    constexpr auto kDraw = Outcome::Draw;
    const std::string instance = "0123456789abcdef0123456789abcdef";
    const std::string other = "abcdef0123456789abcdef0123456789";
    const auto empty = make_local_round_robin(
        {"Alice", "BOB", "Carol"}, {"course:01", "course:04"});
    check(bool(empty) && empty->fixtures.size() == 3u,
          "canonical three-entrant schedule");

    // Receipt origin is the exact explicit fixture. Source seats may swap.
    const auto first = admitted(
        *empty, 0, "1111111111111111", kWin1);
    const auto second = admitted(
        *empty, 1, "2222222222222222", kWin2, true);
    const auto a = seal(*empty, instance, 0, first);
    const auto b = seal(*empty, instance, 1, second);

    const auto no_results =
        restore_local_tournament_receipts(*empty, instance, {});
    check(no_results.restored() &&
        local_tournament_standings(*no_results.state).size() == 3u,
        "empty explicit batch is a valid zero-fixture restore");
    const auto result =
        restore_local_tournament_receipts(*empty, instance, {b, a});
    check(result.restored(), "out-of-order receipts both restored");
    check(result.state->results.size() == empty->results.size() &&
          result.state->results[0] && result.state->results[1] &&
          !result.state->results[2],
          "only exactly attested fixtures gain results");
    check(result.state->results[0]->run_artifact_checksum ==
              "1111111111111111" &&
          result.state->results[1]->run_artifact_checksum ==
              "2222222222222222" &&
          result.state->results[1]->seats_swapped,
          "run identity and reversed seats survive restore");
    check(!empty->results[0] && !empty->results[1],
          "input schedule remains completely unchanged");
    const auto standings = local_tournament_standings(*result.state);
    std::size_t total_played = 0, total_points = 0;
    for (const auto& row : standings) {
        total_played += row.played;
        total_points += row.points;
    }
    check(total_played == 4u && total_points == 6u,
          "standings derive only from two validated wins");

    rejected(*empty, other, {a},
        LocalTournamentRestoreStatus::UnboundEvidence,
        "wrong active tournament ID refuses complete batch");
    rejected(*empty, "garbage", {a},
        LocalTournamentRestoreStatus::InvalidInstance,
        "noncanonical active tournament ID refused");
    rejected(*empty, instance, {a, a},
        LocalTournamentRestoreStatus::DuplicateFixture,
        "duplicate fixture cannot credit same result twice");

    auto corrupt = b;
    corrupt.canonical_receipt_bytes.pop_back();
    rejected(*empty, instance, {a, corrupt},
        LocalTournamentRestoreStatus::MalformedReceipt,
        "late corrupt receipt invalidates whole batch");
    auto wrong_pair = b;
    wrong_pair.admitted_pair.match.context.course_id = "course:39";
    rejected(*empty, instance, {a, wrong_pair},
        LocalTournamentRestoreStatus::UnboundEvidence,
        "course mismatch invalidates whole batch");
    wrong_pair = b;
    wrong_pair.admitted_pair.match.context.match.result.outcome = kDraw;
    rejected(*empty, instance, {a, wrong_pair},
        LocalTournamentRestoreStatus::UnboundEvidence,
        "stock outcome mismatch invalidates whole batch");
    wrong_pair = b;
    wrong_pair.admitted_pair.match.run_artifact_checksum =
        "ffffffffffffffff";
    rejected(*empty, instance, {a, wrong_pair},
        LocalTournamentRestoreStatus::UnboundEvidence,
        "changed run checksum invalidates whole batch");

    // Individually valid receipts may refer to one reused run checksum.
    // Batch restore must reject even when the fixture indices differ.
    const auto duplicate_run = admitted(
        *empty, 1, "1111111111111111", kWin2, true);
    const auto replayed = seal(*empty, instance, 1, duplicate_run);
    rejected(*empty, instance, {a, replayed},
        LocalTournamentRestoreStatus::DuplicateArtifact,
        "one saved match cannot count for two fixtures");

    auto already_played = *empty;
    already_played.results[1] = LocalTournamentRecordedResult{
        "2222222222222222", kWin2, true};
    rejected(already_played, instance, {a},
        LocalTournamentRestoreStatus::InvalidPlan,
        "restore never silently merges with preexisting results");
    auto drifted = *empty;
    drifted.fixtures[2].course_id = "course:39";
    rejected(drifted, instance, {a},
        LocalTournamentRestoreStatus::InvalidPlan,
        "tampered unplayed fixture invalidates immutable schedule");
    drifted = *empty;
    drifted.fixtures[1].player1 = drifted.fixtures[1].player2;
    rejected(drifted, instance, {a},
        LocalTournamentRestoreStatus::InvalidPlan,
        "tampered seat assignment rejected even on other fixture");

    std::vector<LocalTournamentReceiptEvidence> overflow(4, a);
    rejected(*empty, instance, overflow,
        LocalTournamentRestoreStatus::TooManyReceipts,
        "bounded number of attestations");
    const auto third = seal(*empty, instance, 2,
        admitted(*empty, 2, "3333333333333333", kDraw));
    const auto complete = restore_local_tournament_receipts(
        *empty, instance, {third, a, b});
    check(complete.restored() && complete.state->results[2],
          "full independently sealed fixture set restores");
    check(local_tournament_standings(*complete.state).size() == 3,
          "complete standings available without scanning general Records");

    std::puts("local_tournament_receipt_restore_test: ok");
    return 0;
}

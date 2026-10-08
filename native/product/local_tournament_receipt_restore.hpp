#pragma once

#include "local_tournament_fixture_receipt.hpp"

#include <cstddef>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace ur::product {

// Each receipt must come from a separately persisted, explicitly launched
// fixture. The paired run MUST already have been admitted by the strict
// multiplayer match catalog; a raw filesystem .urrun is not this type's
// admission authority. Never manufacture receipts from Records history.
struct LocalTournamentReceiptEvidence {
    std::string canonical_receipt_bytes;
    StoredMultiplayerMatch admitted_pair;
};

enum class LocalTournamentRestoreStatus {
    Restored,
    InvalidInstance,
    InvalidPlan,
    TooManyReceipts,
    MalformedReceipt,
    DuplicateFixture,
    UnboundEvidence,
    DuplicateArtifact,
    ResultRejected,
};

struct LocalTournamentRestoreResult {
    LocalTournamentRestoreStatus status =
        LocalTournamentRestoreStatus::InvalidPlan;
    std::optional<LocalTournamentState> state;

    bool restored() const noexcept {
        return status == LocalTournamentRestoreStatus::Restored &&
            state.has_value();
    }
};

// Read-only, all-or-nothing recovery over EXPLICIT receipt + validated-pair
// associations. No catalog scan, guest state, mutable input state, disk I/O or
// guessing tournament membership from equivalent courses/profiles.
//
// The caller supplies a freshly reconstructed canonical schedule with no
// results and the exact active tournament ID from separate durable authority.
// Receipt order may vary; fixture indices, source seats, checksum and outcome
// cannot. A single invalid/duplicate entry rejects the *entire* batch, never
// returning partially credited standings.
inline LocalTournamentRestoreResult restore_local_tournament_receipts(
    const LocalTournamentState& expected_empty_plan,
    std::string_view active_tournament_id,
    const std::vector<LocalTournamentReceiptEvidence>& evidence) {
    auto reject = [](LocalTournamentRestoreStatus status) {
        return LocalTournamentRestoreResult{status, std::nullopt};
    };
    if (!local_tournament_lower_hex(active_tournament_id, 32)) {
        return reject(LocalTournamentRestoreStatus::InvalidInstance);
    }
    const auto canonical = make_local_round_robin(
        expected_empty_plan.entrants, expected_empty_plan.course_pool);
    if (!canonical ||
        expected_empty_plan.fixtures.size() != canonical->fixtures.size() ||
        expected_empty_plan.results.size() != canonical->results.size()) {
        return reject(LocalTournamentRestoreStatus::InvalidPlan);
    }
    for (std::size_t i = 0; i < canonical->fixtures.size(); ++i) {
        const auto& actual = expected_empty_plan.fixtures[i];
        const auto& authored = canonical->fixtures[i];
        if (expected_empty_plan.results[i] ||
            actual.round != authored.round ||
            actual.player1 != authored.player1 ||
            actual.player2 != authored.player2 ||
            actual.course_id != authored.course_id) {
            return reject(LocalTournamentRestoreStatus::InvalidPlan);
        }
    }
    if (evidence.size() > canonical->fixtures.size()) {
        return reject(LocalTournamentRestoreStatus::TooManyReceipts);
    }

    // Reconstruct from the canonical empty schedule. The original input is
    // never modified, including when a later item invalidates earlier ones.
    LocalTournamentState rebuilt = *canonical;
    std::vector<bool> seen(rebuilt.fixtures.size(), false);
    for (const auto& entry : evidence) {
        const auto receipt =
            decode_local_tournament_receipt(entry.canonical_receipt_bytes);
        if (!receipt) {
            return reject(LocalTournamentRestoreStatus::MalformedReceipt);
        }
        if (receipt->fixture_index >= seen.size()) {
            return reject(LocalTournamentRestoreStatus::UnboundEvidence);
        }
        if (seen[receipt->fixture_index]) {
            return reject(LocalTournamentRestoreStatus::DuplicateFixture);
        }
        if (!local_tournament_receipt_matches(
                *receipt, rebuilt, active_tournament_id,
                entry.admitted_pair)) {
            return reject(LocalTournamentRestoreStatus::UnboundEvidence);
        }
        const auto status = record_local_tournament_result(
            rebuilt, receipt->fixture_index, entry.admitted_pair);
        if (status == LocalTournamentRecordStatus::DuplicateArtifact) {
            return reject(LocalTournamentRestoreStatus::DuplicateArtifact);
        }
        if (status != LocalTournamentRecordStatus::Applied) {
            return reject(LocalTournamentRestoreStatus::ResultRejected);
        }
        seen[receipt->fixture_index] = true;
    }
    return {LocalTournamentRestoreStatus::Restored, std::move(rebuilt)};
}

} // namespace ur::product

#pragma once

#include "local_tournament_round_robin.hpp"

#include <cstddef>
#include <optional>
#include <string>
#include <string_view>

namespace ur::product {

// Session-owned *launch* authority, not a historical Records query. The host
// must mint distinct instance/attempt IDs before guest routing and hand the
// attempt ID back from its live ordinary-2P capture, never a directory scan.
// Persistence, guest routing and durable fixture receipts are other layers.
struct LocalTournamentPendingFixture {
    std::string tournament_id; // exact 32-char lowercase hex instance ID
    std::string attempt_id;    // exact 32-char lowercase hex live-launch ID
    std::size_t fixture_index = 0;
    std::size_t round = 0;
    std::string first_profile_key;
    std::string second_profile_key;
    std::string course_id;
};

struct LocalTournamentLaunchState {
    std::optional<LocalTournamentPendingFixture> pending;
};

enum class LocalTournamentLaunchStatus {
    Armed,
    AlreadyArmed,
    InvalidInstance,
    InvalidFixture,
    AlreadyCompleted,
    NoActiveFixture,
    StaleAttempt,
    StaleTournament,
    StaleFixture,
    MatchRejected,
    Recorded,
    Cancelled,
};

inline bool local_tournament_valid_instance_token(
    std::string_view token) noexcept {
    if (token.size() != 32) return false;
    for (const char ch : token) {
        if (!((ch >= '0' && ch <= '9') ||
              (ch >= 'a' && ch <= 'f'))) return false;
    }
    return true;
}

inline bool local_tournament_pending_matches_fixture(
    const LocalTournamentPendingFixture& pending,
    const LocalTournamentState& tournament) {
    if (pending.fixture_index >= tournament.fixtures.size() ||
        pending.fixture_index >= tournament.results.size() ||
        tournament.results[pending.fixture_index]) return false;
    const auto& fixture = tournament.fixtures[pending.fixture_index];
    if (fixture.player1 >= tournament.entrants.size() ||
        fixture.player2 >= tournament.entrants.size() ||
        fixture.player1 == fixture.player2 ||
        !local_tournament_ordinary_race_course(fixture.course_id)) {
        return false;
    }
    const std::string p1 =
        local_tournament_storage_key(tournament.entrants[fixture.player1]);
    const std::string p2 =
        local_tournament_storage_key(tournament.entrants[fixture.player2]);
    return !p1.empty() && !p2.empty() && p1 != p2 &&
        fixture.round == pending.round &&
        fixture.course_id == pending.course_id &&
        p1 == pending.first_profile_key &&
        p2 == pending.second_profile_key;
}

// This call must be made at the *explicit* user choice of an unfinished
// fixture, before starting the stock route. Never mint from Records history.
inline LocalTournamentLaunchStatus local_tournament_arm_fixture(
    LocalTournamentLaunchState& launch,
    const LocalTournamentState& tournament,
    std::string_view tournament_id,
    std::string_view attempt_id,
    std::size_t fixture_index) {
    if (launch.pending) return LocalTournamentLaunchStatus::AlreadyArmed;
    if (!local_tournament_valid_instance_token(tournament_id) ||
        !local_tournament_valid_instance_token(attempt_id) ||
        tournament_id == attempt_id) {
        return LocalTournamentLaunchStatus::InvalidInstance;
    }
    if (tournament.fixtures.size() != tournament.results.size() ||
        fixture_index >= tournament.fixtures.size()) {
        return LocalTournamentLaunchStatus::InvalidFixture;
    }
    if (tournament.results[fixture_index]) {
        return LocalTournamentLaunchStatus::AlreadyCompleted;
    }
    const auto& fixture = tournament.fixtures[fixture_index];
    if (fixture.player1 >= tournament.entrants.size() ||
        fixture.player2 >= tournament.entrants.size() ||
        fixture.player1 == fixture.player2 ||
        fixture.round == 0 ||
        !local_tournament_ordinary_race_course(fixture.course_id)) {
        return LocalTournamentLaunchStatus::InvalidFixture;
    }
    LocalTournamentPendingFixture snapshot{
        std::string(tournament_id), std::string(attempt_id),
        fixture_index, fixture.round,
        local_tournament_storage_key(tournament.entrants[fixture.player1]),
        local_tournament_storage_key(tournament.entrants[fixture.player2]),
        fixture.course_id,
    };
    if (snapshot.first_profile_key.empty() ||
        snapshot.second_profile_key.empty() ||
        snapshot.first_profile_key == snapshot.second_profile_key) {
        return LocalTournamentLaunchStatus::InvalidFixture;
    }
    launch.pending = std::move(snapshot);
    return LocalTournamentLaunchStatus::Armed;
}

// Called by the live, attempt-tagged ordinary-2P result producer after it has
// independently admitted the checksum/course-bound .urrun + .urmatch pair.
// The attempt ID must be supplied by that producer, NOT inferred from the
// saved pair or a filename. On any rejection neither state nor launch changes.
// A later receipt producer may seal the recorded fixture and source pair.
inline LocalTournamentLaunchStatus local_tournament_commit_live_result(
    LocalTournamentLaunchState& launch,
    LocalTournamentState& tournament,
    std::string_view tournament_id,
    std::string_view capture_attempt_id,
    const StoredMultiplayerMatch& admitted) {
    if (!launch.pending) return LocalTournamentLaunchStatus::NoActiveFixture;
    const auto& pending = *launch.pending;
    if (pending.tournament_id != tournament_id) {
        return LocalTournamentLaunchStatus::StaleTournament;
    }
    if (pending.attempt_id != capture_attempt_id) {
        return LocalTournamentLaunchStatus::StaleAttempt;
    }
    if (!local_tournament_pending_matches_fixture(pending, tournament)) {
        return LocalTournamentLaunchStatus::StaleFixture;
    }
    if (record_local_tournament_result(
            tournament, pending.fixture_index, admitted) !=
        LocalTournamentRecordStatus::Applied) {
        return LocalTournamentLaunchStatus::MatchRejected;
    }
    launch.pending.reset();
    return LocalTournamentLaunchStatus::Recorded;
}

// A failed/cancelled stock route invalidates the exact launch; a stale caller
// cannot cancel the next attempt. No result is ever fabricated by cancellation.
inline LocalTournamentLaunchStatus local_tournament_cancel_launch(
    LocalTournamentLaunchState& launch,
    std::string_view tournament_id,
    std::string_view attempt_id) {
    if (!launch.pending) return LocalTournamentLaunchStatus::NoActiveFixture;
    if (launch.pending->tournament_id != tournament_id) {
        return LocalTournamentLaunchStatus::StaleTournament;
    }
    if (launch.pending->attempt_id != attempt_id) {
        return LocalTournamentLaunchStatus::StaleAttempt;
    }
    launch.pending.reset();
    return LocalTournamentLaunchStatus::Cancelled;
}

} // namespace ur::product

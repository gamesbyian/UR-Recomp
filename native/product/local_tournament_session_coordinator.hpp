#pragma once

#include "local_tournament_session_store.hpp"
#include "local_tournament_fixture_launch_store.hpp"
#include "local_tournament_result_link_store.hpp"

#include <cstddef>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace ur::product {
class TournamentLaunchPathLock;

// Host-supplied location in the EXISTING per-user data root. All tournament
// files are owned under this root; authoritative 2P Records stay in the
// existing shared multiplayer-runs namespace.
struct LocalTournamentCoordinatorPaths {
    std::string tournaments_root;
    std::string multiplayer_runs_directory;
};

struct LocalTournamentCoordinator {
    LocalTournamentSessionDefinition definition;
    LocalTournamentState results;
    LocalTournamentLaunchState launch;
    LocalTournamentCoordinatorPaths paths;
    // OS-handle live fixture lease, held across the guest race by the host.
    // Copies share ownership; death of the last process releases it.
    std::shared_ptr<TournamentLaunchPathLock> live_fixture_lock;
};

enum class LocalTournamentCoordinatorStatus {
    Created,
    Restored,
    Armed,
    Busy, // another still-running game owns this fixture instance
    Committed,
    Cancelled,
    InvalidRequest,
    AlreadyExists,
    Unavailable,
    StorageFailed,
    EvidenceRejected,
};

struct LocalTournamentCoordinatorResult {
    LocalTournamentCoordinatorStatus status =
        LocalTournamentCoordinatorStatus::InvalidRequest;
    std::optional<LocalTournamentCoordinator> session;
    std::string detail;

    bool usable() const noexcept {
        return session.has_value() &&
            (status == LocalTournamentCoordinatorStatus::Created ||
             status == LocalTournamentCoordinatorStatus::Restored);
    }
};

// Caller must have explicitly selected this roster and minted a fresh,
// unpredictable 32-hex tournament instance ID. Does not launch a guest race.
LocalTournamentCoordinatorResult create_local_tournament_coordinator(
    const LocalTournamentCoordinatorPaths& paths,
    std::string_view new_instance_id,
    const std::vector<std::string>& explicitly_selected_profiles,
    const std::vector<HostProfileCatalogEntry>& authoritative_catalog,
    const std::vector<std::string>& ordinary_race_course_pool,
    bool replace_existing_tournament = false,
    std::size_t legs = 1);

// Restore only the current durable session and fixture-indexed validated
// receipts. An interrupted previous process's pending race is never resumed;
// the guest race state is gone, so no run can be credited from its checkpoint.
LocalTournamentCoordinatorResult restore_local_tournament_coordinator(
    const LocalTournamentCoordinatorPaths& paths,
    const std::vector<HostProfileCatalogEntry>& authoritative_catalog);

// Read-only history of COMPLETED, independently identified tournaments.
// Each row is restored from its immutable per-instance session file plus the
// exact receipt-linked saved ordinary-2P pairs. No global Records scan can
// manufacture tournament membership or results. Random instance ID order is
// deterministic, not claimed chronological.
struct LocalTournamentCompletedHistory {
    bool scanned = false;
    bool truncated = false;
    std::size_t unavailable_instances = 0;
    std::size_t incomplete_instances = 0;
    std::vector<LocalTournamentCoordinator> completed;
};

LocalTournamentCompletedHistory load_completed_local_tournament_history(
    const LocalTournamentCoordinatorPaths& paths);

// A fixture must be explicitly chosen and both Modern participant profile IDs
// confirmed before the host enters the stock two-player route. The host mints
// a distinct new 32-hex capture-attempt token. Failures never enter guest
// menus, write guest SRAM, or arm a session locally.
LocalTournamentCoordinatorStatus arm_local_tournament_fixture(
    LocalTournamentCoordinator& session,
    std::size_t fixture_index,
    std::string_view new_capture_attempt_id,
    std::string_view confirmed_p1_profile,
    std::string_view confirmed_p2_profile);

// Called at the live existing ordinary-2P recorder's start. Returns the
// retained capture attempt ID only if the guest-observed course and confirmed
// participant IDs match the explicitly armed fixture. The caller must carry
// this token forward from the live capture, never derive it on results.
std::optional<std::string> local_tournament_capture_attempt_for(
    const LocalTournamentCoordinator& session,
    std::string_view confirmed_p1_profile,
    std::string_view confirmed_p2_profile,
    std::string_view guest_observed_course_id);

// Called only AFTER existing append_multiplayer_match_pair has published an
// authoritative stock-result pair. This re-admits that exact saved pair and
// persists its explicit fixture receipt before updating standings.
LocalTournamentCoordinatorStatus commit_local_tournament_capture(
    LocalTournamentCoordinator& session,
    std::string_view live_capture_attempt_id,
    const std::string& already_published_run_path);

// Abort ONLY the exact attempt, leaving the selected fixture unplayed.
LocalTournamentCoordinatorStatus cancel_local_tournament_capture(
    LocalTournamentCoordinator& session,
    std::string_view live_capture_attempt_id);

bool local_tournament_coordinator_complete(
    const LocalTournamentCoordinator& session) noexcept;
std::optional<std::size_t> local_tournament_next_unplayed_fixture(
    const LocalTournamentCoordinator& session) noexcept;

} // namespace ur::product

#include "local_tournament_session_coordinator.hpp"

#include <algorithm>
#include <filesystem>
#include <string>
#include <string_view>
#include <utility>

namespace ur::product {
namespace {
namespace fs = std::filesystem;
using Status = LocalTournamentCoordinatorStatus;

bool valid_paths(const LocalTournamentCoordinatorPaths& paths) {
    return !paths.tournaments_root.empty() &&
        !paths.multiplayer_runs_directory.empty();
}

std::string active_session_path(const LocalTournamentCoordinatorPaths& paths) {
    return (fs::path(paths.tournaments_root) / "active.urtournament").string();
}

std::string instance_directory(const LocalTournamentCoordinator& session) {
    return (fs::path(session.paths.tournaments_root) /
            session.definition.instance_id).string();
}

std::string receipts_directory(const LocalTournamentCoordinator& session) {
    return (fs::path(instance_directory(session)) / "fixtures").string();
}

std::string archived_session_path(const LocalTournamentCoordinator& session) {
    return (fs::path(instance_directory(session)) /
            "session.urtournament").string();
}

std::string pending_path(const LocalTournamentCoordinator& session) {
    return (fs::path(instance_directory(session)) / "pending.urlaunch").string();
}

bool same_fixture_participants(const LocalTournamentPendingFixture& pending,
                               std::string_view p1,
                               std::string_view p2) {
    const auto first = local_tournament_storage_key(p1);
    const auto second = local_tournament_storage_key(p2);
    return (first == pending.first_profile_key &&
            second == pending.second_profile_key) ||
           (second == pending.first_profile_key &&
            first == pending.second_profile_key);
}

LocalTournamentCoordinatorResult error(Status status, const char* message) {
    return {status, std::nullopt, message};
}
} // namespace

LocalTournamentCoordinatorResult create_local_tournament_coordinator(
    const LocalTournamentCoordinatorPaths& paths,
    std::string_view new_instance_id,
    const std::vector<std::string>& explicitly_selected_profiles,
    const std::vector<HostProfileCatalogEntry>& authoritative_catalog,
    const std::vector<std::string>& ordinary_race_course_pool,
    bool replace_existing_tournament) {
    if (!valid_paths(paths)) {
        return error(Status::InvalidRequest, "missing host-owned storage roots");
    }
    const auto definition = make_local_tournament_session_definition(
        new_instance_id, explicitly_selected_profiles,
        authoritative_catalog, ordinary_race_course_pool);
    if (!definition) {
        return error(Status::InvalidRequest, "invalid explicitly selected tournament");
    }
    LocalTournamentCoordinator next{*definition, definition->empty_schedule,
                                    {}, paths};
    const fs::path session_file(active_session_path(paths));
    std::error_code ec;
    const bool present = fs::exists(session_file, ec);
    if (ec) return error(Status::StorageFailed, "cannot inspect existing session");
    if (present && !replace_existing_tournament) {
        return error(Status::AlreadyExists, "explicit replacement required");
    }
    // A reused instance ID would silently inherit old fixture receipts even
    // when explicit replacement was requested. Refuse reuse whether or not
    // the prior instance is currently active; IDs are unique across events.
    ec.clear();
    const bool instance_exists = fs::exists(instance_directory(next), ec);
    if (ec) {
        return error(Status::StorageFailed, "cannot inspect instance identity");
    }
    if (instance_exists) {
        return error(Status::AlreadyExists, "tournament instance already used");
    }
    if (!fs::create_directories(receipts_directory(next), ec) && ec) {
        return error(Status::StorageFailed, "cannot create fixture directory");
    }
    // Preserve the canonical immutable plan inside the unique instance root
    // BEFORE replacing the active pointer. Completed tournaments then stay
    // restorable after their successor becomes active. A failed active write
    // may leave an inert archive but cannot redirect the old active session.
    if (save_local_tournament_session_definition(
            archived_session_path(next), next.definition) !=
        LocalTournamentSessionFileStatus::Saved) {
        return error(Status::StorageFailed, "cannot archive immutable tournament");
    }
    if (save_local_tournament_session_definition(
            session_file.string(), next.definition) !=
        LocalTournamentSessionFileStatus::Saved) {
        return error(Status::StorageFailed, "cannot publish active session");
    }
    return {Status::Created, std::move(next), {}};
}

LocalTournamentCoordinatorResult restore_local_tournament_coordinator(
    const LocalTournamentCoordinatorPaths& paths,
    const std::vector<HostProfileCatalogEntry>& authoritative_catalog) {
    if (!valid_paths(paths)) {
        return error(Status::InvalidRequest, "missing host-owned storage roots");
    }
    const auto loaded = load_local_tournament_session_definition(
        active_session_path(paths), authoritative_catalog);
    if (!loaded.loaded()) {
        return error(loaded.status == LocalTournamentSessionFileStatus::Missing
                ? Status::Unavailable : Status::StorageFailed,
            "active session absent or invalid");
    }
    LocalTournamentCoordinator next{
        *loaded.session, loaded.session->empty_schedule, {}, paths,
    };
    const std::string immutable_path = archived_session_path(next);
    const auto archived = load_local_tournament_session_definition(
        immutable_path, authoritative_catalog);
    if (archived.status == LocalTournamentSessionFileStatus::Missing) {
        // Upgrade existing active sessions created before per-instance
        // archives without altering guest state or crediting any result.
        if (save_local_tournament_session_definition(
                immutable_path, next.definition) !=
            LocalTournamentSessionFileStatus::Saved) {
            return error(Status::StorageFailed, "cannot migrate active session archive");
        }
    } else if (!archived.loaded() ||
               encode_local_tournament_session_definition(*archived.session) !=
                   encode_local_tournament_session_definition(next.definition)) {
        return error(Status::EvidenceRejected,
                     "active pointer does not match archived instance plan");
    }
    // Creation always provisions this instance-owned receipts directory.
    // If it disappears, treating all fixtures as unplayed could silently
    // erase previously earned standings from the user's presentation.
    std::error_code directory_error;
    const bool receipt_directory_ok =
        fs::is_directory(receipts_directory(next), directory_error);
    if (directory_error || !receipt_directory_ok) {
        return error(Status::EvidenceRejected,
                     "active tournament receipt directory unavailable");
    }
    const auto restored = restore_saved_local_tournament_fixtures(
        receipts_directory(next), paths.multiplayer_runs_directory,
        next.definition.instance_id, next.definition.empty_schedule);
    if (!restored.restored()) {
        return error(Status::EvidenceRejected,
                     "fixture links cannot reconstruct verified standings");
    }
    next.results = *restored.state;
    // Previous-process pending checkpoint is deliberately NOT promoted to
    // a live capture, regardless of whether its fixture remains unfinished.
    return {Status::Restored, std::move(next), {}};
}

LocalTournamentCompletedHistory load_completed_local_tournament_history(
    const LocalTournamentCoordinatorPaths& paths,
    const std::vector<HostProfileCatalogEntry>& authoritative_catalog) {
    LocalTournamentCompletedHistory history;
    if (!valid_paths(paths)) return history;
    std::error_code ec;
    const fs::path root(paths.tournaments_root);
    const bool exists = fs::exists(root, ec);
    if (ec) return history;
    if (!exists) {
        history.scanned = true;
        return history;
    }
    if (!fs::is_directory(root, ec) || ec) return history;

    constexpr std::size_t kMaxArchives = 256;
    std::vector<fs::path> archive_paths;
    fs::directory_iterator it(root, ec);
    if (ec) return history;
    for (; it != fs::directory_iterator{}; it.increment(ec)) {
        if (ec) break;
        std::error_code entry_error;
        if (!it->is_directory(entry_error)) {
            if (entry_error) ++history.unavailable_instances;
            continue;
        }
        const auto instance_id = it->path().filename().string();
        if (!local_tournament_valid_instance_token(instance_id)) continue;
        if (archive_paths.size() >= kMaxArchives) {
            history.truncated = true;
            break;
        }
        archive_paths.push_back(it->path());
    }
    if (ec) return history; // do not publish a partial, successful scan
    std::sort(archive_paths.begin(), archive_paths.end());
    for (const auto& instance_root : archive_paths) {
        const std::string instance = instance_root.filename().string();
        // Historical completed events remain readable after profiles are
        // deleted/renamed. All credited fixtures still require exact stored
        // receipts and catalog-independent, authoritative saved 2P pairs.
        const auto loaded = load_historical_local_tournament_session_definition(
            (instance_root / "session.urtournament").string());
        if (!loaded.loaded() || loaded.session->instance_id != instance) {
            ++history.unavailable_instances;
            continue;
        }
        LocalTournamentCoordinator candidate{
            *loaded.session, loaded.session->empty_schedule, {}, paths,
        };
        std::error_code receipts_error;
        if (!fs::is_directory(receipts_directory(candidate), receipts_error) ||
            receipts_error) {
            ++history.unavailable_instances;
            continue;
        }
        const auto results = restore_saved_local_tournament_fixtures(
            receipts_directory(candidate), paths.multiplayer_runs_directory,
            instance, candidate.definition.empty_schedule);
        if (!results.restored()) {
            ++history.unavailable_instances;
            continue;
        }
        candidate.results = *results.state;
        if (local_tournament_coordinator_complete(candidate)) {
            history.completed.push_back(std::move(candidate));
        } else {
            ++history.incomplete_instances;
        }
    }
    history.scanned = true;
    return history;
}

LocalTournamentCoordinatorStatus arm_local_tournament_fixture(
    LocalTournamentCoordinator& session,
    std::size_t fixture_index,
    std::string_view new_capture_attempt_id,
    std::string_view confirmed_p1_profile,
    std::string_view confirmed_p2_profile) {
    if (!valid_paths(session.paths) || session.launch.pending) {
        return Status::InvalidRequest;
    }
    LocalTournamentLaunchState planned = session.launch;
    if (local_tournament_arm_fixture(
            planned, session.results, session.definition.instance_id,
            new_capture_attempt_id, fixture_index) !=
        LocalTournamentLaunchStatus::Armed ||
        !planned.pending ||
        !same_fixture_participants(
            *planned.pending, confirmed_p1_profile, confirmed_p2_profile)) {
        return Status::InvalidRequest;
    }
    // The checkpoint MUST be on disk before the guest route begins.
    if (save_local_tournament_launch_file(
            pending_path(session), *planned.pending) !=
        LocalTournamentLaunchFileStatus::Saved) {
        return Status::StorageFailed;
    }
    session.launch = std::move(planned);
    return Status::Armed;
}

std::optional<std::string> local_tournament_capture_attempt_for(
    const LocalTournamentCoordinator& session,
    std::string_view confirmed_p1_profile,
    std::string_view confirmed_p2_profile,
    std::string_view guest_observed_course_id) {
    if (!session.launch.pending ||
        !local_tournament_pending_matches_fixture(
            *session.launch.pending, session.results) ||
        session.launch.pending->tournament_id != session.definition.instance_id ||
        !same_fixture_participants(
            *session.launch.pending, confirmed_p1_profile,
            confirmed_p2_profile) ||
        session.launch.pending->course_id != guest_observed_course_id) {
        return std::nullopt;
    }
    return session.launch.pending->attempt_id;
}

LocalTournamentCoordinatorStatus commit_local_tournament_capture(
    LocalTournamentCoordinator& session,
    std::string_view live_capture_attempt_id,
    const std::string& already_published_run_path) {
    if (!session.launch.pending ||
        !local_tournament_valid_instance_token(live_capture_attempt_id) ||
        session.launch.pending->attempt_id != live_capture_attempt_id) {
        return Status::InvalidRequest;
    }
    const auto pending = *session.launch.pending;
    if (commit_saved_local_tournament_fixture(
            receipts_directory(session), session.paths.multiplayer_runs_directory,
            already_published_run_path, session.definition.instance_id,
            live_capture_attempt_id, session.launch, session.results) !=
        LocalTournamentResultLinkStatus::Committed) {
        return Status::EvidenceRejected;
    }
    // The receipt is durable and authoritative now. Retirement failures can
    // leave an inert old checkpoint, but never roll back or duplicate points.
    (void)retire_local_tournament_launch_file(
        pending_path(session), pending);
    return Status::Committed;
}

LocalTournamentCoordinatorStatus cancel_local_tournament_capture(
    LocalTournamentCoordinator& session,
    std::string_view live_capture_attempt_id) {
    if (!session.launch.pending ||
        session.launch.pending->attempt_id != live_capture_attempt_id ||
        session.launch.pending->tournament_id != session.definition.instance_id) {
        return Status::InvalidRequest;
    }
    const auto status = retire_local_tournament_launch_file(
        pending_path(session), *session.launch.pending);
    if (status != LocalTournamentLaunchFileStatus::Saved &&
        status != LocalTournamentLaunchFileStatus::Missing) {
        return Status::StorageFailed;
    }
    if (local_tournament_cancel_launch(
            session.launch, session.definition.instance_id,
            live_capture_attempt_id) != LocalTournamentLaunchStatus::Cancelled) {
        return Status::InvalidRequest;
    }
    return Status::Cancelled;
}

bool local_tournament_coordinator_complete(
    const LocalTournamentCoordinator& session) noexcept {
    return !session.results.results.empty() &&
        std::all_of(
            session.results.results.begin(), session.results.results.end(),
            [](const auto& result) { return result.has_value(); });
}

std::optional<std::size_t> local_tournament_next_unplayed_fixture(
    const LocalTournamentCoordinator& session) noexcept {
    for (std::size_t i = 0; i < session.results.results.size(); ++i) {
        if (!session.results.results[i]) return i;
    }
    return std::nullopt;
}

} // namespace ur::product

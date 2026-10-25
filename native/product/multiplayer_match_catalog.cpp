#include "multiplayer_match_catalog.hpp"
#include "local_tournament_utf8_path.hpp"

#include <algorithm>
#include <filesystem>

namespace ur::product {
namespace {

bool is_run_artifact(const std::filesystem::directory_entry& entry) {
    std::error_code ec;
    // directory_entry::is_regular_file follows links, which would silently
    // admit a different archive's run. Preserve symlinked .urrun entries
    // as unavailable evidence rather than loading them or hiding them.
    const auto status = entry.symlink_status(ec);
    if (ec) return false;
    return entry.path().extension() == ".urrun" &&
        (std::filesystem::is_regular_file(status) ||
         std::filesystem::is_symlink(status));
}

}  // namespace

std::vector<InspectedMultiplayerMatchArtifact>
inspect_multiplayer_match_artifacts(const std::string& directory,
                                   bool* scan_succeeded) {
    if (scan_succeeded) *scan_succeeded = false;
    std::vector<InspectedMultiplayerMatchArtifact> inspected;
    if (directory.empty()) return inspected;

    std::error_code ec;
    std::filesystem::directory_iterator it(host_native_path_from_utf8(directory), ec);
    if (ec) return inspected;

    std::vector<std::filesystem::path> paths;
    // A partial or failed enumeration cannot masquerade as empty history.
    // Use the error-code increment so mid-scan I/O failures also fail closed.
    const std::filesystem::directory_iterator end;
    for (; it != end; it.increment(ec)) {
        if (is_run_artifact(*it)) paths.push_back(it->path());
    }
    if (ec) return inspected;
    if (scan_succeeded) *scan_succeeded = true;
    std::sort(paths.begin(), paths.end());

    inspected.reserve(paths.size());
    for (const auto& path : paths) {
        InspectedMultiplayerMatchArtifact artifact;
        artifact.run_path = path.u8string();

        // An archive entry is only authoritative when it is a real file in
        // this directory, not a live/dangling alias outside the user root.
        std::error_code file_error;
        const auto run_status = std::filesystem::symlink_status(
            path, file_error);
        if (file_error || !std::filesystem::is_regular_file(run_status) ||
            std::filesystem::is_symlink(run_status)) {
            artifact.status = MultiplayerMatchArtifactStatus::RunUnreadable;
            artifact.detail = "run artifact is not a direct regular file";
            inspected.push_back(std::move(artifact));
            continue;
        }

        const auto run = load_completed_run_record_file(artifact.run_path);
        if (!run.loaded()) {
            artifact.status = MultiplayerMatchArtifactStatus::RunUnreadable;
            artifact.detail = run.detail;
            inspected.push_back(std::move(artifact));
            continue;
        }
        if (run.record->provenance.mode != "race-2p") {
            artifact.status = MultiplayerMatchArtifactStatus::WrongRunMode;
            artifact.detail = "completed run is not race-2p";
            inspected.push_back(std::move(artifact));
            continue;
        }

        // Sidecars must also be local direct files. A symlink to another
        // match (even one whose checksum fits) is not this run's canonical
        // sibling artifact and must not contribute to match totals.
        file_error.clear();
        const auto sidecar_path =
            multiplayer_match_record_path_for_run(artifact.run_path);
        const auto sidecar_status = std::filesystem::symlink_status(
            host_native_path_from_utf8(sidecar_path), file_error);
        if (file_error ||
            !std::filesystem::is_regular_file(sidecar_status) ||
            std::filesystem::is_symlink(sidecar_status)) {
            artifact.status =
                MultiplayerMatchArtifactStatus::MatchMissingOrUnreadable;
            artifact.detail = "match sidecar is not a direct regular file";
            inspected.push_back(std::move(artifact));
            continue;
        }
        const auto match =
            load_multiplayer_match_record_for_run(
                artifact.run_path, *run.record);
        if (!match) {
            artifact.status =
                MultiplayerMatchArtifactStatus::MatchMissingOrUnreadable;
            artifact.detail = match.error;
            inspected.push_back(std::move(artifact));
            continue;
        }

        artifact.status = MultiplayerMatchArtifactStatus::Loaded;
        artifact.stored = StoredMultiplayerMatch{
            artifact.run_path,
            *run.record,
            *match.record,
        };
        inspected.push_back(std::move(artifact));
    }
    return inspected;
}

MultiplayerMatchArtifactHealth summarize_multiplayer_match_artifact_health(
    const std::vector<InspectedMultiplayerMatchArtifact>& artifacts) {
    MultiplayerMatchArtifactHealth health;
    health.total_run_artifacts = artifacts.size();
    for (const auto& artifact : artifacts) {
        switch (artifact.status) {
        case MultiplayerMatchArtifactStatus::Loaded:
            ++health.loaded_pairs;
            break;
        case MultiplayerMatchArtifactStatus::RunUnreadable:
            ++health.unreadable_runs;
            break;
        case MultiplayerMatchArtifactStatus::WrongRunMode:
            ++health.wrong_mode_runs;
            break;
        case MultiplayerMatchArtifactStatus::MatchMissingOrUnreadable:
            ++health.unavailable_match_metadata;
            break;
        }
    }
    return health;
}

std::vector<StoredMultiplayerMatch> load_valid_multiplayer_matches(
    const std::string& directory) {
    const auto inspected = inspect_multiplayer_match_artifacts(directory);
    std::vector<StoredMultiplayerMatch> loaded;
    for (const auto& artifact : inspected) {
        if (artifact.loaded()) loaded.push_back(*artifact.stored);
    }
    return loaded;
}

std::vector<StoredMultiplayerMatch> filter_multiplayer_matches_for_profile(
    const std::vector<StoredMultiplayerMatch>& matches,
    const std::string& profile_id) {
    std::vector<StoredMultiplayerMatch> filtered;
    if (profile_id.empty()) return filtered;
    for (const auto& match : matches) {
        if (match.match.context.match.player1.profile_id == profile_id ||
            match.match.context.match.player2.profile_id == profile_id) {
            filtered.push_back(match);
        }
    }
    return filtered;
}

std::vector<StoredMultiplayerMatch> filter_multiplayer_matches_for_course(
    const std::vector<StoredMultiplayerMatch>& matches,
    const std::string& course_id) {
    std::vector<StoredMultiplayerMatch> filtered;
    if (course_id.empty()) return filtered;
    for (const auto& match : matches) {
        if (match.match.context.course_id == course_id) {
            filtered.push_back(match);
        }
    }
    return filtered;
}

}  // namespace ur::product

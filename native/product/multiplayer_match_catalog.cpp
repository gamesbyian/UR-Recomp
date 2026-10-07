#include "multiplayer_match_catalog.hpp"

#include <algorithm>
#include <filesystem>

namespace ur::product {
namespace {

bool is_run_artifact(const std::filesystem::directory_entry& entry) {
    std::error_code ec;
    if (!entry.is_regular_file(ec) || ec) return false;
    return entry.path().extension() == ".urrun";
}

}  // namespace

std::vector<InspectedMultiplayerMatchArtifact>
inspect_multiplayer_match_artifacts(const std::string& directory) {
    std::vector<InspectedMultiplayerMatchArtifact> inspected;
    if (directory.empty()) return inspected;

    std::error_code ec;
    std::filesystem::directory_iterator it(directory, ec);
    if (ec) return inspected;

    std::vector<std::filesystem::path> paths;
    for (const auto& entry : it) {
        if (is_run_artifact(entry)) paths.push_back(entry.path());
    }
    std::sort(paths.begin(), paths.end());

    inspected.reserve(paths.size());
    for (const auto& path : paths) {
        InspectedMultiplayerMatchArtifact artifact;
        artifact.run_path = path.string();

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

}  // namespace ur::product

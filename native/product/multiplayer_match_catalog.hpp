#pragma once

#include "completed_run_record.hpp"
#include "multiplayer_match_record.hpp"

#include <cstddef>
#include <optional>
#include <string>
#include <vector>

namespace ur::product {

enum class MultiplayerMatchArtifactStatus {
    Loaded = 0,
    RunUnreadable = 1,
    WrongRunMode = 2,
    MatchMissingOrUnreadable = 3,
};

struct StoredMultiplayerMatch {
    std::string run_path;
    CompletedRunRecord run;
    MultiplayerMatchRecord match;
};

struct InspectedMultiplayerMatchArtifact {
    std::string run_path;
    MultiplayerMatchArtifactStatus status =
        MultiplayerMatchArtifactStatus::RunUnreadable;
    std::string detail;
    std::optional<StoredMultiplayerMatch> stored;

    bool loaded() const noexcept {
        return status == MultiplayerMatchArtifactStatus::Loaded &&
               stored.has_value();
    }
};

struct MultiplayerMatchArtifactHealth {
    std::size_t total_run_artifacts = 0;
    std::size_t loaded_pairs = 0;
    std::size_t unreadable_runs = 0;
    std::size_t wrong_mode_runs = 0;
    std::size_t unavailable_match_metadata = 0;

    std::size_t unavailable_pairs() const noexcept {
        return total_run_artifacts - loaded_pairs;
    }
};

/*
 * Inspect the shared multiplayer-runs namespace without promoting standalone
 * .urrun files or malformed/missing sidecars into multiplayer history.
 *
 * Filename order is host storage order only. Match/result authority remains
 * the validated run+sidecar pair.
 */
std::vector<InspectedMultiplayerMatchArtifact>
inspect_multiplayer_match_artifacts(const std::string& directory);

MultiplayerMatchArtifactHealth summarize_multiplayer_match_artifact_health(
    const std::vector<InspectedMultiplayerMatchArtifact>& artifacts);

/* Return only fully validated race-2p run+match pairs in storage order. */
std::vector<StoredMultiplayerMatch> load_valid_multiplayer_matches(
    const std::string& directory);

/* Query only already-admitted pairs. These helpers do not compute standings. */
std::vector<StoredMultiplayerMatch> filter_multiplayer_matches_for_profile(
    const std::vector<StoredMultiplayerMatch>& matches,
    const std::string& profile_id);

std::vector<StoredMultiplayerMatch> filter_multiplayer_matches_for_course(
    const std::vector<StoredMultiplayerMatch>& matches,
    const std::string& course_id);

}  // namespace ur::product

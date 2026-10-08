#include "multiplayer_match_summary.hpp"

#include <algorithm>
#include <cctype>
#include <cstdio>
#include <map>
#include <utility>

namespace ur::product {
namespace {

using ur::title::OrdinaryTwoPlayerRaceOutcome;

// Same case-insensitive storage identity the match binder enforces.
std::string storage_identity(const std::string& profile_id) {
    std::string key = profile_id;
    for (char& ch : key) {
        ch = static_cast<char>(
            std::tolower(static_cast<unsigned char>(ch)));
    }
    return key;
}

}  // namespace

MultiplayerMatchSummary summarize_multiplayer_matches(
    const std::vector<StoredMultiplayerMatch>& matches) {
    MultiplayerMatchSummary summary;
    std::map<std::string, MultiplayerProfileMatchRecord> profiles;
    std::map<std::pair<std::string, std::string>, MultiplayerHeadToHeadRecord>
        rivalries;

    for (const auto& stored : matches) {
        const auto& match = stored.match.context.match;
        const std::string key1 = storage_identity(match.player1.profile_id);
        const std::string key2 = storage_identity(match.player2.profile_id);
        if (key1.empty() || key2.empty() || key1 == key2) {
            ++summary.ignored_matches;
            continue;
        }
        ++summary.matches;

        const auto outcome = match.result.outcome;
        auto record = [&](const HostProfileCatalogEntry& participant,
                          const std::string& key,
                          OrdinaryTwoPlayerRaceOutcome win) {
            auto& entry = profiles[key];
            // Storage order is chronological, so the latest spelling wins.
            entry.profile_id = participant.profile_id;
            entry.racer_name = participant.identity.name;
            ++entry.played;
            if (outcome == OrdinaryTwoPlayerRaceOutcome::Draw) {
                ++entry.draws;
            } else if (outcome == win) {
                ++entry.wins;
            } else {
                ++entry.losses;
            }
        };
        record(match.player1, key1, OrdinaryTwoPlayerRaceOutcome::Player1Win);
        record(match.player2, key2, OrdinaryTwoPlayerRaceOutcome::Player2Win);

        const bool player1_first = key1 < key2;
        auto& rivalry = rivalries[player1_first
            ? std::make_pair(key1, key2)
            : std::make_pair(key2, key1)];
        rivalry.first_profile_id = player1_first
            ? match.player1.profile_id : match.player2.profile_id;
        rivalry.second_profile_id = player1_first
            ? match.player2.profile_id : match.player1.profile_id;
        ++rivalry.played;
        if (outcome == OrdinaryTwoPlayerRaceOutcome::Draw) {
            ++rivalry.draws;
        } else if ((outcome == OrdinaryTwoPlayerRaceOutcome::Player1Win) ==
                   player1_first) {
            ++rivalry.first_wins;
        } else {
            ++rivalry.second_wins;
        }
    }

    summary.profiles.reserve(profiles.size());
    for (auto& [key, entry] : profiles) {
        (void)key;
        summary.profiles.push_back(std::move(entry));
    }
    summary.head_to_head.reserve(rivalries.size());
    for (auto& [key, entry] : rivalries) {
        (void)key;
        summary.head_to_head.push_back(std::move(entry));
    }
    return summary;
}

const MultiplayerProfileMatchRecord* find_multiplayer_profile_record(
    const MultiplayerMatchSummary& summary,
    const std::string& profile_id) noexcept {
    const std::string key = storage_identity(profile_id);
    for (const auto& entry : summary.profiles) {
        if (storage_identity(entry.profile_id) == key) return &entry;
    }
    return nullptr;
}

std::optional<MultiplayerMatchHeadToHead> multiplayer_head_to_head_for_match(
    const MultiplayerMatchSummary& summary,
    const StoredMultiplayerMatch& match) {
    const std::string key1 =
        storage_identity(match.match.context.match.player1.profile_id);
    const std::string key2 =
        storage_identity(match.match.context.match.player2.profile_id);
    if (key1.empty() || key2.empty() || key1 == key2) return std::nullopt;
    const bool player1_first = key1 < key2;
    const std::string& first = player1_first ? key1 : key2;
    const std::string& second = player1_first ? key2 : key1;
    for (const auto& rivalry : summary.head_to_head) {
        if (storage_identity(rivalry.first_profile_id) != first ||
            storage_identity(rivalry.second_profile_id) != second) {
            continue;
        }
        MultiplayerMatchHeadToHead oriented;
        oriented.played = rivalry.played;
        oriented.draws = rivalry.draws;
        oriented.player1_wins =
            player1_first ? rivalry.first_wins : rivalry.second_wins;
        oriented.player2_wins =
            player1_first ? rivalry.second_wins : rivalry.first_wins;
        return oriented;
    }
    return std::nullopt;
}

std::string format_multiplayer_head_to_head(
    const MultiplayerMatchHeadToHead& head_to_head) {
    char text[64];
    std::snprintf(
        text, sizeof(text), "P1 %zu  P2 %zu  DRAW %zu",
        head_to_head.player1_wins,
        head_to_head.player2_wins,
        head_to_head.draws);
    return text;
}

}  // namespace ur::product

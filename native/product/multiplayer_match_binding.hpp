#pragma once

#include "host_profile_catalog.hpp"
#include "modern_racer_identity.hpp"
#include "uniracers_two_player_result.hpp"

#include <optional>
#include <string>

namespace ur::product {

struct MultiplayerMatchParticipant {
    std::optional<std::string> profile_id;
    HostRacerIdentity racer;

    bool operator==(const MultiplayerMatchParticipant& other) const noexcept {
        return profile_id == other.profile_id && racer == other.racer;
    }
};

struct BoundOrdinaryTwoPlayerRaceMatch {
    std::string course_id;
    ur::title::OrdinaryTwoPlayerRaceResult result;
    MultiplayerMatchParticipant player1;
    MultiplayerMatchParticipant player2;
};

/*
 * Bind authoritative stock result/rider identity to Modern participant
 * identity without treating controller/device identity as player identity.
 *
 * A supplied profile must agree with the stock rider used in the observed
 * match. A missing profile means an explicit local guest whose racer identity
 * is the exact legacy preset selected by the guest.
 */
std::optional<BoundOrdinaryTwoPlayerRaceMatch>
bind_ordinary_two_player_race_match(
    const ur::title::OrdinaryTwoPlayerRaceResult& result,
    const std::string& course_id,
    const std::optional<HostProfileCatalogEntry>& player1_profile,
    const std::optional<HostProfileCatalogEntry>& player2_profile);

}  // namespace ur::product

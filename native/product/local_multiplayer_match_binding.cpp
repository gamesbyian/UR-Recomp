#include "local_multiplayer_match_binding.hpp"

namespace ur::product {

LocalMultiplayerMatchBindingResult bind_local_multiplayer_match(
    const ur::title::OrdinaryTwoPlayerRaceResult& result,
    const HostProfileCatalogEntry& player1,
    const HostProfileCatalogEntry& player2) noexcept {
    if (player1.profile_id.empty() || player2.profile_id.empty()) {
        return {
            LocalMultiplayerMatchBindingStatus::MissingProfileIdentity,
            std::nullopt,
        };
    }
    if (player1.profile_id == player2.profile_id) {
        return {
            LocalMultiplayerMatchBindingStatus::DuplicateProfileIdentity,
            std::nullopt,
        };
    }
    if (!valid_racer_identity(player1.identity) ||
        !valid_racer_identity(player2.identity)) {
        return {
            LocalMultiplayerMatchBindingStatus::InvalidRacerIdentity,
            std::nullopt,
        };
    }
    if (player1.identity.rider_index != result.player1_rider ||
        player2.identity.rider_index != result.player2_rider) {
        return {
            LocalMultiplayerMatchBindingStatus::RiderMismatch,
            std::nullopt,
        };
    }

    return {
        LocalMultiplayerMatchBindingStatus::Bound,
        BoundOrdinaryTwoPlayerMatch{player1, player2, result},
    };
}

}  // namespace ur::product

#pragma once

#include "host_profile_catalog.hpp"
#include "uniracers_two_player_result.hpp"

#include <cstdint>
#include <optional>

namespace ur::product {

enum class LocalMultiplayerMatchBindingStatus : std::uint8_t {
    Bound = 0,
    MissingProfileIdentity = 1,
    DuplicateProfileIdentity = 2,
    InvalidRacerIdentity = 3,
    RiderMismatch = 4,
};

struct BoundOrdinaryTwoPlayerMatch {
    HostProfileCatalogEntry player1;
    HostProfileCatalogEntry player2;
    ur::title::OrdinaryTwoPlayerRaceResult result;
};

struct LocalMultiplayerMatchBindingResult {
    LocalMultiplayerMatchBindingStatus status =
        LocalMultiplayerMatchBindingStatus::MissingProfileIdentity;
    std::optional<BoundOrdinaryTwoPlayerMatch> match;

    bool bound() const noexcept {
        return status == LocalMultiplayerMatchBindingStatus::Bound &&
               match.has_value();
    }
};

/*
 * Bind one authoritative stock ordinary-2P result to explicit Modern profile
 * identities supplied by the session layer.
 *
 * This function does not infer identity from controller seats, active profile,
 * result time, filenames, input masks or rider names. The supplied profile
 * entries must be distinct, valid and must agree with the stock rider indices
 * observed at the result surface. It writes no guest or persistent state.
 */
LocalMultiplayerMatchBindingResult bind_local_multiplayer_match(
    const ur::title::OrdinaryTwoPlayerRaceResult& result,
    const HostProfileCatalogEntry& player1,
    const HostProfileCatalogEntry& player2) noexcept;

}  // namespace ur::product

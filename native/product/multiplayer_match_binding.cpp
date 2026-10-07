#include "multiplayer_match_binding.hpp"

namespace ur::product {
namespace {

std::optional<MultiplayerMatchParticipant> bind_participant(
    std::uint8_t rider,
    const std::optional<HostProfileCatalogEntry>& profile) {
    if (profile) {
        if (profile->profile_id.empty() ||
            !valid_racer_identity(profile->identity) ||
            profile->identity.rider_index != rider) {
            return std::nullopt;
        }
        return MultiplayerMatchParticipant{
            profile->profile_id,
            profile->identity,
        };
    }

    const auto legacy = make_legacy_racer_identity(rider);
    if (!legacy) return std::nullopt;
    return MultiplayerMatchParticipant{std::nullopt, *legacy};
}

}  // namespace

std::optional<BoundOrdinaryTwoPlayerRaceMatch>
bind_ordinary_two_player_race_match(
    const ur::title::OrdinaryTwoPlayerRaceResult& result,
    const std::string& course_id,
    const std::optional<HostProfileCatalogEntry>& player1_profile,
    const std::optional<HostProfileCatalogEntry>& player2_profile) {
    if (course_id.empty()) return std::nullopt;

    const auto p1 = bind_participant(result.player1_rider, player1_profile);
    const auto p2 = bind_participant(result.player2_rider, player2_profile);
    if (!p1 || !p2) return std::nullopt;

    if (p1->profile_id && p2->profile_id &&
        *p1->profile_id == *p2->profile_id) {
        return std::nullopt;
    }

    return BoundOrdinaryTwoPlayerRaceMatch{
        course_id,
        result,
        *p1,
        *p2,
    };
}

}  // namespace ur::product

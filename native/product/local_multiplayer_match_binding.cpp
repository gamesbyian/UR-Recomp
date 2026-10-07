#include "local_multiplayer_match_binding.hpp"

#include "host_profile_runtime.hpp"

#include <cctype>
#include <cstdio>
#include <string_view>

namespace ur::product {
namespace {

bool same_profile_storage_identity(
    std::string_view lhs,
    std::string_view rhs) noexcept {
    if (lhs.size() != rhs.size()) return false;
    for (std::size_t i = 0; i < lhs.size(); ++i) {
        const unsigned char a = static_cast<unsigned char>(lhs[i]);
        const unsigned char b = static_cast<unsigned char>(rhs[i]);
        if (std::tolower(a) != std::tolower(b)) return false;
    }
    return true;
}

}  // namespace

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
    if (!is_safe_profile_storage_id(player1.profile_id) ||
        !is_safe_profile_storage_id(player2.profile_id)) {
        return {
            LocalMultiplayerMatchBindingStatus::InvalidProfileIdentity,
            std::nullopt,
        };
    }
    if (same_profile_storage_identity(
            player1.profile_id, player2.profile_id)) {
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

LocalMultiplayerMatchContextResult bind_local_multiplayer_match_context(
    const ur::title::OrdinaryTwoPlayerRaceResult& result,
    const HostProfileCatalogEntry& player1,
    const HostProfileCatalogEntry& player2,
    UrUniracersCourseIdentity course) noexcept {
    const auto participants =
        bind_local_multiplayer_match(result, player1, player2);
    if (!participants.bound()) {
        return {
            LocalMultiplayerMatchContextStatus::ParticipantBindingRejected,
            participants.status,
            std::nullopt,
        };
    }

    if (!course.valid || course.course_index < 1 || course.course_index > 45) {
        return {
            LocalMultiplayerMatchContextStatus::InvalidCourseIdentity,
            participants.status,
            std::nullopt,
        };
    }

    char course_id[16];
    const int written = std::snprintf(
        course_id, sizeof(course_id), "course:%02d", course.course_index);
    if (written <= 0 ||
        written >= static_cast<int>(sizeof(course_id))) {
        return {
            LocalMultiplayerMatchContextStatus::InvalidCourseIdentity,
            participants.status,
            std::nullopt,
        };
    }

    return {
        LocalMultiplayerMatchContextStatus::Bound,
        participants.status,
        BoundOrdinaryTwoPlayerMatchContext{
            *participants.match,
            std::string(course_id),
        },
    };
}

}  // namespace ur::product

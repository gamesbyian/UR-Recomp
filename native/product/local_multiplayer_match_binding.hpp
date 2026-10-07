#pragma once

#include "host_profile_catalog.hpp"
#include "uniracers_two_player_result.hpp"
#include "uniracers_course_identity.h"

#include <cstdint>
#include <optional>
#include <string>

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

struct BoundOrdinaryTwoPlayerMatchContext {
    BoundOrdinaryTwoPlayerMatch match;
    std::string course_id;
};

enum class LocalMultiplayerMatchContextStatus : std::uint8_t {
    Bound = 0,
    ParticipantBindingRejected = 1,
    InvalidCourseIdentity = 2,
};

struct LocalMultiplayerMatchContextResult {
    LocalMultiplayerMatchContextStatus status =
        LocalMultiplayerMatchContextStatus::ParticipantBindingRejected;
    LocalMultiplayerMatchBindingStatus participant_status =
        LocalMultiplayerMatchBindingStatus::MissingProfileIdentity;
    std::optional<BoundOrdinaryTwoPlayerMatchContext> context;

    bool bound() const noexcept {
        return status == LocalMultiplayerMatchContextStatus::Bound &&
               context.has_value();
    }
};

/*
 * Extend the participant-bound ordinary-2P result with the canonical course
 * identity observed from the title's decoded-course header. The course string
 * deliberately reuses the completed-run namespace: course:01 .. course:45.
 */
LocalMultiplayerMatchContextResult bind_local_multiplayer_match_context(
    const ur::title::OrdinaryTwoPlayerRaceResult& result,
    const HostProfileCatalogEntry& player1,
    const HostProfileCatalogEntry& player2,
    UrUniracersCourseIdentity course) noexcept;

}  // namespace ur::product

#pragma once

#include "host_profile_catalog.hpp"
#include "local_multiplayer_setup.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace ur::product {

enum class LocalMultiplayerParticipantStatus : std::uint8_t {
    Applied = 0,
    InvalidProfile = 1,
    DuplicateProfile = 2,
    SlotUnjoined = 3,
    NoProfiles = 4,
};

struct LocalMultiplayerParticipantSelection {
    std::optional<HostProfileCatalogEntry> player1;
    std::optional<HostProfileCatalogEntry> player2;
    std::size_t player1_cursor = 0;
    std::size_t player2_cursor = 0;
};

struct LocalMultiplayerParticipantResult {
    LocalMultiplayerParticipantSelection state;
    LocalMultiplayerParticipantStatus status =
        LocalMultiplayerParticipantStatus::Applied;
    LocalMultiplayerSlot slot = LocalMultiplayerSlot::Player1;

    bool applied() const noexcept {
        return status == LocalMultiplayerParticipantStatus::Applied;
    }
};

const std::optional<HostProfileCatalogEntry>&
local_multiplayer_participant(
    const LocalMultiplayerParticipantSelection& state,
    LocalMultiplayerSlot slot) noexcept;

bool local_multiplayer_participants_ready(
    const LocalMultiplayerSetupState& devices,
    const LocalMultiplayerParticipantSelection& participants) noexcept;

/*
 * Select one explicit profile for an already-joined local multiplayer slot.
 * Device identity and participant identity stay independent: joining a
 * controller never chooses a profile, and choosing a profile never changes
 * controller ownership.
 */
LocalMultiplayerParticipantResult local_multiplayer_select_profile(
    LocalMultiplayerParticipantSelection state,
    const LocalMultiplayerSetupState& devices,
    LocalMultiplayerSlot slot,
    const HostProfileCatalogEntry& profile) noexcept;

LocalMultiplayerParticipantResult local_multiplayer_clear_profile(
    LocalMultiplayerParticipantSelection state,
    LocalMultiplayerSlot slot) noexcept;

/*
 * Move a slot's profile cursor through the authoritative catalog. This only
 * changes the highlighted candidate; confirm remains an explicit selection.
 */
LocalMultiplayerParticipantResult local_multiplayer_move_profile_cursor(
    LocalMultiplayerParticipantSelection state,
    const std::vector<HostProfileCatalogEntry>& catalog,
    LocalMultiplayerSlot slot,
    int delta) noexcept;

const HostProfileCatalogEntry* local_multiplayer_profile_candidate(
    const LocalMultiplayerParticipantSelection& state,
    const std::vector<HostProfileCatalogEntry>& catalog,
    LocalMultiplayerSlot slot) noexcept;

}  // namespace ur::product

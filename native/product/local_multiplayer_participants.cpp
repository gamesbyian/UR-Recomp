#include "local_multiplayer_participants.hpp"

namespace ur::product {
namespace {

std::optional<HostProfileCatalogEntry>& participant(
    LocalMultiplayerParticipantSelection& state,
    LocalMultiplayerSlot slot) noexcept {
    return slot == LocalMultiplayerSlot::Player1
        ? state.player1
        : state.player2;
}

std::size_t& cursor(
    LocalMultiplayerParticipantSelection& state,
    LocalMultiplayerSlot slot) noexcept {
    return slot == LocalMultiplayerSlot::Player1
        ? state.player1_cursor
        : state.player2_cursor;
}

bool slot_joined(
    const LocalMultiplayerSetupState& devices,
    LocalMultiplayerSlot slot) noexcept {
    return local_multiplayer_assignment(devices, slot).assigned &&
           local_multiplayer_source_valid(
               local_multiplayer_assignment(devices, slot).source);
}

const std::optional<HostProfileCatalogEntry>& other_participant(
    const LocalMultiplayerParticipantSelection& state,
    LocalMultiplayerSlot slot) noexcept {
    return slot == LocalMultiplayerSlot::Player1
        ? state.player2
        : state.player1;
}

}  // namespace

const std::optional<HostProfileCatalogEntry>&
local_multiplayer_participant(
    const LocalMultiplayerParticipantSelection& state,
    LocalMultiplayerSlot slot) noexcept {
    return slot == LocalMultiplayerSlot::Player1
        ? state.player1
        : state.player2;
}

bool local_multiplayer_participants_ready(
    const LocalMultiplayerSetupState& devices,
    const LocalMultiplayerParticipantSelection& participants) noexcept {
    if (!local_multiplayer_launch_eligible(devices) ||
        !participants.player1 || !participants.player2) {
        return false;
    }
    if (participants.player1->profile_id.empty() ||
        participants.player2->profile_id.empty() ||
        participants.player1->profile_id == participants.player2->profile_id) {
        return false;
    }
    return valid_racer_identity(participants.player1->identity) &&
           valid_racer_identity(participants.player2->identity);
}

LocalMultiplayerParticipantResult local_multiplayer_select_profile(
    LocalMultiplayerParticipantSelection state,
    const LocalMultiplayerSetupState& devices,
    LocalMultiplayerSlot slot,
    const HostProfileCatalogEntry& profile) noexcept {
    if (!slot_joined(devices, slot)) {
        return {
            state,
            LocalMultiplayerParticipantStatus::SlotUnjoined,
            slot,
        };
    }
    if (profile.profile_id.empty() ||
        !valid_racer_identity(profile.identity)) {
        return {
            state,
            LocalMultiplayerParticipantStatus::InvalidProfile,
            slot,
        };
    }
    const auto& other = other_participant(state, slot);
    if (other && other->profile_id == profile.profile_id) {
        return {
            state,
            LocalMultiplayerParticipantStatus::DuplicateProfile,
            slot,
        };
    }

    participant(state, slot) = profile;
    return {state, LocalMultiplayerParticipantStatus::Applied, slot};
}

LocalMultiplayerParticipantResult local_multiplayer_clear_profile(
    LocalMultiplayerParticipantSelection state,
    LocalMultiplayerSlot slot) noexcept {
    participant(state, slot).reset();
    return {state, LocalMultiplayerParticipantStatus::Applied, slot};
}

LocalMultiplayerParticipantResult local_multiplayer_move_profile_cursor(
    LocalMultiplayerParticipantSelection state,
    const std::vector<HostProfileCatalogEntry>& catalog,
    LocalMultiplayerSlot slot,
    int delta) noexcept {
    if (catalog.empty()) {
        return {
            state,
            LocalMultiplayerParticipantStatus::NoProfiles,
            slot,
        };
    }
    if (delta == 0) {
        return {state, LocalMultiplayerParticipantStatus::Applied, slot};
    }

    std::size_t& index = cursor(state, slot);
    if (index >= catalog.size()) index = 0;
    if (delta > 0) {
        index = (index + 1u) % catalog.size();
    } else {
        index = index == 0 ? catalog.size() - 1u : index - 1u;
    }
    return {state, LocalMultiplayerParticipantStatus::Applied, slot};
}

const HostProfileCatalogEntry* local_multiplayer_profile_candidate(
    const LocalMultiplayerParticipantSelection& state,
    const std::vector<HostProfileCatalogEntry>& catalog,
    LocalMultiplayerSlot slot) noexcept {
    if (catalog.empty()) return nullptr;
    std::size_t index = slot == LocalMultiplayerSlot::Player1
        ? state.player1_cursor
        : state.player2_cursor;
    if (index >= catalog.size()) index = 0;
    return &catalog[index];
}

}  // namespace ur::product

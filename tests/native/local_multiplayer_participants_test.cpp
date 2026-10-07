#include "local_multiplayer_participants.hpp"

#include <cassert>
#include <vector>

using namespace ur::product;

namespace {

HostProfileCatalogEntry profile(
    const char* id,
    const char* name,
    std::uint8_t rider) {
    return {id, HostRacerIdentity{name, rider}};
}

LocalMultiplayerSetupState joined_devices() {
    LocalMultiplayerSetupState state;
    state.player1 = {
        true,
        {LocalInputKind::Keyboard, 1, true},
    };
    state.player2 = {
        true,
        {LocalInputKind::Controller, 2, true},
    };
    return state;
}

}  // namespace

int main() {
    const auto ian = profile("ian", "MIKE", 0);
    const auto friend_profile = profile("friend", "ANDREW", 1);
    const auto third = profile("third", "MARTIN", 2);
    const std::vector<HostProfileCatalogEntry> catalog{
        ian, friend_profile, third};

    auto participants = LocalMultiplayerParticipantSelection{};

    // Joining devices never manufactures participant identity.
    assert(!local_multiplayer_participants_ready(
        joined_devices(), participants));

    auto p1 = local_multiplayer_select_profile(
        participants,
        joined_devices(),
        LocalMultiplayerSlot::Player1,
        ian);
    assert(p1.applied());
    participants = p1.state;
    assert(participants.player1);
    assert(participants.player1->profile_id == "ian");
    assert(!participants.player2);

    // The same profile cannot own both participants.
    auto duplicate = local_multiplayer_select_profile(
        participants,
        joined_devices(),
        LocalMultiplayerSlot::Player2,
        ian);
    assert(!duplicate.applied());
    assert(duplicate.status ==
           LocalMultiplayerParticipantStatus::DuplicateProfile);
    assert(!duplicate.state.player2);

    const auto case_alias = profile("IAN", "ANDREW", 1);
    auto case_duplicate = local_multiplayer_select_profile(
        participants,
        joined_devices(),
        LocalMultiplayerSlot::Player2,
        case_alias);
    assert(!case_duplicate.applied());
    assert(case_duplicate.status ==
           LocalMultiplayerParticipantStatus::DuplicateProfile);

    auto p2 = local_multiplayer_select_profile(
        participants,
        joined_devices(),
        LocalMultiplayerSlot::Player2,
        friend_profile);
    assert(p2.applied());
    participants = p2.state;
    assert(local_multiplayer_participants_ready(
        joined_devices(), participants));

    // Selection is refused for a slot that has no usable input source.
    auto missing_device = joined_devices();
    missing_device.player2.source.connected = false;
    const auto rejected = local_multiplayer_select_profile(
        participants,
        missing_device,
        LocalMultiplayerSlot::Player2,
        third);
    assert(!rejected.applied());
    assert(rejected.status ==
           LocalMultiplayerParticipantStatus::SlotUnjoined);

    // Cursor movement is independent from confirmed participant identity.
    const auto moved = local_multiplayer_move_profile_cursor(
        participants,
        catalog,
        LocalMultiplayerSlot::Player2,
        1);
    assert(moved.applied());
    assert(moved.state.player2);
    assert(moved.state.player2->profile_id == "friend");
    const auto* candidate = local_multiplayer_profile_candidate(
        moved.state, catalog, LocalMultiplayerSlot::Player2);
    assert(candidate);
    assert(candidate->profile_id == "friend");

    auto moved_again = local_multiplayer_move_profile_cursor(
        moved.state,
        catalog,
        LocalMultiplayerSlot::Player2,
        1);
    const auto* next_candidate = local_multiplayer_profile_candidate(
        moved_again.state, catalog, LocalMultiplayerSlot::Player2);
    assert(next_candidate);
    assert(next_candidate->profile_id == "third");

    auto cleared = local_multiplayer_clear_profile(
        participants, LocalMultiplayerSlot::Player2);
    assert(cleared.applied());
    assert(!cleared.state.player2);
    assert(!local_multiplayer_participants_ready(
        joined_devices(), cleared.state));

    HostProfileCatalogEntry invalid{"CON", HostRacerIdentity{"MIKE", 0}};
    auto invalid_result = local_multiplayer_select_profile(
        participants,
        joined_devices(),
        LocalMultiplayerSlot::Player2,
        invalid);
    assert(!invalid_result.applied());
    assert(invalid_result.status ==
           LocalMultiplayerParticipantStatus::InvalidProfile);

    const std::vector<HostProfileCatalogEntry> empty;
    auto no_profiles = local_multiplayer_move_profile_cursor(
        participants, empty, LocalMultiplayerSlot::Player1, 1);
    assert(!no_profiles.applied());
    assert(no_profiles.status ==
           LocalMultiplayerParticipantStatus::NoProfiles);

    return 0;
}

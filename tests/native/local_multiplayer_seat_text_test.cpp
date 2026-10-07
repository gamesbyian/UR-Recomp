#include "local_multiplayer_seat_text.hpp"

#include <cassert>
#include <string>

int main() {
    using ur::product::LocalInputKind;
    using ur::product::LocalInputSource;
    using ur::product::LocalMultiplayerSeatPresentation;
    using ur::product::LocalMultiplayerSetupState;
    using ur::product::LocalMultiplayerSlot;
    using ur::product::local_multiplayer_assign;
    using ur::product::local_multiplayer_seat_device_text;
    using ur::product::local_multiplayer_seat_presentation;
    using ur::product::local_multiplayer_set_connected;

    // An empty seat has no device line.
    LocalMultiplayerSetupState state{};
    assert(local_multiplayer_seat_device_text(
               local_multiplayer_seat_presentation(
                   state, LocalMultiplayerSlot::Player2),
               "IGNORED")
               .empty());

    // A joined controller shows its sanitized framework name, or a generic
    // label when the device reports none.
    const LocalInputSource pad{LocalInputKind::Controller, 7u, true};
    state = local_multiplayer_assign(state, LocalMultiplayerSlot::Player2, pad)
                .state;
    const auto joined = local_multiplayer_seat_presentation(
        state, LocalMultiplayerSlot::Player2);
    assert(local_multiplayer_seat_device_text(joined, "XBOX 360 CONTROLLER") ==
           std::string("PAD XBOX 360 CONTROLLER"));
    assert(local_multiplayer_seat_device_text(joined, "") ==
           std::string("CONTROLLER"));

    // Disconnect is reported from the projection, never from the stale name.
    state = local_multiplayer_set_connected(state, pad, false);
    assert(local_multiplayer_seat_device_text(
               local_multiplayer_seat_presentation(
                   state, LocalMultiplayerSlot::Player2),
               "XBOX 360 CONTROLLER") ==
           std::string("CONTROLLER DISCONNECTED"));

    // Keyboard can occupy P1 only through the explicit keyboard source.
    const LocalInputSource keyboard{LocalInputKind::Keyboard, 1u, true};
    state = local_multiplayer_assign(
                state, LocalMultiplayerSlot::Player1, keyboard)
                .state;
    assert(local_multiplayer_seat_device_text(
               local_multiplayer_seat_presentation(
                   state, LocalMultiplayerSlot::Player1),
               "IGNORED") == std::string("KEYBOARD"));
    assert(local_multiplayer_seat_device_text(
               LocalMultiplayerSeatPresentation::KeyboardDisconnected, "") ==
           std::string("KEYBOARD DISCONNECTED"));

    // Participant rows always fit the 28-cell panel; the racer name stays
    // whole and the profile id is truncated first.
    using ur::product::LocalMultiplayerParticipantRowState;
    using ur::product::local_multiplayer_participant_row_text;
    assert(local_multiplayer_participant_row_text(
               "P1", LocalMultiplayerParticipantRowState::NotJoined, "", "",
               28) == std::string("P1 PRESS A / START"));
    assert(local_multiplayer_participant_row_text(
               "P2", LocalMultiplayerParticipantRowState::NoProfiles, "", "",
               28) == std::string("P2 NO PROFILES"));
    assert(local_multiplayer_participant_row_text(
               "P1", LocalMultiplayerParticipantRowState::Choosing, "MIKE",
               "join.alpha", 28) == std::string("P1 <MIKE> join.alpha"));
    assert(local_multiplayer_participant_row_text(
               "P2", LocalMultiplayerParticipantRowState::Ready, "ANNA",
               "join.bravo", 28) == std::string("P2 READY ANNA join.bravo"));
    const std::string long_id(40, 'x');
    const std::string sixteen = "ABCDEFGHIJKLMNOP";
    const auto choosing = local_multiplayer_participant_row_text(
        "P1", LocalMultiplayerParticipantRowState::Choosing, sixteen, long_id,
        28);
    assert(choosing.size() == 28u);
    assert(choosing.find("<" + sixteen + ">") == 3u);
    const auto ready = local_multiplayer_participant_row_text(
        "P2", LocalMultiplayerParticipantRowState::Ready, sixteen, long_id, 28);
    assert(ready.size() <= 28u);
    assert(ready.find("READY " + sixteen) == 3u);
    // No room for even one id character: the id is omitted, not squeezed.
    assert(local_multiplayer_participant_row_text(
               "P2", LocalMultiplayerParticipantRowState::Ready, sixteen,
               "id", 25) == "P2 READY " + sixteen);
    return 0;
}

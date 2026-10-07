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
    return 0;
}

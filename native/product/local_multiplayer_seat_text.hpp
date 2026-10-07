#pragma once

#include "local_multiplayer_setup.hpp"

#include <string>
#include <string_view>

namespace ur::product {

// Player-facing device line for one local multiplayer seat on the Modern 2P
// join surface. It reads only the presentation-safe seat projection plus the
// host's already-sanitized framework device name, so the overlay never shows
// opaque source IDs and never reinterprets assignment state itself. An empty
// seat has no device line; its row already says how to join.
inline std::string local_multiplayer_seat_device_text(
    LocalMultiplayerSeatPresentation presentation,
    std::string_view device_name) {
    switch (presentation) {
    case LocalMultiplayerSeatPresentation::Empty:
        return {};
    case LocalMultiplayerSeatPresentation::KeyboardConnected:
        return "KEYBOARD";
    case LocalMultiplayerSeatPresentation::KeyboardDisconnected:
        return "KEYBOARD DISCONNECTED";
    case LocalMultiplayerSeatPresentation::ControllerConnected:
        return device_name.empty() ? std::string("CONTROLLER")
                                   : "PAD " + std::string(device_name);
    case LocalMultiplayerSeatPresentation::ControllerDisconnected:
    default:
        return "CONTROLLER DISCONNECTED";
    }
}

}  // namespace ur::product

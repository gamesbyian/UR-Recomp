#pragma once

#include "local_multiplayer_setup.hpp"

#include <cstdint>

#include <cstddef>
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

// One participant row on the join surface, fitted to `max_chars` overlay
// cells (the panel is 28 cells wide on a 256-pixel frame). The racer name is
// kept whole because the player must pick that rider in the stock picker; the
// profile id fills whatever width remains and is truncated first.
enum class LocalMultiplayerParticipantRowState : std::uint8_t {
    NotJoined,
    NoProfiles,
    Choosing,
    Ready,
};

inline std::string local_multiplayer_participant_row_text(
    std::string_view slot_label,
    LocalMultiplayerParticipantRowState state,
    std::string_view racer_name,
    std::string_view profile_id,
    std::size_t max_chars) {
    std::string row(slot_label);
    switch (state) {
    case LocalMultiplayerParticipantRowState::NotJoined:
        row += " PRESS A / START";
        break;
    case LocalMultiplayerParticipantRowState::NoProfiles:
        row += " NO PROFILES";
        break;
    case LocalMultiplayerParticipantRowState::Choosing:
        row += " <";
        row += racer_name;
        row += ">";
        break;
    case LocalMultiplayerParticipantRowState::Ready:
        row += " READY ";
        row += racer_name;
        break;
    }
    const bool with_id =
        state == LocalMultiplayerParticipantRowState::Choosing ||
        state == LocalMultiplayerParticipantRowState::Ready;
    if (with_id && !profile_id.empty() && row.size() + 2u <= max_chars) {
        row += ' ';
        row += profile_id.substr(0, max_chars - row.size());
    }
    if (row.size() > max_chars) row.resize(max_chars);
    return row;
}

}  // namespace ur::product

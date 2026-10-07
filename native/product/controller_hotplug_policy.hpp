#pragma once

#include "host_product_state.hpp"

#include <array>
#include <cstddef>
#include <cstdint>

namespace ur::product {

// Session-local view of SNESRecomp's two framework controller seats. The
// framework owns device discovery, seat assignment, GamepadMap bindings and
// polling; this model only remembers which opaque source currently occupies a
// seat so Modern can explain a disconnect and pause safely. It never chooses a
// seat, never persists and never writes guest input.
inline constexpr std::size_t kControllerSeatCount = 2;

struct ControllerSeat {
    bool connected = false;
    std::uint64_t source_id = 0;
};

enum class ControllerSeatNotice : std::uint8_t {
    None,
    Disconnected,
    Reconnected,
};

struct ControllerHotplugState {
    std::array<ControllerSeat, kControllerSeatCount> seats{};
    std::array<ControllerSeatNotice, kControllerSeatCount> notices{};
    // Set by a disconnect of the device occupying a seat; consumed at the next
    // completed-frame boundary so the pause uses the ordinary session command.
    bool disconnect_pause_pending = false;
};

constexpr bool controller_seat_valid(int seat) noexcept {
    return seat >= 0 && static_cast<std::size_t>(seat) < kControllerSeatCount;
}

constexpr ControllerHotplugState controller_hotplug_observe(
    ControllerHotplugState state,
    int seat,
    std::uint64_t source_id,
    bool connected) noexcept {
    if (!controller_seat_valid(seat)) return state;
    const auto index = static_cast<std::size_t>(seat);
    auto& current = state.seats[index];
    if (connected) {
        current = {true, source_id};
        if (state.notices[index] == ControllerSeatNotice::Disconnected) {
            state.notices[index] = ControllerSeatNotice::Reconnected;
        }
        return state;
    }
    // A removal for a source that no longer occupies the seat is stale (the
    // seat was already vacated or reassigned); it must not raise a notice or
    // pause the player who now owns that seat.
    if (!current.connected || current.source_id != source_id) return state;
    current = {};
    state.notices[index] = ControllerSeatNotice::Disconnected;
    state.disconnect_pause_pending = true;
    return state;
}

struct ControllerDisconnectPauseDecision {
    ControllerHotplugState state{};
    bool pause = false;
};

// Consumes the pending latch exactly once. Pausing is Modern-only, limited to
// the title's validated pause/restart surfaces, and never re-pauses an already
// paused session. Authentic execution therefore observes no product effect.
constexpr ControllerDisconnectPauseDecision controller_hotplug_take_pause(
    ControllerHotplugState state,
    ExecutionMode mode,
    bool pause_surface,
    bool already_paused) noexcept {
    const bool pending = state.disconnect_pause_pending;
    state.disconnect_pause_pending = false;
    return {
        state,
        policy_for(mode).modern_commands && pending && pause_surface &&
            !already_paused,
    };
}

constexpr ControllerHotplugState controller_hotplug_clear_notices(
    ControllerHotplugState state) noexcept {
    state.notices = {};
    return state;
}

constexpr bool controller_hotplug_any_notice(
    const ControllerHotplugState& state) noexcept {
    for (const auto notice : state.notices) {
        if (notice != ControllerSeatNotice::None) return true;
    }
    return false;
}

// Static player-facing text. Disconnected wins over Reconnected so a second
// lost seat is never hidden behind the first seat's recovery.
constexpr const char* controller_hotplug_notice_text(
    const ControllerHotplugState& state) noexcept {
    constexpr const char* kDisconnected[kControllerSeatCount] = {
        "P1 CONTROLLER DISCONNECTED",
        "P2 CONTROLLER DISCONNECTED",
    };
    constexpr const char* kReconnected[kControllerSeatCount] = {
        "P1 CONTROLLER RECONNECTED",
        "P2 CONTROLLER RECONNECTED",
    };
    for (std::size_t i = 0; i < kControllerSeatCount; ++i) {
        if (state.notices[i] == ControllerSeatNotice::Disconnected) {
            return kDisconnected[i];
        }
    }
    for (std::size_t i = 0; i < kControllerSeatCount; ++i) {
        if (state.notices[i] == ControllerSeatNotice::Reconnected) {
            return kReconnected[i];
        }
    }
    return nullptr;
}

}  // namespace ur::product

#pragma once

#include <cstdint>

namespace ur::product {

enum class LocalInputKind : std::uint8_t {
    Controller,
    Keyboard,
};

struct LocalInputSource {
    LocalInputKind kind = LocalInputKind::Controller;
    std::uint64_t stable_id = 0;
    bool connected = false;
};

constexpr bool operator==(LocalInputSource lhs, LocalInputSource rhs) noexcept {
    return lhs.kind == rhs.kind && lhs.stable_id == rhs.stable_id;
}

enum class LocalMultiplayerSlot : std::uint8_t {
    Player1,
    Player2,
};

enum class LocalMultiplayerSetupStatus : std::uint8_t {
    Applied,
    InvalidSource,
    DuplicateSource,
    SlotOccupied,
    SlotEmpty,
    NoOpenSlot,
};

struct LocalMultiplayerAssignment {
    bool assigned = false;
    LocalInputSource source{};
};

struct LocalMultiplayerSetupState {
    LocalMultiplayerAssignment player1{};
    LocalMultiplayerAssignment player2{};
};

struct LocalMultiplayerSetupResult {
    LocalMultiplayerSetupState state{};
    LocalMultiplayerSetupStatus status = LocalMultiplayerSetupStatus::Applied;
    LocalMultiplayerSlot slot = LocalMultiplayerSlot::Player1;

    constexpr bool applied() const noexcept {
        return status == LocalMultiplayerSetupStatus::Applied;
    }
};

constexpr bool local_multiplayer_source_valid(LocalInputSource source) noexcept {
    return source.connected && source.stable_id != 0;
}

constexpr const LocalMultiplayerAssignment& local_multiplayer_assignment(
    const LocalMultiplayerSetupState& state,
    LocalMultiplayerSlot slot) noexcept {
    return slot == LocalMultiplayerSlot::Player1 ? state.player1 : state.player2;
}

constexpr LocalMultiplayerAssignment& local_multiplayer_assignment(
    LocalMultiplayerSetupState& state,
    LocalMultiplayerSlot slot) noexcept {
    return slot == LocalMultiplayerSlot::Player1 ? state.player1 : state.player2;
}

constexpr bool local_multiplayer_source_in_use(
    const LocalMultiplayerSetupState& state,
    LocalInputSource source,
    LocalMultiplayerSlot except) noexcept {
    const auto other = except == LocalMultiplayerSlot::Player1
        ? state.player2
        : state.player1;
    return other.assigned && other.source == source;
}

constexpr LocalMultiplayerSetupResult local_multiplayer_assign(
    LocalMultiplayerSetupState state,
    LocalMultiplayerSlot slot,
    LocalInputSource source) noexcept {
    if (!local_multiplayer_source_valid(source)) {
        return {state, LocalMultiplayerSetupStatus::InvalidSource, slot};
    }
    if (local_multiplayer_source_in_use(state, source, slot)) {
        return {state, LocalMultiplayerSetupStatus::DuplicateSource, slot};
    }

    auto& assignment = local_multiplayer_assignment(state, slot);
    assignment = {true, source};
    return {state, LocalMultiplayerSetupStatus::Applied, slot};
}

constexpr LocalMultiplayerSetupResult local_multiplayer_join(
    LocalMultiplayerSetupState state,
    LocalInputSource source) noexcept {
    if (!local_multiplayer_source_valid(source)) {
        return {state, LocalMultiplayerSetupStatus::InvalidSource,
                LocalMultiplayerSlot::Player1};
    }
    if (state.player1.assigned && state.player1.source == source) {
        return {state, LocalMultiplayerSetupStatus::DuplicateSource,
                LocalMultiplayerSlot::Player1};
    }
    if (state.player2.assigned && state.player2.source == source) {
        return {state, LocalMultiplayerSetupStatus::DuplicateSource,
                LocalMultiplayerSlot::Player2};
    }
    if (!state.player1.assigned) {
        return local_multiplayer_assign(state, LocalMultiplayerSlot::Player1, source);
    }
    if (!state.player2.assigned) {
        return local_multiplayer_assign(state, LocalMultiplayerSlot::Player2, source);
    }
    return {state, LocalMultiplayerSetupStatus::NoOpenSlot,
            LocalMultiplayerSlot::Player2};
}

constexpr LocalMultiplayerSetupResult local_multiplayer_leave(
    LocalMultiplayerSetupState state,
    LocalMultiplayerSlot slot) noexcept {
    auto& assignment = local_multiplayer_assignment(state, slot);
    if (!assignment.assigned) {
        return {state, LocalMultiplayerSetupStatus::SlotEmpty, slot};
    }
    assignment = {};
    return {state, LocalMultiplayerSetupStatus::Applied, slot};
}

constexpr LocalMultiplayerSetupState local_multiplayer_set_connected(
    LocalMultiplayerSetupState state,
    LocalInputSource source,
    bool connected) noexcept {
    if (state.player1.assigned && state.player1.source == source) {
        state.player1.source.connected = connected;
    }
    if (state.player2.assigned && state.player2.source == source) {
        state.player2.source.connected = connected;
    }
    return state;
}

enum class LocalMultiplayerSeatPresentation : std::uint8_t {
    Empty,
    ControllerConnected,
    ControllerDisconnected,
    KeyboardConnected,
    KeyboardDisconnected,
};

constexpr LocalMultiplayerSeatPresentation local_multiplayer_seat_presentation(
    const LocalMultiplayerSetupState& state,
    LocalMultiplayerSlot slot) noexcept {
    const auto& assignment = local_multiplayer_assignment(state, slot);
    if (!assignment.assigned) {
        return LocalMultiplayerSeatPresentation::Empty;
    }
    if (assignment.source.kind == LocalInputKind::Keyboard) {
        return assignment.source.connected
            ? LocalMultiplayerSeatPresentation::KeyboardConnected
            : LocalMultiplayerSeatPresentation::KeyboardDisconnected;
    }
    return assignment.source.connected
        ? LocalMultiplayerSeatPresentation::ControllerConnected
        : LocalMultiplayerSeatPresentation::ControllerDisconnected;
}

constexpr const char* local_multiplayer_slot_label(
    LocalMultiplayerSlot slot) noexcept {
    return slot == LocalMultiplayerSlot::Player1 ? "P1" : "P2";
}

constexpr const char* local_multiplayer_seat_source_label(
    LocalMultiplayerSeatPresentation presentation) noexcept {
    switch (presentation) {
    case LocalMultiplayerSeatPresentation::ControllerConnected:
    case LocalMultiplayerSeatPresentation::ControllerDisconnected:
        return "CONTROLLER";
    case LocalMultiplayerSeatPresentation::KeyboardConnected:
    case LocalMultiplayerSeatPresentation::KeyboardDisconnected:
        return "KEYBOARD";
    case LocalMultiplayerSeatPresentation::Empty:
    default:
        return "EMPTY";
    }
}

constexpr bool local_multiplayer_seat_connected(
    LocalMultiplayerSeatPresentation presentation) noexcept {
    return presentation ==
               LocalMultiplayerSeatPresentation::ControllerConnected ||
           presentation ==
               LocalMultiplayerSeatPresentation::KeyboardConnected;
}

constexpr bool local_multiplayer_launch_eligible(
    const LocalMultiplayerSetupState& state) noexcept {
    if (!state.player1.assigned || !state.player2.assigned) return false;
    if (!local_multiplayer_source_valid(state.player1.source) ||
        !local_multiplayer_source_valid(state.player2.source)) return false;
    return !(state.player1.source == state.player2.source);
}

}  // namespace ur::product

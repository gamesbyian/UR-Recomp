#include "local_multiplayer_setup.hpp"

#include <cassert>

using namespace ur::product;

constexpr LocalInputSource controller(std::uint64_t id, bool connected = true) {
    return {LocalInputKind::Controller, id, connected};
}

int main() {
    LocalMultiplayerSetupState state{};

    const auto p1 = local_multiplayer_join(state, controller(10));
    assert(p1.applied());
    assert(p1.slot == LocalMultiplayerSlot::Player1);
    state = p1.state;

    const auto duplicate = local_multiplayer_join(state, controller(10));
    assert(!duplicate.applied());
    assert(duplicate.status == LocalMultiplayerSetupStatus::DuplicateSource);
    assert(!state.player2.assigned);

    const auto p2 = local_multiplayer_join(state, controller(20));
    assert(p2.applied());
    assert(p2.slot == LocalMultiplayerSlot::Player2);
    state = p2.state;
    assert(local_multiplayer_launch_eligible(state));

    const auto full = local_multiplayer_join(state, controller(30));
    assert(full.status == LocalMultiplayerSetupStatus::NoOpenSlot);

    state = local_multiplayer_set_connected(state, controller(20), false);
    assert(state.player2.assigned);
    assert(!state.player2.source.connected);
    assert(!local_multiplayer_launch_eligible(state));

    state = local_multiplayer_set_connected(state, controller(20), true);
    assert(state.player2.source.connected);
    assert(local_multiplayer_launch_eligible(state));

    const auto swapped_p1 = local_multiplayer_assign(
        state, LocalMultiplayerSlot::Player1, controller(30));
    assert(swapped_p1.applied());
    state = swapped_p1.state;
    assert(state.player1.source.stable_id == 30);
    assert(state.player2.source.stable_id == 20);
    assert(local_multiplayer_launch_eligible(state));

    const auto collide = local_multiplayer_assign(
        state, LocalMultiplayerSlot::Player1, controller(20));
    assert(collide.status == LocalMultiplayerSetupStatus::DuplicateSource);
    assert(collide.state.player1.source.stable_id == 30);

    const auto left = local_multiplayer_leave(
        state, LocalMultiplayerSlot::Player2);
    assert(left.applied());
    state = left.state;
    assert(!state.player2.assigned);
    assert(!local_multiplayer_launch_eligible(state));

    const auto invalid = local_multiplayer_join(state, controller(0));
    assert(invalid.status == LocalMultiplayerSetupStatus::InvalidSource);

    const LocalInputSource keyboard{LocalInputKind::Keyboard, 1, true};
    const auto keyboard_p2 = local_multiplayer_join(state, keyboard);
    assert(keyboard_p2.applied());
    assert(keyboard_p2.slot == LocalMultiplayerSlot::Player2);
    assert(local_multiplayer_launch_eligible(keyboard_p2.state));

    return 0;
}

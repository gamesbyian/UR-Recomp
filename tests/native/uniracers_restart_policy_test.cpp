#include "uniracers_restart_policy.h"

#include <cassert>
#include <initializer_list>

int main() {
    // Active-race identity outranks incidental frontend scratch values.
    for (int menu = 0; menu < 256; ++menu) {
        assert(ur_uniracers_classify_restart_surface(
                   0x01, static_cast<unsigned char>(menu)) ==
               UR_UNIRACERS_RESTART_ACTIVE_RACE);
    }

    for (const unsigned char menu : {0x99, 0xBC, 0x18}) {
        assert(ur_uniracers_classify_restart_surface(0x00, menu) ==
               UR_UNIRACERS_RESTART_RESULTS);
    }

    for (const unsigned char menu : {0xD7, 0x3C, 0x6D, 0xF6, 0x16}) {
        assert(ur_uniracers_classify_restart_surface(0x00, menu) ==
               UR_UNIRACERS_RESTART_RETIRE_ATTEMPT);
    }

    for (const unsigned char menu : {0x00, 0x01, 0x55, 0x98, 0x9A, 0xFF}) {
        assert(ur_uniracers_classify_restart_surface(0x00, menu) ==
               UR_UNIRACERS_RESTART_UNSUPPORTED);
    }

    // Only the established byte value 1 means active race.
    assert(ur_uniracers_classify_restart_surface(0x02, 0x99) ==
           UR_UNIRACERS_RESTART_RESULTS);

    UrUniracersRestartPolicyState state{};
    ur_uniracers_restart_policy_reset(&state);

    // Pre-race stable frontend states do not retire anything.
    auto d = ur_uniracers_restart_policy_observe(&state, 0x00, 0xF6);
    assert(d.surface == UR_UNIRACERS_RESTART_RETIRE_ATTEMPT);
    assert(!d.retire_attempt);

    // Active race begins a fresh attempt.
    d = ur_uniracers_restart_policy_observe(&state, 0x01, 0x00);
    assert(d.surface == UR_UNIRACERS_RESTART_ACTIVE_RACE);
    assert(!d.retire_attempt);

    // A normal finish may transiently look frontend-like before results.
    d = ur_uniracers_restart_policy_observe(&state, 0x00, 0xF6);
    assert(d.surface == UR_UNIRACERS_RESTART_RETIRE_ATTEMPT);
    assert(!d.retire_attempt);

    // Results latches Retry retention.
    d = ur_uniracers_restart_policy_observe(&state, 0x00, 0x99);
    assert(d.surface == UR_UNIRACERS_RESTART_RESULTS);
    assert(!d.retire_attempt);
    assert(state.seen_results);

    // The next stable frontend/pre-race state retires the completed attempt.
    d = ur_uniracers_restart_policy_observe(&state, 0x00, 0xF6);
    assert(d.surface == UR_UNIRACERS_RESTART_RETIRE_ATTEMPT);
    assert(d.retire_attempt);
    assert(!state.seen_results);

    return 0;
}

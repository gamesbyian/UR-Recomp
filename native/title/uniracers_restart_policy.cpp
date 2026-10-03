#include "uniracers_restart_policy.h"

extern "C" UrUniracersRestartSurface ur_uniracers_classify_restart_surface(
    uint8_t race_active_state,
    uint8_t frontend_state) {
    if (race_active_state == 0x01) {
        return UR_UNIRACERS_RESTART_ACTIVE_RACE;
    }

    switch (frontend_state) {
    case 0x99:
    case 0xBC:
    case 0x18:
        return UR_UNIRACERS_RESTART_RESULTS;

    case 0xD7:
    case 0x3C:
    case 0x6D:
    case 0xF6:
    case 0x16:
        return UR_UNIRACERS_RESTART_RETIRE_ATTEMPT;

    default:
        return UR_UNIRACERS_RESTART_UNSUPPORTED;
    }
}

extern "C" void ur_uniracers_restart_policy_reset(
    UrUniracersRestartPolicyState* state) {
    if (state) {
        state->seen_results = 0;
    }
}

extern "C" UrUniracersRestartDecision ur_uniracers_restart_policy_observe(
    UrUniracersRestartPolicyState* state,
    uint8_t race_active_state,
    uint8_t frontend_state) {
    const UrUniracersRestartSurface surface =
        ur_uniracers_classify_restart_surface(
            race_active_state, frontend_state);

    UrUniracersRestartDecision decision{surface, 0};
    if (!state) {
        return decision;
    }

    if (surface == UR_UNIRACERS_RESTART_ACTIVE_RACE) {
        state->seen_results = 0;
    } else if (surface == UR_UNIRACERS_RESTART_RESULTS) {
        state->seen_results = 1;
    } else if (surface == UR_UNIRACERS_RESTART_RETIRE_ATTEMPT &&
               state->seen_results) {
        decision.retire_attempt = 1;
        state->seen_results = 0;
    }

    return decision;
}

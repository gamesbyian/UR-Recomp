#pragma once

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum UrUniracersRestartSurface {
    UR_UNIRACERS_RESTART_UNSUPPORTED = 0,
    UR_UNIRACERS_RESTART_ACTIVE_RACE = 1,
    UR_UNIRACERS_RESTART_RESULTS = 2,
    UR_UNIRACERS_RESTART_RETIRE_ATTEMPT = 3,
} UrUniracersRestartSurface;

typedef struct UrUniracersRestartPolicyState {
    int seen_results;
} UrUniracersRestartPolicyState;

typedef struct UrUniracersRestartDecision {
    UrUniracersRestartSurface surface;
    int retire_attempt;
} UrUniracersRestartDecision;

/* Pure title-state classifier. It never reads or writes guest memory.
 *
 * race_active_state is WRAM $0313 and frontend_state is WRAM $009F, sampled
 * by the title host at a completed guest-frame boundary.
 *
 * Known supported Restart Race surfaces:
 *   - $0313 == 1: active race
 *   - $009F == 0x99, 0xBC, 0x18 while not active: race/circuit/stunt results
 *
 * Known stable frontend/pre-race states are retirement candidates:
 *   - 0xD7 main menu
 *   - 0x3C rider select
 *   - 0x6D tours
 *   - 0xF6 tracks
 *   - 0x16 now playing / committed pre-race
 *
 * Unknown/transient states are unsupported.
 */
UrUniracersRestartSurface ur_uniracers_classify_restart_surface(
    uint8_t race_active_state,
    uint8_t frontend_state);

/* Stateful lifecycle policy layered over the pure classifier.
 *
 * A normal finish can pass through frontend-coded transient/candidate states
 * before the stock results screen appears. Therefore a retirement candidate
 * only clears the prior attempt after a results surface has actually been
 * observed. Before results it hides Retry but retains the anchor. A new active
 * race resets the results latch and supersedes the prior anchor through the
 * generic RaceRestartLifecycle.
 */
void ur_uniracers_restart_policy_reset(
    UrUniracersRestartPolicyState* state);

UrUniracersRestartDecision ur_uniracers_restart_policy_observe(
    UrUniracersRestartPolicyState* state,
    uint8_t race_active_state,
    uint8_t frontend_state);

#ifdef __cplusplus
}
#endif

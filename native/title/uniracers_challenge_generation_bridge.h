#pragma once

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef uint8_t (*UrChallengeGenerationFilter)(uint8_t stock_generation);

/*
 * Narrow generated-code seam for the stock tour-confirm generation snapshot.
 * With no installed Modern filter this is exact stock pass-through.
 */
uint8_t ur_uniracers_challenge_generation_filter(
    uint8_t stock_generation);

/*
 * Product integration may install one typed filter at a controlled lifecycle
 * boundary. Passing null restores exact stock behavior.
 */
void ur_uniracers_set_challenge_generation_filter(
    UrChallengeGenerationFilter filter);

#ifdef __cplusplus
}
#endif

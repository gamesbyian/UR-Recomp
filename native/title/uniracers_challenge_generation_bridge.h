#pragma once

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef uint8_t (*UrChallengeGenerationFilter)(uint8_t stock_generation);
typedef uint8_t (*UrChallengeQualificationGenerationFilter)(
    uint8_t stock_generation);
typedef uint8_t (*UrChallengeAwardPreviousMedalFilter)(
    uint8_t stock_previous_medal);

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

/*
 * Stunt QUALIFY only: stock normally derives generation from the persistent
 * medal before indexing 83:A218. Default behavior is exact pass-through.
 */
uint8_t ur_uniracers_challenge_qualification_generation_filter(
    uint8_t stock_generation);
void ur_uniracers_set_challenge_qualification_generation_filter(
    UrChallengeQualificationGenerationFilter filter);

/*
 * Tour-award only: stock reads the previous medal immediately before its own
 * INC/clamp/store transaction. Default behavior is exact pass-through.
 */
uint8_t ur_uniracers_challenge_award_previous_medal_filter(
    uint8_t stock_previous_medal);
void ur_uniracers_set_challenge_award_previous_medal_filter(
    UrChallengeAwardPreviousMedalFilter filter);

#ifdef __cplusplus
}
#endif

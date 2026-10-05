#include "uniracers_challenge_generation_bridge.h"

static UrChallengeGenerationFilter g_filter;
static UrChallengeQualificationGenerationFilter g_qualification_filter;
static UrChallengeAwardPreviousMedalFilter g_award_filter;

uint8_t ur_uniracers_challenge_generation_filter(
    uint8_t stock_generation) {
    return g_filter ? g_filter(stock_generation) : stock_generation;
}

void ur_uniracers_set_challenge_generation_filter(
    UrChallengeGenerationFilter filter) {
    g_filter = filter;
}

uint8_t ur_uniracers_challenge_qualification_generation_filter(
    uint8_t stock_generation) {
    return g_qualification_filter
        ? g_qualification_filter(stock_generation)
        : stock_generation;
}

void ur_uniracers_set_challenge_qualification_generation_filter(
    UrChallengeQualificationGenerationFilter filter) {
    g_qualification_filter = filter;
}

uint8_t ur_uniracers_challenge_award_previous_medal_filter(
    uint8_t stock_previous_medal) {
    return g_award_filter ? g_award_filter(stock_previous_medal)
                          : stock_previous_medal;
}

void ur_uniracers_set_challenge_award_previous_medal_filter(
    UrChallengeAwardPreviousMedalFilter filter) {
    g_award_filter = filter;
}

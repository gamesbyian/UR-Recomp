#include "uniracers_challenge_generation_bridge.h"

static UrChallengeGenerationFilter g_filter;

uint8_t ur_uniracers_challenge_generation_filter(
    uint8_t stock_generation) {
    return g_filter ? g_filter(stock_generation) : stock_generation;
}

void ur_uniracers_set_challenge_generation_filter(
    UrChallengeGenerationFilter filter) {
    g_filter = filter;
}

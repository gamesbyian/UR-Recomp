#include "uniracers_challenge_generation_bridge.h"

#include <assert.h>
#include <stdint.h>

static uint8_t force_gold(uint8_t stock_generation) {
    (void)stock_generation;
    return 2;
}

static uint8_t force_silver(uint8_t stock_generation) {
    (void)stock_generation;
    return 1;
}

static uint8_t award_gold(uint8_t stock_previous_medal) {
    (void)stock_previous_medal;
    return 2;
}

int main(void) {
    assert(ur_uniracers_challenge_generation_filter(0) == 0);
    assert(ur_uniracers_challenge_generation_filter(1) == 1);
    assert(ur_uniracers_challenge_generation_filter(2) == 2);

    ur_uniracers_set_challenge_generation_filter(&force_gold);
    assert(ur_uniracers_challenge_generation_filter(0) == 2);
    assert(ur_uniracers_challenge_generation_filter(1) == 2);

    ur_uniracers_set_challenge_generation_filter(0);
    assert(ur_uniracers_challenge_generation_filter(1) == 1);

    assert(ur_uniracers_challenge_qualification_generation_filter(0) == 0);
    ur_uniracers_set_challenge_qualification_generation_filter(&force_silver);
    assert(ur_uniracers_challenge_qualification_generation_filter(0) == 1);
    assert(ur_uniracers_challenge_qualification_generation_filter(2) == 1);
    ur_uniracers_set_challenge_qualification_generation_filter(0);
    assert(ur_uniracers_challenge_qualification_generation_filter(2) == 2);

    assert(ur_uniracers_challenge_award_previous_medal_filter(0) == 0);
    ur_uniracers_set_challenge_award_previous_medal_filter(&award_gold);
    assert(ur_uniracers_challenge_award_previous_medal_filter(0) == 2);
    ur_uniracers_set_challenge_award_previous_medal_filter(0);
    assert(ur_uniracers_challenge_award_previous_medal_filter(1) == 1);
    return 0;
}

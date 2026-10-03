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
    return 0;
}

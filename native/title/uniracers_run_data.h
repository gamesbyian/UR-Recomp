#pragma once

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct UrUniracersRunData {
    int valid;
    int minutes;
    int tens_seconds;
    int seconds;
    int tenths;
    int sub_tick;
} UrUniracersRunData;

/* Decode the established Uniracers race/stunt timer digits from WRAM.
 * This adapter is read-only and title-specific; product UI should consume the
 * typed result rather than indexing title WRAM directly.
 */
UrUniracersRunData ur_uniracers_read_run_data(
    const unsigned char* wram,
    size_t wram_size);

/* Convert a validated timer sample to exact guest ticks at the established
 * 60 Hz timer granularity. Returns -1 for an invalid sample. */
int64_t ur_uniracers_run_data_ticks60(UrUniracersRunData data);

#ifdef __cplusplus
}
#endif

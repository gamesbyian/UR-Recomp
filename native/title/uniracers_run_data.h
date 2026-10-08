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

/* Per-player line-crossing snapshot. At each lap/finish line crossing the
 * title copies the shared timer digits into a per-player slot (81:80B6:
 * minutes 0E39, tens 0E3D, seconds 0E41, tenths 0E45, plus a synthesized
 * hundredths digit at 0E35, each indexed by 2*player). The shared timer at
 * 0E0F.. keeps running while other racers are still on course, so the last
 * snapshot written before results -- not the shared timer at results -- is
 * the player's official finish (it is what the stock results table prints).
 */
typedef struct UrUniracersLineSnapshot {
    int valid;
    int minutes;
    int tens_seconds;
    int seconds;
    int tenths;
    int hundredths;
} UrUniracersLineSnapshot;

UrUniracersLineSnapshot ur_uniracers_read_line_snapshot(
    const unsigned char* wram,
    size_t wram_size,
    int player);

/* Laps remaining for player 0/1 (7E:0EF1 / 7E:0EF3). The line-crossing
 * handler decrements it on the same frame it writes the snapshot, so the
 * write that leaves it at zero is the finish. Returns -1 when unavailable. */
int ur_uniracers_read_laps_remaining(
    const unsigned char* wram,
    size_t wram_size,
    int player);

int ur_uniracers_line_snapshot_equal(
    UrUniracersLineSnapshot a,
    UrUniracersLineSnapshot b);

/* Exact 60 Hz ticks of a snapshot, given the shared timer sampled at the end
 * of the guest frame on which the snapshot was written. The snapshot keeps
 * only whole tenths, so the shared sample supplies the sub-tick. Returns -1
 * when the two samples cannot describe the same instant: the shared timer
 * must still be in the snapshot's tenth, or exactly at the first tick of the
 * next tenth (a carry after the copy, so the copy was taken at sub-tick 5). */
int64_t ur_uniracers_line_snapshot_ticks60(
    UrUniracersRunData shared_at_write,
    UrUniracersLineSnapshot snapshot);

#ifdef __cplusplus
}
#endif

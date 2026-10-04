#ifndef UR_UNIRACERS_WS_MARGINS_H
#define UR_UNIRACERS_WS_MARGINS_H

/* Uniracers Widescreen margin presentation for the single-viewport race.
 *
 * BG1 carries the course. Its tilemap is a 32x32 ring of 16x16 tiles that
 * the game streams only one column beyond the 256-wide view, so the widened
 * margins cannot be read from VRAM. Every BG1 tilemap entry is, however, a
 * pure function of its course cell: the live course tables in bank $7F map a
 * 16-pixel world cell to the exact word the game uploads. This module serves
 * the margins from those tables through the framework's world-keyed
 * ws_shadow store, so presentation never writes guest VRAM.
 *
 * Course space and BG1 scroll differ by a per-race constant. It is
 * calibrated from the live native view (every visible BG1 entry must equal
 * its course cell) and fails closed: until a unique calibration exists the
 * margins are left to the renderer's plain fallback.
 */

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

enum {
    UR_WS_BG1_TILE_SHIFT = 4,
    UR_WS_BG1_VIEW_COLS = 17, /* 256 px of 16 px tiles plus fine phase */
    UR_WS_BG1_VIEW_ROWS = 15, /* 224 px of 16 px tiles plus fine phase */
};

/* Course tilemap word for a 16-pixel course cell from 128 KiB of WRAM.
 * Returns 0 when the cell lies outside the live course. */
int ur_ws_course_tile(const uint8_t* wram, int cell_x, int cell_y,
                      uint16_t* out);

/* Find the course cell shown at BG1 tile (scroll_x >> 4, scroll_y >> 4).
 * `vram` is the 64 KiB PPU VRAM, `map_base_word` the BG1 32x32 tilemap base.
 * Candidates are searched within +/-radius cells of the guess; a candidate is
 * accepted only if every visible entry matches and at least `min_nonzero`
 * matching entries are non-blank, and no other candidate also qualifies.
 * Returns 1 and writes the cell offset (course cell - scroll cell) on a
 * unique match. */
int ur_ws_calibrate_bg1(const uint8_t* wram, const uint16_t* vram,
                        uint16_t map_base_word, uint16_t scroll_x,
                        uint16_t scroll_y, int guess_cell_x, int guess_cell_y,
                        int radius, int min_nonzero, int* offset_x,
                        int* offset_y);

/* Per-frame entry point, called from the title's prepare_frame hook.
 * `enabled` is nonzero only for a live single-viewport world-expand race. */
void ur_ws_margins_prepare_frame(int enabled, int extra_pixels);

/* Diagnostics: 1 while a calibration is held for the current race. */
int ur_ws_margins_calibrated(void);

#ifdef __cplusplus
}
#endif

#endif

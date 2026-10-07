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

/* Course tilemap word for a 16-pixel course cell from exactly 128 KiB of
 * SNES WRAM. The caller must provide the complete 0x20000-byte guest address
 * space; dynamically derived bank-$7F offsets are validated before reads.
 * Returns 0 when the cell lies outside the live course or the derived record
 * address cannot fit in that bank. */
int ur_ws_course_tile(const uint8_t* wram, int cell_x, int cell_y,
                      uint16_t* out);

/* Find the course cell shown at BG1 tile (scroll_x >> 4, scroll_y >> 4) for
 * the screen lines [first_line, first_line + line_count). `vram` is the
 * 64 KiB PPU VRAM and `map_base_word` that band's BG1 32x32 tilemap base.
 * Candidates are searched within +/-radius cells of the guess; a candidate is
 * accepted only if every visible entry matches and at least `min_nonzero`
 * matching entries are non-blank, and no other candidate also qualifies.
 * Returns 1 and writes the cell offset (course cell - scroll cell) on a
 * unique match. */
int ur_ws_calibrate_bg1(const uint8_t* wram, const uint16_t* vram,
                        uint16_t map_base_word, uint16_t scroll_x,
                        uint16_t scroll_y, int first_line, int line_count,
                        int guess_cell_x, int guess_cell_y, int radius,
                        int min_nonzero, int* offset_x, int* offset_y);

/* One BG1 viewport band from the game's per-frame HDMA tables: the 1P race
 * has one, split-screen races have one per player. */
enum {
    UR_WS_BG1_SCROLL_TABLE = 0x2046, /* channel 4 -> $210D/$210E */
    UR_WS_BG1_SC_TABLE = 0x207F,     /* channel 2 -> $2107 */
    UR_WS_PPU_FIRST_LINE = 1,        /* PPU numbers visible lines from 1 */
};

typedef struct UrWsBg1Band {
    int first_line; /* 0-based screen line */
    int line_count;
    uint16_t scroll_x;
    uint16_t scroll_y;
    uint16_t map_base_word;
} UrWsBg1Band;

/* `wram` must provide the complete 0x20000-byte guest WRAM image. Returns the
 * band count (0 when the tables are absent, in repeat mode, misaligned, or
 * describe more than max_bands origins). */
int ur_ws_parse_bg1_bands(const uint8_t* wram, UrWsBg1Band* bands,
                          int max_bands);

/* Per-frame entry point, called from the title's prepare_frame hook.
 * `enabled` is nonzero only for a live world-expand race. */
void ur_ws_margins_prepare_frame(int enabled, int extra_pixels);

/* Diagnostics: 1 while a calibration is held for the current race. */
int ur_ws_margins_calibrated(void);

#ifdef __cplusplus
}
#endif

#endif

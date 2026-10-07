#include "uniracers_ws_margins.h"

#include <stddef.h>

/* Live course presentation tables in bank $7F (docs/COURSE-FORMAT.md):
 * $7F:000F is the u16 coarse-sector index (64 px sectors), $7F:800F holds
 * 32-byte 4x4 fine records of tilemap words (16 px cells). The coarse
 * dimensions are $04F1/$04F3 in sectors. */
enum {
    kWramBank7F = 0x10000,
    kCoarseTable = 0x000F,
    kFineRecords = 0x800F,
    kCoarseWidth = 0x04F1,
    kCoarseHeight = 0x04F3,
};

static uint16_t read16(const uint8_t* wram, uint32_t addr) {
    return (uint16_t)(wram[addr] | (wram[addr + 1] << 8));
}

int ur_ws_course_tile(const uint8_t* wram, int cell_x, int cell_y,
                      uint16_t* out) {
    if (!wram || !out)
        return 0;
    const int coarse_w = read16(wram, kCoarseWidth);
    const int coarse_h = read16(wram, kCoarseHeight);
    if (coarse_w <= 0 || coarse_h <= 0 || cell_x < 0 || cell_y < 0 ||
        cell_x >= coarse_w * 4 || cell_y >= coarse_h * 4)
        return 0;
    const uint32_t coarse_index =
        (uint32_t)(cell_y >> 2) * (uint32_t)coarse_w + (uint32_t)(cell_x >> 2);
    const uint32_t coarse_addr = kCoarseTable + coarse_index * 2u;
    if (coarse_addr > 0xFFFEu)
        return 0;
    const uint16_t record = read16(wram, kWramBank7F + coarse_addr);
    const uint32_t fine_addr = kFineRecords + (uint32_t)record * 32u +
                               (uint32_t)(((cell_y & 3) * 4) + (cell_x & 3)) * 2u;
    /* Mirrors the hook materializer: a sentinel/non-record entry renders
     * blank in stock, so an out-of-bank record is a blank cell. */
    *out = fine_addr <= 0xFFFEu ? read16(wram, kWramBank7F + fine_addr) : 0;
    return 1;
}

/* BG1 tile rows drawn for screen lines [first_line, first_line + count).
 * The PPU numbers visible lines from 1, so screen line L samples BG row
 * (scroll_y + L + 1) >> 4. */
static void band_rows(uint16_t scroll_y, int first_line, int line_count,
                      int* row_first, int* row_last) {
    *row_first = (scroll_y + first_line + 1) >> UR_WS_BG1_TILE_SHIFT;
    *row_last = (scroll_y + first_line + line_count) >> UR_WS_BG1_TILE_SHIFT;
}

static int view_matches(const uint8_t* wram, const uint16_t* vram,
                        uint16_t map_base_word, uint16_t scroll_x,
                        uint16_t scroll_y, int first_line, int line_count,
                        int offset_x, int offset_y, int* nonzero,
                        int* mismatches) {
    const int sx = scroll_x >> UR_WS_BG1_TILE_SHIFT;
    int row_first = 0;
    int row_last = 0;
    band_rows(scroll_y, first_line, line_count, &row_first, &row_last);
    int matched_nonzero = 0;
    int bad = 0;
    for (int row = row_first; row <= row_last; row++) {
        for (int col = 0; col < UR_WS_BG1_VIEW_COLS; col++) {
            const uint16_t word = (uint16_t)(map_base_word +
                                             ((row & 31) << 5) +
                                             ((sx + col) & 31));
            const uint16_t live = vram[word & 0x7FFF];
            uint16_t course = 0;
            if (!ur_ws_course_tile(wram, sx + col + offset_x,
                                   row + offset_y, &course) ||
                course != live) {
                bad++;
                continue;
            }
            if (live)
                matched_nonzero++;
        }
    }
    if (nonzero)
        *nonzero = matched_nonzero;
    if (mismatches)
        *mismatches = bad;
    return bad == 0;
}

int ur_ws_calibrate_bg1(const uint8_t* wram, const uint16_t* vram,
                        uint16_t map_base_word, uint16_t scroll_x,
                        uint16_t scroll_y, int first_line, int line_count,
                        int guess_cell_x, int guess_cell_y, int radius,
                        int min_nonzero, int* offset_x, int* offset_y) {
    if (!wram || !vram || radius < 0 || line_count <= 0)
        return 0;
    const int base_x = guess_cell_x - (scroll_x >> UR_WS_BG1_TILE_SHIFT);
    /* The guess is the camera, which sits at the band's first line: a lower
     * split-screen band scrolls up by its first line to show its own top. */
    const int base_y = guess_cell_y -
                       ((scroll_y + first_line) >> UR_WS_BG1_TILE_SHIFT);
    int found = 0;
    int best_x = 0;
    int best_y = 0;
    for (int dy = -radius; dy <= radius; dy++) {
        for (int dx = -radius; dx <= radius; dx++) {
            int nonzero = 0;
            if (!view_matches(wram, vram, map_base_word, scroll_x, scroll_y,
                              first_line, line_count, base_x + dx,
                              base_y + dy, &nonzero, NULL) ||
                nonzero < min_nonzero)
                continue;
            if (found)
                return 0; /* ambiguous view: fail closed */
            found = 1;
            best_x = base_x + dx;
            best_y = base_y + dy;
        }
    }
    if (!found)
        return 0;
    if (offset_x)
        *offset_x = best_x;
    if (offset_y)
        *offset_y = best_y;
    return 1;
}

int ur_ws_parse_bg1_bands(const uint8_t* wram, UrWsBg1Band* bands,
                          int max_bands) {
    if (!wram || !bands || max_bands <= 0)
        return 0;
    /* Channel 4 ($210D/$210E): count, H word, V word. Channel 2 ($2107):
     * count, BG1SC byte. Both tables carry the same line counts. */
    uint32_t scroll_at = UR_WS_BG1_SCROLL_TABLE;
    uint32_t sc_at = UR_WS_BG1_SC_TABLE;
    int line = 0;
    int count = 0;
    for (;;) {
        const uint8_t lines = wram[scroll_at];
        const uint8_t sc_lines = wram[sc_at];
        if (lines == 0 || sc_lines == 0 || line >= 224)
            break;
        if ((lines & 0x80) || lines != sc_lines)
            return 0; /* repeat-mode or misaligned tables: fail closed */
        const uint16_t h = (uint16_t)(read16(wram, scroll_at + 1) & 0x3FF);
        const uint16_t v = (uint16_t)(read16(wram, scroll_at + 3) & 0x3FF);
        const uint16_t base = (uint16_t)((wram[sc_at + 1] & 0xFC) << 8);
        if (count > 0 && bands[count - 1].scroll_x == h &&
            bands[count - 1].scroll_y == v &&
            bands[count - 1].map_base_word == base) {
            /* Same origin continues: extend the previous band. */
        } else {
            if (count == max_bands)
                return 0; /* more viewports than the store can hold */
            bands[count].first_line = line;
            bands[count].scroll_x = h;
            bands[count].scroll_y = v;
            bands[count].map_base_word = base;
            count++;
        }
        line += lines;
        scroll_at += 5;
        sc_at += 2;
    }
    /* The last entry's values persist to the bottom of the screen. */
    for (int i = 0; i < count; i++)
        bands[i].line_count =
            (i + 1 < count ? bands[i + 1].first_line : 224) - bands[i].first_line;
    return count;
}

#ifndef UR_WS_MARGINS_NO_RUNTIME

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "common_rtl.h"
#include "snes/ppu.h"
#include "snes/ws_shadow.h"

enum {
    kCalibrationRadius = 3,
    kCalibrationMinNonzero = 4,
    /* Live views may transiently expose a stale cell while an edge streams;
     * margins stay presented through a few, a real drift trips this. */
    kMaxFrameMismatches = 8,
    kMaxBands = 2,
};

/* Camera of the player each band shows: band 0 is P1, band 1 is P2. */
static const uint16_t kCameraX[kMaxBands] = {0x0419, 0x041B};
static const uint16_t kCameraY[kMaxBands] = {0x041D, 0x041F};

typedef struct BandState {
    int calibrated;
    uint32_t world_x;
    uint32_t world_y;
    uint16_t prev_scroll_x;
    uint16_t prev_scroll_y;
    unsigned consecutive_bad_frames;
} BandState;

static BandState s_band[kMaxBands];
static int s_band_count;
static int s_ever_active;
static unsigned s_presented_frames;
static unsigned s_mismatch_frames;
static int s_max_mismatches;
static int s_trace = -1;

static int trace_enabled(void) {
    if (s_trace < 0) {
        const char* v = getenv("URRECOMP_WS_NATIVE_TRACE");
        s_trace = (v && *v && strcmp(v, "0") != 0) ? 1 : 0;
    }
    return s_trace;
}

int ur_ws_margins_calibrated(void) {
    if (s_band_count <= 0)
        return 0;
    for (int i = 0; i < s_band_count; i++)
        if (!s_band[i].calibrated)
            return 0;
    return 1;
}

static int32_t signed10(uint16_t delta) {
    delta &= 0x3FF;
    return delta >= 0x200 ? (int32_t)delta - 0x400 : (int32_t)delta;
}

/* Margins are served from the course model, which is the content the game
 * itself streams; force it so stale captures never win. */
static void force_margins(const UrWsBg1Band* band, const BandState* state,
                          int extra_pixels) {
    const int row_first = (int)(state->world_y + band->first_line + 1) >>
                          UR_WS_BG1_TILE_SHIFT;
    const int row_last = (int)(state->world_y + band->first_line +
                               band->line_count) >> UR_WS_BG1_TILE_SHIFT;
    const int left_px = (int)state->world_x - extra_pixels;
    const int right_px = (int)state->world_x + 256;
    const int span = extra_pixels + 16;
    for (int side = 0; side < 2; side++) {
        const int start_px = side ? right_px : left_px;
        const int tx_first = start_px >> UR_WS_BG1_TILE_SHIFT;
        const int tx_last = (start_px + span - 1) >> UR_WS_BG1_TILE_SHIFT;
        for (int tx = tx_first; tx <= tx_last; tx++) {
            for (int ty = row_first; ty <= row_last; ty++) {
                uint16_t entry = 0;
                if (tx < 0 || ty < 0 || !ur_ws_course_tile(g_ram, tx, ty, &entry))
                    continue;
                WsShadowForceTile(0, (uint32_t)tx, (uint32_t)ty, entry);
            }
        }
    }
}

static void deactivate(void) {
    if (s_ever_active) {
        if (trace_enabled())
            fprintf(stderr,
                    "URWS_MARGINS SUMMARY presented=%u mismatch_frames=%u max_mismatches=%d\n",
                    s_presented_frames, s_mismatch_frames, s_max_mismatches);
        s_presented_frames = 0;
        s_mismatch_frames = 0;
        s_max_mismatches = 0;
        /* Leaving the race drops this course's world-keyed history. */
        WsShadowReset();
        WsShadowFrame(g_ppu);
        s_ever_active = 0;
    }
    memset(s_band, 0, sizeof(s_band));
    s_band_count = 0;
}

static int update_band(int index, const UrWsBg1Band* band) {
    BandState* state = &s_band[index];
    if (state->calibrated) {
        state->world_x = (uint32_t)((int32_t)state->world_x +
            signed10((uint16_t)(band->scroll_x - state->prev_scroll_x)));
        state->world_y = (uint32_t)((int32_t)state->world_y +
            signed10((uint16_t)(band->scroll_y - state->prev_scroll_y)));
        const int offset_x = (int)(state->world_x >> UR_WS_BG1_TILE_SHIFT) -
                             (band->scroll_x >> UR_WS_BG1_TILE_SHIFT);
        const int offset_y = (int)(state->world_y >> UR_WS_BG1_TILE_SHIFT) -
                             (band->scroll_y >> UR_WS_BG1_TILE_SHIFT);
        int mismatches = 0;
        view_matches(g_ram, g_ppu->vram, band->map_base_word, band->scroll_x,
                     band->scroll_y, band->first_line, band->line_count,
                     offset_x, offset_y, NULL, &mismatches);
        if (mismatches) {
            s_mismatch_frames++;
            if (mismatches > s_max_mismatches)
                s_max_mismatches = mismatches;
        }
        if (mismatches > kMaxFrameMismatches) {
            state->consecutive_bad_frames++;
            if (state->consecutive_bad_frames >= 2u) {
                state->calibrated = 0;
                state->consecutive_bad_frames = 0;
                if (trace_enabled())
                    fprintf(stderr,
                            "URWS_MARGINS LOST band=%d mismatches=%d sustained=2\n",
                            index, mismatches);
            }
        } else {
            state->consecutive_bad_frames = 0;
        }
    }
    if (!state->calibrated) {
        int offset_x = 0;
        int offset_y = 0;
        if (ur_ws_calibrate_bg1(g_ram, g_ppu->vram, band->map_base_word,
                                band->scroll_x, band->scroll_y,
                                band->first_line, band->line_count,
                                read16(g_ram, kCameraX[index]) >> 4,
                                read16(g_ram, kCameraY[index]) >> 4,
                                kCalibrationRadius, kCalibrationMinNonzero,
                                &offset_x, &offset_y)) {
            state->calibrated = 1;
            state->consecutive_bad_frames = 0;
            state->world_x = (uint32_t)(((band->scroll_x >> UR_WS_BG1_TILE_SHIFT) +
                                         offset_x) << UR_WS_BG1_TILE_SHIFT) |
                             (band->scroll_x & 15u);
            state->world_y = (uint32_t)(((band->scroll_y >> UR_WS_BG1_TILE_SHIFT) +
                                         offset_y) << UR_WS_BG1_TILE_SHIFT) |
                             (band->scroll_y & 15u);
            if (trace_enabled())
                fprintf(stderr,
                        "URWS_MARGINS CALIBRATED band=%d lines=%d+%d offset=%d,%d world=%u,%u scroll=%u,%u\n",
                        index, band->first_line, band->line_count, offset_x,
                        offset_y, (unsigned)state->world_x,
                        (unsigned)state->world_y, (unsigned)band->scroll_x,
                        (unsigned)band->scroll_y);
        }
    }
    state->prev_scroll_x = band->scroll_x;
    state->prev_scroll_y = band->scroll_y;
    return state->calibrated;
}

void ur_ws_margins_prepare_frame(int enabled, int extra_pixels) {
    if (!g_ppu)
        return;
    UrWsBg1Band bands[kMaxBands];
    const int count = (enabled && extra_pixels > 0 && PPU_bigTiles(g_ppu, 0))
        ? ur_ws_parse_bg1_bands(g_ram, bands, kMaxBands) : 0;
    if (count <= 0) {
        deactivate();
        return;
    }
    if (count != s_band_count) {
        memset(s_band, 0, sizeof(s_band));
        s_band_count = count;
    }

    int all_calibrated = 1;
    for (int i = 0; i < count; i++)
        all_calibrated &= update_band(i, &bands[i]);

    if (!all_calibrated) {
        if (s_ever_active)
            WsShadowFrame(g_ppu); /* deactivate: nothing registered */
        return;
    }

    WsShadowSetWorld(0, s_band[0].world_x, s_band[0].world_y);
    WsShadowSetScroll(0, bands[0].scroll_x, bands[0].scroll_y);
    if (count > 1)
        WsShadowSetSplit(0, bands[1].first_line + UR_WS_PPU_FIRST_LINE,
                         s_band[1].world_x, s_band[1].world_y,
                         bands[1].scroll_x, bands[1].scroll_y);
    WsShadowFrame(g_ppu);
    for (int i = 0; i < count; i++)
        force_margins(&bands[i], &s_band[i], extra_pixels);
    s_ever_active = 1;
    s_presented_frames++;
}

#endif /* UR_WS_MARGINS_NO_RUNTIME */

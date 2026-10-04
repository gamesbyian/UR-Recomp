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

static int view_matches(const uint8_t* wram, const uint16_t* vram,
                        uint16_t map_base_word, uint16_t scroll_x,
                        uint16_t scroll_y, int offset_x, int offset_y,
                        int* nonzero, int* mismatches) {
    const int sx = scroll_x >> UR_WS_BG1_TILE_SHIFT;
    const int sy = scroll_y >> UR_WS_BG1_TILE_SHIFT;
    int matched_nonzero = 0;
    int bad = 0;
    for (int row = 0; row < UR_WS_BG1_VIEW_ROWS; row++) {
        for (int col = 0; col < UR_WS_BG1_VIEW_COLS; col++) {
            const uint16_t word = (uint16_t)(map_base_word +
                                             (((sy + row) & 31) << 5) +
                                             ((sx + col) & 31));
            const uint16_t live = vram[word & 0x7FFF];
            uint16_t course = 0;
            if (!ur_ws_course_tile(wram, sx + col + offset_x,
                                   sy + row + offset_y, &course) ||
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
                        uint16_t scroll_y, int guess_cell_x, int guess_cell_y,
                        int radius, int min_nonzero, int* offset_x,
                        int* offset_y) {
    if (!wram || !vram || radius < 0)
        return 0;
    const int base_x = guess_cell_x - (scroll_x >> UR_WS_BG1_TILE_SHIFT);
    const int base_y = guess_cell_y - (scroll_y >> UR_WS_BG1_TILE_SHIFT);
    int found = 0;
    int best_x = 0;
    int best_y = 0;
    for (int dy = -radius; dy <= radius; dy++) {
        for (int dx = -radius; dx <= radius; dx++) {
            int nonzero = 0;
            if (!view_matches(wram, vram, map_base_word, scroll_x, scroll_y,
                              base_x + dx, base_y + dy, &nonzero, NULL) ||
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

#ifndef UR_WS_MARGINS_NO_RUNTIME

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "common_rtl.h"
#include "snes/ppu.h"
#include "snes/ws_shadow.h"

/* BG1 scroll HDMA table (channel 4 -> $210D/$210E): line count, then H and
 * V words. The game rebuilds it each frame before the PPU frame runs. */
enum {
    kBg1ScrollTable = 0x2046,
    kCameraX = 0x0419,
    kCameraY = 0x041D,
    kCalibrationRadius = 3,
    kCalibrationMinNonzero = 4,
    /* Live views may transiently expose a stale cell while an edge streams;
     * margins stay presented through a few, a real drift trips this. */
    kMaxFrameMismatches = 8,
};

static int s_ever_active;
static int s_calibrated;
static uint32_t s_world_x;
static uint32_t s_world_y;
static uint16_t s_prev_scroll_x;
static uint16_t s_prev_scroll_y;
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

int ur_ws_margins_calibrated(void) { return s_calibrated; }

static int32_t signed10(uint16_t delta) {
    delta &= 0x3FF;
    return delta >= 0x200 ? (int32_t)delta - 0x400 : (int32_t)delta;
}

static void prefill_margins(int extra_pixels) {
    const int rows = UR_WS_BG1_VIEW_ROWS + 1;
    const int ty0 = (int)(s_world_y >> UR_WS_BG1_TILE_SHIFT);
    const int left_px = (int)s_world_x - extra_pixels;
    const int right_px = (int)s_world_x + 256;
    const int span = extra_pixels + 16;
    for (int side = 0; side < 2; side++) {
        const int start_px = side ? right_px : left_px;
        const int tx_first = start_px >> UR_WS_BG1_TILE_SHIFT;
        const int tx_last = (start_px + span - 1) >> UR_WS_BG1_TILE_SHIFT;
        for (int tx = tx_first; tx <= tx_last; tx++) {
            for (int row = 0; row < rows; row++) {
                uint16_t entry = 0;
                if (tx < 0 || !ur_ws_course_tile(g_ram, tx, ty0 + row, &entry))
                    continue;
                WsShadowPrefillTile(0, (uint32_t)tx, (uint32_t)(ty0 + row),
                                    entry);
            }
        }
    }
}

void ur_ws_margins_prepare_frame(int enabled, int extra_pixels) {
    if (!g_ppu)
        return;
    if (!enabled || extra_pixels <= 0) {
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
        s_calibrated = 0;
        return;
    }

    const uint16_t scroll_x = (uint16_t)(read16(g_ram, kBg1ScrollTable + 1) & 0x3FF);
    const uint16_t scroll_y = (uint16_t)(read16(g_ram, kBg1ScrollTable + 3) & 0x3FF);
    const uint16_t map_base = (uint16_t)PPU_bgTilemapAdr(g_ppu, 0);
    const int big_tiles = PPU_bigTiles(g_ppu, 0) != 0;

    if (s_calibrated) {
        s_world_x = (uint32_t)((int32_t)s_world_x +
                               signed10((uint16_t)(scroll_x - s_prev_scroll_x)));
        s_world_y = (uint32_t)((int32_t)s_world_y +
                               signed10((uint16_t)(scroll_y - s_prev_scroll_y)));
        const int offset_x = (int)(s_world_x >> UR_WS_BG1_TILE_SHIFT) -
                             (scroll_x >> UR_WS_BG1_TILE_SHIFT);
        const int offset_y = (int)(s_world_y >> UR_WS_BG1_TILE_SHIFT) -
                             (scroll_y >> UR_WS_BG1_TILE_SHIFT);
        int mismatches = 0;
        view_matches(g_ram, g_ppu->vram, map_base, scroll_x, scroll_y,
                     offset_x, offset_y, NULL, &mismatches);
        if (mismatches) {
            s_mismatch_frames++;
            if (mismatches > s_max_mismatches)
                s_max_mismatches = mismatches;
        }
        if (!big_tiles || mismatches > kMaxFrameMismatches) {
            s_calibrated = 0;
            if (trace_enabled())
                fprintf(stderr, "URWS_MARGINS LOST mismatches=%d big_tiles=%d\n",
                        mismatches, big_tiles);
        }
    }
    if (!s_calibrated && big_tiles) {
        int offset_x = 0;
        int offset_y = 0;
        if (ur_ws_calibrate_bg1(g_ram, g_ppu->vram, map_base, scroll_x,
                                scroll_y, read16(g_ram, kCameraX) >> 4,
                                read16(g_ram, kCameraY) >> 4,
                                kCalibrationRadius, kCalibrationMinNonzero,
                                &offset_x, &offset_y)) {
            s_calibrated = 1;
            s_world_x = (uint32_t)(((scroll_x >> UR_WS_BG1_TILE_SHIFT) + offset_x)
                                   << UR_WS_BG1_TILE_SHIFT) | (scroll_x & 15u);
            s_world_y = (uint32_t)(((scroll_y >> UR_WS_BG1_TILE_SHIFT) + offset_y)
                                   << UR_WS_BG1_TILE_SHIFT) | (scroll_y & 15u);
            if (trace_enabled())
                fprintf(stderr,
                        "URWS_MARGINS CALIBRATED offset=%d,%d world=%u,%u scroll=%u,%u\n",
                        offset_x, offset_y, (unsigned)s_world_x,
                        (unsigned)s_world_y, (unsigned)scroll_x,
                        (unsigned)scroll_y);
        }
    }
    s_prev_scroll_x = scroll_x;
    s_prev_scroll_y = scroll_y;

    if (!s_calibrated) {
        if (s_ever_active)
            WsShadowFrame(g_ppu); /* deactivate: nothing registered */
        return;
    }

    WsShadowSetWorld(0, s_world_x, s_world_y);
    WsShadowSetScroll(0, scroll_x, scroll_y);
    WsShadowFrame(g_ppu);
    prefill_margins(extra_pixels);
    s_ever_active = 1;
    s_presented_frames++;
}

#endif /* UR_WS_MARGINS_NO_RUNTIME */

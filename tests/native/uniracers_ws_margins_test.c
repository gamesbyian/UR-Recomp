#include "uniracers_ws_margins.h"

#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/* Synthetic course: 8x4 coarse sectors (32x16 cells). Each sector gets its
 * own 32-byte fine record whose 16 words encode (cell_x, cell_y) so every
 * cell is distinguishable, except a blank row band to exercise blanks. */
enum { kCoarseW = 8, kCoarseH = 4 };

static uint16_t cell_word(int x, int y) {
    if (y == 3)
        return 0;
    return (uint16_t)(0x1000 | (y << 6) | x);
}

static void put16(uint8_t* wram, uint32_t addr, uint16_t v) {
    wram[addr] = (uint8_t)v;
    wram[addr + 1] = (uint8_t)(v >> 8);
}

static uint8_t* build_wram(void) {
    uint8_t* wram = calloc(0x20000, 1);
    assert(wram);
    put16(wram, 0x04F1, kCoarseW);
    put16(wram, 0x04F3, kCoarseH);
    for (int sy = 0; sy < kCoarseH; sy++) {
        for (int sx = 0; sx < kCoarseW; sx++) {
            const uint16_t record = (uint16_t)(sy * kCoarseW + sx);
            put16(wram, 0x10000 + 0x000F + (uint32_t)record * 2u, record);
            for (int fy = 0; fy < 4; fy++)
                for (int fx = 0; fx < 4; fx++)
                    put16(wram,
                          0x10000 + 0x800F + (uint32_t)record * 32u +
                              (uint32_t)(fy * 4 + fx) * 2u,
                          cell_word(sx * 4 + fx, sy * 4 + fy));
        }
    }
    return wram;
}

/* Stream the 32x32 ring as the game would for a view whose top-left course
 * cell is (cx, cy) at BG1 scroll (scroll_x, scroll_y). */
static void stream_view(const uint8_t* wram, uint16_t* vram, uint16_t base,
                        uint16_t scroll_x, uint16_t scroll_y, int cx, int cy) {
    for (int row = 0; row <= UR_WS_BG1_VIEW_ROWS; row++) {
        for (int col = 0; col < UR_WS_BG1_VIEW_COLS; col++) {
            uint16_t v = 0;
            (void)ur_ws_course_tile(wram, cx + col, cy + row, &v);
            const int mr = ((scroll_y >> 4) + row) & 31;
            const int mc = ((scroll_x >> 4) + col) & 31;
            vram[(base + (mr << 5) + mc) & 0x7FFF] = v;
        }
    }
}

int main(void) {
    uint8_t* wram = build_wram();
    uint16_t* vram = calloc(0x8000, sizeof(uint16_t));
    assert(vram);

    uint16_t v = 0;
    assert(ur_ws_course_tile(wram, 5, 2, &v) && v == cell_word(5, 2));
    assert(ur_ws_course_tile(wram, 31, 15, &v) && v == cell_word(31, 15));
    assert(!ur_ws_course_tile(wram, 32, 0, &v));
    assert(!ur_ws_course_tile(wram, -1, 0, &v));
    assert(!ur_ws_course_tile(wram, 0, 16, &v));

    /* Corrupt dimensions must not wrap the bank-$7F coarse-table address back
     * into a readable range. */
    put16(wram, 0x04F1, 0xFFFF);
    put16(wram, 0x04F3, 0xFFFF);
    assert(!ur_ws_course_tile(wram, 262139, 262139, &v));
    put16(wram, 0x04F1, kCoarseW);
    put16(wram, 0x04F3, kCoarseH);

    /* Public calibration bounds are part of the guest-memory contract. */
    assert(!ur_ws_calibrate_bg1(wram, vram, 0, 0, 0, -1, 1, 0, 0, 0, 0,
                                NULL, NULL));
    assert(!ur_ws_calibrate_bg1(wram, vram, 0, 0, 0, 223, 2, 0, 0, 0, 0,
                                NULL, NULL));

    /* Scroll cell (9,12) shows course cell (10,0): offset (+1,-12). The
     * course is only 32 wide, so keep the view inside it. */
    const uint16_t base = 0x0C00;
    stream_view(wram, vram, base, 152, 203, 10, 0);
    int ox = 0, oy = 0;
    assert(ur_ws_calibrate_bg1(wram, vram, base, 152, 203, 0, 224, 11, 1, 3, 4, &ox, &oy));
    assert(ox == 1 && oy == -12);

    /* Outside the search radius: fail closed. */
    assert(!ur_ws_calibrate_bg1(wram, vram, base, 152, 203, 0, 224, 2, 1, 3, 4, &ox, &oy));

    /* A corrupted visible entry rejects the calibration. */
    const uint16_t word = (uint16_t)(base + (((203 >> 4) + 4) << 5) + ((152 >> 4) + 4));
    const uint16_t saved = vram[word];
    vram[word] ^= 0x0001;
    assert(!ur_ws_calibrate_bg1(wram, vram, base, 152, 203, 0, 224, 11, 1, 3, 4, &ox, &oy));
    vram[word] = saved;

    /* An all-blank view matches every candidate: ambiguous, fail closed. */
    uint8_t* blank = calloc(0x20000, 1);
    assert(blank);
    memcpy(blank, wram, 0x20000);
    for (uint32_t a = 0x10000 + 0x800F; a < 0x10000 + 0x800F + kCoarseW * kCoarseH * 32; a++)
        blank[a] = 0;
    memset(vram, 0, 0x8000 * sizeof(uint16_t));
    assert(!ur_ws_calibrate_bg1(blank, vram, base, 152, 203, 0, 224, 11, 1, 3, 0, &ox, &oy));
    /* ...and with a non-blank minimum, no candidate qualifies. */
    assert(!ur_ws_calibrate_bg1(blank, vram, base, 152, 203, 0, 224, 11, 1, 3, 4, &ox, &oy));

    /* A lower split-screen band scrolls up by its first line, so the same
     * camera guess still finds the same course offset. */
    {
        uint16_t* bvram = calloc(0x8000, sizeof(uint16_t));
        assert(bvram);
        const uint16_t bbase = 0x1C00;
        const uint16_t bv = (uint16_t)(203 - 112);
        /* Course row 0 is shown at the band's first line (112). */
        const int want_oy = -(((int)bv + 112) >> 4);
        for (int row = 0; row <= 8; row++) {
            for (int col = 0; col < UR_WS_BG1_VIEW_COLS; col++) {
                uint16_t cv = 0;
                (void)ur_ws_course_tile(wram, 10 + col, row, &cv);
                const int mr = ((((int)bv + 112) >> 4) + row) & 31;
                const int mc = ((152 >> 4) + col) & 31;
                bvram[(bbase + (mr << 5) + mc) & 0x7FFF] = cv;
            }
        }
        assert(ur_ws_calibrate_bg1(wram, bvram, bbase, 152, bv, 112, 112,
                                   11, 1, 3, 4, &ox, &oy));
        assert(ox == 1 && oy == want_oy);
        free(bvram);
    }

    /* HDMA band tables: one 1P band, two split-screen bands, fail-closed
     * on repeat mode and misaligned tables. */
    {
        uint8_t* t = calloc(0x20000, 1);
        assert(t);
        UrWsBg1Band bands[2];
        const uint8_t one[] = {0x70, 0xEA, 0x2B, 0xD0, 0x00, 0x00};
        memcpy(t + UR_WS_BG1_SCROLL_TABLE, one, sizeof(one));
        t[UR_WS_BG1_SC_TABLE] = 0x70;
        t[UR_WS_BG1_SC_TABLE + 1] = 0x0C;
        assert(ur_ws_parse_bg1_bands(t, bands, 2) == 1);
        assert(bands[0].first_line == 0 && bands[0].line_count == 224);
        assert(bands[0].scroll_x == 0x3EA && bands[0].scroll_y == 0xD0);
        assert(bands[0].map_base_word == 0x0C00);

        const uint8_t two[] = {0x70, 0x98, 0x00, 0x11, 0x01,
                               0x01, 0x98, 0x00, 0xA1, 0x00, 0x00};
        const uint8_t two_sc[] = {0x70, 0x0C, 0x01, 0x1C, 0x00};
        memcpy(t + UR_WS_BG1_SCROLL_TABLE, two, sizeof(two));
        memcpy(t + UR_WS_BG1_SC_TABLE, two_sc, sizeof(two_sc));
        assert(ur_ws_parse_bg1_bands(t, bands, 2) == 2);
        assert(bands[0].line_count == 112 && bands[0].scroll_y == 0x111);
        assert(bands[1].first_line == 112 && bands[1].line_count == 112);
        assert(bands[1].scroll_y == 0xA1 && bands[1].map_base_word == 0x1C00);
        assert(ur_ws_parse_bg1_bands(t, bands, 1) == 0);

        t[UR_WS_BG1_SC_TABLE + 2] = 0x02; /* misaligned line counts */
        assert(ur_ws_parse_bg1_bands(t, bands, 2) == 0);
        t[UR_WS_BG1_SC_TABLE + 2] = 0x01;
        t[UR_WS_BG1_SCROLL_TABLE] = 0xF0; /* repeat mode */
        t[UR_WS_BG1_SC_TABLE] = 0xF0;
        assert(ur_ws_parse_bg1_bands(t, bands, 2) == 0);
        free(t);
    }

    free(blank);
    free(vram);
    free(wram);
    return 0;
}

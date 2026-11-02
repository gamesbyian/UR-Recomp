#include "uniracers_ws_margins.h"
#include "common_rtl.h"
#include "snes/ws_shadow.h"
#include <assert.h>
#include <stdint.h>
#include <string.h>

/* Compile the actual production C source against instrumented shadow calls.
 * No emulator/ROM, synthetic unique course words and effective BG1 VRAM. */
uint8_t g_ram[0x20000];
static Ppu ppu;
Ppu* g_ppu = &ppu;
static int frames, worlds, forces, splits, resets;
void WsShadowReset(void) { resets++; }
void WsShadowFrame(Ppu* unused) { (void)unused; frames++; }
void WsShadowSetWorld(int layer,uint32_t x,uint32_t y) {
    (void)layer; (void)x; (void)y; worlds++;
}
void WsShadowSetScroll(int layer,uint32_t x,uint32_t y) {
    (void)layer; (void)x; (void)y;
}
void WsShadowSetSplit(int layer,int first_line,uint32_t wx,uint32_t wy,
                      uint32_t sx,uint32_t sy) {
    (void)layer; (void)first_line; (void)wx; (void)wy;
    (void)sx; (void)sy; splits++;
}
void WsShadowForceTile(int layer,uint32_t x,uint32_t y,uint16_t entry) {
    (void)layer; (void)x; (void)y; (void)entry; forces++;
}
static void put16(uint32_t addr,uint16_t v) {
    g_ram[addr]=(uint8_t)v;
    g_ram[addr+1]=(uint8_t)(v>>8);
}
static void course(void) {
    memset(g_ram,0,sizeof(g_ram));
    memset(&ppu,0,sizeof(ppu));
    put16(0x04F1,8); put16(0x04F3,8);
    for(int sy=0;sy<8;sy++) for(int sx=0;sx<8;sx++) {
        uint16_t rec=(uint16_t)(sy*8+sx);
        put16(0x10000+0x000F+2u*rec,rec);
        for(int fy=0;fy<4;fy++) for(int fx=0;fx<4;fx++) {
            int x=sx*4+fx,y=sy*4+fy;
            put16(0x10000+0x800F+32u*rec+2u*(fy*4+fx),
                  (uint16_t)(0x1000|(y<<6)|x));
        }
    }
}
static void hdma(int split) {
    const uint32_t scroll=UR_WS_BG1_SCROLL_TABLE;
    const uint32_t sc=UR_WS_BG1_SC_TABLE;
    g_ram[scroll]=112; g_ram[scroll+5]=112; g_ram[scroll+10]=0;
    g_ram[sc]=112; g_ram[sc+1]=0x0C;
    g_ram[sc+2]=112; g_ram[sc+3]=split?0x1C:0x0C;
    g_ram[sc+4]=0;
    put16(0x0419,0); put16(0x041D,0);
    put16(0x041B,0); put16(0x041F,112);
}
static void stream(uint16_t base,int first_row,int last_row) {
    for(int row=first_row;row<=last_row;row++) for(int col=0;col<17;col++) {
        uint16_t tile=0;
        assert(ur_ws_course_tile(g_ram,col,row,&tile));
        ppu.vram[base+((row&31)<<5)+col]=tile;
    }
}
static void flip_nine(uint16_t base,int row) {
    for(int col=1;col<=9;col++)
        ppu.vram[base+((row&31)<<5)+col]^=1;
}
static void counters(void) { frames=worlds=forces=splits=0; }
static void present(void) {
    counters(); ur_ws_margins_prepare_frame(1,43);
    assert(frames==1 && worlds==1 && forces>0);
}
static void suppress(void) {
    counters(); ur_ws_margins_prepare_frame(1,43);
    assert(frames==1 && worlds==0 && forces==0 && splits==0);
}
int main(void) {
    course(); hdma(0); stream(0x0C00,0,14);
    present(); assert(ur_ws_margins_calibrated());
    flip_nine(0x0C00,1);
    suppress(); assert(ur_ws_margins_calibrated());
    flip_nine(0x0C00,1);
    present();
    flip_nine(0x0C00,1);
    suppress(); suppress(); assert(!ur_ws_margins_calibrated());
    ur_ws_margins_prepare_frame(0,0);

    course(); hdma(1); stream(0x0C00,0,7); stream(0x1C00,7,14);
    counters(); ur_ws_margins_prepare_frame(1,43);
    assert(frames==1 && worlds==1 && forces>0 && splits==1);
    flip_nine(0x1C00,8);
    suppress(); assert(ur_ws_margins_calibrated());
    flip_nine(0x1C00,8);
    counters(); ur_ws_margins_prepare_frame(1,43);
    assert(frames==1 && worlds==1 && forces>0 && splits==1);
    return 0;
}

#ifndef UR_TEST_WS_SHADOW_H
#define UR_TEST_WS_SHADOW_H
#include <stdint.h>
#include "snes/ppu.h"
void WsShadowReset(void);
void WsShadowFrame(Ppu* ppu);
void WsShadowSetWorld(int layer, uint32_t x, uint32_t y);
void WsShadowSetScroll(int layer, uint32_t x, uint32_t y);
void WsShadowSetSplit(int layer, int first_line, uint32_t wx, uint32_t wy,
                      uint32_t sx, uint32_t sy);
void WsShadowForceTile(int layer, uint32_t x, uint32_t y, uint16_t entry);
#endif

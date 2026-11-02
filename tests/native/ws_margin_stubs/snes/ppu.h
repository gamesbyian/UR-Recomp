#ifndef UR_TEST_PPU_H
#define UR_TEST_PPU_H
#include <stdint.h>
typedef struct Ppu { uint16_t vram[0x8000]; } Ppu;
static inline int PPU_bigTiles(Ppu* ppu, int layer) {
    (void)ppu; (void)layer; return 1;
}
#endif

# Uniracers active-display OAM behavior

Retrieved: 2026-09-28

Uniracers is unusually valuable as an emulator-accuracy test because its split-screen rendering appears to depend on sprite/OAM behavior during active display.

## Snes9x

Pinned source revision:
https://github.com/snes9xgit/snes9x/tree/1bcc369e89f08243e0a462882fb1f3e42e51de3a

Relevant files:

- `dma.cpp`, blob `e1ad324c6e94149a777b69054bda5e09337631a6`
- `memmap.cpp`, blob `04ce87e7362b8dda8cb7a79abfa226e13d3568f4`

At this revision Snes9x explicitly recognizes the internal ROM name `UNIRACERS` and enables a game-specific OAM workaround. During an HDMA transfer to PPU register $2104 (OAM data), that workaround forces the OAM address to 0x10c and resets the write flip state. The source labels this a hack necessitated by incomplete understanding of OAM address invalidation.

This gives UR-Recomp an exact implementation seam to test rather than merely “the graphics glitch in some emulators.”

## MAME

Pinned source:
https://github.com/mamedev/mame/blob/dcca0e9b281be806813848db869d9ee54b4ad92e/src/devices/video/snes_ppu.cpp

Blob:
`525911c9cf3015b27676bcc0aebfecd6e6dd3b64`

MAME's SNES PPU implementation independently documents that OAM access during active display uses an address affected by the PPU's own rendering accesses. Its comment identifies Uniracers as the known commercial game relying on this behavior and routes active-display OAM access to offset 0x0218 as an emulation workaround.

The Snes9x value 0x10c is a word-style OAM address corresponding to byte offset 0x218, so the two implementations are pointing at the same effective location.

## Hardware research and developer history

Later SNES-development discussions on NESdev analyze this in terms of the internal OAM address used during sprite evaluation rather than the programmer-visible OAM address registers. Those discussions are useful for replacing emulator hacks with a hardware model.

Mike Dailly has also described DMA-era “sprite ripping” / raster manipulation in Uniracers: sprite positions were changed during display to achieve the game's split-screen presentation, and Nintendo reportedly asked DMA to verify it on older SNES hardware because the technique pushed outside normal documented usage.

## Project implication

Before adding a compatibility hack to SNESRecomp, capture the game's HDMA writes to $2104 and the runtime's OAM behavior. The target should be a hardware-faithful explanation if practical, with a narrowly scoped compatibility path only if necessary.

This is a particularly high-value early validation case because an incorrect implementation can look like a game/rendering bug while actually being a PPU timing/addressing mismatch.

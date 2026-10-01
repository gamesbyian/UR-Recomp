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


## jgenesis: precise Vs.-mode behavior

jgenesis issue #164 and the corresponding modern sprite implementation substantially sharpen the model.

The issue author reports that Uniracers writes OAMDATA during HBlank on scanlines 0 and 112 every frame, around H=282–284 in that emulator. The values are 0xA5 on line 0 and 0x5A on line 112, and both are expected to affect byte $18 of high OAM, which contains high-X and size/tile-selection bits for sprites 96–99.

The intended display trick is very specific:

- sprites 98–99 are visible only in the top half;
- sprites 96–97 are visible only in the bottom half;
- the line-0 write moves 96–97 offscreen and 98–99 onscreen;
- the line-112 write reverses that arrangement.

jgenesis models the relevant PPU behavior by retaining the OAM index of the last fetched sprite tile and using that index for mid-scanline OAM writes when no sprites were scanned in range. The source explicitly notes that Uniracers depends on this in Vs. mode.

Mirrored source:
`reference/imported/emulators/jgenesis/sprites.rs`

Issue:
https://github.com/jsgroth/jgenesis/issues/164

This is much more actionable than the older emulator hacks because it gives us expected scanlines, write values, affected sprite indices and the rendering intent.

## Canoe / SNES Classic investigation

A separate 2018 reverse-engineering effort by sluffy for Nintendo's Canoe emulator reportedly diagnosed essentially the same behavior. Contemporary discussion describes Uniracers as relying on four sprites arranged so that the last sprite accessed lands on the required OAM location. A later patch reportedly fixed the disappearing/ghost-racer behavior in 1P, 2P and Vs. modes.

The surviving forum trail is useful even before the patch itself is recovered because it independently corroborates that the game's split-screen trick depends on the PPU's internal OAM-access state, not merely on ordinary OAM register semantics.

## ZSNES history

The mirrored ZSNES history records “Uniracers works in 2 player mode” in v1.337. That gives us a historical lower bound for when another emulator first corrected enough of the relevant behavior to make multiplayer functional.

Mirrored history:
`reference/imported/emulators/zsnes/history.html`


## Earlier Snes9x compatibility history

The preserved 1.43-era changelog shows that Uniracers was historically sensitive to more than the active-display OAM issue:

- a LoROM SRAM mapping fix was specifically noted as making Uniracers work;
- an XOR window logic/area inversion fix was noted as making Uniracers render correctly;
- an experiment switched empty-subscreen color addition from fixed color to backdrop color because “Uniracers seems to need it,” but that change was disabled again because it caused regressions, including later Uniracers screens;
- a later entry explicitly announces a “Working Uniracers hack (dma.cpp),” corresponding to the OAM/HDMA workaround preserved beside the changelog.

This history is useful as a regression-test inventory: SRAM mapping, window-combination logic, color math/subscreen semantics, and active-display OAM should all be tested independently rather than treating every visual problem as the same quirk.

Mirrored file:
`reference/imported/emulators/snes9x-1.43/changes.txt`


## Local deterministic validation

The recovered external predictions are now locally reproduced by the frozen canonical-ROM VS fixture rather than remaining historical-only clues.

The permanent `VS split-screen reference regression` drives the same neutral two-controller stream through patched pinned Snes9x and independent repository-owned Beetle/bsnes. Both reach stable split-screen gameplay. The Snes9x debug journal then records exactly:

```text
scanline 0    $2104 <- $A5  via HDMA
scanline 112  $2104 <- $5A  via HDMA
```

at every sampled stable race checkpoint. HDMA channel 1 is mode 0 to `$2104`, sourced from `7E:206C`, whose stable table is `70 A5 70 5A 00`: 112 lines of `$A5`, then 112 lines of `$5A`, then termination.

The captured end-of-frame OAM snapshot also has `OAM[0x218] = 0x5A` at every stable race checkpoint. That local result aligns with the independent Snes9x/MAME/jgenesis/SNESdev interpretation that the active-display write is routed to byte offset `0x218`. Since high OAM occupies `0x200..0x21F`, offset `0x218` is high-table byte index `0x18`, and one high-table byte carries two bits each for four sprites: **sprites 96-99**.

The two alternating values decode as:

| value | sprite 96 | sprite 97 | sprite 98 | sprite 99 |
| --- | --- | --- | --- | --- |
| `$A5` | X-msb 1, size 0 | X-msb 1, size 0 | X-msb 0, size 1 | X-msb 0, size 1 |
| `$5A` | X-msb 0, size 1 | X-msb 0, size 1 | X-msb 1, size 0 | X-msb 1, size 0 |

This is exactly the pairwise swap expected by the recovered jgenesis description of the top/bottom-half rider sprite trick.

Durable assertions:

- `tools/assert_uniracers_vs_oam_seam.py` checks the active-display scanline/value events.
- `tools/decode_uniracers_oam_split.py` checks `OAM[0x218]`, maps it to sprites 96-99, and exposes the four two-bit high-OAM fields.
- `.github/workflows/vs-split-screen-reference.yml` runs both assertions on the frozen race route.

What remains open is implementation architecture, not the target: SNESRecomp should preferably reproduce the general internal OAM cursor behavior that naturally routes the write to `0x218`; a title-specific compatibility rule is a fallback only if a faithful general model is impractical.

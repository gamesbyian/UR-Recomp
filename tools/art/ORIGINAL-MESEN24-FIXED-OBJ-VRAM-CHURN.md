# ART-4K: the original racer source OBJ graphics change through VRAM tile payloads

**Original 1994 game observation, November 3–4 2026.** The genuine source racer's 64×64 held SNES sprite uses fixed OAM tile references while its 4bpp tile graphics **change every captured original emulator tick**. This establishes a concrete source-level graphics update mechanism but **does not identify which CPU/DMA/PPU writer or original 3D algorithm produces those bytes**.

## Independent original source

Reuse the already **merged** no-frame-skip Mesen 24-consecutive-PPU archive [#3103](https://github.com/gamesbyian/UR-Recomp/pull/3103), original bridge ticks **1601–1624**, SHA-256 `28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6`. Its original-USA-ROM SHA and controller replay are independently pinned, and original overlap ticks 1601/1607/1618 match the previously archived sparse run byte-for-byte in OAM, VRAM, CGRAM and completed-screen P6. No new original emulator execution or ROM checkout is needed for this analysis.

The existing original OBJ decoder `tools/art/audit_original_mesen_obj_screen_pixels.py` uses the previous authenticated PPU **OBSEL mode 4**, OBJ word base `0x6000`, second table offset `0x1000` and SNES tile-row/column wrapping. **OBSEL was not independently sampled at every tick in this 24-tick capture**; the same frozen previous register witness is used for every new sample. The source-only auditor verifies the exact zip and every backing PPU region before reading the fixed original OAM slots 96/97 and their 64 original 8×8 4bpp tiles (32 bytes each, 2,048 relevant VRAM bytes per racer per tick). The source sprite’s own alpha and 4bpp index plane are independently decoded from those bytes.

## Actual original held-source observations

| Source OAM sprite property / pixel payload | Blue (OAM 96) | Red (OAM 97) |
|---|---:|---:|
| OAM tile-number/upper-bank word | **136**, unchanged | **0**, unchanged |
| OBJ palette ID | **4**, unchanged | **3**, unchanged |
| OAM size, source H/V flips | 64×64, none | 64×64, none |
| Fixed unique 8×8 tile word addresses | 64 | 64 |
| Total tile bytes backing the sprite | 2,048 | 2,048 |
| Changed backing tile-byte instances across 23 real adjacent ticks | **1,457** | **1,565** |
| Changed 8×8 tile instances across those ticks | 122 | 127 |
| Adjacent frames with changed relevant VRAM bytes | **23/23** | **23/23** |
| Adjacent frames with changed source 4bpp index plane | **23/23** | **23/23** |
| Changed selected 16-colour CGRAM palette bytes | **0** | **0** |

These are **changed-byte/tile instances summed across 23 transitions**, not a count of unique source VRAM addresses over time. Every original source tile number, selected palette, size flag, source horizontal flip, source vertical flip and set of 64 VRAM tile addresses stays fixed throughout the 24 observed frames. Original OAM positions are *not* globally constant: blue held OAM X advances exactly **82→105** one pixel per tick, with held OAM Y=151; red held OAM X/Y remain 48/48. Do not confuse sprite position updates with sprite tile-content changes.

At the original **blue 1602→1603** upper-silhouette event, the relevant sprite VRAM tile payload changes **253 bytes across 15 tile instances**. At the **red 1605→1606** event it changes **238 bytes across 15 tiles**. Ordinary **1609→1610** changes **57 bytes across six blue tiles** and **71 bytes across six red tiles**. The source index-plane and alpha events coincide with actual backing tile-byte differences. The source-selected CGRAM palette remains unchanged across all 24 snapshots, excluding palette-only recolouring as an explanation of the decoded index changes.

**Causal distinction:** The observed 2D sprite cannot be explained as a mere OAM tile-number switch, player palette swap, or H/V flip in this window. Its decoded original 4bpp image changes because the graphics data at its **unchanged VRAM tile addresses** changes. This makes the original producer of those tile bytes a direct, verifiable reverse-engineering target. The co-timed state snapshots alone **cannot** distinguish writes made by the original CPU, DMA transfer, intervening producer buffers, per-scanline effects or other source code, nor prove that a 3D mesh was rasterized on the SNES.

## Consequence for the unapproved 2026 GLB

The author's current experimental one-GLB rig in [#3101](https://github.com/gamesbyian/UR-Recomp/pull/3101) only changes visible 2026 material boundaries at **9–16** pixels over three selected genuine original adjacent transitions, while the corresponding actual original 4bpp source changes at up to **176 blue / 192 red** opaque-interior pixels. The original 1994 game clearly produces evolving 2D tile content, whether via source drawing/animation, transformations or a deeper 3D engine. No inference that the current 2026 mesh's symmetric materials represent those original source pixels is justified.

**Next cheap causal investigation:** inspect the existing Mesen bridge/PPU write tracing capability and ROM/disassembly provenance for **writes or DMA transfers into the stable VRAM tile address sets of OAM96 and OAM97**. Begin at the two 15-tile upper events with the existing deterministic replay, and determine source writer PC/call path, buffer lifetime and whether a reusable pose/geometry input exists. First reuse existing traces, VRAM/DMA instrumentation and ROM research; only add one *targeted* original emulator capture if available evidence cannot identify the writer. Predeclare the exact CPU/DMA/PPU observation, provenance and stop criterion. A producer of 2D tiles is not automatically a recovered 3D model; preserve all alternatives.

No part semantics, original physical camera, user-approved character likeness, production artwork or Windows release gate is established by this original source evidence.

## Replay-free reproduction and receipt

```sh
python3 -m unittest tests.unit.test_art4k_mesen24_fixed_obj_vram_payload
python3 -m tools.art.audit_original_mesen24_racer_vram_payload \
  --source-zip analysis/data/racer-original-mesen-consecutive-1601-1624-20261103.zip \
  --out /private/new/original-vram-tile-payload.json
```

The concrete source-only numerical report is `analysis/data/racer-original-mesen24-fixed-obj-vram-payload-20261103.json`, SHA-256 **`05c0e44a9143778c15d8119f74931ce65c03b59a638d087f9405f5409c72566c`**. The no-overwrite reporter authenticates exact source archives and their member hashes, all 24 source OAM descriptors, each of the 64 tile payloads at every tick, the original relevant CGRAM palette and per-edge byte/tile counts. Its five standard-library unit tests cover SNES 15-bit VRAM word-address wrap, 4bpp 16-word/32-byte decoding, immutable report hash, all 23 byte-change witnesses, source-held position variations, event counts and corrupt/missing source rejection. The HP real-archive run and all five unit tests passed. No new emulator run, new workflow, geometry variants or API costs were required.

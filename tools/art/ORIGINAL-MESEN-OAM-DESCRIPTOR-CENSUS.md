# Original live-Mesen SNES OAM descriptor anatomy-free census

## Why this exists

The authenticated original PPU raw capture in [#3065](https://github.com/gamesbyian/UR-Recomp/pull/3065) exposed real SNES OAM, VRAM and CGRAM on two consecutively held MesenCE emulator ticks. Its proven 544-byte OAM array does **not** by itself specify pixel ownership, OBJ size in pixels, onscreen racer identity, source 1994 3D geometry or camera. The first follow-up is strictly to decode the **128 SNES OBJ descriptors** correctly without silently assigning them source character bones.

`tools/art/audit_original_mesen_oam_descriptors.py` requires the exact original [run #41560222232 raw source ZIP #13196973168](https://github.com/gamesbyian/UR-Recomp/actions/runs/41560222232/artifacts/13196973168) and its independently matched SHA-256. No substitute screenshots or authored-registry time labels pass. The decoder derives each OAM entry's low X/Y/tile/attribute bytes and the **two high-table bits per slot**: 9th X bit and small/large OBJ selection. It converts nine-bit X to signed screen-relative coordinates, separates tile MSB, OBJ palette, priority and H/V flip, but **does not infer concrete 8×8/16×16/32×32/64×64 dimensions without original OBSEL configuration**. It reports all 128 entries and, as a neutral reduction, the most common *descriptor* plus exceptional slots. A modal offscreen-looking descriptor is a statistical pattern; never call it an invisible tile without source PPU framebuffer and size/clip validation.

## Measured result

At original emulator bridge ticks **1219 and 1220**, the OAM SHA is unchanged: `14b0cfa18b3bd1c7ca0a1459490047d6b57a95eccdf4d258cff249265ee083f7`. Exactly **123 of 128** slots have the identical descriptor with nine-bit signed X **−32**, raw Y **224**, tile index **0**, palette **0**, priority **0**, no flip and small-size selection.

Five slots depart from that mode in *both* live states: **0, 96, 97, 98, 99**. Slot 0 differs only by raw Y=0. Slots 96 and 97 share signed X=104/Y=153 with large-size selection and tile words 136 and 0, palette 4 and 3, priority 2, horizontally flipped. Slots 98 and 99 share signed X=−152/Y=40 with small-size selection, the same two palette/tile alternatives. These are genuine real original-emulator OAM records; they remain **unidentified OBJ source candidates**, without proven 1P/2P racer membership or visibility.

Across the adjacent ticks, **zero** OAM bytes changed while **38** VRAM and **17** CGRAM bytes changed. Thus further source animation evaluation must inspect VRAM/CGRAM and the actual simultaneously captured framebuffer, not count changed OAM positions as an animation proxy. This source-only anomaly inventory does **not** validate original 1994 motion cadence, canonical 3D rig pivots, wheel material, physical contact or owner likeness.

The one-off authenticated source execution [run #41564535323](https://github.com/gamesbyian/UR-Recomp/actions/runs/41564535323) passed both synthetic tests and real original emulator archive decoding. Its [bounded numerical output #13198528214](https://github.com/gamesbyian/UR-Recomp/actions/runs/41564535323/artifacts/13198528214) contains 7,101 bytes, SHA-256 `bf28344faa6f176bc70f00b0e56964dcdfff732b58ce36ae03826401c3c51ae5`. Independently decoding the original actual 544-byte OAM with the SNES high-table word positions reproduced all five outlier slot IDs, source 9-bit X, palette/priority/flip/size-selection flags, 123 modal records, and all 0/38/17 raw memory byte differences. It did not establish framebuffer visibility or OBJSEL pixel dimensions.

The source ZIP expires around November 10, 2026. The complete bounded numerical observation, exact raw-source SHA, decoded slot numbers and explicit negative claims remain in `analysis/data/racer-original-mesen-oam-structure-20261103.json`. The test suite covers 2-bit high table packing, signed X, palette/priority/hflip/vflip, tile MSB and fail-closed archived-source SHA checks:

```sh
python3 -m unittest tests.unit.test_audit_original_mesen_oam_descriptors
python3 -m tools.art.audit_original_mesen_oam_descriptors \
  --original-raw-archive /path/to/actual-run41560222232-original-PPU.zip \
  --out /private/new/original-OAM-descriptor-census.json
```

**Next acceptance discriminator:** source PPU OBJSEL/size+VRAM+CGRAM decoding, 1P/2P OAM membership and actual source framebuffer pixel comparison **from the same emulator pause**. Do not infer original 3D part labels from per-slot IDs or merely from 2D colour/alpha patterns.


## Actual original source OBJ size and address mode (executed MesenCE, November 3)

The source-only [real pinned original Mesen register census #41582586941](https://github.com/gamesbyian/UR-Recomp/actions/runs/41582586941) succeeded under no-frame-skip and independently produced [seven-day original PPU register evidence #13206716770](https://github.com/gamesbyian/UR-Recomp/actions/runs/41582586941/artifacts/13206716770) (ZIP SHA-256 `849abdaf241c5951e8b1627c0c9622989d421266bfcdd1c47ac2918c5c81df21`, selected source JSON SHA-256 `b3b80d032cbfc3a6fa225c8cb524172e924e633ae27916be37dc9e2293c2cf40`). The source emulator returned 598 total serialized fields per halted tick; 18 relevant PPU fields, selected by their exact upstream `ppu.` namespace and original serializer suffixes, were present at **both held bridge ticks 1219 and 1220**.

The two original source snapshots have identical selected PPU register values except the frame counter. Source `ppu.scanline=225`, `ppu.oamMode=4`, `ppu.oamBaseAddress=24576 (0x6000)`, `ppu.oamAddressOffset=4096 (0x1000)`, `ppu.oamRamAddress=256`, priority rotation disabled, PPU `bgMode=1`, brightness `15`, and forced blank false. **Source OBJ size-mode 4 resolves the previously unknown dimensions**: pinned MesenCE `SnesPpu::FetchSpritePosition` has small **16×16** and large **64×64** source sprite modes for OamMode 4; OAM high table bits select which. Thus authentic held OAM slots **96–97 are 64×64**, at source X=104/Y=153, and 98–99 are **16×16**, at signed X=−152/Y=40. The early OAM descriptor census was correct but intentionally did not infer sizes without this register source.

**Critical address-unit distinction:** MesenCE `SnesPpu::FetchSpriteAttributes` assembles `tileStart = (OamBaseAddress + (tileIndex << 4) + secondTableOffset)` in **word-addressed VRAM units** before its `& 0x7FFF` mask. The raw 65,536-byte VRAM capture is **byte addressed**; an independent decoder must apply the correct factor of two and 0x7FFF word mask, not read `0x6000` as a byte offset. The exact source values, all negative evidentiary flags and archive identities are frozen in `analysis/data/racer-original-live-mesen-ppu-serialized-registers-20261103.json`.

**Scope:** these are source PPU register values at one held point per original emulator tick; they do not establish which OBJ was on which split-screen scanline, visible source racer identity, final pixel alpha, original 1994 3D wheel/fork/saddle/rig, or source camera. The two known P6 screenshots are **countdown-overlaid**. Prefer an authenticated, no-skip, post-countdown source capture before any 3D registration or part-mapping inference.

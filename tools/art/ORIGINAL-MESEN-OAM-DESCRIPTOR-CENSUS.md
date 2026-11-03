# Original live-Mesen SNES OAM descriptor anatomy-free census

## Why this exists

The authenticated original PPU raw capture in [#3065](https://github.com/gamesbyian/UR-Recomp/pull/3065) exposed real SNES OAM, VRAM and CGRAM on two consecutively held MesenCE emulator ticks. Its proven 544-byte OAM array does **not** by itself specify pixel ownership, OBJ size in pixels, onscreen racer identity, source 1994 3D geometry or camera. The first follow-up is strictly to decode the **128 SNES OBJ descriptors** correctly without silently assigning them source character bones.

`tools/art/audit_original_mesen_oam_descriptors.py` requires the exact original [run #41560222232 raw source ZIP #13196973168](https://github.com/gamesbyian/UR-Recomp/actions/runs/41560222232/artifacts/13196973168) and its independently matched SHA-256. No substitute screenshots or authored-registry time labels pass. The decoder derives each OAM entry's low X/Y/tile/attribute bytes and the **two high-table bits per slot**: 9th X bit and small/large OBJ selection. It converts nine-bit X to signed screen-relative coordinates, separates tile MSB, OBJ palette, priority and H/V flip, but **does not infer concrete 8×8/16×16/32×32/64×64 dimensions without original OBSEL configuration**. It reports all 128 entries and, as a neutral reduction, the most common *descriptor* plus exceptional slots. A modal offscreen-looking descriptor is a statistical pattern; never call it an invisible tile without source PPU framebuffer and size/clip validation.

## Measured result

At original emulator bridge ticks **1219 and 1220**, the OAM SHA is unchanged: `14b0cfa18b3bd1c7ca0a1459490047d6b57a95eccdf4d258cff249265ee083f7`. Exactly **123 of 128** slots have the identical descriptor with nine-bit signed X **−32**, raw Y **224**, tile index **0**, palette **0**, priority **0**, no flip and small-size selection.

Five slots depart from that mode in *both* live states: **0, 96, 97, 98, 99**. Slot 0 differs only by raw Y=0. Slots 96 and 97 share signed X=104/Y=153 with large-size selection and tile words 136 and 0, palette 4 and 3, priority 2, horizontally flipped. Slots 98 and 99 share signed X=−152/Y=40 with small-size selection, the same two palette/tile alternatives. These are genuine real original-emulator OAM records; they remain **unidentified OBJ source candidates**, without proven 1P/2P racer membership or visibility.

Across the adjacent ticks, **zero** OAM bytes changed while **38** VRAM and **17** CGRAM bytes changed. Thus further source animation evaluation must inspect VRAM/CGRAM and the actual simultaneously captured framebuffer, not count changed OAM positions as an animation proxy. This source-only anomaly inventory does **not** validate original 1994 motion cadence, canonical 3D rig pivots, wheel material, physical contact or owner likeness.

The source ZIP expires around November 10, 2026. The complete bounded numerical observation, exact raw-source SHA, decoded slot numbers and explicit negative claims remain in `analysis/data/racer-original-mesen-oam-structure-20261103.json`. The test suite covers 2-bit high table packing, signed X, palette/priority/hflip/vflip, tile MSB and fail-closed archived-source SHA checks:

```sh
python3 -m unittest tests.unit.test_audit_original_mesen_oam_descriptors
python3 -m tools.art.audit_original_mesen_oam_descriptors \
  --original-raw-archive /path/to/actual-run41560222232-original-PPU.zip \
  --out /private/new/original-OAM-descriptor-census.json
```

**Next acceptance discriminator:** source PPU OBJSEL/size+VRAM+CGRAM decoding, 1P/2P OAM membership and actual source framebuffer pixel comparison **from the same emulator pause**. Do not infer original 3D part labels from per-slot IDs or merely from 2D colour/alpha patterns.

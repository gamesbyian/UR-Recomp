# Research Ledger

Use this for claims about the ROM, formats, routines, RAM, graphics or hardware behavior. Separate observation from interpretation.

## Entry template

### R-000 — Title

**Status:** hypothesis | supported | confirmed | rejected  
**Date:** YYYY-MM-DD  
**Area:** CPU | RAM | PPU | DMA/HDMA | physics | camera | course | compression | UI | audio | other

**Observation:** what was actually observed.  
**Evidence:** addresses, traces, hashes, debugger output, source references or repeatable steps.  
**Interpretation:** what it probably means.  
**Discriminating test:** smallest test distinguishing this from alternatives.  
**Dependencies:** assumptions this relies upon.

---

## Seed leads to verify locally

### R-SEED-001 — Rob Northen Compression

Historical reverse-engineering reports that original DMA developer Mike Dailly identified course/level data as Rob Northen Compression (RNC), and that investigators decompressed course data.

**Action:** independently locate and verify the decompression path in the supported ROM.

### R-SEED-002 — Course structure

Historical work reported block/tile-based course representations and very wide layouts.

**Action:** verify exact units, dimensions and indexing rather than inheriting old terminology.

### R-SEED-003 — OAM/HDMA special behavior

Snes9x has historically carried Uniracers-specific handling related to OAM address behavior during HDMA.

**Action:** test the current SNESRecomp runtime before designing a workaround.


---

## External evidence harvested 2026-09-28

### R-EXT-001 — Historical RNC/course extraction

**Status:** supported historical lead  
**Date:** 2026-09-28  
**Area:** compression | course

**Observation:** A preserved ROMhacking.net investigation records successful extraction/decompression of Uniracers course data after Mike Dailly reportedly identified it as Rob Northen Compression (RNC). The same work reports a 256-tile course width and says generated viewer output aligned with independently hand-made maps.  
**Evidence:** `references/notes/course-reverse-engineering-history.md` and its pinned source URLs.  
**Interpretation:** The ROM should contain an identifiable RNC-based course-data path, but exact record boundaries, RNC method and the meaning of “tile” remain to be reproduced.  
**Discriminating test:** locate candidate RNC headers/decompressor calls in the supported ROM and produce one course image/data structure that independently matches gameplay.  
**Dependencies:** historical forum archive and reported Mike Dailly correspondence.

### R-EXT-002 — Uniracers depends on active-display OAM behavior

**Status:** supported  
**Date:** 2026-09-28  
**Area:** PPU | DMA/HDMA

**Observation:** Current Snes9x source enables an explicit `UNIRACERS` game fix during HDMA writes to $2104, forcing OAM address 0x10c. MAME independently documents Uniracers as the known game that accesses OAM during active display and routes such access to byte offset 0x0218.  
**Evidence:** `references/notes/oam-active-display.md`; Snes9x revision `1bcc369e89f08243e0a462882fb1f3e42e51de3a`, `dma.cpp` blob `e1ad324c6e94149a777b69054bda5e09337631a6`, `memmap.cpp` blob `04ce87e7362b8dda8cb7a79abfa226e13d3568f4`; MAME revision `dcca0e9b281be806813848db869d9ee54b4ad92e`, `snes_ppu.cpp` blob `525911c9cf3015b27676bcc0aebfecd6e6dd3b64`.  
**Interpretation:** The values are consistent because word-style OAM address 0x10c corresponds to byte offset 0x218. This is a concrete compatibility seam for SNESRecomp bring-up.  
**Discriminating test:** trace Uniracers HDMA writes to $2104 and compare sprite/OAM results on SNESRecomp, a known-correct emulator and, if needed, hardware behavior documentation.  
**Dependencies:** correct interpretation of emulator OAM address units.

### R-EXT-003 — Cheat database as behavioral-address probe set

**Status:** hypothesis generator  
**Date:** 2026-09-28  
**Area:** RAM | physics | UI | other

**Observation:** libretro-database contains 24 Uniracers cheat entries affecting timer behavior, CPU braking, racer speed, stunt scoring, color state, course selection and race/qualification completion.  
**Evidence:** `references/imported/libretro/Uniracers (USA).cht`, upstream revision and license recorded in `references/imported/libretro/ATTRIBUTION.md`.  
**Interpretation:** Even without trusting cheat descriptions blindly, these codes are a compact set of candidate ROM/RAM locations for quickly locating important gameplay systems.  
**Discriminating test:** decode each Game Genie code to ROM addresses where applicable, classify RAM-vs-ROM effects, and verify each behavior against the supported ROM.  
**Dependencies:** cheat-code format/version compatibility with the supported US ROM.


### R-EXT-004 — Exact HBlank OAM writes in Vs. mode

**Status:** supported  
**Date:** 2026-09-28  
**Area:** PPU | DMA/HDMA

**Observation:** jgenesis issue #164 reports OAMDATA writes on scanlines 0 and 112 every frame, with values 0xA5 and 0x5A respectively. Both writes are expected to affect high-OAM byte $18, controlling sprites 96–99. The top-half/bottom-half split is implemented by alternately moving sprite pairs 96–97 and 98–99 on/off screen.  
**Evidence:** jgenesis issue #164 and mirrored `references/imported/emulators/jgenesis/sprites.rs`.  
**Interpretation:** This specifies the exact raster-time mechanism behind the long-known Uniracers OAM quirk and gives us concrete trace assertions for SNESRecomp.  
**Discriminating test:** trace $2104 writes during Vs. mode and verify scanlines, values and resulting high-OAM location against these expectations.  
**Dependencies:** supported ROM behaves equivalently to the version tested by jgenesis.

### R-EXT-005 — Released PAL prototype exists

**Status:** confirmed external artifact  
**Date:** 2026-09-28  
**Area:** other

**Observation:** Hidden Palace lists a publicly released European prototype built 1994-11-29 from a 4-EPROM SHVC-4PV5B-01 board labelled UNIRALLY PAL.  
**Evidence:** `references/catalog.yml` entry `hidden-palace-uniracers-prototype`.  
**Interpretation:** Binary-diffing this build against retail PAL and US versions could reveal late changes to physics, content, censoring, region logic, compression tables or rendering workarounds.  
**Discriminating test:** acquire the prototype artifact, hash it, identify header/version differences and perform structured binary/behavioral diffs.  
**Dependencies:** exact public prototype file retrieval.


### R-EXT-006 — Recovered Canoe compatibility patch

**Status:** confirmed external artifact  
**Date:** 2026-09-28  
**Area:** PPU | DMA/HDMA | other

**Observation:** The surviving public Google Drive file `uniracers_canoe.ips` was recovered byte-for-byte. It is a 295-byte IPS file created/modified on 2018-03-30. It contains seven records, including JSL hooks at ROM offsets `0x01534C` and `0x015714` into code installed at `0x1FFF00`, plus several smaller patches.  
**Evidence:** `references/imported/patches/uniracers_canoe.ips` and `references/imported/patches/uniracers_canoe.md`; SHA-256 `35b695d9cc0667d09f950a05cb3066ada5f0078a50818bc04d348f5ef4f852cf`.  
**Interpretation:** This preserves an independent software workaround for the same active-display OAM behavior documented by Snes9x, MAME and jgenesis. Disassembling it may reveal exactly which game routines Canoe needed redirected and what state the patch synthesizes.  
**Discriminating test:** apply to the verified US baseline, disassemble changed routines, and compare runtime OAM writes with unpatched hardware-faithful behavior.  
**Dependencies:** exact patch revision chronology is inferred from public 2018 discussion and Drive timestamps.

### R-EXT-007 — SRAM tour/progression layout

**Status:** historical lead  
**Date:** 2026-09-28  
**Area:** RAM | other

**Observation:** TASVideos research attributes medal state to nine 16-byte tour blocks spanning SRAM `0x069C–0x072B`, with one byte per unicycle and values 00/01/02/03 for none/bronze/silver/gold. Tour unlock count is reported at `0x10D3–0x10E2`.  
**Evidence:** `references/notes/tas-and-sram-research.md` and TASVideos Uniracers topic 979.  
**Interpretation:** This is a useful starting map for decoding save structure and can rapidly expose per-unicycle progression fields.  
**Discriminating test:** compare clean SRAM, controlled medal changes and unlock transitions byte-for-byte.  
**Dependencies:** historical emulator SRAM format and ROM revision must be matched.

### R-EXT-008 — USJO autonomous stunt bot

**Status:** supported historical lead; artifact missing  
**Date:** 2026-09-28  
**Area:** physics | RAM | other

**Observation:** TASVideos submission #3072 describes a Lua script named USJO, originating with Halamantariel and improved with Nitrodon, that automated frame-precise stunt behavior and reportedly evolved to play Uniracers autonomously.  
**Evidence:** `references/notes/tas-and-sram-research.md`; TASVideos submission #3072.  
**Interpretation:** The script likely encodes practical RAM addresses, timing rules and control-state knowledge directly useful for behavioral reconstruction.  
**Discriminating test:** recover any USJO version or derivative and validate its memory accesses/actions against the supported ROM.  
**Dependencies:** recovery of the script or sufficiently detailed contemporary discussion.

### R-EXT-009 — Halamantariel course-map corpus

**Status:** confirmed external reference corpus  
**Date:** 2026-09-28  
**Area:** course | UI

**Observation:** VGMaps currently indexes 44 complete Uniracers course maps credited to Halamantariel. Several are extremely large stitched images, including a 28,128×152 Dragster map and a 36,864×16,111 Downer map.  
**Evidence:** `references/notes/tas-and-sram-research.md`; VGMaps Uniracers index.  
**Interpretation:** These maps can serve as independent geometric ground truth for a ROM course extractor and may connect directly to the hand-made maps mentioned in the historical level-viewer investigation.  
**Discriminating test:** reproduce a course from ROM data and align its topology/segment ordering against the corresponding map.  
**Dependencies:** obtain direct image files or sufficient map access for pixel-level comparison.


### R-EXT-010 — RetroAchievements independently corroborates progression RAM and exposes stunt-state RAM

**Status:** supported  
**Date:** 2026-09-28  
**Area:** RAM | physics | other

**Observation:** A public snapshot of the Uniracers RetroAchievements set contains 24 raw memory-condition definitions. Its medal addresses at `0x02069C`, `0x0206AC`, ... `0x02071C` independently match Halamantariel's historical per-tour medal offsets. It additionally exposes a dense stunt-state block from `0x02076B` through `0x0207AF` and per-tour five-byte state groups from `0x021075` through `0x0210A1`.  
**Evidence:** `references/imported/retroachievements/1295.json` and `references/notes/retroachievements-ram.md`.  
**Interpretation:** These are high-value watchpoints for reconstructing stunt and race state because they were used in live achievement conditions, not merely guessed from static inspection.  
**Discriminating test:** instrument the supported ROM while deliberately triggering one stunt/result at a time and map exact transition semantics.  
**Dependencies:** RetroAchievements' SNES address-domain mapping must be translated correctly to native WRAM/SRAM addresses.

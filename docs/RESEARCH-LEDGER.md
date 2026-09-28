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

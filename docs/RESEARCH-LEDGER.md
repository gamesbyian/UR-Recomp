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

**Status:** confirmed at packed-data level  
**Date:** 2026-09-28  
**Area:** compression | course

**Observation:** both canonical USA retail and 1994-11-29 PAL prototype ROMs contain exactly 45 valid RNC headers, all Method 1, at identical offsets with matching packed/unpacked sizes and CRCs.

**Evidence:** `analysis/generated/retail-vs-prototype-structure.md`; preserved ProPack sources under `references/imported/tools/rnc_propack-2.14/`.

**Interpretation:** RNC Method 1 is established binary fact for this 45-stream corpus. Whether every stream is course data remains to be established.

**Action:** independently decompress all 45 streams, verify CRCs, locate the game decoder, and identify semantics.

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


### R-EXT-011 — Period SNES RNC decoder source preserved

**Status:** confirmed external artifact  
**Date:** 2026-09-28  
**Area:** compression | course

**Observation:** The public mirror of RNC ProPack 2.14 includes the original packer package and separate SNES assembly unpackers for RNC Method 1 and Method 2. The package has been mirrored byte-for-byte into this repository.  
**Evidence:** `references/imported/tools/rnc_propack-2.14/`; upstream revision `08406a33e700aa33936e4c4800cd0887a468a31b`; SNES source blobs `ad4f5c58590dcc1357fb01c138084ff78ad22d75` (Method 1) and `0055f7fad678ef226757b3b7fa9fb06e48fc8929` (Method 2).  
**Interpretation:** We now have period reference implementations suitable for structural comparison with the Uniracers ROM. This can independently test the historical claim that course data uses RNC and determine the exact method/variant.  
**Discriminating test:** locate candidate RNC records and the ROM decompressor, compare against both supplied SNES implementations, then decompress one candidate and connect it to a known course load.  
**Dependencies:** The public 2.14 package may not be the exact ProPack revision used by DMA Design, so algorithmic agreement matters more than byte-identical source.


### R-EXT-012 — TAS-native WRAM watch addresses

**Status:** supported historical lead  
**Date:** 2026-09-28  
**Area:** RAM | physics | camera

**Observation:** Halamantariel published an explicit Snes9x memory-watch list used during Uniracers TAS work: `7E:04B7` signed 16-bit speed, `7E:11CD` unsigned 16-bit boost meter, `7E:0411`/ `7E:0415` unsigned 16-bit X/Y position, `7E:1509` screen-X, plus one-byte stunt counters at `7E:11FD`, `7E:11F9`, `7E:0F61`, `7E:042B`, and `7E:042F`.  
**Evidence:** `references/notes/tas-and-sram-research.md`; TASVideos Uniracers topic post dated 2008-03-12.  
**Interpretation:** These provide directly named native WRAM watchpoints for core movement/boost/stunt state and are prime anchors for symbol reconstruction.  
**Discriminating test:** watch each address during controlled gameplay and verify direction, units, signedness and reset/update behavior.  
**Dependencies:** Snes9x memory-domain notation is interpreted as native banks `7E/7F`; exact supported US ROM should be verified.

### R-EXT-013 — USJO v13 exact filename and behavioral role

**Status:** supported historical lead; artifact missing  
**Date:** 2026-09-28  
**Area:** physics | RAM | other

**Observation:** The 2008 Snes9x Lua-development thread links `usjo13.lua` under the title “Uniracers Stunts & Jump Optimizer v13.” Its author describes it as starting before a jump, intelligently trying stunt combinations, optimizing for speed and replaying the best input.  
**Evidence:** `references/notes/tas-and-sram-research.md`; historical direct URL preserved in `references/catalog.yml`.  
**Interpretation:** Recovering this exact script could expose the evaluator, search strategy, RAM accesses, stunt grammar and timing assumptions used by an expert TASer.  
**Discriminating test:** recover the byte-identical script from an archive/mirror and inspect all memory reads and scoring rules.  
**Dependencies:** surviving archive of the former obellemare.com speedruns directory.

---

## Original-development leads added on main

### R-SEED-004 — Copier-sensitive anti-piracy path

**Status:** supported historical lead  
**Date:** 2026-09-28  
**Area:** CPU | other

Andrew Innes states that DMA discovered a behavioral difference between a proper cartridge and their fast copy-device development image and deliberately used it for anti-piracy protection. Mike Dailly independently confirms Magicom/devkit use during Unirally development.

**Evidence:** docs/original-development/SOURCE-INDEX.md entries OD-004 and OD-005.  
**Action:** identify cartridge/copier-sensitive code paths and validate them against a trustworthy reference emulator or hardware model.

### R-SEED-005 — Bespoke DMA SNES framework and SNasm conventions

**Status:** supported historical lead  
**Date:** 2026-09-28  
**Area:** CPU | DMA/HDMA | other

Mike Dailly credits himself with the Uniracers SNES framework/tools, lists SNasm as a bespoke 65816 macro assembler, and stated in 2008 that he had found his old SNES framework source.

**Evidence:** OD-001 through OD-004 in docs/original-development/SOURCE-INDEX.md.  
**Action:** search for surviving framework/tool source and compare recovered code idioms against the ROM before imposing modern assembler conventions.

### R-SEED-006 — Multidimensional unicycle animation corpus

**Status:** supported historical lead  
**Date:** 2026-09-28  
**Area:** PPU | other

Developer recollections describe rendered unicycle graphics with multiple pose dimensions, while Dailly lists dedicated Unicycle Compression and A0-plotter tools.

**Evidence:** OD-001, OD-003, OD-005.  
**Action:** correlate controlled animation states with ROM source ranges and sprite uploads; seek stride/table dimensions rather than assuming a simple linear frame strip.

### R-SEED-007 — 1994-11-29 PAL prototype as differential oracle

**Status:** acquired, fingerprinted, and structurally diffed  
**Date:** 2026-09-28  
**Area:** other

Hidden Palace documents a European prototype from a four-EPROM SHVC-4PV5B-01 development cartridge.

**Evidence:** OD-007.  
**Action:** acquire, hash, normalize, and diff against canonical USA retail at byte, block, pointer-table and disassembly levels.


### R-SEED-008 — Intentional per-scanline sprite-state changes

**Status:** strong developer-confirmed historical behavior  
**Date:** 2026-09-28  
**Area:** PPU | DMA/HDMA

**Observation:** Mike Dailly explicitly states that Uniracers changed SNES state on a scanline basis, and separately identifies the split-screen method as C64-style sprite ripping. His later technical explanation describes changing sprite position while the raster is drawing it and says the Uniracers implementation required Nintendo R&D hardware verification.

**Evidence:** OD-019 through OD-021 in docs/original-development/SOURCE-INDEX.md.

**Interpretation:** the two-player renderer deliberately changes sprite/OAM-related state within the visible frame to obtain a clean viewport split.

**Discriminating test:** trace writes to OAM address/data and any DMA/HDMA or sprite-position state around the split scanlines; compare one-player and two-player modes; correlate exact scanlines with visible sprite discontinuities.

**Dependencies:** the later explanatory article accurately describes the same shipped implementation Dailly referenced in 2008.


### R-SEED-009 — Four-build differential ROM corpus

**Status:** confirmed at byte-identity level  
**Date:** 2026-09-28  
**Area:** other | compression

**Observation:** the local reference set now contains four verified 2 MiB images: USA retail, Europe retail, the historical GoodSNES-listed `Uniracers (Beta)`, and the 1994-11-29 PAL prototype. USA retail vs the legacy beta differs in exactly 486 bytes across 486 one-byte runs; all 45 RNC streams are byte-identical and remain at identical offsets. The legacy beta also shares the USA retail reset vector and header checksum/complement.

Europe retail contains 45 Method 1 streams, but only 38 are byte-identical by content with the other three builds. By ordinal stream position, the differing PAL-retail streams are 4, 16, 20, 26, 27, 35 and 36. The other 38 move after size-changing streams but preserve exact packed bytes.

**Evidence:** `analysis/generated/reference-rom-inventory.md`; `analysis/generated/reference-rom-comparison.md`; deterministic generators `tools/inventory_reference_roms.py` and `tools/compare_reference_roms.py`.

**Interpretation:** the legacy beta is extraordinarily close to USA retail and is a high-sensitivity oracle for isolated late byte changes, but its historical “beta” label does not by itself establish build chronology or authenticity. PAL retail contains seven genuine decoded-content candidates that changed after the 1994-11-29 prototype/USA content corpus; these are unusually strong candidates for region-specific or late content edits.

**Discriminating test:** independently decompress the seven changed PAL streams and their USA/prototype counterparts, then characterize the exact decoded deltas before assigning course or localization semantics.

**Dependencies:** stream ordinal is used only as a stable comparison index, not yet as a semantic course ID.


### R-SEED-010 — Independent RNC1 decompression verified across preserved builds

**Status:** confirmed  
**Date:** 2026-09-28  
**Area:** compression | course

**Observation:** project-owned `tools/rnc_method1.py` independently decoded every detected Method 1 stream in all four preserved ROMs. All 180 decode operations (45 per build) passed both the packed CRC16 in the RNC header and the unpacked CRC16 after decompression. Each build contains 45 unique decoded outputs.

USA retail, the legacy beta, and the 1994-11-29 PAL prototype have identical decoded content for all 45 stream positions. Europe retail differs after decompression at exactly seven ordinal positions: 4, 16, 20, 26, 27, 35 and 36.

**Evidence:** `analysis/generated/rnc-stream-manifest.json`; `analysis/generated/rnc-stream-manifest.md`; CI run 36491695742; decoder `tools/rnc_method1.py`; generator `tools/analyze_rnc_streams.py`.

**Interpretation:** RNC extraction/decompression is no longer a blocker. The seven PAL-retail deltas are real content changes rather than merely recompression or relocation, because their unpacked CRCs, lengths and SHA-256 hashes differ.

**Discriminating test:** characterize record structure in decoded bytes and map at least one stream to an independently known course; compare the seven PAL deltas structurally after the record format is understood.

**Dependencies:** semantic mapping of stream ordinal to course/content identity remains unresolved.


### R-SEED-011 — Shipped RNC1 unpacker identified in ROM code

**Status:** confirmed  
**Date:** 2026-09-28  
**Area:** CPU | compression | course

**Observation:** a masked opcode signature derived from the preserved 1992 Super NES ProPack Method 1 source, `references/imported/tools/rnc_propack-2.14/SOURCE/SUPERNES/RNC_1.S`, produces one unpacker-entry hit per preserved build. The USA retail and legacy beta entry is ROM offset `0x00B8F1` (LoROM `01:B8F1`); Europe retail is `0x00B8E2` (`01:B8E2`); the 1994-11-29 PAL prototype is `0x00B8D1` (`01:B8D1`). Surrounding instructions reproduce the period routine's distinctive entry sequence: `REP $39`, stack-relative source/destination argument loads, direct-page stores, `PHB/XBA/PHA/PLB/PLB`, input pointer adjustment by 17 bytes, block-count read, bit-buffer initialization, and calls into the Huffman/bit-reader machinery.

The same search also finds the expected Huffman-builder-shaped code later in the routine region, with build-relative address shifts consistent with the unpacker entry shifts.

**Evidence:** `analysis/generated/rnc-decoder-signature-search.md`; generator `tools/find_rnc_decoder_signature.py`; preserved period source `references/imported/tools/rnc_propack-2.14/SOURCE/SUPERNES/RNC_1.S`.

**Interpretation:** Uniracers/Unirally contains a directly recognizable integration of Rob Northen's SNES Method 1 unpacker, rather than merely a format-compatible independent decoder. Build-to-build movement of the routine provides an additional code-alignment landmark.

**Discriminating test:** map direct callers and packed-stream pointer references, then trace one course-load path from a caller through `RNC1_Unpack` into the decoded WRAM buffer.

**Dependencies:** LoROM address notation uses the low-bank mirror; equivalent high-bank mirrors may appear in call operands.

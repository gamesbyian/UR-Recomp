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


### R-SEED-012 — 45 RNC payloads align with track order; stunt timer field identified

**Status:** supported, with byte-level observation confirmed  
**Date:** 2026-09-28  
**Area:** course | compression

**Observation:** the canonical USA ROM has 45 validated decoded RNC Method 1 payloads. When grouped into nine sets of five, decoded byte offset 2 equals `0x2D` only at ordinals 3, 8, 13, 18, 23, 28, 33, 38 and 43. It is `0x00` for the other 36 payloads. No exception occurs.

External gameplay documentation states that each tour's five tracks occur in the fixed order Race, Circuit, Stunt, Race, Circuit, and independently describes stunt courses as 45-second events. Decimal 45 is `0x2D`.

**Evidence:** `analysis/generated/course-header-cadence.md`; generator `tools/analyze_course_header_cadence.py`; `references/notes/course-order-and-stunt-timer.md`.

**Interpretation:** the simplest explanation is one RNC payload per shipped track, ordered by tour and slot. Decoded byte 2 is very likely the stunt-course time limit in seconds, or a directly equivalent stunt-only parameter. This is the first semantically identified field in the decompressed course record.

**Discriminating test:** trace selection/loading of one known stunt track and one race track, then trace decoded byte 2 into the gameplay timer initialization. Independently verify the stream ordinal through the course selector.

**Dependencies:** external track-order/timer descriptions are used only for semantic interpretation; the 45-stream count and byte cadence are local binary observations.


### R-SEED-013 — Recovered frontend and race-state RAM reproduced in native and reference runs

**Status:** confirmed for observed states  
**Date:** 2026-09-28  
**Area:** RAM | UI | race

**Observation:** Dessyreqt's 2014 bot labels WRAM `7E:009F` as the current frontend menu and `7E:0313` as `inRace`. The project-owned shared deterministic input fixture reproduces, in both native SNESRecomp execution and Snes9x through `snesref`, the sequence `0xD7` main menu, `0x3C` one-player rider selection, `0x6D` first one-player tours page, `0xF6` track selection, `0x16` now-playing, then `7E:0313 = 0x01` after race entry.

**Evidence:** `references/imported/tas-bots/uniracers-tabletop-bot-2014.lua`; GitHub Actions runs 36506120930 and 36506281320; `tests/input/reach-first-race.script`; `docs/BRINGUP.md`.

**Interpretation:** the recovered frontend state model and active-race flag are now locally validated cross-runtime rather than merely inherited historical labels. A newly visible menu-state byte can precede input readiness; the deterministic fixture therefore retains a conservative scene-settle period before confirmation.

**Discriminating test:** compare complete WRAM dumps at each shared checkpoint byte-for-byte, then extend the same fixture into controlled movement and validate the bot's race-driving RAM labels.

**Dependencies:** only values/scenes actually reproduced are promoted; other recovered bot fields remain historical leads until independently observed.


### R-SEED-014 — Native and Snes9x race-entry timing/state differential

**Status:** confirmed as timing/residual-state differential  
**Date:** 2026-09-28  
**Area:** timing | RAM | other

**Observation:** the shared race-entry script reaches `7E:0313 = 1` at native frame 984 and Snes9x/snesref frame 975. Full 128 KiB WRAM comparison at seven settled checkpoints shows 19 differing bytes at main menu, roughly 250 through the animated frontend scenes, and only **7 differing bytes** at settled race entry.

The final seven are `0x00C6`, `0x00C8`, `0x00C9`, and contiguous `0x01D1–0x01D4`. At race entry the four-byte block is native `90 13 20 80` versus Snes9x `00 00 00 00`.

**Evidence:** GitHub Actions runs 36506120930, 36506281320 and combined differential run 36508095522; artifact 11007769197; `tools/compare_wram_checkpoints.py`.

**Interpretation:** much of the frontend mismatch is compatible with the known several-frame timing offset inside animated scenes, because the difference set collapses drastically after race entry settles. The persistent `0x01D1–0x01D4` block is a sharper candidate for a genuine runtime/state divergence. The three `0x00C6/0x00C8/0x00C9` differences remain unclassified, but all three take changing small values across every captured frontend/race checkpoint rather than preserving a fixed native-only payload. That temporal pattern makes timing/phase counters a stronger working explanation than a stable semantic-state split.

**Resolution:** trace run 36511207129 shows `0x00C6` is decremented once per frame by `bank_80_FADF_M1X0`, while `0x00C8` and `0x00C9` are periodic countdown/phase values written by interpreted code at `$00:8588` (`0x00C8` changing every frame within its cycle and `0x00C9` on a seven-frame cadence). Their different race-entry values therefore reflect the already-observed native/reference phase offset rather than a stable semantic race-state mismatch. The remaining four bytes are resolved separately in R-SEED-015.

**Dependencies:** both engines execute the same script and zero-filled initial WRAM; Snes9x reports its existing Uniracers-specific compatibility hack as active.


### R-SEED-015 — Persistent 0x01D1–0x01D4 divergence is stale stack residue

**Status:** confirmed  
**Date:** 2026-09-28  
**Area:** CPU | RAM | timing

**Observation:** the settled native/reference race-entry differential leaves four contiguous differing bytes at WRAM `0x01D1–0x01D4`: native `90 13 20 80`, Snes9x `00 00 00 00`. This block appears by rider-select and persists through later captured frontend states into race entry. A checkpoint-by-checkpoint reinspection of the full-WRAM artifact shows many other transient native/reference differences throughout page `$01` before race entry (13 at main menu, 13 at rider select, 20 at tours, 13 at tracks, 18 after confirmation, 18 at now-playing), but all of those other page-$01 differences disappear at the settled race checkpoint, leaving only `0x01D1–0x01D4`. The block lies in the conventional 65C816 stack page, and SNESRecomp's own low-WRAM differential tooling explicitly treats this region as containing stack state as well as game logic.

**Evidence:** combined differential run 36508095522; `tools/compare_wram_checkpoints.py`; SNESRecomp low-WRAM trace/debug infrastructure and stack model.

**Interpretation:** one plausible explanation is differing residual stack contents caused by different call/interrupt execution paths or stack depth, rather than a durable gameplay variable. The broader page-$01 pattern strengthens that hypothesis: the region behaves like a churned scratch/stack area whose cross-runtime differences mostly evaporate once the race settles, while this four-byte residue survives. This is still not proof: Uniracers could also use page `$01` for ordinary RAM while in native mode.

**Static candidate scan:** run 36509923408 scanned raw 65816 store/RMW encodings for all seven divergent offsets. For `0x01D1–0x01D4` it found only a small set of instruction-shaped byte patterns, dominated by RMW/STZ forms; it did not expose an obvious direct semantic store sequence. Because this is a raw-byte candidate scan rather than control-flow-aware disassembly, hits may be data and absence of a direct store does not cover stack pushes, JSR/JSL return frames, interrupts or indirect/indexed effects. The result is therefore weakly consistent with, but does not establish, the stack-residue interpretation.

**Dynamic resolution:** trace run 36511207129 reaches `inRace = 1` at native frame 984 with the 65C816 in native mode (`E = false`) and `SP = $01FF`. The four bytes remain `90 13 20 80` at `$01D1–$01D4`, far below the live top of stack. Reverse-debug writer history records zero ordinary WRAM writes to all four addresses across the captured run, while explicit semantic/timing variables such as `$00C6/$00C8/$00C9` produce abundant attributed writes. Together with the broader transient `$01xx` churn seen at earlier checkpoints, this identifies the four-byte block as stale stack history rather than live gameplay state. Its exact historical push sequence is not needed for fidelity gating.

**Dependencies:** the stack interpretation depends on actual Uniracers stack-pointer behavior at the relevant frames; address location alone is insufficient.


### R-SEED-016 — Player-1 X position and signed X speed validated cross-runtime

**Status:** confirmed  
**Date:** 2026-09-28  
**Area:** RAM | physics | input

**Observation:** Dessyreqt's effective player-1 word table labels `7E:0411` as X position and `7E:04B7` as X speed. In deterministic run 36512546762, native and Snes9x begin at `xPos=1088`, `xSpeed=0`, receive the same staged Right input, and match exactly at every semantic checkpoint. At `accel-180`, both report `xPos=1655` and `xSpeed=+447`.

**Evidence:** workflow run 36512546762; artifact 11009592846; recovered bot source; `tests/input/race-acceleration.script`.

**Interpretation:** `7E:0411` and signed `7E:04B7` are confirmed player-1 horizontal position/velocity anchors for the observed stock race. Positive speed corresponds to rightward movement.

**Next discriminator:** use the moving state as the baseline for B-jump and L/R rotation while validating Y speed, effective air state and pitch.


### R-SEED-017 — Recovered race countdown field advances in 8.8-style frame quanta

**Status:** supported  
**Date:** 2026-09-28  
**Area:** RAM | timing

**Observation:** the recovered bot labels `7E:11BA` as `countdownTimer`. Across the event-relative checkpoints in run 36512546762, both engines produce the same sequence: 54528, 46592, 38656, 30720, 22784, 7168. Each 31-frame staged interval decreases the word by 7936 = 31 × 256, and the final 61-frame interval decreases it by 15616 = 61 × 256.

**Interpretation:** the field decrements by exactly `0x0100` per guest frame during this race-start window, strongly supporting a fixed-point/frame-countdown interpretation. The precise player-visible thresholds and meaning of the low byte remain to be characterized.

**Evidence:** workflow run 36512546762 and its native/reference player-state reports.


### R-SEED-018 — B-jump execution matches cross-runtime; airborne-state address requires causal control

**Status:** supported / active discriminator  
**Date:** 2026-09-28  
**Area:** input | physics | RAM

**Observation:** run 36513247475 applies a two-frame `Right+B` pulse from the validated moving Dragster state and samples through `jump-settle`. Native and Snes9x match exactly at every recovered semantic field checkpoint. X motion continues identically, `pitch` reaches 33 at `jump-mid`, and the earlier duplicate `7E:0547` follows 0 → 3 → 9 → 9 → 0 while the Lua-effective `7E:0545` remains 0.

**Complication:** the recovered bot source contains duplicate player-1 keys, with later Lua semantics selecting `7E:0545` as `airValue`, but the observed B-window response is at `7E:0547`. The race framebuffer contains two unicycles/ghost-like sprites, so visual correlation alone cannot safely assign the changing byte to the controlled player.

**Paired-slot clue:** the same dumps show the table-[2] block changing coherently with the apparent airborne event: at `jump-mid`, `7E:0417=796`, signed `7E:04BD=-21`, and `7E:0547=9`, while table-[1] remains `7E:0415=859`, `7E:04BB=0`, `7E:0545=0`. The preserved bot runs `singlePlayer=true`, `controller=1`, and reads table [1], so this strongly suggests the visually obvious arc belongs to the second racer rather than the intended controlled-player block.

**Recovered-policy timing:** on Dragster, `jumpAreas[0]` spans X 1090–25278 and Y 790–870. At the validated moving checkpoint (X 1655, Y 858), `ShouldJump()` would continue returning true every bot frame until its own air/Y-speed conditions changed. The original policy therefore behaves like a sustained B hold in this region, not a two-frame pulse.

**Matched-control result:** run 36513805265 replays the same route/timing with Right-only instead of the two-frame Right+B pulse. A paired-slot reinspection of the artifact confirms that every sampled table-[1] and table-[2] field is numerically identical between B and no-B at every checkpoint, including the second racer's full arc (`ySpeed=-154`, `air=9` at `jump-rise`). The short B pulse therefore produces no semantic player-state change. In native, the only persistent full-WRAM difference is `$0069`, but it already differs at `accel-180` before B is pressed and therefore is not B-causal. In Snes9x, jump-vs-control differences are limited to transient stack bytes. The second-slot airborne arc therefore occurs independently of the two-frame B pulse.

**Interpretation:** the initial "jump" fixture was a negative intervention. It did not launch the intended table-[1] player. The visually obvious airborne motion belonged to the second racer. This validates the duplicate-key/paired-slot caution and prevents falsely promoting `$0547` as player-1 air state.

**Next discriminator:** replace the short pulse with sustained Right+B input across the Dragster jump area, matching the recovered bot's actual per-frame `ShouldJump()` policy, and require a causal change in table-[1] Y/air/related state before calling the controlled player airborne.

**Evidence:** workflow run 36513247475; `tests/input/race-jump.script`; matched control `tests/input/race-jump-control.script`.


### R-SEED-019 — Active Dragster payload is resident at 7F:0000

**Status:** confirmed  
**Date:** 2026-09-28  
**Area:** course | RAM | decompression

**Observation:** run 36514985916 independently decodes all 45 USA streams and scores them against live WRAM `7F:0000`. Stream 1 matches 33,814 of 33,815 decoded bytes across its entire 33,815-byte payload. The sole mismatch is decoded offset `0x000B`, which changes from `0x0F` to live `0x16`.

**Interpretation:** decoded stream 1 is the active Dragster course payload and is loaded directly at `7F:0000`; at least byte 11 is subsequently mutable in place. This supersedes the older `7E:2080` breadcrumb as the primary decoded-course runtime landmark.

**Evidence:** decoded stream-1 structural report and native race-entry WRAM artifact from run 36508095522.


### R-SEED-020 — Dragster header X coordinate maps exactly to runtime start X at ×16

**Status:** strongly supported single-course field hypothesis  
**Date:** 2026-09-28  
**Area:** course | RAM | physics

**Observation:** decoded stream 1 has LE16 pairs `(68,50)` at offsets 3/5 and again at 7/9. At settled Dragster race entry, both racer slots have X position 1088; `68 × 16 = 1088` exactly. Runtime Y is 858/857, not `50 × 16 = 800`.

**Interpretation:** the header pairs are coordinate-like and may encode the two racer spawn/start locations in 16-unit X coordinates. Y either uses an additional object-anchor offset or has different semantics.

**Discriminating test:** load a second known course and compare its header pairs with runtime racer positions, or mutate one decoded coordinate causally and observe the predicted runtime displacement.


### R-SEED-021 — Sustained B input produces coherent player-1 airborne state cross-runtime

**Status:** supported; matched sustained control pending  
**Date:** 2026-09-28  
**Area:** input | physics | RAM

**Observation:** run 36514394117 advances the validated moving Dragster state with sustained `Right+B` input. Before an unrelated workflow-ordering failure, both native and Snes9x completed and summarized the sustained intervention identically. At `accel-180`, player 1 is grounded: `x=1655`, `y=858`, `xSpeed=447`, `ySpeed=0`, effective `airValue(0545)=0`, effective `pitch(0F49)=7`. At `jump-hold-024`, both engines report `x=2005`, `y=797`, `xSpeed=447`, signed `ySpeed=-21`, `airValue=9`, `pitch=27`. By `jump-hold-048`, both are back at `y=858`, `ySpeed=0`, `airValue=0`.

**Interpretation:** unlike the earlier two-frame negative intervention, sustained B produces a coherent airborne transition in the intended table-[1] player block, and the recovered effective addresses `7E:04BB` and `7E:0545` now move in the expected direction together. Native and reference semantics match exactly at every sampled sustained-jump checkpoint.

**Caution:** because the matched sustained Right-only control did not run in this failed workflow instance, causality is not yet formally closed. The repaired workflow runs the control before its paired-slot analysis.

**Next discriminator:** require the timing-identical sustained Right-only control to remain grounded at the corresponding table-[1] checkpoints; then promote Y speed and air state and proceed to controlled rotation.


### R-SEED-022 — Dragster payload is installed after Now Playing confirm, before active race

**Status:** confirmed timing window  
**Date:** 2026-09-28  
**Area:** course | compression | RAM

**Observation:** run 36515555816 compares decoded stream 1 with live `7F:0000` at `tracks-ready`, `after-track-confirm`, `now-playing-ready`, and `race-entered`. Stream 1 is not installed at the first three checkpoints. At `race-entered` it matches 33,814 / 33,815 decoded bytes, with only offset `0x000B` changed from `0x0F` to `0x16`.

**Interpretation:** Dragster decompression/copy into `7F:0000` occurs after the final A confirm on the Now Playing screen and before the race-active state. In the deterministic reference route this is a roughly 151-frame transition window.

**Caution:** pre-load "best stream" scores are not semantic evidence because sparse decoded streams can coincidentally match zero-heavy live WRAM. The focused expected-stream full-length match is the useful test.

**Discriminating test:** add dense post-confirm checkpoints to locate the first full stream-1 residency frame and observe byte 11 before/after its runtime mutation.


### R-SEED-023 — L input rejects 0F49 as the direct rotation accumulator and implicates 04C7

**Status:** supported; mirror-R discriminator active  
**Date:** 2026-09-28  
**Area:** input | physics | RAM

**Observation:** airborne-rotation run 36515746538 applies eight frames of L during the causally validated player-1 airborne interval and compares against a timing-identical jump-only control. Native and Snes9x agree on every sampled recovered semantic field. The recovered bot field `7E:0F49` is identical between L and control at the intervention checkpoint (`45` in both) and throughout the sampled window.

The full-WRAM causal differential, however, shows `7E:04C7` changing from `0x07` in jump-only control to `0x37` under L at the eight-frame intervention checkpoint, then `0x3C` vs `0x07` at the next checkpoint before relaxing toward baseline. The adjacent paired-racer byte `7E:04C9` follows the second-racer trajectory and does not show this player-1 L-causal response.

**Interpretation:** `7E:0F49` may still be a useful derived/display/stunt-facing quantity used by the historical bot, but it is not the direct player-1 rotation accumulator for this intervention. `7E:04C7` is a much stronger candidate for player-1 physical rotation/orientation state, with `7E:04C9` plausibly the paired player-2 slot.

**Discriminating test:** run the mirrored eight-frame R intervention against the same jump-only control. If `7E:04C7` responds in the opposite direction while native/reference agree, promote the paired `04C7/04C9` rotation interpretation.

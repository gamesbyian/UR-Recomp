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


### R-SEED-024 — Course payload installs progressively between +16 and +64 frames

**Status:** confirmed  
**Date:** 2026-09-28  
**Area:** course | compression | RAM

**Observation:** run 36516395510 samples `7F:0000` after final Now Playing confirm. Through +16 frames, stream 1 is not installed. At +32 frames, the live buffer has an exact 10,307-byte prefix of decoded Dragster and byte 11 is still `0x0F`. At +64 frames, the full 33,815-byte payload is resident with only byte 11 changed to `0x16`; that state persists thereafter.

**Interpretation:** the active RNC payload is written progressively during the transition, not atomically at race activation. The byte-11 mutation occurs sometime after its decoded value has been written and by the time the full payload is resident.

**Discriminating test:** sample every 4 frames from +32 through +64 to bracket decompression completion and byte-11 mutation separately.


### R-SEED-025 — Dragster header coordinates map exactly to racer initialization at ×16

**Status:** confirmed for Dragster initialization; pair ownership unresolved  
**Date:** 2026-09-28  
**Area:** course | physics | RAM

**Observation:** decoded stream 1 contains two identical LE16 pairs `(68,50)`. At +64 frames after Now Playing confirm, when the full course payload is resident, both runtime racer slots are exactly `(1088,800)`. These are exact ×16 mappings: `68×16=1088`, `50×16=800`.

**Interpretation:** the header pairs are coordinate fields in 1/16 runtime racer units and supply or coincide with racer initialization/spawn positions. The later settled race Y≈858/857 reflects subsequent state evolution.

**Limitation:** Dragster cannot identify pair1→slot1 vs pair2→slot2 because both encoded pairs and both initial runtime positions are identical.

**Discriminating test:** load a course whose two header pairs differ, or causally mutate one pair, and observe which racer slot moves.


### R-SEED-026 — 04C7/04C9 are paired persistent pitch slots; 0F49 is shared working state

**Status:** confirmed structural pairing; direction convention still under mirror test  
**Date:** 2026-09-28  
**Area:** CPU | RAM | physics

**Observation:** targeted store scan run 36516801647 finds exactly one direct absolute writer candidate for `7E:04C7`: `STY $04C7` at LoROM `02:8D84`. Its surrounding shipped bytes decode to a player-copy sequence including `LDY $0F49; STY $04C7`, plus stores to player-1-shaped destinations `$0BA1/$0BAD/$0BB1`.

A sibling sequence at `02:9272` performs `LDY $0F49; STY $04C9`, with the neighboring destinations shifted coherently to `$0BA3/$0BAF/$0BB3`. The same source scratch values `$0F49/$0F4B/$0F4D` feed both sibling routines.

Dynamic run 36515746538 independently shows airborne L input changing `$04C7` from `0x07` in jump-only control to `0x37` at the intervention checkpoint, while the historical bot-read `$0F49` is unchanged between intervention and control at sampled checkpoints.

**Interpretation:** `$04C7/$04C9` are persistent paired per-racer pitch/rotation state slots. `$0F49` is a shared current-player working/scratch value copied into whichever racer slot is being updated, explaining why the historical bot could use it operationally while it is not stable player-1 storage.

**Discriminating test:** mirrored R input should drive player-1 `$04C7` complementarily to L, establishing the input-direction convention.


### R-SEED-027 — Player pitch is a modulo-64 persistent angle with L/R direction confirmed

**Status:** confirmed  
**Date:** 2026-09-28  
**Area:** input | physics | RAM

**Observation:** mirrored rotation run 36516524308 applies eight frames of L or R during the same validated airborne state, with jump-only control. Native and Snes9x produce identical persistent slot values. At the intervention checkpoint, control is `7E:04C7 = 0x07`; L gives `0x37`; R gives `0x17`. The paired player-2 `7E:04C9` and scratch `7E:0F49` follow the second/current-player update path rather than the controlled player-1 intervention.

**Interpretation:** the observed player-1 pitch/orientation domain is circular modulo 64. From 7, L changes the angle by −16 modulo 64 (`7−16 ≡ 55 = 0x37`), while R changes it by +16 (`7+16 = 23 = 0x17`). This matches the historical bot's threshold bands around 14/24/32/40/50 much better than treating the value as an unconstrained linear byte.

**Evidence:** run 36516524308; artifact 11011037312; direct WRAM dumps; sibling shipped-code stores at `02:8D84` and `02:9272`.

**Consequence:** `7E:04C7` is confirmed persistent player-1 pitch angle; `7E:04C9` is the paired player-2 slot; `7E:0F49` remains shared current-player working state. Rotation milestone is cleared.


### R-SEED-028 — Course completion, header mutation and racer initialization are distinct setup phases

**Status:** confirmed sequencing windows  
**Date:** 2026-09-28  
**Area:** course | compression | RAM | physics

**Observation:** run 36516675672 samples the Dragster setup transition every four frames. At +40, stream 1 has a 29,289-byte exact prefix and byte 11 is still decoded value `0x0F`; racer slots are `(0,0)`. At +44, the full 33,815-byte payload is resident and byte 11 is already `0x16`, but racer slots remain `(0,0)`. At +48, the course remains complete and both racer slots have become `(1088,800)`.

**Interpretation:** progressive decompression/copy, byte-11 postprocessing, and racer-coordinate initialization are separable phases. Course completion/header mutation occur in +40→+44; racer initialization occurs later in +44→+48.

**Discriminating test:** sample individual frames +41 through +48 to split these windows further.


### R-SEED-029 — Dragster setup sequence is frame-exact: complete +43, header settles +44, spawns +45

**Status:** confirmed  
**Date:** 2026-09-28  
**Area:** course | compression | RAM | physics

**Observation:** run 36517460851 samples every guest frame around setup completion. At +42, stream 1 is incomplete with a 33,359-byte exact prefix and byte 11=`0x0F`. At +43, all 33,815 bytes are resident (33,814 exact) and byte 11=`0x12`, while racer slots remain zero. At +44, byte 11=`0x16`, racers remain zero. At +45, both racers become `(1088,800)`.

**Interpretation:** course decompression/copy completes on guest frame +43; header byte 11 is postprocessed across +43/+44; racer spawn initialization occurs on +45. These are ordered, separable setup phases.

**Next discriminator:** dynamic writer history for `7F:000B` and nearby course-buffer bytes to identify the responsible guest routines and distinguish decompressor output from header postprocessing.


### R-SEED-030 — Landing transition matches cross-runtime and exposes two-stage contact settling

**Status:** confirmed event-relative landing behavior  
**Date:** 2026-09-28  
**Area:** physics | RAM | input

**Observation:** landing run 36517502791 samples the validated player-1 jump trajectory in both native SNESRecomp and pinned Snes9x. Every tracked semantic checkpoint matches exactly. At `landing-032`, player 1 is still airborne (`Y=843`, `YSpeed=182`, `air=9`). At `landing-034`, position has reached track height `Y=859` and `air=0`, while `YSpeed=222` remains non-zero. At `landing-036`, `Y=859`, `YSpeed=0`, `air=0` in both engines.

**Interpretation:** the sampled update sequence clears airborne/contact state when the racer reaches the track surface, then settles/resets vertical velocity by the next observed checkpoint. Native/reference simulation agrees through this transition.

**Harness caveat:** each scripted `press` entry is followed by one idle frame in the pinned runner/snesref grammar. These are event-relative checkpoints under a deterministic 2-held/1-idle input cadence, not claims about an uninterrupted B-held guest-frame number.

**Consequence:** the landing milestone is cleared for functional native/reference validation. A continuous-hold microtrace is optional future archaeology, not required before moving to collision/finish coverage.


### R-SEED-031 — Course decode and header mutation writers identified dynamically

**Status:** confirmed writers; routine roles under static classification  
**Date:** 2026-09-28  
**Area:** CPU | RAM | course | compression

**Observation:** trace run 36517696016 records `interp@$81BB73` writing the decoded Dragster output buffer at frame 867, including `7F:000B: 0x00→0x0F`. At frame 879, `interp@$81BA96` performs seven successive writes to `7F:000B`, incrementing `0x0F→0x10→0x11→0x12→0x13→0x14→0x15→0x16` within one guest frame. Attempt-2 run 36538122650 then captured exact interpreted PCs: the decoded `0x0F` write occurs at IPC `81:B9C8`, while every `0x10..0x16` mutation write occurs at IPC `82:E1E1`. The durable capture is `analysis/generated/course-byte11-exact-writes.json`.

**Interpretation:** the settled `0x16` value is not an unexplained differential or copy artifact. It is produced explicitly after the decoded `0x0F` has been written. The exact-IPC capture also resolves the tooling ambiguity: `81BB73` and `81BA96` are interpreter bridge scope entries, while the literal mutation store is at `82:E1E1`.

**Consequence:** do not attribute course-buffer stores to bridge scope labels. Static RNC classification and dynamic store-PC attribution are now separate, reconciled evidence surfaces.

**Next discriminator:** disassemble/label the code around exact IPC `82:E1E1` and connect that store to the course-loader control path; retain `81:B9C8` as the exact decoded-output write site for comparison.


### R-SEED-032 — Recovered 2008 WIP controller stream is directly parseable

**Status:** confirmed container/input facts; modern-reference replay desynchronization confirmed  
**Date:** 2026-09-28  
**Area:** input | TAS | autonomous play

**Observation:** `references/imported/tas-bots/uniracers-2008-wip-microstorage.smv` is a raw SMV v1 file, 10,542 bytes, reset-anchored, with one recorded controller and 4,974 header frames. Controller data starts at offset 592. Per the SMV v1 reset-movie format, the block from the savestate offset to controller data is a gzip-compressed 128 KiB SRAM snapshot; the replay tooling now extracts it and emits the canonical game's 8 KiB cartridge SRAM for both reference and native preload. Direct bit translation into the project/snesref 12-bit mask exposes a long regular control block around frames 1184–2655, including repeated `B+Right+R`, periodic `X`, short left corrections, and a final 359-frame Right interval. A later complex block begins around frame 3472.

**Interpretation:** this is a high-value candidate source for an exact known-working Dragster controller sequence, potentially preferable to approximating the 2014 Lua policy. The apparent race boundaries are not yet promoted because they are inferred from input shape alone.

**Replay result:** the repaired evidence-persistence path has now promoted `analysis/generated/historical-2008-dragster-reference.json`. The full 4,975-sample reference replay completes, but under the current pinned modern Snes9x/snesref route it never reaches the project's `inRace` or race-results states: `first_in_race_frame=null`, `first_race_results_frame=null`, `reference_reached_race=false`, `reference_reached_results=false`. The trace does record frontend/menu transitions, so this is a synchronization/timing failure rather than a parser/no-input failure.

**Interpretation:** do not use the 2008 WIP as a modern reference oracle until WIP1 timing compatibility is reproduced or otherwise explained. The 2014 movie is now the preferred exact historical reference corpus for race/finish work.


### R-SEED-033 — 2008 WIP requires no mid-movie reset emulation

**Status:** confirmed  
**Date:** 2026-09-28  
**Area:** input | TAS | replay fidelity

Direct inspection of all 4,975 controller samples in the reset-anchored 2008 WIP finds no `0xFFFF` SMV reset markers. The historical replay therefore needs the movie's reset-anchored initial machine state and embedded SRAM, but no later reset event. Treating reset markers as neutral input is harmless for this specific corpus; generic SMV tooling should still preserve/report marker positions.


### R-SEED-034 — Header bytes 13/14 form a fixed-area dimension pair

**Status:** strong structural evidence  
**Date:** 2026-09-28  
**Area:** course | format | dimensions

**Observation:** across all 45 decoded USA course payloads, header bytes 13 and 14 are restricted to complementary power-of-two-style pairs. Interpreting encoded byte value `0x00` as 256, every pair multiplies to exactly 1024. Observed pairs span `256×4`, `128×8`, `64×16`, `32×32`, `16×64`, `8×128` and `4×256`.

**Interpretation:** bytes 13/14 very likely encode complementary dimensions or strides for a fixed 1024-unit course-layout structure. This is compatible with, but does not yet prove, historical descriptions involving 256-wide course data.

**Discriminating test:** compare decoded structure and runtime traversal for courses at the extreme `256×4` / `4×256` encodings versus `32×32`; identify which subsequent region length/stride changes with the header pair and trace one consumer of either byte.


### R-SEED-035 — 1024-byte block-map hypothesis

**Status:** strong combined local/historical hypothesis; not yet runtime-confirmed  
**Date:** 2026-09-28  
**Area:** course | format | geometry

**Local evidence:** decoded header bytes 13/14 reshape to 45/45 complementary dimension pairs with constant area 1024 when zero is interpreted as 256.

**Historical evidence:** OD-006 preserves Spinal's report that Mike Dailly described levels as 256 tiles wide; after RNC decompression and map-overlay work, Spinal reported that one byte in the decompressed level corresponds to a 64×64 block.

**Hypothesis:** one immediate 1024-byte decoded region is a one-byte-per-64×64-block course-layout plane whose width/height are encoded by bytes 13/14. Provisional name alignment is suggestive rather than decisive: Dragster maps to `256×4`, Vertical to `16×64`, and Little Dipper to `4×256`.

**Discriminating test:** mechanically characterize the first several 1024-byte post-header regions across all 45 payloads, then trace whichever region exhibits map/index-like structure into a runtime course consumer. A mutation/viewer round trip should follow only after that consumer relationship is identified.


### R-SEED-036 — Interpreter writer labels are scope entries, not store PCs

**Status:** confirmed tooling-semantics correction  
**Date:** 2026-09-28  
**Area:** tracing | course | RNC

**Observation:** SNESRecomp synthesizes `interp@$XXXXXX` from the entry PC of an interpreter bridge run and uses that string as the write-attribution scope for all still-interpreted writes during the run. Therefore run 36517696016 proves that the Dragster install and byte-11 mutation write groups occur under scopes entered at `81BB73` and `81BA96`, but does not identify those addresses as the literal store instructions.

**Static cross-check:** `01:BA96` is inside generic RNC Method-1 `GTBITS2`; the shipped bytes align with preserved source `LSR A / ROR BITBUFL / DEY / BEQ / DEX / ...`. That makes a literal “course-byte store at BA96” interpretation impossible and validates the scope-entry reading.

**Discriminating test:** capture exact interpreted opcode PC at WRAM-write time, or narrow the interpreter bridge scope enough to isolate the true store instruction. Keep the established write values/timing unchanged.


### R-SEED-037 — 2008 WIP sample zero is correctly aligned; legacy WIP1 timing remains a compatibility variable

**Status:** sample alignment confirmed; legacy timing compatibility open  
**Date:** 2026-09-28  
**Area:** TAS | input | emulator compatibility

**Source-level observation:** Snes9x movie playback reads sample 0 as baseline controller data before starting movie playback, then sets movie frame/sample counters to zero. The next movie update advances to later samples. The project's `start-frame:duration:mask` conversion therefore has the correct frame-zero convention.

**Movie-specific observation:** the 2008 WIP is SMV v1 with sync-data-present and `MOVIE_SYNC_WIP1TIMING` set; all other legacy behavioral sync flags except ROM-info are clear. Modern Snes9x no longer uses WIP1 timing.

**Observed modern behavior:** the durable reference result in `analysis/generated/historical-2008-dragster-reference.json` confirms that current pinned Snes9x/snesref does diverge before race: no `inRace` or results transition is reached across the full movie stream.

**Interpretation:** do not introduce an arbitrary input-frame offset to force synchronization. The next meaningful discriminator is reproducing/characterizing Snes9x 1.43 WIP1 timing semantics, or demonstrating another exact legacy-state difference that explains the desync.


### R-SEED-038 — 2008 WIP embeds the canonical USA ROM identity

**Status:** confirmed  
**Date:** 2026-09-28  
**Area:** TAS | provenance | replay fidelity

The SMV v1 ROM-info record embedded in `references/imported/tas-bots/uniracers-2008-wip-microstorage.smv` identifies internal ROM name `UNIRACERS` and CRC32 `383858c7`. That CRC exactly matches the canonical project's USA ROM in `rom_identity.txt`. The movie metadata names its author as `Olivier Bellemare aka Halamantariel`.

This closes ROM-revision mismatch as a possible cause of historical replay desynchronization. The extractor now preserves author/ROM metadata and the historical replay workflow refuses to proceed when an embedded movie CRC disagrees with the canonical ROM.


### R-SEED-039 — 2014 full-game movie provides a post-WIP1 timing oracle

**Status:** reference-side first-race replay confirmed; native comparison open  
**Date:** 2026-09-29  
**Area:** TAS | input | emulator compatibility

TASVideos submission #4250 identifies Dessyreqt's full-game Uniracers movie as Snes9x 1.51 v17 and describes a blank-SRAM start. Its sync notes record successful verification using the movie's embedded settings. Unlike the 2008 SMV-v1 WIP, this movie therefore does not depend on the obsolete WIP1 timing flag.

**Local replay evidence:** attempt-2 run 36538122590 successfully extracts the reset-anchored movie, verifies the canonical ROM identity, replays the first historical race window on pinned Snes9x/snesref, and composes the durable result `analysis/generated/historical-2014-first-race-reference.json`. The trace reaches `inRace` at frame 794 and the first race-results state at frame 2874. The emitted canonical 8 KiB SRAM hash is recorded alongside the source/movie metadata in `analysis/generated/historical-2014-smv-metadata.json`.

**Interpretation:** a post-WIP1 historical movie now supplies a deterministic reference-side race-and-finish oracle independent of the 2008 WIP timing regime. This does not yet prove native replay fidelity.

**Next discriminator:** drive the same extracted frame masks and starting SRAM through the native bridge and compare the same transition/state checkpoints. Keep the 2008 WIP as a separate old-timing corpus rather than conflating a failure there with generic SMV playback.


### R-SEED-040 — Shipped RNC1 body ends at BB6E; BB73 is following helper code

**Status:** confirmed static source alignment  
**Date:** 2026-09-28  
**Area:** RNC | course loader | code archaeology

The preserved Method-1 `MAKEHUFF` tail aligns at USA `01:BB60`; its source-final `RTS` is exactly `01:BB6E`. This establishes the USA/legacy-beta RNC1 body boundary as `01:B8F1..01:BB6E`. The next helper starts at `01:BB6F`; `01:BB71` increments the input pointer and `01:BB73` is its following `BNE`.

Combined with the prior `GTBITS2` alignment at `01:BA96`, the two trace attribution scopes are statically separated: BA96 is generic RNC bit-reader code; BB73 is integration/helper code after RNC. Attempt-2 exact-IPC capture in run 36538122650 closes the remaining attribution gap: the `0x10..0x16` mutation stores execute at `82:E1E1`, not at BA96.


### R-SEED-041 — BB6F is the LoROM-safe RNC packed-word reader

**Status:** confirmed static behavior  
**Date:** 2026-09-29  
**Area:** RNC | LoROM | course loader | code archaeology

**Observation:** USA `01:BB6F` starts with a 16-bit `LDA [IN]`, probes whether `INC IN` wrapped, and on the wrap path reconstructs the high byte from next-bank `$8000` before restoring the original packed-stream pointer. On the normal path it simply restores `IN` and returns. The helper is called from the shipped RNC integration where preserved source performs direct `LDA [IN]` packed-word reads.

**Interpretation:** name the helper `RNC1_ReadWordLoROMSafe`. It adapts the preserved linear RNC decoder to LoROM bank-boundary semantics. `01:BB73` is the helper's `BNE` wrap test, so the earlier `interp@$81BB73` write attribution is conclusively a bridge-scope label rather than a literal store PC.

**Exact-IPC follow-up:** run 36538122650 identifies the decoded `0x0F` write at `81:B9C8` and all seven increment writes at `82:E1E1`. Future analysis should explain those literal store sites and their callers rather than infer store ownership from interpreter scope labels.


### R-SEED-042 — LE16@11 is a 16-byte-aligned pre-trailer cursor

**Status:** runtime behavior confirmed on two courses; exact trailer semantics open  
**Date:** 2026-09-29  
**Area:** course format | runtime mutation | loader

**Observation:** across all 45 USA decoded streams, `LE16@11 + 1` is 16-byte aligned. Between 7 and 36 decoded bytes remain after that cursor. Dragster has `LE16@11=0x840F`, so its trailing region starts at aligned offset `0x8410` and contains exactly seven bytes through EOF at `0x8416`. The already observed seven runtime increments produce `0x8416`, exactly the final valid decoded offset.

**Rejected stronger claim:** `LE16@11 + 8 == decoded_size` is **not** a corpus invariant; it holds only for stream 1. The other 44 gaps range from 11 through 37 bytes.

**Second-course runtime confirmation:** attempt-2 run 36538122823 loads the first event of tour index 2. The best decoded match is the expected stream 11 (`best_equal_fraction=0.9999842263829519`). Its decoded cursor is 63375, 21 bytes remain after it, and the live cursor settles at 63396: an advance of exactly 21 to `decoded_size - 1` for decoded size 63397. The durable result is `analysis/generated/course-runtime-tour2-tail-cursor.json`.

**Interpretation:** Dragster's seven-step mutation was not a one-course coincidence. On two courses with different trailer lengths, the field starts immediately before the variable trailing region and advances by exactly that region's length to the final decoded byte. Treat `LE16@11` as a mutable pre-trailer/setup cursor. The meaning and grammar of the bytes it traverses remain open.

**Next discriminator:** decode the trailer grammar and trace the exact `82:E1E1` store consumer/loop. A third course is useful as regression coverage but is no longer required to justify the cursor model.


### R-SEED-043 — Cursor boundary is 16-byte aligned, not generally 1024-byte aligned

**Status:** stronger interpretation rejected  
**Date:** 2026-09-29  
**Area:** course format | layout | negative evidence

**Observation:** `LE16@11 + 1` is 16-byte aligned for all 45 USA decoded streams. Dragster additionally happens to satisfy `LE16@11 + 1 = 16 + 33×1024`, which superficially meshes with the independent header-dimension product of 1024.

**Falsification:** only 4/45 USA streams satisfy `LE16@11 + 1 = 16 + N×1024` (streams 1, 7, 9 and 16). The other 41 boundaries land on smaller 16-byte subdivisions.

**Conclusion:** retain the 16-byte boundary invariant. Do **not** interpret the cursor as the end of a stack containing only whole 1024-byte planes, and do not merge this fact with the separate 1024-unit dimension invariant without new runtime/structural evidence.


### R-SEED-044 — Post-cursor region length varies by track-order role

**Status:** confirmed corpus association; semantics open  
**Date:** 2026-09-29  
**Area:** course format | track type | structural statistics

**Observation:** using `LE16@11 + 1` as the aligned start of the decoded trailing region, the nine known stunt-slot streams (tour slot 3) have lengths 10–21 bytes, median 17 and mean 17.0. The other fixed tour slots have medians 26 (slot 1 Race), 27 (slot 2 Circuit), 23 (slot 4 Race) and 27 (slot 5 Circuit); their means are approximately 23.89, 27.22, 23.78 and 26.78 respectively.

**Interpretation:** the trailing region is unlikely to be arbitrary alignment padding alone. Its length distribution is associated with the fixed Race/Circuit/Stunt track-order role, with stunt courses systematically shorter. This does not yet identify the records or prove the trailer is track-type metadata; geometry complexity or another correlated property could produce the same pattern.

**Evidence update:** attempt-2 run 36538122757 regenerated the full trailer corpus; the durable human-readable report is `analysis/generated/course-trailer-structure.md`. Attempt-2 run 36538122823 independently confirms that the non-Dragster stream-11 runtime advances through all 21 trailer bytes to EOF−1.

**Discriminating tests:** classify the trailer byte grammar and compare Europe-retail variants. The former runtime question, whether a non-Dragster course walks the entire region, is now closed positively.

### R-SEED-045 — Beetle/bsnes teardown abort has a concrete double-free path

**Status:** source-level root cause identified; fix deferred to a non-conflicting toolchain change  
**Date:** 2026-09-29  
**Area:** emulator oracle | libretro | island toolchain

**Observation:** independent-reference run 36627766874 completes the full first-race fixture under the repository-owned Beetle/bsnes core, writes all expected evidence, and then exits 134 during libretro teardown. The vendored core's `retro_deinit()` manually frees `surf->pixels` / `surf->pixels16` and immediately executes `delete surf`. `MDFN_Surface::~MDFN_Surface()` independently frees the same pixel pointer. Therefore the normal teardown path contains a deterministic double free.

**Interpretation:** the post-fixture abort is an adapter/core cleanup defect, not evidence of failed emulation or incomplete fixture execution. The smallest correction is to let `MDFN_Surface` own and free its allocation exactly once, preferably as a narrow project-owned patch rather than silently editing the pristine vendored source.

**Concurrency note:** the active OAM/2P branch currently owns `tools/toolchain.json`, so registering the patch there is intentionally deferred until that work lands or moves clear. Preserve the current exit-134 allowance only until the ownership-safe patch can be applied and validated.


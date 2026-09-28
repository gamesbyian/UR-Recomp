# Resource Collection and Development Research Plan

Last updated: 2026-09-28

This document is the canonical plan for combining external-resource collection, original-development archaeology, ROM reverse engineering, and SNESRecomp bring-up. It replaces the earlier posture of broad collection-first research.

## Objective

The end-to-end product architecture is owned by `docs/PROJECT-PLAN.md`. This document owns the research and evidence program that unlocks that plan.

Reach a trustworthy native execution of Uniracers while progressively converting external evidence into reproducible knowledge of the ROM, especially course data, renderer/OAM behavior, player-state addresses, protection paths, and original DMA tooling conventions.

The project has crossed an important threshold: several former historical leads are now binary-confirmed facts. Research should increasingly be driven by discriminating experiments rather than broad searching.

## Established state

The following are considered established unless contradicted by stronger evidence:

- Canonical USA retail ROM is fingerprinted and machine-verifiable.
- November 29, 1994 PAL prototype is preserved and fingerprinted.
- Europe retail and the historical GoodSNES-listed `Uniracers (Beta)` images are also preserved, fingerprinted, and organized under `reference/roms/`.
- A deterministic four-build comparison is generated at `analysis/generated/reference-rom-comparison.md`.
- USA retail vs the legacy beta differs in only 486 isolated one-byte positions; all 45 RNC streams are byte-identical at the same offsets.
- Europe retail retains 38 of the 45 RNC streams byte-for-byte but changes seven ordinal streams: 4, 16, 20, 26, 27, 35 and 36.
- The retail and prototype ROMs are both 2 MiB LoROM builds.
- Structural comparison is generated at `analysis/generated/retail-vs-prototype-structure.md`.
- Both ROMs contain exactly 45 valid RNC streams.
- All 45 streams use RNC Method 1.
- All 45 streams occur at identical offsets and have matching packed/unpacked sizes and CRCs across USA retail and the 1994-11-29 PAL prototype. Europe retail relocates most streams after seven content/size changes, so cross-build RNC matching must use content fingerprints rather than offsets alone.
- The RNC corpus begins at `0x0C0000` and extends through the last stream beginning at `0x0FB9D7`.
- Period RNC ProPack 2.14 source, including SNES Method 1 and Method 2 unpackers, is preserved under `references/imported/tools/rnc_propack-2.14/`.
- The active-display OAM / split-screen behavior is supported by independent emulator implementations and first-hand Mike Dailly testimony describing scanline-based C64-style sprite ripping.
- jgenesis supplies concrete expected HBlank OAM writes in Vs. mode: scanlines 0 and 112, values 0xA5 and 0x5A, affecting high OAM for sprites 96-99.
- The recovered Canoe patch hooks original ROM code at offsets `0x01534C` and `0x015714`.
- TAS and RetroAchievements sources provide useful WRAM/SRAM anchors for speed, boost, position, stunt state, medal state, and progression.
- Historical SNasm 1.7.1 is preserved locally, and Dailly's documented 65816 syntax/conventions provide lineage evidence for future reconstructed assembly.
- The strict native smoke harness builds and launches the actual `UniracersSNESRecomp` target. Run 36493358927 also captured and visually verified a coherent stock Uniracers title screen from the native executable. The next native milestone is deterministic input through menus into a playable race.

## Operating priorities

### 1. Extend native bring-up from verified title screen to deterministic menu/race execution

The build/executable-discovery and visible-title gates are cleared. The next execution task is deterministic controller input through the frontend into a representative one-player race, followed by independent reference comparison.

Actions:
- keep `.github/workflows/native-build-smoke.yml` strict about the exact generated Uniracers target;
- retain deterministic screenshot/frame evidence from the real native process;
- add deterministic input and reach menu selection and a stock one-player race;
- run the same route through `snesref` and compare bounded state/frame evidence;
- characterize the first deterministic runtime/visual/input failure only after it is observed;
- classify it as configuration, runtime/framework behavior, unsupported SNES hardware behavior, generated-code problem, or project integration;
- record the first failing observable state in `docs/BRINGUP.md`;
- prefer the smallest correct framework/configuration fix over game-specific patches;
- keep stock 4:3 behavior as the oracle.

Exit condition: deterministic menu navigation reaches a stock one-player race and either executes correctly against the reference route or its first genuine divergence is reduced to a reproducible state.

### 2. Decode and inventory all 45 RNC streams

RNC is no longer a hypothesis. Build deterministic tooling around the confirmed corpus.

Actions:
- extract each stream by offset;
- independently decompress Method 1;
- verify unpacked length and CRC;
- emit hashes and structural summaries for every decoded output;
- preserve generated outputs outside Git when bulky, but commit compact manifests/reports and reproducible tooling;
- compare decoded outputs across streams for common headers, dimensions, dictionaries, repeated blocks, and record structure.

Exit condition: **met 2026-09-28**. All 45 streams in each of four preserved builds decode reproducibly with packed/unpacked CRC verification; compact manifests are generated in CI.

### 3. Identify the semantic course format

Use the decoded RNC corpus to test historical claims rather than inheriting them.

Actions:
- test the reported 256-tile width and 64x64-block interpretation against bytes;
- correlate decoded stream sizes and structures with the 44 VGMaps course maps and in-game course count;
- use the historical `7E:2080` course-load breadcrumb and known WRAM state where applicable;
- identify course index/pointer tables and the loader;
- distinguish geometry, visual tiles, metadata, hazards, boosts, starts/finishes, themes, and parallel tables;
- generate at least one course representation independently matching a known map.

Exit condition: a parser can turn one or more ROM course records into a documented structural representation that matches gameplay/reference maps.

### 4. Use all preserved builds as targeted differential oracles

USA retail and the 1994-11-29 PAL prototype share the complete 45-stream packed corpus, while Europe retail changes seven streams and the legacy beta differs from USA retail only outside that corpus.

Actions:
- classify the 486 isolated USA-retail vs legacy-beta byte changes;
- independently decode and compare PAL retail streams 4, 16, 20, 26, 27, 35 and 36 against their USA/prototype counterparts;
- classify the largest executable/data diff runs outside the RNC region;
- prioritize code-shaped differences and regions near known hooks/entry points;
- identify regional timing, frontend/text, protection, late fixes, graphics/audio, and table changes;
- use shared code blocks to align functions and changed blocks to expose boundaries;
- annotate useful differential landmarks in the research ledger/symbol map.

Exit condition: the largest useful diff regions are classified and at least several function/table boundaries are established.

### 5. Map the OAM/sprite-ripping behavior back to game code

The conceptual mechanism is already strong. The remaining task is exact implementation mapping.

Actions:
- disassemble around the Canoe hook offsets `0x01534C` and `0x015714`;
- trace writes to `$2104` and related OAM/HDMA state;
- verify scanline 0/112 and 0xA5/0x5A behavior where possible;
- compare unpatched behavior, Canoe workaround behavior, and emulator special cases;
- determine whether the correct SNESRecomp fix belongs in generic PPU/OAM emulation rather than game code.

Exit condition: the exact ROM routine(s) responsible for the split-screen sprite behavior are identified and symbolized.

### 6. Turn known WRAM/TAS evidence into symbols

Use the known runtime addresses as anchors for code discovery.

Priority anchors include:
- `7E:04B7` signed speed;
- `7E:11CD` boost meter;
- `7E:0411` / `7E:0415` X/Y position;
- `7E:1509` screen X;
- published stunt-state addresses;
- progression/medal SRAM offsets from TAS/RetroAchievements.

Actions:
- find writers/readers;
- classify update cadence and units;
- connect addresses to routines;
- add stable names to `docs/SYMBOLS.md`;
- use controlled gameplay to verify semantics.

### 7. Continue resource collection only where it can unlock current work

Broad "find everything Uniracers" searching is now lower priority.

Highest-value missing artifacts:
1. Mike Dailly's historical SNES framework source.
2. `usjo13.lua` / Uniracers Stunts & Jump Optimizer v13.
3. Halamantariel's historical boost table.
4. Old Uniracers SMV/WIP files and fall-through-glitch savestates.
5. Original 1993-era SNasm or Uniracers-specific development-tool source/binaries/screenshots.
6. Dailly Flickr/Wayback material specifically attributable to Uniracers/`1x1`.
7. Published Hammond/DMA archive material that contains Uniracers-specific development documents.
8. gamesTM issue 64 only if its physical layout/captions/images can add material omitted from the Nintendo Life republication.

For every recovered artifact:
- preserve original filename;
- record source URL and retrieval date;
- record byte size and SHA-256;
- preserve archive/container provenance;
- document redistribution status where known;
- commit only when useful and appropriate;
- add the source to `references/catalog.yml` and/or the acquisition ledger.

## Resource-search strategy

Searches should now begin from exact names, filenames, URLs, people, or technical behaviors rather than generic Uniracers terms.

Preferred search keys:
- `usjo13.lua`
- `Uniracers Stunts & Jump Optimizer`
- Halamantariel + boost table / speed / Uniracers
- old obellemare.com speedruns paths
- Dailly SNES framework / 65816 framework
- `1x1` + DMA Design
- SNasm + javalemmings/minus4
- Unicycle Compression
- Uniracers Editor / A0 plotter
- Malcolm Scott Maxwell / Martin Good + Unirally/Uniracers
- Canoe Uniracers patch provenance
- known old SMV filenames/URLs from TASVideos threads

Wayback, old forum archives, preserved personal sites, source mirrors, and exact historical URLs should take precedence over generic modern search results.

## Research discipline

- Separate observation, interpretation, and hypothesis.
- Convert external claims into local tests whenever possible.
- Prefer exact addresses, hashes, traces, diffs, source blobs, and reproducible scripts.
- Do not treat modern SNasm syntax as proven identical to the 1993 assembler.
- Do not infer semantic meaning from RNC block count alone.
- Do not assume prototype differences are gameplay changes until classified.
- Do not introduce widescreen or presentation changes before stock execution is trustworthy.
- Keep generated C disposable; durable knowledge belongs in configs, hand-authored tooling, symbols, tests, and documentation.

## Current execution loop

The preferred single-agent loop is:

1. inspect current CI/bring-up state;
2. reduce the native boot failure;
3. while blocked or once a clean checkpoint is reached, build RNC extraction/decompression tooling;
4. characterize decoded streams and begin course-format identification;
5. classify prototype/retail diff regions using emerging symbols;
6. map OAM/Canoe hooks and known WRAM anchors;
7. perform narrowly targeted archival recovery when a missing artifact can materially accelerate one of the above;
8. update canonical docs and commit coherent checkpoints.

The agent should move between these tracks based on evidence and blockers rather than completing them as rigid phases.

## Canonical supporting documents

- `docs/WORK-QUEUE.md` — execution milestones and status.
- `docs/BRINGUP.md` — empirical runtime/build chronology.
- `docs/COURSE-FORMAT.md` — course/RNC investigation.
- `docs/RESEARCH-LEDGER.md` — evidence-backed technical claims.
- `docs/SYMBOLS.md` — reconstructed code/data symbols.
- `docs/original-development/DEVELOPER-TECHNICAL-HISTORY.md` — original-development history.
- `docs/original-development/SOURCE-INDEX.md` — source provenance.
- `docs/original-development/ACQUISITION-LEDGER.md` — missing/acquired artifacts.
- `references/catalog.yml` and `references/notes/` — external-source corpus.
- `analysis/generated/retail-vs-prototype-structure.md` — original USA-retail vs PAL-prototype structural comparison.
- `analysis/generated/reference-rom-inventory.md` — exact local identities for all preserved ROMs.
- `analysis/generated/reference-rom-comparison.md` — current four-build pairwise and RNC comparison.
- `docs/TOOLCHAIN.md` — pinned external research/development tools and bootstrap policy.

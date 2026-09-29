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
- The strict native smoke harness builds and launches the actual `UniracersSNESRecomp` target. Deterministic controller-only input reaches the first one-player race in both native SNESRecomp and Snes9x/snesref. The former seven-byte settled race-entry WRAM mismatch is now explained: four bytes are stale stack residue and three are free-running timing/phase counters.

## Operating priorities

### 1. Extend deterministic differential coverage into race behavior

The build, title, deterministic frontend, race-entry, reference replay and first settled-race WRAM-divergence gates are cleared. Run 36511207129 resolves the former seven-byte race-entry mismatch as non-semantic residue: `$01D1–$01D4` is stale stack history, while `$00C6/$00C8/$00C9` are free-running phase counters.

Actions:
- keep `.github/workflows/native-build-smoke.yml` strict about the exact generated Uniracers target;
- preserve `tests/input/reach-first-race.script` and its native/reference checkpoint corpus as the baseline;
- extend the shared deterministic fixture into race start, acceleration, jump, rotation, landing, collision and finish;
- validate Dessyreqt's recovered player-state labels, especially X/Y position, X/Y speed, pitch, air state and countdown timer, against both runtimes;
- compare event-relative semantic state instead of requiring equality of stale stack bytes or free-running presentation counters;
- promote stable race behaviors into durable fixtures and assertions;
- trace the earliest meaningful writer/state divergence only if a semantic invariant actually disagrees;
- keep stock 4:3 behavior as the oracle while race simulation coverage expands.

Exit condition: the first-race fixture exercises representative movement/physics events with confirmed player-state semantics and objective native/reference assertions, leaving no unexplained simulation-state mismatch in those cases.

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

### 5. Convert emulator-specific compatibility history into local tests

The active-display OAM mechanism is already strongly supported, and historical Snes9x records show that Uniracers also exposed separate SRAM-mapping, window/XOR and color-math/subscreen issues. Treat these as a small compatibility research program rather than one generic "Uniracers hack."

#### Active-display OAM / sprite ripping

Actions:
- disassemble around the Canoe hook offsets `0x01534C` and `0x015714` and injected handler at `0x1FFF00`;
- identify the original routines affected by those hooks;
- trace writes to `$2104` and related OAM/HDMA state in the canonical USA ROM;
- verify the jgenesis scanline 0/112 and `0xA5`/`0x5A` observations where possible;
- verify the effective high-OAM byte and sprites 96-99;
- compare unpatched behavior, Canoe workaround behavior, Snes9x's title-specific special case, MAME/jgenesis hardware models, bsnes/ares and SNESRecomp;
- determine whether the correct SNESRecomp fix belongs in generic PPU/OAM emulation rather than game code.

#### Other historical compatibility seams

Actions:
- reproduce the historical LoROM SRAM-mapping issue or demonstrate that the current runtime already handles it, then preserve a deterministic clean/save/load byte-roundtrip test;
- locate a screen affected by the historical XOR/window-area logic fix and preserve PPU/window-state plus frame evidence;
- locate a screen affected by the historical color-addition / empty-subscreen behavior and preserve color-math/subscreen state plus frame evidence;
- keep these tests independent so a rendering failure is not automatically attributed to the OAM path.

Exit condition: each known historical Uniracers emulator-compatibility seam has a local explanation and a deterministic regression test, or a documented demonstration that it does not apply to the canonical runtime.

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

### 8. Establish visual-reference capture tooling without stealing the critical path

RetroArch, the Libretro Slang shader corpus and bsnes-hd are now pinned as on-demand resources. Their primary value belongs to Phase E/HD Presentation, but they may be pulled forward when a concrete rendering investigation benefits from matched presentation variants or layer/sprite isolation.

Actions:
- curate a small project-owned preset matrix covering raw/nearest controls, ScaleNx, HQx, xBR/xBRZ, SABR, ScaleFX, Super-xBR and representative NTSC/CRT treatments;
- prove one deterministic identical-frame RetroArch capture route under Linux/headless automation and measure startup/runtime/storage cost;
- identify reliable offline implementations for scaler families that can process extracted PNG assets without emulator/frontend startup;
- test bsnes-hd layer/sprite isolation against one useful Uniracers scene before promoting it beyond specialist status;
- for PPU, color-math, window, OAM or other fidelity work, preserve and compare raw captures first, then use presentation processing only as a secondary diagnostic view;
- add producer/consumer contracts to `tools/tool_interop.json` only after a concrete capture experiment establishes real commands and outputs.

Priority: opportunistic now, high when Phase E begins producing deterministic graphics assets, and immediately useful earlier only when a rendering seam specifically benefits from these capabilities.

Canonical visual-reference design: `HD-VISUAL-REFERENCE-PIPELINE.md`.

## Research before reinvention

External research is also an escalation mechanism for technical work, not only a way to collect Uniracers artifacts.

When an experiment exposes unexplained emulator behavior, a recompilation/analyzer limitation, an unfamiliar ROM/data pattern, a rendering or timing quirk, a difficult reverse-engineering problem, or a retro-porting problem with no established local technique, search the wider ecosystem before inventing another bespoke layer.

The search should be problem-shaped rather than game-shaped. In addition to Uniracers-specific evidence, look for analogous techniques and failure modes in:

- SNESRecomp and related static/dynamic recompilation projects, including N64 recompilation work where the engineering pattern transfers;
- game decompilation and native source-port projects;
- bsnes/higan/ares, Mesen, Snes9x, jgenesis, MAME and other emulator implementation histories, tests and issue discussions;
- consoledev documentation and hardware test ROMs;
- ROM-hacking, restoration, widescreen/enhancement and randomizer projects;
- TAS, botting and debugger automation;
- asset extraction, tile/sprite conversion, compression/decompression and reassembly tooling;
- Ghidra/IDA/disassembler processor modules and reverse-engineering workflows for old consoles.

Do not wait for complete blockage. If two or three materially different local attempts have failed without reducing the uncertainty around a problem, broaden the search before building more custom instrumentation or accepting a workaround.

Search results remain leads. Before adopting a technique:
1. identify which part of the external solution actually transfers;
2. test that claim against the canonical ROM/runtime;
3. prefer a general explanation over a title-specific workaround when evidence supports one;
4. capture provenance for code, patches, technical claims and important issue discussions;
5. promote the useful result into a project-owned test, tool, symbol, fixture or documented invariant.

This rule is intended to prevent local tunnel vision and repeated reinvention, not to encourage open-ended browsing. Stop searching when the current uncertainty has a good discriminator and return to local evidence.

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

## Frontend / screen-flow mapping

Maintain a machine-readable UI state graph in `analysis/ui-state-map.yml` and the corresponding human guide in `docs/UI-STATE-MAP.md`.

This is a cross-cutting research aid, not a presentation-only task. Use it to connect player-visible screens to controller inputs, WRAM/menu-state IDs, local framebuffer dumps, runtime routines, deterministic fixtures, and later frontend replacement work. Public screenshots and manual descriptions are valid bootstrap evidence; important behavior should migrate toward locally reproduced controller-only routes.

Do not spend compute deriving obvious button behavior from assembly when a screenshot plus the documented menu convention gives a strong candidate. Run the cheap candidate first, capture the resulting state, and only instrument deeper if the observation is ambiguous or fails.

## Experimental apparatus

The research program should attack important unknowns from multiple independent directions rather than treating disassembly as the final product.

Already implemented:
- deterministic controller fixtures shared by native recompilation and `snesref`, cataloged in `tests/fixtures.json`;
- full-WRAM checkpoint comparison and native write-history tracing on the first-race fixture;
- machine-readable symbol export at `analysis/generated/symbols.json`, generated from the human authority `docs/SYMBOLS.md`;
- controlled byte mutation with `tools/mutate_rom.py`, including before/after bytes and ROM hashes;
- pinned on-demand DiztinGUIsh, bsnes-plus, MesenCE, and mesen-for-ai source checkouts in the toolchain manifest.

Next apparatus work, in dependency order:
1. Extend the replay corpus through acceleration, jump, rotation, landing, collision, finish, two-player, save/load, and known emulator-sensitive scenes.
2. Extend checkpoint capture from WRAM into relevant CPU, PPU, OAM, VRAM and audio state only when a discrepancy requires it.
3. Add code/data coverage capture using Mesen CDL or DiztinGUIsh/bsnes+ traces; merge repeated runs into a compact ROM coverage map and feed mode/bank knowledge back into static disassembly.
4. Build a smallest-first first-divergence reducer: checkpoint mismatch → last matching frame → first differing frame → first differing write/register event → owning guest routine.
5. Use controlled ROM mutation only against specific hypotheses and classify effects by deterministic replay, never by undocumented manual observation alone.
6. Build reproducible asset extract → decode → inspect → modify → repack/patch → replay loops for graphics/course/resource formats as they become understood.
7. Introduce a secondary high-accuracy oracle for hardware-sensitive findings and, where practical, compare against real-hardware captures before declaring an emulator-specific behavior to be hardware truth.

The goal is a closed evidence loop: ROM bytes → static hypothesis → dynamic observation → controlled perturbation → deterministic differential → promoted symbol/format knowledge.

## Research discipline

- Separate observation, interpretation, and hypothesis.
- Convert external claims into local tests whenever possible.
- Prefer exact addresses, hashes, traces, diffs, source blobs, and reproducible scripts.
- Do not treat modern SNasm syntax as proven identical to the 1993 assembler.
- Do not infer semantic meaning from RNC block count alone.
- Do not assume prototype differences are gameplay changes until classified.
- Do not introduce the Widescreen feature or other presentation changes before stock execution is trustworthy.
- Keep generated C disposable; durable knowledge belongs in configs, hand-authored tooling, symbols, tests, and documentation.

## Current execution loop

The preferred continuation loop is:

1. inspect the latest race-behavior fixture/run and preserve the last verified semantic checkpoint before extending the workload; the active whole-race candidate is `tests/input/race-finish-dragster.script`, gated on stock race-results state in both native and Snes9x;
2. treat straight-line acceleration as established: `7E:0411` X position and signed `7E:04B7` X speed are confirmed cross-runtime, with `7E:11BA` decrementing by `0x0100` per guest frame during the sampled start window;
3. treat jump, rotation, event-relative landing and one failed-landing/contact case as established: `7E:0415` Y position, signed `7E:04BB` Y speed, `7E:0545` air state and modulo-64 `7E:04C7` pitch angle are validated cross-runtime; deterministic stock-race finish is now the active race-behavior milestone;
4. resolve recovered-source ambiguities before promoting symbols; in particular, respect Lua duplicate-key semantics and distinguish effective bot addresses from earlier overwritten candidates;
5. promote confirmed race-state fields/routines into `docs/SYMBOLS.md`, regenerate `analysis/generated/symbols.json`, and record evidence-backed conclusions in the research ledger/knowledge base;
6. promote durable replay cases into `tests/fixtures.json` and compare semantic/event-relative state rather than stale stack or free-running presentation counters;
7. when WRAM/write-history evidence is insufficient, add the smallest useful CPU/PPU/OAM/VRAM/audio capture or use the pinned MesenCE/mesen-for-ai or DiztinGUIsh/bsnes+ workbench for code/data coverage;
8. use `tools/mutate_rom.py` only for specific causal hypotheses and score mutations through deterministic replay; use asset round-trip experiments when a resource format is sufficiently understood;
9. when a technical problem stays weird after two or three materially different local attempts, search the broader decomp/recomp/emulation/ROM-hacking/retro-porting ecosystem for analogous techniques before adding another bespoke layer;
10. continue course-format, emulator-compatibility and archival work opportunistically when the active execution evidence exposes a discriminating question or a missing artifact can materially accelerate it;
11. update canonical docs and the active PR description at coherent checkpoints.

The agent should move between these tracks based on evidence and blockers rather than completing them as rigid phases. Repository state is authoritative over conversational summaries.

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

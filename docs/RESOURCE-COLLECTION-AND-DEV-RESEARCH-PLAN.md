# 2026-09-30 direct-contact evidence update

The Nitrodon workspace is now recovered, preserved and mined. It supplies a detailed WRAM map, annotated banks 80-83, stunt disassembly, message IDs, ROM/course-offset notes and a bounce trace. This materially lowers the expected value of hunting generic TAS-era notes: future Nitrodon/Dessyreqt outreach should target only **distinct** artifacts such as later USJO/Lua versions, savestates, SRAMs, SMVs, alternate traces or additional working directories.

The still-missing `usjo13.lua` remains useful as a version-delta artifact, but it is no longer needed to reconstruct stunt counters, shared velocity/boost state, landing stunt classification, or the base-5 stunt-combination table. Original DMA framework/tool/source artifacts remain the highest-leverage unrecovered class.
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
- USJO internal version 8 (2008-02-10) is preserved as exact source under `references/imported/tas-bots/usjo8.lua`. It directly exposes the historical stunt optimizer's savestate search loop, RAM reads, timing constants, stunt counters, boost scoring model and best-input replay behavior. `tools/inventory_usjo8.py` now converts that source into `analysis/generated/usjo8-static-inventory.{json,md}` so each historical address/rule can be queued for local reproduction without treating source labels as game truth.
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

### 4. Build a multi-ROM × multi-analyzer comparative code atlas

USA retail and the 1994-11-29 PAL prototype share the complete 45-stream packed corpus, while Europe retail changes seven streams and the legacy beta differs from USA retail only outside that corpus. The four preserved builds are now the expected ROM corpus; do not assume additional language/region releases exist or spend acquisition effort on speculative regional variants without a concrete catalog/provenance lead.

Use the four builds as repeated observations of the lost source program. Cross-build correspondence and independent analyzer agreement should be first-class evidence.

Actions:
- classify the 486 isolated USA-retail vs legacy-beta byte changes;
- independently decode and compare PAL retail streams 4, 16, 20, 26, 27, 35 and 36 against their USA/prototype counterparts;
- run corresponding executable regions through SNESRecomp manifest/generated-code analysis, snes2asm, bounded da65, and Ghidra/ghidra-snes when cross-reference persistence is useful;
- evaluate additional 65816 control-flow analyzers only if they provide a genuinely independent interpretation;
- create machine-readable fingerprints for candidate functions and data objects using instruction sequences, normalized operands, CFG shape, callers/callees, ROM references and WRAM/PPU accesses;
- align corresponding functions/tables across builds even when absolute addresses move;
- classify code-vs-data, function-boundary, M/X-state, indirect-target, jump-table and cross-reference disagreements between analyzers;
- prioritize disagreements and regions where one build exposes a boundary/target more clearly than another;
- identify regional timing, frontend/text, protection, late fixes, graphics/audio and table changes;
- propagate only locally verified semantic labels from Nitrodon/Dessyreqt/TAS/RetroAchievements/dynamic traces across matched functions, preserving provenance and confidence;
- annotate useful differential landmarks in the research ledger/symbol map;
- keep generated SNESRecomp C explicitly classified as execution-oriented translation evidence rather than a complete semantic decompilation.

Exit condition: a reproducible comparative-code-atlas artifact covers the useful executable corpus, major cross-build correspondences are machine-queryable, and analyzer disagreements form a bounded research queue rather than remaining invisible.

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

The ROM-release hunt is considered **closed unless a concrete new provenance lead appears**. Current evidence supports the preserved USA retail, Europe retail, historical beta and 1994-11-29 PAL prototype as the useful known build corpus; speculative searches for nonexistent language/region releases should not consume project time. A newly surfaced prototype, review build, manufacturing revision with distinct payload, or other independently built image would still be high-value and should be admitted immediately.

Missing-artifact priority is now marginal-value based rather than completeness based:

**P0 — active hunt because the artifact could materially reduce reverse-engineering work**
1. Mike Dailly's historical SNES framework source.
2. Original Uniracers/DMA development-tool source/binaries/screenshots, especially the editor, compression and conversion pipeline.
3. Original Uniracers/DMA development artifacts adjacent to already-known tooling, especially anything that exposes editor/physics/conversion internals.

**P1 — useful independent evidence; pursue opportunistically**
4. `usjo13.lua` or later USJO siblings. Internal v8 is now recovered and actionable, so v13 is a passive delta-recovery target rather than a blocker; do not wait on it before using v8.
5. Sinister Translations' independent 100% patch.
6. Actual FallThrough/Jumpover savestates or SMVs and other movies with unique behavioral coverage.
7. Dailly Flickr/Wayback material specifically attributable to Uniracers/`1x1`.

**P2 — optional accelerants; easy acquisition only**
8. Halamantariel's historical boost table, because surviving TASVideos posts already preserve several of its important conclusions and local physics tests can recover the rest.
9. Uniracers-specific Hammond/DMA archive material, manual scans, and course-map/reference-image corpora.

**P3 — archival tail; keep searchable but do not build recovery machinery around it**
10. SNasm 1.7.2 after 1.7.1 and the modern descendant are already preserved.
11. gamesTM issue 64 unless inspection proves it contains material omitted from the Nintendo Life republication.
12. Uniracers Uncensored unless a patch file reappears through a cheap direct/archive route.
13. Generic DMA media or fan-remake media without source, measurements, or Uniracers-specific technical evidence.

The full per-artifact need judgment lives in `docs/original-development/ACQUISITION-LEDGER.md`. P2/P3 artifacts remain valid leads, but no milestone should wait for them.

For every recovered artifact:
- preserve original filename;
- record source URL and retrieval date;
- record byte size and SHA-256;
- preserve archive/container provenance;
- document redistribution status where known;
- commit only when useful and appropriate;
- add the source to `references/catalog.yml` and/or the acquisition ledger.

### External-evidence intake and preservation

The source registry and active acquisition/reproduction queue have distinct owners:

- `references/catalog.yml` records source identity, provenance, rights status and relevance;
- `references/evidence-worklist.json` records live uncertainty, value/cost, acquisition state, next discriminator, expected deliverables and any genuinely necessary user action;
- `docs/EXTERNAL-EVIDENCE-INTAKE.md` defines the intake pipeline from public lead through local reproduction and promotion into durable project knowledge.

Do not leave actionable findings trapped in a conversational research report. Convert useful leads into the worklist, then close them by producing a local test, report, symbol, fixture, format description or explicit dead-end record. Independent translation patches and SPC dumps are first-class reverse-engineering evidence when their transformations can be mapped back to canonical ROM/runtime behavior. Social remake/rerelease discussions are lower-priority breadcrumb graphs unless their replies expose a project, author, artifact or technical measurement.

Prefer automated acquisition and one-shot workflows before asking for manual downloads. One-shot acquisition workflows are temporary and should be removed after evidence is harvested; they are not recurring CI.

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

## Value-of-information rule

Research effort should be proportional to the expected value of the uncertainty removed.

For any non-trivial investigation, especially video/frame mining, multi-core comparison, long traces, exhaustive static analysis, or custom instrumentation, record mentally or in the owning issue/work item:

- **decision:** what implementation, priority, or validation choice could change;
- **uncertainty:** which competing explanations remain plausible;
- **cheapest discriminator:** the smallest observation likely to separate them;
- **expected payoff:** what downstream work becomes safer or unnecessary if resolved;
- **stop rule:** when further evidence is unlikely to change the decision.

Default evidence ladder:

1. already-owned evidence, docs, symbols, screenshots, logs;
2. one cheap targeted observation;
3. bounded deterministic capture/diff;
4. fine-grained state/write/PC trace around a localized interval;
5. independent emulator or hardware-model corroboration only for claims whose consequence warrants it.

Do not jump to level 4 or 5 merely because the tooling exists.

For video and frame analysis, prefer coarse-to-fine localization: scene/timestamp scan → frame hashes or image deltas → short candidate windows → manual inspection of only the discriminating frames. Enhancement/compositing is worthwhile when it can recover a specific hidden fact that would change the plan; it is not a default requirement for every ambiguous image.

A useful heuristic is **decision value / investigation cost**, not confidence maximization. Low-cost, high-upside checks can be run speculatively. High-cost work needs a clear downstream hinge. Stop at “good enough to act” unless the claim will become a permanent fidelity invariant.

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
- `usjo8.lua`, `usjo13.lua`, and adjacent USJO version-family names
- `Uniracers Stunts & Jump Optimizer`
- plausible USJO version-family names (`usjo1.lua` through later variants) and directory-level backups containing sibling SMV/SRM/WR files
- published Uniracers WRAM literals combined with period Snes9x Lua APIs, to find renamed/copied descendants
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

Two-player and VS coverage is a required part of this workstream, not a deferred nicety. The shared neutral P1/P2 transport now exists; `docs/TWO-PLAYER-FIXTURE-PLAN.md` owns the behavioral acceptance route and downstream atlas/fidelity obligations. Continue single-controller atlas work in parallel, but do not treat frontend/fidelity coverage as complete while 2P/VS handoff, split-screen race entry, and cross-runtime multiplayer checkpoints remain unverified.

Do not optimize for 100% atlas closure as an end in itself. Classify remaining gaps before spending effort:

- **critical fidelity:** close it;
- **cheap completeness:** take the free evidence;
- **archaeological tail:** preserve known evidence and move on unless another task makes it relevant.

The default escalation budget for an archaeology-only gap is zero beyond cheap observation. Do not trace, disassemble, build bespoke tooling, or create recurring CI merely to answer trivia such as exact forbidden-name behavior, every intermediate tally state, editor punctuation wrapping, or exact attract-mode timing.

## Experimental apparatus

The research program should attack important unknowns from multiple independent directions rather than treating disassembly as the final product.

Already implemented:
- deterministic controller fixtures shared by native recompilation and `snesref`, cataloged in `tests/fixtures.json`;
- full-WRAM checkpoint comparison and native write-history tracing on the first-race fixture;
- machine-readable symbol export at `analysis/generated/symbols.json`, generated from the human authority `docs/SYMBOLS.md`;
- controlled byte mutation with `tools/mutate_rom.py`, including before/after bytes and ROM hashes;
- pinned on-demand DiztinGUIsh, bsnes-plus, MesenCE, and mesen-for-ai source checkouts in the toolchain manifest.

Next apparatus work, in dependency order:
1. Extend the replay corpus through acceleration, jump, rotation, landing, collision, finish, two-player, save/load, and known emulator-sensitive scenes. Use the shared neutral P1/P2 stream for multiplayer transport and the acceptance/checkpoint requirements in `docs/TWO-PLAYER-FIXTURE-PLAN.md` for the first durable 2P/VS atlas route.
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


## External-practice archaeology

Use outside decompilation, disassembly, recompilation, emulator and ROM-hacking work as a source of tested workflow ideas, especially when a new reverse-engineering phase begins or a recurring manual bottleneck appears.

Canonical notes and source list: `references/notes/external-reverse-engineering-practices.md`.

Operating rules:

- search in native-language vocabulary as well as English;
- prefer first-hand project docs, issue/PR history, dev blogs, talks and debugger/tool documentation;
- translate useful practice into a concrete local experiment, tool change or planning rule rather than accumulating a reading list;
- keep static and dynamic evidence distinct, particularly for 65816 code/data boundaries and M/X-dependent instruction widths;
- treat code/data logging as corpus-scoped observation, never proof that unseen bytes are non-code;
- preserve evidence strength on semantic names and symbols instead of allowing a plausible name to become an unqualified fact;
- continue the current selective-reverse-engineering strategy: understand deeply where the product needs hooks, validation or modification, and let generated recompilation carry unrelated code.

Immediate integration targets:

- [ ] Finish the canonical Mesen first-race route and validate the Mesen CDL adapter with per-fixture provenance.
- [ ] Preserve code/data/unknown and individual-vs-union coverage semantics when CDL feeds static tooling.
- [ ] Record relevant 65816 M/X entry-state evidence for canonical static regions where immediate-width ambiguity can affect decoding.
- [ ] Pilot deterministic extract -> semantic artifact -> unchanged reconstruction validation on the first suitable graphics/course asset family.
- [ ] Add evidence strength/class metadata to promoted symbols when the symbol schema is next extended.
- [ ] Add compact failure-capsule generation only if repeated first-divergence investigations show manual artifact bundling is recurring work.


## Recovery ownership: evidence-to-executable backlog (2026-09-29)

The project has largely solved *evidence intake*; current research should emphasize conversion of evidence into executable knowledge. The canonical product plan's **Evidence-to-executable recovery backlog (2026-09-29)** is binding. This research plan owns the investigative side of that backlog.

Priority research lanes, in current impact order:

1. **Bracket and explain the exact 2014 native/reference divergence around guest frame 440.** Capture increasingly fine state/PC/write evidence until the first causal divergence is localized. Treat this as the highest-value fidelity signal because it may expose a translated-code, host-timing, startup-state, controller-stream, or hardware-model defect that affects everything downstream.
2. **Expand the comparative decompilation atlas on executed/high-value code.** Use the four preserved ROMs plus SNESRecomp, snes2asm, bounded da65 and Ghidra where useful. Resolve analyzer disagreement, align moved routines, and prioritize the three unresolved indirect dispatch sites, two LLE-only variants, and the five explicit core semantic placeholders.
3. **Promote core simulation/rendering semantics required by the product architecture.** Main loop, player update/physics, course loader/representation, camera, OAM/sprite construction/culling and race state outrank low-impact archaeological completeness because they unlock exact fidelity, widescreen/HD presentation and course tooling.
4. **Close the deterministic stock-race/2P fidelity gates using the improved semantic map.** Finish, simultaneous two-player behavior and remaining active-display OAM seams are higher-value once the frame-440 divergence is understood.
5. Continue four-ROM differential archaeology for executable/table/frontend/localization/timing/protection deltas, especially where it helps lanes 1-4.
6. Continue TAS/cheat/RetroAchievements/Nitrodon/Dessyreqt evidence promotion when it names or constrains code used by lanes 1-4. The `usjo13.lua` hunt is now passive unless a concrete lead appears.
7. Keep CPU-side audio, Sayans/Sinister translation archaeology, UI-tail completion and unused-content confirmation moving opportunistically, but do not let them outrank unresolved core fidelity/decompilation work. Audio package attribution is already substantially closed.
8. Continue archival reconstruction of DMA's original authoring pipeline opportunistically. Original editor/framework/conversion source remains potentially high-leverage, but acquisition is not a gating dependency and should not displace executable local work.

For every lane, the preferred end product is a fixture, verified symbol, parser, generated report, regression, implementation constraint or durable negative result. A link alone is intake, not completion.

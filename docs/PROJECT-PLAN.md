# Uniracers Modern Port Plan

Last updated: 2026-09-29

This is the canonical product-development plan for turning the original SNES Uniracers / Unirally into a faithful modern native port.

For current reverse-engineering priorities, evidence collection and archival work, see `RESOURCE-COLLECTION-AND-DEV-RESEARCH-PLAN.md`. For day-to-day milestone status, see `WORK-QUEUE.md`. Remaining global tooling-audit work is bounded by `TOOLING-AUDIT-CLOSEOUT.md`; experiments transferred from that audit are owned by the relevant phases below. This document owns the longer path from stock native execution to the intended modern port.

## Terminology

The project as a whole is the **UR-Recomp project**, **Uniracers modern port**, or simply **the project**. Do not use `widescreen` or `HD` as shorthand names for the project, its overall architecture, or its end state.

**Widescreen** means the specific feature that expands the logical horizontal view beyond the original 4:3 presentation.

**HD Presentation** means the specific feature that substitutes or renders higher-resolution visual assets/presentation while preserving authoritative game state.

Use those terms only when discussing those features or their implementation. Other work should be named for what it actually is: native execution, fidelity validation, reverse engineering, course decoding, asset extraction, tooling, audio modernization, custom courses, and so on.

## Product definition

The target is **Uniracers itself**, not a mechanically similar recreation.

The original game simulation remains authoritative for:

- physics;
- collision and track contact;
- player and opponent state;
- stunt recognition;
- acceleration, boost and braking;
- RNG;
- race rules and progression;
- timing;
- AI;
- course semantics;
- save/progression behavior.

The modern port may replace or extend presentation, input plumbing, display aspect, windowing, asset resolution, UI composition and optional audio presentation, but stock gameplay must remain reproducible from the original logic.

The end-state should support:

- native desktop execution;
- authentic 4:3 presentation as a permanent regression/reference mode;
- the **Widescreen** feature, providing true additional horizontal view rather than stretched 4:3;
- modern window sizes including 4K output;
- high-resolution replacement art while preserving original animation/state timing;
- original courses and simulation behavior;
- deterministic validation against the original ROM;
- eventual documented course tooling and custom courses;
- a public-release path that does not require distributing proprietary ROM bytes.

## Architecture decision

The default architecture is:

```
original ROM
    |
    v
SNESRecomp analyzer + generated native 65816 code
    |
    v
authoritative original simulation / SNES state
    |
    +------------------------------+
    |                              |
    v                              v
authentic PPU path          enhancement policy
4:3 oracle                  game-state / symbols
    |                              |
    |                        +-----+------+
    |                        |            |
    v                        v            v
stock framebuffer      true-wide PPU   overlay extraction
                       rendering       / HD Presentation
                            |            |
                            +-----+------+
                                  |
                                  v
                           modern host compositor
                                  |
                                  v
                         4:3 / 16:9 / 4K output
```

A separate gameplay rewrite in Godot, Unity or another engine is **not** the primary plan. It would create a second simulation that must independently reproduce every quirk already present in the executable original. A separate renderer or editor may eventually use decoded project data, but the shipping simulation should remain the recompiled game unless evidence shows that approach cannot meet the presentation goals.

Generated C is disposable implementation output. Durable game-specific knowledge belongs in:

- analysis configuration;
- runtime/host integration;
- enhancement hooks;
- symbols;
- parsers;
- asset manifests;
- deterministic tests;
- compact evidence reports.

## What the project already has

The plan begins from a much stronger baseline than a normal blind SNES port.

### Native execution

The canonical USA ROM already builds through the pinned SNESRecomp stack and reaches a visually verified stock Uniracers title screen in the actual generated executable.

The current smoke proves:

- the intended native executable is built, not a CMake helper;
- the canonical ROM loads;
- SNES initialization succeeds;
- SDL/X11 video initializes;
- audio initializes;
- the main loop runs;
- frames are simulated;
- a real presented frame can be captured;
- frame 300 has been visually identified as the coherent stock title screen.

The next execution target is deterministic menu navigation and a playable race.

### Four-ROM differential corpus

The repository contains:

- USA retail;
- Europe retail;
- historical GoodSNES-listed `Uniracers (Beta)`;
- 1994-11-29 PAL prototype.

Important current observations:

- USA retail and the legacy beta differ in only 486 isolated byte positions;
- their 45 RNC streams are byte-identical;
- USA retail and the November PAL prototype also share the complete 45-stream RNC corpus;
- Europe retail changes seven decoded streams while preserving 38 byte-for-byte.

These builds are differential oracles for late fixes, regional behavior and executable/data boundaries.

### Course corpus

There are exactly 45 validated RNC Method 1 streams in each preserved build.

The repository owns an independent Method 1 decoder. All 180 stream decodes pass their packed and unpacked CRC16 checks.

Evidence now strongly supports one decoded payload per shipped track in tour order. In particular, decoded byte 2 equals decimal 45 on exactly the nine third-position tracks in the nine five-track tours, matching the game's 45-second stunt events.

The shipped Rob Northen Method 1 unpacker has also been identified in ROM code:

- USA / legacy beta: `01:B8F1`;
- Europe retail: `01:B8E2`;
- PAL prototype: `01:B8D1`.

### Autonomous player source recovered

Dessyreqt's public 2014 **Uniracers Tabletop bot** source has been located at Pastebin ID `A0XpKw9v`, via TASVideos submission #4250. The submission states that the bot completes the game without savestate search and can be adjusted for a human to race against it. The script contains frontend navigation, course-specific driving regions and a large labeled RAM map. It should be treated as a major input/fidelity/reverse-engineering resource and adapted into the project's deterministic harness after its addresses are locally verified.

### Frontend/UI state model

The frontend should be treated as a state machine rather than a loose screenshot collection. The seed model lives in `analysis/ui-state-map.yml` with human guidance in `docs/UI-STATE-MAP.md`.

Use public screenshots and the original manual to bootstrap recognition and candidate controls, then promote important edges to local evidence with controller-only fixtures. Existing `dump <tag>` checkpoints already emit framebuffer BMPs plus machine state, so the same deterministic routes can serve UI archaeology, regression testing, future frontend/HD Presentation work, and symbol discovery without inventing a parallel capture system.

Prefer cheap visual/menu inference before code archaeology when the UI is self-explanatory; escalate to tracing/disassembly when timing, hidden conditions, visually identical states, or progression-sensitive behavior make observation ambiguous.

### Runtime state anchors

Historical TAS work and RetroAchievements provide strong runtime probes for:

- speed;
- X/Y position;
- screen X;
- boost meter;
- flips, rolls, twists, Z-flips and tabletops;
- medal/progression state;
- dense stunt-state and per-tour result blocks.

These should become symbol and validation anchors rather than remaining reference notes.

### Split-screen/OAM behavior

The project has unusually rich independent evidence for Uniracers' raster sprite trick:

- developer testimony describes C64-style sprite ripping and scanline-state changes;
- Snes9x carries a title-specific OAM workaround;
- MAME independently models the same effective active-display OAM location;
- jgenesis documents writes on scanlines 0 and 112 with values `0xA5` and `0x5A`, affecting sprites 96-99;
- the recovered Canoe patch hooks two original ROM locations and installs replacement logic.

This is both a correctness seam and a future presentation opportunity. Authentic mode must model the original behavior; the HD Presentation compositor may eventually render the same logical sprites without needing to reproduce the visual trick at the final-host layer.

### Original graphics pipeline evidence

Developer history says the unicycle was a detailed 3D model rendered down into tiny SNES frames. The animation corpus spans stunt rotations, tilt/stretch, saddle movement, and many pedal/wheel phases. Mike Dailly also lists dedicated **Unicycle Compression** and **A0 plotter** tools.

Therefore the unicycle graphics should be treated as a multidimensional animation system, not merely a sprite sheet.

A major HD Presentation goal is to recover the dimensions and indexing of that corpus so high-resolution assets can be selected from the same original game state that selects the SNES frame.

### Toolkit capabilities already available

The pinned SNESRecomp framework supplies several pieces directly relevant to the remaster:

- hybrid native execution with interpreter fallback;
- `snesref` for deterministic independent-emulator comparison;
- raw frame, memory and audio capture;
- reusable support patterns for the Widescreen feature developed across existing ports;
- PPU layer policies and margin rendering;
- host-overlay extraction for BG and OBJ content;
- host-side substitution of higher-resolution art;
- data-only `.snesmod` packages for optional assets/features;
- frontend aspect controls;
- optional MSU-1 support if remastered audio is ever desired.

The project toolchain additionally pins:

- Snes9x libretro;
- bsnes libretro;
- SuperFamiconv;
- snes2asm + WLA-DX;
- da65/cc65;
- ghidra-snes;
- Floating IPS;
- ares;
- RetroArch plus the pinned Libretro Slang shader corpus for controlled visual-reference/upscaling experiments;
- bsnes-hd as an on-demand high-resolution/layer-isolation specialist;
- ffmpeg, ImageMagick, jq, ripgrep and standard build tools.

Use these before inventing parallel infrastructure.

---

# Program phases

The phases below are gates, not calendar estimates. Research tracks may run in parallel when they do not weaken the dependency order.

## Phase A - trustworthy stock native game

### Goal

Reach and complete a normal one-player race in the native executable with no presentation enhancement enabled.

### Work

1. Make the title-screen smoke deterministic and non-flaky.
2. Add deterministic controller input, using the recovered 2014 Dessyreqt full-game bot's menu-state policy as a primary accelerator rather than rediscovering frontend navigation from scratch.
3. Navigate:
   - boot;
   - title;
   - player/name/front-end flow as required;
   - mode/course selection;
   - race start.
4. Exercise:
   - acceleration;
   - braking;
   - jumping;
   - rotation;
   - landing;
   - stunt recognition;
   - boost;
   - finish.
5. Capture bounded evidence from both recomp and `snesref`.
6. Record analyzer/AOT/interpreter coverage and unresolved dynamic dispatch encountered by the route.
7. Turn any actual failure into the smallest reproducible test.

### Build a multi-interpretation visual reference corpus

Do not ask one upscaler to invent the final art. Build a reproducible ensemble of processed references from the same native source and treat them as competing hypotheses about contour/edge structure and period display appearance.

The initial matrix should include:

- raw/native pixels and nearest-neighbor integer scaling as factual controls;
- Scale2x/ScaleNx-style conservative edge continuation;
- HQx;
- xBR/xBRZ;
- SABR;
- ScaleFX;
- Super-xBR;
- simple bilinear/bicubic/Lanczos controls where informative;
- representative NTSC RGB/S-Video/composite treatments;
- a deliberately small CRT reference set;
- bsnes-hd captures only where its higher-resolution rendering or layer/sprite isolation answers a concrete question.

Use RetroArch plus the pinned Slang shader corpus as the main batch visual-reference frontend. Use existing Snes9x/bsnes/Beetle routes, ares and bsnes-hd when an independent renderer or specialist capability adds information. Prefer offline CPU/image-domain implementations for bulk extracted-asset processing whenever they reproduce the same scaler result more cheaply and deterministically.

Run the matrix at two levels:

1. **matched deterministic framebuffer captures** for composited PPU/display behavior;
2. **isolated extracted assets** once ROM graphics, palettes and semantic animation keys are known.

The second route is preferred for eventual 4K reconstruction because it avoids asking a scaler to disentangle already-composited backgrounds, transparency and neighboring sprites.

For each semantic asset, eventually generate a compact reference dossier containing the native data/palette, animation neighbors, selected scaler outputs, representative in-game captures, optional NTSC/CRT references and exact provenance/tool revisions. Agreement across unrelated algorithms is useful evidence; disagreement marks ambiguity for explicit design review.

Canonical implementation details and the capture/reproducibility contract live in `HD-VISUAL-REFERENCE-PIPELINE.md`.

### Gate

A scripted stock route reaches and completes a race, with no known simulation divergence on the compared state surfaces.

## Phase B - deterministic fidelity harness

### Goal

Make simulation fidelity continuously falsifiable before widening or replacing presentation.

### Core oracle

Use `snesref` with the pinned Snes9x core by default. Cross-check PPU/OAM-sensitive findings with bsnes/ares and, where necessary, documented hardware behavior. Once the pinned MesenCE route is proven against the shared fixture grammar, use it as a third deterministic execution engine rather than inventing a separate replay language.

For rendering investigations, keep the fidelity oracle raw. RetroArch/Slang, NTSC/CRT filters and other presentation processing may be used as diagnostic/reference views only after an unprocessed capture is preserved. This separation can help determine whether a discrepancy belongs to SNES/core rendering, frontend presentation, or the recomp runtime without contaminating the actual regression evidence.

### Build canonical scripts

Create short deterministic input scripts for:

- boot/title;
- menu navigation;
- flat straight race;
- jump and clean landing;
- failed landing;
- each major stunt class;
- boost gain and depletion;
- collision;
- race finish;
- a representative AI race;
- one stunt course;
- two-player split-screen;
- Vs.-mode OAM raster behavior.

### Compare

Prefer machine-readable comparison over screenshots alone:

- WRAM writes;
- selected WRAM values;
- CPU state around first divergence;
- frame hashes/raw frame buffers;
- PPU state;
- OAM/high-OAM;
- audio hashes/captures;
- RNG or other discovered state;
- race timer and result state.

### Special golden test

The original developers reportedly reduced feel/fairness testing to a flat straight race. Recreate that idea as a canonical deterministic test using the published speed/position/boost WRAM anchors.

### Emulator-compatibility seam program

Treat historical Uniracers-specific emulator fixes as a source of concrete fidelity requirements, not as folklore or patches to copy blindly.

Build a compatibility matrix with at least these independent seams:

| Seam | Existing evidence | Required project test |
| --- | --- | --- |
| Active-display OAM / sprite ripping | Snes9x title-specific workaround, MAME active-display OAM handling, jgenesis hardware model, Mike Dailly testimony, recovered Canoe patch | Trace writes to `$2104`, scanlines, values, effective high-OAM byte and sprites 96-99; compare native/reference behavior in affected one-player, two-player and Vs. paths |
| LoROM SRAM mapping | historical Snes9x fixes explicitly mentioning Uniracers | Deterministic clean/save/load round trip with byte-level SRAM comparison |
| XOR/window-area logic | historical Snes9x fixes explicitly mentioning Uniracers | Capture affected scenes with PPU/window state and deterministic frame comparison |
| Color math / empty-subscreen behavior | historical Snes9x experiments and regressions involving Uniracers | Capture affected scenes with color-math/subscreen state and deterministic frame comparison |

For the active-display OAM seam specifically:

1. disassemble the recovered Canoe patch hooks at ROM offsets `0x01534C` and `0x015714` and its injected handler at `0x1FFF00`;
2. identify the original routines those hooks replace or bypass;
3. reproduce the canonical ROM's `$2104` behavior under a trusted reference runtime;
4. test the jgenesis observations of scanlines 0/112 and values `0xA5`/`0x5A`;
5. compare Snes9x, bsnes/ares, jgenesis's documented model, the Canoe workaround and SNESRecomp;
6. prefer a correct general SNES PPU/OAM implementation when practical, with game-specific compatibility only as a narrowly justified fallback.

The emulator-history findings are complete only when converted into project-owned regression tests or explicitly rejected as irrelevant to the canonical ROM.

### Gate

4:3 native mode has a repeatable regression suite capable of identifying the first meaningful divergence.

## Phase C - executable and state map

### Goal

Recover enough semantic structure to make enhancement hooks deliberate rather than pattern guesses.

### Priority symbols

Map readers/writers and update routines around:

- `7E:04B7` speed;
- `7E:11CD` boost;
- `7E:0411` / `7E:0415` position;
- `7E:1509` screen X;
- stunt counters;
- camera state;
- current game/mode state;
- current tour/course index;
- current player/opponent state;
- race timer;
- RNG;
- sprite/OAM builder;
- background/tilemap streamer;
- object activation/culling;
- course loader;
- RNC source/destination selector.

### Tools

Use:

- SNESRecomp analyzer and runtime trace surfaces first;
- `snesref` WRAM traces;
- snes2asm/da65 for bounded static regions;
- Ghidra only where cross-reference work earns its setup cost, with canonical project symbols imported from the same generated symbol authority used by snes2asm/da65/Mesen;
- four-ROM diffs to align unchanged functions and expose late changes;
- historical SNasm syntax only as lineage evidence, not as an assumed source language.

### Gate

The symbol map includes the major gameplay, camera, course-loading, sprite-construction and rendering boundaries needed by later presentation features.

## Phase D - exact course model

### Goal

Turn the 45 decoded payloads into a semantic course representation that can be rendered, inspected and eventually edited without changing game physics.

### Immediate work

1. Trace the single known caller path into `RNC1_Unpack`.
2. Identify how the game selects one of the 45 streams.
3. Confirm stream ordinal against a known selected course at runtime.
4. Follow the decompressed destination into its consumers.
5. Test the historical `7E:2080` breadcrumb.
6. Determine the role of the first decoded header words.
7. Test, rather than assume, the historical:
   - 256-wide claim;
   - 64x64-block observation;
   - 8x8 tile relationship.
8. Separate:
   - visual track layout;
   - collision/physics;
   - hazards;
   - boosts;
   - start/finish/checkpoints;
   - metadata/theme;
   - auxiliary dictionaries/tables.

### Independent validation

Render extracted structures and align them against:

- gameplay captures;
- Halamantariel's VGMaps atlas;
- known very long course dimensions;
- the seven PAL-retail changed tracks.

The seven PAL deltas are particularly useful because changed geometry or metadata fields should reveal their meaning when aligned with otherwise identical format structure.

### Deliverables

- documented binary schema;
- parser;
- ROM-to-neutral-course exporter;
- structural visualizer;
- lossless round-trip tests where practical;
- stable course IDs/names once runtime mapping confirms them.

### Gate

At least one course is reproduced structurally from ROM data and matches independent gameplay/map evidence. Then extend to all 45.

## Phase E - original graphics and animation model

### Goal

Understand what the SNES renderer is drawing well enough to replace presentation without changing animation decisions.

### Asset extraction

Build deterministic extraction for:

- unicycle graphics;
- track/background tiles;
- palettes;
- UI;
- fonts;
- logos;
- menu arrows and other sprites;
- HUD pieces;
- effects.

Use SuperFamiconv where possible. Write custom extraction only for genuinely game-specific packing/indexing.

Before SuperFamiconv output becomes an authoritative replacement path, prove an exact real-asset round trip through snes2asm native bytes → SuperFamiconv → the generated reconstruction worktree → WLA-DX. Fixtures must catch palette/tile order, flips, dimensions, deduplication, base offsets and padding/unused-byte changes.

Public sprite/background sheets are comparison references, not authority. Our extractor should reproduce their content from the canonical ROM.

### Unicycle animation archaeology

Treat this as an indexing problem.

Recover dimensions such as:

- wheel/pedal phase;
- body/saddle pose;
- tilt/stretch;
- rotation/orientation;
- stunt state;
- player color/palette;
- animation timing.

Correlate:

- game-state variables;
- tile/CHR uploads;
- OAM composition;
- ROM source ranges;
- rendered frame identity.

The desired output is a stable semantic asset key such as an original animation/state identifier, not a screenshot hash.

### Why this matters for HD Presentation

A high-resolution unicycle should be chosen by the same original state that chose the low-resolution sprite. That preserves exact animation cadence, stunt poses and gameplay timing while allowing the host to substitute a higher-resolution render.

### Gate

Original rendered elements can be deterministically identified from authoritative game state and reproduced through an extraction manifest.

## Phase F - Widescreen feature with stock art

### Goal

Implement the Widescreen feature with stock art before introducing the HD Presentation feature.

This separates geometry/camera problems from asset-resolution problems.

### First rule

Establish the 4:3 release gate before any Widescreen hook. With the Widescreen feature disabled, enhancement work must leave the authentic path bit-identical on defined deterministic captures.

### Apply SNESRecomp's proven Widescreen patterns deliberately

For Uniracers, investigate each applicable pattern rather than copying another game's addresses:

1. **Use PPU scroll phase**, not only WRAM camera mirrors.
2. **Populate newly visible margin data before display** so the first wide frame does not expose stale/wrapped tilemap columns.
3. Classify each background layer as world-anchored, periodic, bounded or HUD.
4. Find a real gameplay-state gate and a separate liveness gate if needed.
5. Widen culling and the OAM emitter together.
6. Preserve signed/negative sprite-X behavior in the left margin.
7. Widen ordinary-object spawn horizons without advancing progression/controller records.
8. Give large objects enough activation slack to prevent visible pop-in.
9. Bias graphics/stage streaming only where widened visibility requires it.
10. Give each widening subsystem an independent kill switch.
11. Preserve the original 4:3 path exactly.

### Course/world boundaries

Uniracers courses can be extremely long and sometimes highly vertical. The Widescreen feature must distinguish:

- continuous track world;
- course boundary;
- repeating decorative backgrounds;
- fixed frontend/HUD surfaces;
- special vertical or looped structures.

Do not invent content by generic tilemap wrap when the authored world has ended.

### HUD/UI

Keep gameplay world widening separate from HUD layout.

Possible policies include:

- keep original HUD centered initially;
- anchor rigid HUD groups to widened edges;
- use SNESRecomp elastic-band handling only for legitimately stretchable chrome/gauges;
- move to host-overlay composition once HD Presentation UI replacement begins.

### Two-player and Vs. mode

This is its own gate, not a postscript.

Authentic mode must reproduce the original scanline/OAM trick. Trace and validate:

- writes around scanlines 0 and 112;
- `0xA5` / `0x5A`;
- sprites 96-99;
- high-OAM byte `$18`;
- the Canoe hook regions.

For the Widescreen feature with stock presentation, first determine whether the PPU path can extend both viewports correctly while retaining original sprite-ripping semantics.

For the final HD Presentation path, host composition may be cleaner: preserve the original logical sprite state and split-screen timing, but render the two viewport sprite sets directly instead of depending on the physical OAM side effect for final pixels. This is acceptable only if simulation state remains unchanged and authentic mode still proves the original path.

### Gate

A representative one-player course and the two-player/Vs. path display true additional world width with stock assets, while deterministic simulation remains equivalent to 4:3.

## Phase G - HD Presentation feature

### Goal

Replace selected low-resolution presentation with high-resolution equivalents without replacing gameplay logic.

### Preferred mechanism

Use SNESRecomp host-overlay extraction and host-side composition.

The runner can expose already-rendered BG/OBJ content without modifying:

- WRAM;
- VRAM;
- OAM;
- registers;
- DMA;
- savestate state.

Game policy determines what element is being captured; the host can then:

- crop/reposition it;
- scale it;
- omit the stock pixels from final composition;
- substitute higher-resolution art;
- choose final draw order.

This is the natural boundary for the HD Presentation feature.

### HD Presentation asset manifest

Create a versioned manifest mapping semantic original assets/states to replacements.

Every replacement should have:

- stable semantic ID;
- source-state or extracted-original identity;
- original dimensions/pivot;
- high-resolution dimensions/pivot;
- animation group and frame;
- palette/color policy;
- intended blend/transparency mode;
- provenance;
- checksum;
- fallback behavior.

Do not key important gameplay art solely on fuzzy image matching.

### Unicycle strategy for HD Presentation

Two useful routes can coexist:

1. manually/artistically rebuilt high-resolution equivalents;
2. newly rendered 3D source assets designed to reproduce the original poses.

Because the original art itself was rendered from a detailed 3D model, a new 3D source model is historically congruent with the original pipeline. The hard requirement is not "pixel art at higher resolution"; it is that each original animation state selects the corresponding replacement pose with the same timing and pivot behavior.

### Track/world strategy for HD Presentation

Use a staged approach.

**G1: pristine stock geometry at higher output resolution**

Keep original tiles but render/composite cleanly at modern resolution. This establishes coordinates, layer boundaries and camera correctness.

**G2: high-resolution tile/background replacement**

Replace known backgrounds, track tiles and decorative elements through asset identities while keeping the original course/tile structure.

**G3: semantic track renderer, only after the course model is understood**

If the decoded course format reveals track primitives cleanly enough, a host renderer may draw curves/surfaces/effects directly at arbitrary resolution while the original SNES simulation continues to own collision and gameplay.

This is potentially the strongest final presentation path because it avoids magnifying tile limitations, but it is deliberately gated on a verified semantic course model. Do not infer collision geometry from rendered pixels.

### UI and frontend

Menus/HUD are good early HD Presentation candidates because their screen-space regions are easier to isolate and do not alter simulation.

Use host overlays to replace:

- logos;
- menu art;
- fonts/text panels where practical;
- HUD chrome;
- icons;
- static frontend elements.

Keep original layout available as fallback and regression reference.

### 4K

4K is a host output target, not a new simulation coordinate system.

The authoritative SNES world remains in original units. The presentation layer maps it into an arbitrary host framebuffer, potentially combining:

- true-wide logical view;
- subpixel/high-resolution asset positions;
- modern filtering;
- high-resolution replacement textures;
- modern UI layout.

Do not multiply physics coordinates merely because the output is 3840x2160.

### Gate

A stock gameplay route can be presented with high-resolution replacement art at modern desktop resolutions while producing the same authoritative simulation state as the unenhanced route.

## Phase H - optional audio modernization

Stock SPC audio remains the initial and permanent fallback.

Only after visual fidelity is stable, consider:

- high-quality soundtrack replacement;
- lossless/remastered music packs;
- higher-quality samples/SFX where desired.

SNESRecomp's optional MSU-1 path is one possible integration boundary because it can stream modern PCM while leaving the original ROM path intact when disabled.

This phase must never block the visual remaster.

## Phase I - custom courses and editor

This is downstream of understanding the real course format.

Preferred architecture:

- neutral documented course model;
- importer from original RNC course records;
- validator;
- visual editor;
- exporter/packaging format;
- runtime loader or data-only mod integration.

Original courses remain canonical fixtures for parser and renderer tests.

A custom-course format may be cleaner than requiring recompression into the exact original packed layout, provided it feeds the same simulation semantics.

---

# Validation gates for the remaster

## Gate 1 - authentic 4:3

Enhancements disabled must preserve the reference route.

Tests should include:

- state hashes;
- WRAM landmarks;
- frame captures;
- audio where meaningful;
- OAM/PPU behavior for sensitive scenes.

## Gate 2 - Widescreen simulation equivalence

For the same initial state, inputs and frame count:

- player position/velocity must match;
- stunt state must match;
- timer must match;
- RNG must match;
- opponent/AI simulation must match unless a documented visibility policy intentionally changes activation;
- progression must match.

Any deliberate spawn/visibility exception must be isolated and justified.

## Gate 3 - visual completeness

For every widened scene test:

- no stale tilemap margins;
- no wraparound garbage;
- no cull pop;
- no sprite clipping at left/right edges;
- no early stage/progression trigger;
- no HUD gaps/stretch errors;
- no two-player split corruption.

## Gate 4 - HD Presentation substitution correctness

Replacement presentation must preserve:

- pose identity;
- animation cadence;
- pivot/attachment points;
- draw order;
- transparency;
- palette/color semantics;
- screen/world anchoring.

Disabling the HD Presentation pack must return to the stock renderer with no simulation change.

---

# Tool-to-task map

| Need | First tool/path |
|---|---|
| Recomp/native execution | pinned `snesrecomp` |
| Independent deterministic reference | `snesref` + Snes9x libretro |
| PPU/OAM-sensitive independent check | bsnes libretro / ares |
| First CPU divergence | SNESRecomp trace/co-sim facilities |
| ROM/build differences | project Python tools + four preserved ROMs |
| Course decompression | `tools/rnc_method1.py` |
| Course structure | project Python probes + runtime load trace |
| SNES tiles/palettes/maps | SuperFamiconv |
| Broad ROM disassembly | snes2asm + WLA-DX |
| Bounded 65816 disassembly | da65 with known M/X state |
| Long-lived cross-reference work | Ghidra + ghidra-snes |
| IPS experiments | Floating IPS |
| Frame/audio/image conversion | ffmpeg + ImageMagick |
| Asset provenance/capture | SNESRecomp assetdump/debug surfaces |
| HD Presentation layer extraction | SNESRecomp host-overlay extraction |
| Optional audio modernization | SNESRecomp MSU-1 support |
| Historical syntax/tool lineage | preserved SNasm builds |

---

# Research already in the repo that directly changes implementation strategy

Several collected facts should influence engineering decisions now.

## The unicycle replacement problem is state-identification, not image-upscaling

Developer history describes a high-detail 3D source model and a compressed multidimensional animation corpus. Therefore recover the frame-selection/index logic before committing to the HD Presentation asset pipeline.

## Track graphics and collision are separable

Historical destructive tests reportedly changed visual and physical course behavior independently. The modern port must not derive authoritative collision from an HD Presentation visual mesh. Visual reconstruction can be semantic and modern while collision remains original.

## The 45 RNC payloads are probably the central course asset unit

The exact 45-count, tour cadence and stunt timer byte make them a strong bridge between frontend course selection, course data, runtime load and eventual semantic rendering.

## The game's raster trick is both a compatibility test and a presentation seam

Two-player sprite ripping must be correct in authentic mode, but the final host compositor does not have to reproduce the hardware trick to draw HD Presentation sprites if it can recover the same logical per-viewport sprite state.

## Old emulator bug history gives us a regression inventory

Uniracers has historically exposed issues in:

- LoROM SRAM mapping;
- XOR/window-area inversion;
- color addition / empty-subscreen behavior;
- active-display OAM.

Validate these separately. Do not blame every graphical anomaly on the famous OAM behavior.

## The ROM is aggressively packed

Developer recollection says very little cartridge space remained. Treat apparent gaps cautiously and prefer differential/code-flow evidence before declaring bytes unused.

---

# Near-term execution order

The next work should be:

1. keep the merged repository/toolchain state green and the title-screen smoke reliable;
2. update stale milestone bookkeeping;
3. add deterministic native input and reach a one-player race;
4. run the same input route in `snesref`;
5. promote the known TAS/RetroAchievements WRAM anchors into verified symbols;
6. trace the course selector through the known RNC wrapper and confirm stream-to-track identity;
7. map the first course payload fields and produce one structural course rendering;
8. disassemble/trace the Canoe hook regions and validate the two-player OAM path;
9. build deterministic ROM asset extraction for unicycles/backgrounds/UI;
10. establish a permanent 4:3 fidelity gate;
11. only then begin stock-art Widescreen feature work using the transferable SNESRecomp patterns;
12. after wide stock presentation is stable, integrate host-overlay extraction and the first HD Presentation replacement asset.

## First useful HD Presentation prototype

The first HD Presentation experiment should **not** try to replace the whole game's presentation.

A good vertical slice is:

- one deterministic one-player course;
- stock simulation;
- true 16:9 world view;
- original course geometry;
- one high-resolution unicycle replacement set for the states actually encountered;
- one background/theme treatment;
- original HUD initially, then one HD Presentation overlay pass;
- side-by-side 4:3 regression route proving unchanged simulation.

That slice exercises every architectural boundary without requiring complete asset replacement.

---

# Public-release boundary

The private research repository intentionally contains ROMs and preservation material that must not simply become a public release repository.

Before public distribution:

1. audit tracked proprietary artifacts and Git history;
2. separate the public source/tooling history if necessary;
3. require the user's own verified ROM;
4. generate derived native code locally or use the framework's setup-host model;
5. package optional HD Presentation assets through a clearly versioned data boundary such as `.snesmod`;
6. keep original-ROM validation and fallback behavior explicit.

This release constraint should shape packaging late, but it should not distort current private research.

---

# Definition of done

The project reaches its intended goal when a player can supply the supported original game, launch a native port, and play Uniracers with:

- demonstrably original simulation behavior;
- authentic 4:3 fallback;
- the Widescreen feature;
- modern-resolution output;
- high-resolution presentation assets;
- correct one-player and split-screen behavior;
- deterministic regression coverage against the original;
- documented course/asset structures sufficient to maintain and extend the port.

Everything else, including custom courses, remastered audio, ultrawide modes and additional presentation options, is an extension beyond that core victory.

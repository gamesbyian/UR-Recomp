# HD visual-reference and upscale pipeline

Status: planned support work for Phase E / Phase 9. This document defines how emulator/filter/upscale output may be used as evidence for high-resolution replacement art without confusing processed output with source truth.

## Core rule

The canonical evidence remains the original ROM data, palettes, animation/state mapping, and raw framebuffer behavior. Upscalers and display shaders are **interpretations**. They are useful because different algorithms expose different plausible contour, edge and display reconstructions from the same tiny source.

Never promote one processed image as the authoritative replacement merely because it looks convincing.

## Two capture levels

### 1. Matched in-emulator captures

Drive the same deterministic game state and frame through controlled rendering variants. Use this for questions involving:

- composited PPU output;
- pixel/aspect treatment;
- color math;
- NTSC/display reconstruction;
- CRT appearance;
- shader interactions;
- emulator-specific high-resolution rendering;
- layer/sprite isolation where a workbench supports it.

The factual control is a raw/native capture plus nearest-neighbor integer enlargement.

### 2. Isolated extracted assets

Once Phase E extraction identifies native sprite/tile/UI assets and their palettes, feed the isolated source images through the same useful scaler families.

This is preferred for bulk 4K-art reference because the algorithms see the actual asset rather than a framebuffer already mixed with backgrounds, transparency, neighboring sprites or display effects.

## Initial reference matrix

Keep the matrix curated. Add a new family only when it contributes meaningfully distinct evidence.

1. raw/native pixels;
2. nearest-neighbor integer scaling;
3. Scale2x / ScaleNx family;
4. HQx family;
5. xBR / xBRZ family;
6. SABR;
7. ScaleFX;
8. Super-xBR;
9. bilinear/bicubic/Lanczos controls where useful;
10. representative NTSC RGB, S-Video and composite treatments;
11. a small set of CRT reconstructions;
12. bsnes-hd specialist captures only where its high-resolution or isolation behavior answers a concrete question.

## Tool roles

### RetroArch

Primary comparative presentation frontend because it can apply a large pinned Slang shader corpus to the same libretro-driven source. Treat it as the batch visual-interpretation laboratory, not the gameplay oracle.

### Libretro Slang shaders

Primary shader corpus. Curate project-owned presets and parameter files for the chosen scaler/display families. Pin upstream source, but do not commit a giant generated screenshot corpus by default.

### Existing Snes9x / bsnes / Beetle-bsnes routes

Continue to serve fidelity/oracle roles. Their frame outputs can also seed visual-reference captures, but do not multiply emulator launches when an offline image transform provides equivalent evidence.

### ares

Use when its independent renderer or Slang-capable presentation path provides a useful cross-check, especially if a result could be frontend/core-specific.

### bsnes-hd

Specialist, on-demand tool for high-resolution Mode 7/rendering experiments and clean layer/sprite isolation where applicable. Uniracers' sprite/tile art should not be treated as if HD Mode 7 were a generic solution.

### Offline image processing

Prefer direct CPU/offline implementations for high-volume processing of extracted PNGs when they reproduce the desired algorithm. This avoids unnecessary emulator startup, graphics-driver variance and CI cost.

ImageMagick/ffmpeg remain useful plumbing, but edge-aware pixel-art scalers should use known implementations rather than ad-hoc approximations.

## Reference dossier per semantic asset

The eventual HD-art process should be able to construct a compact dossier containing:

- semantic asset/state identifier;
- native indexed/tile representation where available;
- exact palette;
- original pivot/contact/bounding geometry where meaningful;
- neighboring animation states/frames;
- replacement-sequence temporal-coherence evidence for animated assets;
- raw nearest-neighbor enlargement;
- selected structurally distinct scaler outputs;
- representative in-game isolated/composited captures;
- optional NTSC/CRT appearance references;
- provenance and exact tool revisions.

This dossier is suitable for human redraw, procedural reconstruction, model-assisted generation, or combinations of those approaches.

## Reconstruction decision policy

Reference generation and final-art selection are different jobs.

Before bulk replacement art begins, maintain a project-owned visual-language specification that defines, at minimum:

- silhouette fidelity expectations;
- acceptable invented detail;
- material interpretation;
- outline/edge treatment;
- palette and saturation relationship to the stock game;
- lighting direction and contrast model;
- texture-frequency/detail limits;
- transparency/blend treatment;
- rules for translating CRT-era dithering or hand-authored pixel shading into clean HD presentation;
- when a replacement should remain deliberately pixel-like versus become native-resolution/vector/procedural/3D-derived.

A plausible image is not automatically a canonical reconstruction. When evidence permits multiple readings, record the design choice and its rationale.

## First semantic replacement key

The ordinary-race racer family now has a project-owned exact identity surface in `analysis/generated/racer-presentation-family.json`. HD Presentation should treat the authoritative 16-bit racer presentation ID in `$0FE9/$0FEB` as the primary replacement key, with the original lookup through `83:F296` / `20:8000` retained as the authentic fallback. The exact fallback graphics are also identified: race init loads OBJ assets `0x7F` and `0x80` to VRAM `$0000/$1000`, covering the stable racer OAM tile slots `00/08/80/88`. Player color is a separate semantic input: the fixture proves selectors `0/1` map to palette assets `0x06/0x07` and CGRAM `$B0/$C0`.

This separation is intentional. A later HD asset can substitute presentation for a known frame ID and color identity while the original game continues to own animation timing and state transitions. Unknown frame IDs must fall back to the exact original path until explicitly mapped. The current manifest proves byte identity and provenance; it does not yet prescribe an HD raster/vector interpretation of every packed word.

## Geometry anchors

A semantic asset dossier should carry geometry, not only imagery.

Where meaningful, record:

- original pivot;
- HD pivot;
- contact points such as wheel/track contact;
- logical center;
- original and HD bounding boxes;
- attachment points;
- expected per-frame scale;
- source-state coordinates used to position the stock sprite.

For the unicycle, pivot/contact stability is a correctness property. A beautiful frame that drifts against the track is a failed replacement.

## Temporal-coherence validation

Never approve animated replacement art only as independent still frames.

Generate deterministic animation strips/sequences and check for:

- contour breathing;
- scale drift;
- pivot/contact drift;
- changing wheel/part thickness;
- highlight/material flicker;
- inconsistent invented detail;
- frame-to-frame palette instability;
- accidental cadence changes.

The authoritative game state still selects frames and owns timing. Temporal validation asks whether the replacement sequence remains visually coherent under that original cadence.

## Sampling policy by asset class

Do not apply one global host texture filter.

Define an explicit rendering/sampling policy for each major presentation class, including:

- untouched stock pixel assets;
- reconstructed sprites;
- HD backgrounds/tiles;
- semantic/procedural track geometry;
- UI/chrome;
- fonts/glyphs;
- diagnostic CRT/NTSC presentation.

Policies may choose nearest/integer-aware sampling, linear or mipmapped texture sampling, native vector/procedural rendering, or curated shader treatment as appropriate. The policy must be deterministic and versioned alongside the presentation pack.

## Automation contract

A future capture harness should accept a deterministic frame/state or extracted asset and emit a manifest plus outputs. Record:

- ROM/build identity or source asset hash;
- semantic asset key where known;
- emulator/core/frontend revision;
- shader/scaler and exact parameters;
- source dimensions;
- output dimensions;
- aspect/pixel-aspect assumptions;
- color/display assumptions;
- isolation/composition mode;
- output hash.

Names and manifests must make it impossible to mistake a processed image for original evidence.

## Priority

### Near term

- keep the three visual-reference dependencies pinned in `tools/toolchain.json`;
- identify a minimal curated shader/preset set;
- verify the cheapest deterministic RetroArch screenshot route under Linux/headless automation;
- test one identical stock frame through the matrix and measure startup/runtime/storage cost;
- determine which scaler families can instead be applied offline.

This is useful tooling work but must not displace the current stock-fidelity and course/reverse-engineering critical path.

### Phase E

- integrate the reference matrix with extracted sprites/tiles/UI;
- capture isolated assets wherever possible;
- use disagreement between algorithms to flag ambiguous shapes;
- connect every output to semantic animation/state identifiers.

### Phase 9 / HD Presentation

- use dossiers as source material for 4K replacement assets;
- evaluate replacement art against raw/native and display-reconstruction references;
- preserve authentic nearest/raw modes permanently;
- never let a filter become an accidental substitute for understanding animation/state selection.

## Cross-cutting uses outside final upscaling

The same tools can help earlier work when justified:

- **rendering compatibility diagnosis:** controlled shader-free RetroArch/core captures can expose whether a difference belongs to core rendering, frontend presentation or our runtime;
- **PPU/color-math work:** matched raw versus presentation-processed captures prevent display filters from contaminating fidelity judgments;
- **graphics archaeology:** bsnes-hd or debugger workbenches may isolate layers/sprites to identify which tile/OAM source produced an on-screen element;
- **UI mapping:** clean matched captures can supply additional evidence for screen/state documentation, but UI behavior should still be derived from deterministic input/state evidence;
- **documentation:** curated processed examples can explain why tiny source pixels are ambiguous, provided originals are shown alongside them.

These uses are opportunistic. Do not turn the visual-reference stack into a dependency for unrelated reverse-engineering tasks.


## First product-facing replacement prototype

The bounded replacement contract is implemented by `tools/prototype_racer_hd_replacement.py` and `analysis/data/racer-hd-replacement-prototype.json`. It now covers both racers in the same synchronized ordinary-race proof state: P1 semantic frame `0x0541` and P2 semantic frame `0x0540`.

The primary lookup remains the authoritative 16-bit racer presentation ID. Both `0x0541` (P1) and `0x0540` (P2) are registered against the same retained synchronized composition tuple: P1/P2 primary IDs, companion IDs, selector values and companion gate words must match the exact composition proof promoted into `analysis/data/presentation-assets.json`. This guard remains important because either visible 64x64 racer object can depend on more than the primary packed record alone.

The Original control is reconstructed deterministically from the ROM. The prototype Remastered candidate is intentionally modest: two deterministic Scale2x passes produce a 4x-density contract-only candidate, and its final alpha is locked to the nearest-scaled Original footprint. That keeps the object-local origin, silhouette coverage and contact edge exact while exercising a genuinely different host-side raster path. It is provenance-labelled as a prototype and is not approved shipping art.

Selection happens entirely after semantic state has been chosen. Runtime H/V orientation is applied after Original/Remastered selection. The selector fails closed: replacement disabled, an unregistered semantic ID, or any composition-guard mismatch selects Original. Disabling replacement must emit a PNG byte-identical to the Original 4x control. The focused workflow uploads only the Original control, one Remastered candidate, the disabled-replacement control and a compact manifest.

The synchronized registrations carry explicit geometry anchors before hand-authored HD racer art expands. Coordinates use object-local pixel centres at fixed-point scale 2: both use the exact 64×64 OBJ reflection pivot `[63,63]` = `(31.5,31.5)`; the stock-derived wheel/contact anchors are `[61,76]` for P1 `0x0541` and `[63,76]` for P2 `0x0540`. These contact coordinates are not artist-authored: each is the centre of the lowest occupied alpha span in its deterministic composed stock raster. Runtime OAM H/V reflection transforms anchors only after semantic selection.

Split-screen placement is now modeled separately from semantic identity. In ordinary two-player play, each semantic racer has two OAM instances in the same frame: P1 uses slots 98 (top) and 97 (bottom), while P2 uses slots 99 (top) and 96 (bottom). The proven active-display high-OAM values `0xA5` before the line-112 split and `0x5A` after it select which pair is visible. Low-OAM position/tile/attribute data for both viewport pairs coexists, so host replacement should decode live low-OAM coordinates using this split-instance mapping rather than treating the frame-end high-OAM state as a single authoritative racer position.


## Native replacement-selection seam

The artifact-side prototype is now mirrored by a dependency-free native presentation contract in `native/presentation/racer_replacement_selector.{hpp,cpp}`. This is intentionally a selector, not a renderer rewrite: it consumes already-authoritative semantic presentation state and returns which graphics pack may represent that state.

For the first registration, semantic frame `0x0541` plus the synchronized composition tuple selects the Remastered pack. Original always remains available. Unknown IDs, composition mismatches, and presently unavailable packs such as Reimagined fail closed to Original. The selector carries only presentation registration metadata and has no WRAM/SRAM mutation interface.

The native registration keeps the currently proven geometry explicit: 64×64 logical canvas, occupancy offset `(1,0)`, palette asset `0x06`, 4× candidate density, fixed-point anchor scale 2, semantic flip pivot `[63,63]`, and measured wheel/contact anchor `[61,76]`. Native tests verify exact H/V anchor transforms as well as selection/fallback behavior. The artifact-side prototype independently re-derives both anchors from OBJ geometry and the canonical stock raster and fails if the JSON registration drifts, so hand-authored assets inherit a checked registration target rather than a guessed one.


## Read-only guest-state bridge

`native/presentation/racer_guest_snapshot.{hpp,cpp}` closes the next runtime boundary without giving presentation code write authority. It reads the eight synchronized racer composition words from a caller-supplied WRAM view, exposes the P1/P2 primary IDs as semantic frame identities, and feeds the resulting immutable composition snapshot into the native replacement selector.

The bridge reads the established addresses for primary IDs, companion IDs, selector words and companion-gate words. It rejects null or undersized WRAM views and therefore fails back to Original through the selector rather than reading partial state. It does not retain a mutable WRAM pointer and provides no write operation.

The address constants are exposed as presentation metadata and a focused CI parity test derives the expected values from `analysis/data/presentation-assets.json`. This prevents the native guest-state bridge from silently drifting away from the canonical composition contract.


## Dynamic OAM placement contract

The first synchronized ordinary-2P placement reference is retained compactly in `analysis/data/racer-oam-placement-reference.json`, sourced from workflow run `36943103609`, artifact `11200911852`, checkpoint `two-player-race-1220`. At that exact state, P1 uses large OAM slot 98 at raw `(104,40)`, 64×64, H-flipped and not V-flipped; P2 uses slot 99 with the same geometry and its own tile/palette attributes.

Those coordinates are a regression reference, not replacement policy. `native/presentation/racer_oam_placement.{hpp,cpp}` decodes the live slot every frame from either a caller-supplied 544-byte OAM snapshot plus OBSEL or SNESRecomp's native PPU storage (`oam[256]`, `highOam[32]`, `obsel`). The latter maps directly from the existing public `g_ppu` singleton, so the eventual title-owned `draw_frame` hook needs no new framework accessor or debug-dump repacking. Both paths preserve the SNES 9-bit X coordinate, object size and H/V flip bits. This keeps movement and orientation guest-authored while giving the eventual host compositor the screen-space registration it needs.


## First native draw-frame substitution

`native/presentation/racer_hd_presenter.{hpp,cpp}` closes the first actual presented-pixel substitution loop for the registered `0x0541` racer state. The title-owned host path deliberately composes after the guest PPU raster: semantic identity is selected from the read-only WRAM snapshot, screen placement and H/V orientation are decoded independently from live PPU OAM/high-OAM/OBSEL, and only then is the replacement representation drawn.

Stock suppression uses SNESRecomp's host-overlay OBJ extraction with `kPpuOverlayFlag_RemoveFromGame` and the exact validated racer OAM slot. Overlay policy and storage are host-only; the presenter does not write guest WRAM, VRAM, OAM or CGRAM. If replacement mode is disabled, semantic selection fails, composition guards mismatch, the placement cannot be validated as the registered 64×64 object, or the requested asset is unavailable, capture is not armed and the normal Original raster is presented unchanged.

The first deterministic asset is intentionally contract-only. Its registered source density is 4×, but this `draw_frame` hook still owns a 256×224 logical SNES field, so the prototype samples that denser source into the stock 64×64 object footprint rather than pretending the hook is a final 4K compositor. The important closure here is the ownership seam: the same semantic asset identity moves with live OAM coordinates, H/V transforms happen after selection, and the guest simulation and animation timeline remain authoritative. A later host-resolution compositor can consume the same registration and denser asset without moving this boundary back into guest state.

CI runs the same deterministic two-player route twice with replacement disabled and once enabled. Fresh-process controls expose 24 low-WRAM scratch bytes that are not byte-stable even with identical presentation, so acceptance first derives that control variability set, then requires HD to match every WRAM byte outside it and every promoted fixed-width `7E:` semantic state entry. The presenter also hashes full WRAM plus CGRAM/OAM/high-OAM/VRAM immediately before and after host capture setup and requires no change. The disabled runs must never enter the substitution path; their presented frame-1220 screenshots must be byte-identical to each other; the enabled screenshot must differ. Workflow run `37084977349` closes this acceptance. Focused native contracts retain unknown/composition/pack/absent-asset fallback to Original, prove semantic identity is independent of screen position, and exercise all H/V orientation combinations.


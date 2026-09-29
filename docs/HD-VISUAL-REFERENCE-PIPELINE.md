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
- neighboring animation states/frames;
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

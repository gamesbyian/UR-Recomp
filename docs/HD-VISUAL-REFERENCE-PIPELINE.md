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

## Generated racer approval dossier

The first approval-oriented dossier path is now implemented by `tools/build_racer_hd_asset_dossier.py`. The native Racer HD acceptance route feeds it the exact composition-aware semantic trace rather than registry order, so animation neighbors are observed runtime facts.

For the current deterministic two-player window, the builder:

- requires every frame from `1205` through `1220` to resolve to one exact P1 and one exact P2 registration;
- packages the 14 distinct representations observed in that continuous window;
- re-renders each stock 64×64 racer from the canonical ROM;
- re-derives pivot/contact geometry and rejects registry drift;
- records composition guards, palette identity, observed frames and trace-derived previous/next representation context;
- emits literal stock PNGs, nearest-neighbor 4× controls and the current provenance-labelled contract-only Scale2x candidates with hashes;
- records the resolved geometry/lighting/edge/material/shadow/detail/specular baseline, preserves exact stock opaque-color histograms as tone evidence, and keeps `shipping_art_approved=false` until an actual authored candidate passes review.

This is the handoff surface for actual racer art review. A replacement candidate should be judged against this dossier rather than against an isolated screenshot or an inferred animation ordering.

The handoff is now exercised by the first authored candidate. Exact representation `ordinary-racer-0x0541-p1-sync-reference` carries registry-owned authored-candidate metadata, and the dossier emits its 4x review PNG alongside stock, nearest-4x and contract-only controls. Initial run `37142692369` proved the plumbing but exposed a gameplay-scale silhouette mismatch during review. The dossier now also records a deterministic logical-centre alpha review so large 4x art cannot hide scale drift: stock and tuned candidate both occupy `[22,3]..[39,38]`, the candidate preserves contact `[61,76]`, and alpha IoU improved from the first pilot's roughly 0.377 to `0.6340057637`. Tuned native run `37146779451` / artifact `11283305196` is green through both live split-screen viewports with no guest-state mutation.

The immediately preceding exact frame-1219 representation `ordinary-racer-0x0541-p1-companion-0D2D-reference` now exercises that rule as a second authored asset. The retained stock transition changes only seven logical pixels, all in the upper silhouette, so the authored neighbor preserves the reviewed lower geometry/material solution and changes only the saddle profile. Dossier review matches the stock envelope `[22,2]..[39,38]` and contact `[61,76]`, with 226/349 alpha intersection/union (IoU `0.6475644699`). Native run `37150356100` / artifact `11283522741` is green through the live split-screen presenter and guest-state invariants.

The reversed frame-1218 predecessor now adds a third authored checkpoint. Unlike the seven-pixel 1219→1220 stock change, the 1218 pose has a distinct stock silhouette, so the authored form is locally re-fitted rather than translated. It matches stock envelope `[23,2]..[40,38]`, contact `[63,76]`, and reaches 270/365 alpha intersection/union (IoU `0.7397260274`). Native run `37151331456` / artifact `11284028173` is green through the live split-screen presenter and guest-state invariants.

Retained dossier comparison proves the frame-1217 P1 stock raster is byte-for-byte identical to frame 1218 despite its separate synchronized composition registration. That reuse is now implemented and accepted: both exact guards remain distinct, but their stock RGBA hashes, authored RGBA hashes and gameplay-scale review metrics are required to match. Native run `37151848274` / artifact `11284007664` closes the live split-screen proof.

This establishes an additional pipeline rule: **do not equate exact-state registration count with required art count**. When independently registered contexts reconstruct to identical stock pixels and geometry, one reviewed authored asset should be reused under multiple exact guards. The repeated frame-1215/1216 P1 representation `057F/0542 + 0D4A/0000` is now the next authored visual change. Both temporal occurrences consume one 4x asset; gameplay-scale review is locked to the recovered stock envelope `[22,2]..[41,38]` and contact `[65,76]`, while material, lighting and edge treatment remain inherited from the reviewed sequence.

Native run `37159887643` closes that repeated-pose step through live top/bottom split-screen presentation with no guest-state mutation; artifact `11286898413` retains the dossier. Review measures 264/384 alpha intersection/union (IoU `0.6875`). This extends the **first motion-reviewed sequence to four visual poses plus one context reuse**, while still not constituting final shipping-art approval.

The next retained visual change is already registered rather than newly searched: P1 `057E/0543 + 0D49/0000` occurs at frames `1205–1206` and `1213–1214`. A single authored asset now covers all four occurrences, matching stock envelope `[21,2]..[42,38]` and contact `[67,76]`. Native run `37163141373` is green and artifact `11288098806` records 251/405 alpha intersection/union (IoU `0.6197530864`).

The next actual retained visual change is P1 `057D/0543 + 0D48/0000`, repeated across frames `1207–1212`. One authored asset covers the six-frame run, matching stock envelope `[21,3]..[43,38]` and contact `[69,76]`. Native run `37164968261` is green and artifact `11289251993` records 246/397 alpha intersection/union (IoU `0.6196473552`).

The P1 review strip is now saturated across the retained 1205–1220 window. The canonical frame-1220 P2 `0540` representation is now the first authored blue-player motion-reviewed asset, replacing the generic contract candidate for that exact live synchronized state. It matches stock envelope `[23,3]..[40,38]` and contact `[63,76]`; native run `37166854227` is green and artifact `11290145680` records 266/361 alpha intersection/union (IoU `0.7368421053`).

The immediate frame-1219 P2 `0540` representation under the distinct `0D2D` synchronized context has byte-identical stock pixels to frame 1220. The pipeline therefore keeps the two registrations distinct but reuses the reviewed P2 authored asset, with CI locking both stock and authored hashes. Native run `37169313027` is green and artifact `11290454491` retains the accepted reuse evidence.

Frame 1218 P2 `0541` is the next actual P2 visual change. Its authored blue-player asset derives from the reviewed P2 baseline by the exact one-logical-pixel leftward displacement required to match stock envelope `[22,3]..[39,38]` and contact `[61,76]`. Native run `37169795518` is green; artifact `11290901577` records 250/372 alpha intersection/union (IoU `0.6720430108`). Recovered gameplay-scale envelope/contact and temporal continuity remain acceptance constraints, while smooth geometry/material interpretation stays free inside those constraints.

Frame 1217 P2 `0542` is the next distinct stock pose, with envelope `[21,4]..[40,38]` and contact `[59,76]`. The retained dossier proves its stock raster is byte-identical to the frames-1215–1216 P2 `0542` state under the distinct `057F/0D4A` context, so one authored asset covers all three occurrences under separate exact guards. Native run `37173872885` is green; artifact `11291829520` records 254/384 alpha intersection/union (IoU `0.6614583333`) and locks stock/authored hash parity across the reuse.

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
- display-geometry/pixel-aspect policy and logical-view policy as separate fields, following `DISPLAY-PRESENTATION-POLICY.md`;
- overscan/safe-area policy;
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

The deterministic replacement assets remain intentionally contract-only. Registered coverage now includes multiple exact synchronized composition states, including duplicate primary-ID contexts. Backward temporal coverage now also reaches the repeated `0x057F/0x0542 + 0D4A/0000` state at frames 1215–1216. Prototype run `37099604317` measures P1 pivot/contact `[63,63]` / `[65,76]` with alpha bounds `[22,2,41,38]`, and P2 pivot/contact `[63,63]` / `[59,76]` with bounds `[21,4,40,38]`. Native acceptance run `37099885778` proves four-instance substitution on entry at frame 1215 and continued selected replacement at frame 1216 (`uses_replacement=1`); the presenter intentionally logs the four draw records only when the registration pair changes. The stable-WRAM gate remains zero-difference. P2 therefore holds `[59,76]` into the following `0540/0542` state while P1 advances from `[65,76]` to `[63,76]`, another exact two-half-pixel horizontal step with no vertical drift. Coverage now also includes the two `0x0540/0x0542` companion-context states immediately before that step: frame 1217 uses `0x0D2C/0x0000`, while frame 1467 uses `0x0D4C/0x0000`. Run `37098511872` measures identical geometry in both contexts: P1 pivot/contact `[63,63]` / `[63,76]` with bounds `[23,2,40,38]`, and P2 pivot/contact `[63,63]` / `[59,76]` with bounds `[21,4,40,38]`. Native run `37098665264` substitutes both exact compositions in all four split-screen instances without guest-state mutation. This is a useful negative discriminator: the companion value changes exact composition identity here without changing the measured stock geometry, so the registry keeps separate representations while preserving identical anchors. Coverage now also reaches the immediately preceding reversed-primary state `0x0540/0x0541 + 0D2C/0000` at frames 1218 and 1468. Run `37098034754` measures P1 pivot/contact `[63,63]` / `[63,76]` with alpha bounds `[23,2,40,38]`, and P2 pivot/contact `[63,63]` / `[61,76]` with bounds `[22,3,39,38]`; native acceptance run `37098109510` substitutes both racers in all four split-screen instances at frame 1218 without guest-state mutation. The following frame advances directly into `0x0541/0x0540 + 0D2D/0000`, so this is a retained one-frame adjacency rather than a guessed animation ordering. The original `0x0541/0x0540` semantic pair is now intentionally registered under both `0x0D0D/0x0000` and companion-predecessor `0x0D2D/0x0000` contexts. Run `37096244333` measures the `0x0D2D` composition at frames 1219 and 1469 with P1 pivot/contact `[63,63]` / `[61,76]` and alpha bounds `[22,2,39,38]`, plus P2 pivot/contact `[63,63]` / `[63,76]` and alpha bounds `[23,3,40,38]`. Native acceptance run `37097537479` substitutes that exact state in all four split-screen instances at frame 1219 with `guest_state_unchanged=1`, so the duplicate semantic IDs remain separated by full synchronized composition rather than collapsed. The `0x057E/0x0544` pair is proven under both `0x0D49/0x0000` and `0x0D69/0x0000` companion contexts: P1 contact remains `[67,76]`, but the stock alpha bounds change from `[21,2,42,38]` to `[22,2,42,38]`, proving that the active companion can change the composed silhouette even when both primary IDs and the wheel/contact anchor are unchanged. The predecessor `0x057D/0x0542` state is also retained at frames 1302–1303 and 1381: P1 remains anchored at `[69,76]`, while P2 measures `[59,76]` and advances to `[57,76]` in `0x057D/0x0543`, an exact two-half-pixel horizontal step with no vertical drift. Forward coverage now reaches `0x057F/0x0543 + 0D6A/0000` at frames 1388–1389 and 1466: P2 stays at `[57,76]`, while P1 advances from the preceding `0x057E + 0D69` contact `[67,76]` to `[65,76]`, again exactly two half-pixels horizontally with no vertical drift. `0x057D/0x0543` was selected from dense observed adjacency rather than a sparse checkpoint. The exact tuple occurs at frames 1207–1212, 1304, and 1382–1384. The dense trace therefore supplies ten retained hits, with direct exits to `0x057E/0x0544` on the relevant transition samples and repeated self-holds elsewhere. Its stock-derived contacts are P1 `[69,76]` and P2 `[57,76]`; on each direct exit the following state measures `[67,76]` and `[55,76]`, preserving vertical contact exactly while each horizontal contact advances two half-pixels. The registered source density is 4×, but the current `draw_frame` hook still owns a 256×224 logical SNES field, so the prototype samples denser sources into the stock 64×64 object footprint rather than pretending the hook is a final 4K compositor. The important closure is the ownership seam: semantic identity and timing remain guest-authored while later host-resolution art can reuse the same registration and anchors.

CI runs the same deterministic two-player route twice with replacement disabled and once enabled. Fresh-process controls expose 24 low-WRAM scratch bytes that are not byte-stable even with identical presentation, so acceptance first derives that control variability set, then requires HD to match every WRAM byte outside it and every promoted fixed-width `7E:` semantic state entry. The presenter also hashes full WRAM plus CGRAM/OAM/high-OAM/VRAM immediately before and after host capture setup and requires no change. The disabled runs must never enter the substitution path; their presented frame-1220 screenshots must be byte-identical to each other; the enabled screenshot must differ. Workflow run `37084977349` closes this acceptance. Focused native contracts retain unknown/composition/pack/absent-asset fallback to Original, prove semantic identity is independent of screen position, and exercise all H/V orientation combinations.


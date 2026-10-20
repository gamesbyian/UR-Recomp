# Modern menu animation: source-bound native motion lane

Status: **implemented native root selection accent + deterministic frontend-only motion model; stock unicycle hero asset admission HOLD; Windows packaged screenshot and human visual approval HOLD.** This is a specialist presentation handoff, not a release-gate update. The live [work queue](WORK-QUEUE.md), [Modern visual fidelity gate](MODERN-UI-VISUAL-FIDELITY.md) and [character reconstruction veto](HD-RACER-CHARACTER-RECONSTRUCTION.md) remain authoritative.

## Scope and actual native integration

- `native/product/modern_menu_motion.hpp` owns deterministic animation state. Its only mutable values are host-visible selection and presentation ticks. It is not a gameplay state machine, does not mutate the selected Modern destination, and is reset when root is not visible. Same inputs and clock produce the same pose.
- `native/product/uniracers_modern_host.cpp` calls that module **only after** `render_modern_root_overlay()` for the existing Modern root. The painter writes a measured 2-logical-pixel yellow/blue selected-row accent to the actual host compositing buffer, inside the existing root panel. It does not replace root composition or routes. The host's SDL ticks feed a 60Hz UI clock when the guest is held; no guest frame, SRAM, CPU state or authoritative input advances for animation.
- `UR_REDUCED_MOTION=1` disables cursor spin, selection travel, entrance and hero offsets while retaining immediate selected-state identity. The flag is a temporary host-level preference. A persisted player-facing Options setting must be separately authorized and implemented against the current actual Options capability model; do not add a fake control.
- The composition parameters `ModernMenuMotionAnchors` default to the current root at selected row Y=57, row stride=21, marker X=5. A root/screen agent moving or redesigning rows should update the narrow paint call and anchor together rather than inheriting out-of-date pixel assumptions.
- `native/product/modern_menu_stock_hero.hpp` is a **real native ARGB raster compositor**, complete with 1x through 4x nearest stock reproduction, alpha compositing, bbox guards, provenance admission and bounded frame cycling. It deliberately has no live sprite bound. Unlike the unapproved 4x procedural engine assets, a validated sequence of full **original stock 64x64 pose rasters** can be admitted without changing this renderer. No hero pixels are drawn by the running game until such a verified sequence and a safe placement are supplied. This module is a rendering interface, **not evidence that an animated hero is on-screen now**.

## Source, duration and credibility

`analysis/generated/menu-visual-language.json` measures original 16-frame cursor spin at two ticks per tile (32 ticks), single-row source move steps `6,4,3,3,2,1,1,1,1,0,0,1` (12 ticks) and BG2 256px screen slide in 39 ticks. The pure model preserves these as values; it normalizes the 23px measured movement to the current Modern 21px row step. Modern's measured stock-grammar yellow/blue presentation roles come from `native/product/modern_stock_menu_palette.hpp`.

The stock cursor evidence proves **cursor timing**, not unicycle pedalling/flip cadence. The host-only 6-tick showroom pose ordinal and small 64-tick bob are explicit **provisional animation direction** with no implied original timing proof. Until exact original raster family order and cadence are verified, a real hero stays disabled. The entrance-distance value is available to title/screen agents but not currently applied to the on-screen root panel. Authentic mode and simulation/race animation remain untouched.

### Stock hero admission contract

Before binding even the smallest live hero sequence:

1. Extract registered **Original** composited 64x64 ARGB rasters via the existing `tools/extract_racer_presentation_family.py` / `analysis/data/racer-hd-replacement-prototype.json` original-corpus path, with source ROM identity, source registration, per-frame buffer hash and semantic frame ID. A `verified=true` field alone is not independent source proof.
2. Qualify the intended **ordered** pose sequence across adjacent original visible frames, including source OAM/PPU composition, palette and cadence. Never infer order from ascending semantic IDs or confuse a 4x authored pose for a stock frame.
3. Store a reviewable original pose sequence manifest plus provenance. Supply ARGB 64x64 buffers and digest to `ModernMenuStockHeroSequence`, with `original_raster_source_verified` and `original_pose_order_verified` only once established. The renderer prevalidates **all** pose buffers, semantic IDs and FNV integrity before touching the framebuffer and fails closed on any mismatch.
4. Obtain original-character art comparison and user approval on exact native screenshots. Pixel-perfect 1x stock drawing proves technical source identity, **not** artistic approval for new high-resolution art. The October 10 **4x procedural character-likeness veto** remains in full effect.
5. Wire that sequence only in a safe 16:9 / compact 4:3 region chosen by the screen owner. Do not paint a hero over controller reachability, selected option, records text or modal.

## Three-project reuse preflight

Consulted `tools/select_three_project_reuse.py` and its sourced `analysis/three-project-reuse-opportunities.json` / `analysis/data/three-project-apparatus-capability-matrix-20261010.json` with lane `modern-product`: retain **UR** typed root / renderer and evidence contracts, **Baldosa** pinned guest/SDL presentation lifecycle, and **Malmazuke** as a contextual frontend reference only. The registry classifies `modern-controller-journey` / `baldosa-native-core` as keep-existing and `candidate-evidence-envelope` as a shared provenance seam. Nothing justifies a new emulator, frontend authority, asset format or another menu engine. This preflight is source-inspection of the established algorithm and registry; no local full repository checkout was available to execute the command itself.

## Tests, exact evidence and outstanding checks

`tests/native/modern_menu_motion_test.cpp` exercises fixed-tick cursor states, interrupted selection and wrap, guest-independent hide/return and clock rewind, 39-frame source timing, reduced-motion fallback, native ARGB compositing at 4:3 1x and wide 4x, exact read-only stock-pose digest admission, complete-sequence rejection without partial render, unsupported placement clipping and fake test-only pose cycling. The synthetic test sprites are **not game art**. `tests/unit/test_modern_menu_motion_cpp.py` compiles this real C++17 path with warnings-as-errors. `tests/unit/test_modern_root_overlay_presenter.py` remains an independent guard on the existing root semantics.

**Not yet captured or accepted:** packaged actual Windows PE/ZIP Modern root opening, moving selection at frame-indexed source, actual stock-hero in title/root/profile, capture with source identity (EXE SHA, toolchain, original ROM reference, frame index and input actions), representative 4:3 and 16:9 panels, full-duration side-by-side original-menu kinetics, controller/SFX correlation, title-to-root animated handoff, profile preview, and human visual approval. Current host lacks an admitted original sprite image corpus and capture authority. Do not substitute a standalone mock, extracted trailer frame, unit synthetic image or an older packaged binary and call it current-head visual acceptance.

## Visual workstream handoff

- **Modern title screen:** consume immutable `ModernMenuMotionPose` for proposed title transition timing and stock-verified hero placement; title/logo/background composition belongs to the title agent.
- **Shared visual language:** palette, panels, typography and arrow asset selection belong to the primitives agent. It may replace this narrow accent when an original-derived native arrow primitive ships. Preserve immediate semantic focus.
- **Five-destination root:** change/reanchor the tiny paint call alongside real row geometry and modal foreground order. Root/destination design belongs to that agent.
- **Racer art:** the original-pose producer should supply source-bound 64x64 rasters, pose sequences and explicit reviewed likeness. Do not coerce experimental 4x authored assets into `original_raster_source_verified`.
- **Integration QA:** owns source-exact Windows screenshot and approval matrices and release ledger. This lane leaves `docs/WORK-QUEUE.md` and `docs/RELEASE-QUALITY-LEDGER.json` untouched.

The next decision-bearing blocker is obtaining one honest, verified Original 64x64 racer pose *plus* the following qualifying frames. Until those arrive, current root motion is a bounded, visible native refinement, not a completed animated hero.

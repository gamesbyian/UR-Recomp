# Modern menu animation: source-bound native motion lane

Status: **native Modern/Baldosa root selection motion implemented; original eight-pose racer extraction and opt-in experimental native preview implemented, but default/off and no generated art committed; packaged Windows screenshot and human visual approval HOLD.** This is a specialist presentation handoff, not a release-gate update. The live [work queue](WORK-QUEUE.md), [Modern visual fidelity gate](MODERN-UI-VISUAL-FIDELITY.md) and [character reconstruction veto](HD-RACER-CHARACTER-RECONSTRUCTION.md) remain authoritative.

## Scope and actual native integration

- `native/product/modern_menu_motion.hpp` owns deterministic animation state. Its only mutable values are host-visible selection and presentation ticks. It is not a gameplay state machine, does not mutate the selected Modern destination, and is reset when root is not visible. Same inputs and clock produce the same pose.
- `native/product/uniracers_modern_host.cpp` **and** `tools/baldosa_native_modern_root.cpp` call that module only for Modern root after the shared presenter. The Baldosa call suppresses ornament behind quit, Practice, 2P join, Records, profile and Options modals. The legacy host also retains its original isolation. Both draw in the actual existing compositor; no new UI router.
- `native/product/uniracers_modern_host.cpp` calls that module **only after** `render_modern_root_overlay()` for the existing Modern root. The painter writes a 2-logical-pixel source-blue selected-row accent with subtle phase-based geometric breathing, deliberately avoiding unsupported rapid colour flashes to the actual host compositing buffer, inside the existing root panel. It does not replace root composition or routes. The host's SDL ticks feed a 60Hz UI clock when the guest is held; no guest frame, SRAM, CPU state or authoritative input advances for animation.
- `UR_REDUCED_MOTION=1` disables cursor spin, selection travel, entrance and hero offsets while retaining immediate selected-state identity. The flag is a temporary host-level preference. A persisted player-facing Options setting must be separately authorized and implemented against the current actual Options capability model; do not add a fake control.
- `UR_MODERN_MENU_TEST_TICK60=<decimal>` freezes only the host Modern menu pose at one explicitly selected 60Hz UI tick for reproducible source-bound Windows screenshot capture. It does **not** affect guest/physics/tour clocks, input, SRAM, or replay. A malformed/overflow decimal is refused and ordinary monotonic SDL-derived presentation time is used instead. The capture harness must record this override, selection index, executable hash, viewport, actual source frame and native/SDL raster boundary in its manifest; it is not a player setting or an animation frame driver.
- The composition parameters `ModernMenuMotionAnchors` default to the current root at selected row Y=57, row stride=21, marker X=5. A root/screen agent moving or redesigning rows should update the narrow paint call and anchor together rather than inheriting out-of-date pixel assumptions.
- `native/product/modern_menu_stock_hero.hpp` is a **real native ARGB raster compositor**, complete with 1x through 4x nearest stock reproduction, alpha compositing, bbox guards, provenance admission and one-shot pose/hold rendering. It cannot draw unverified or procedural 4× art. A compiled source asset is optional; ordinary builds have none. Unlike the unapproved 4x procedural engine assets, a validated sequence of full **original stock 64x64 pose rasters** can be admitted without changing this renderer. The pinned Baldosa host has an explicitly opt-in preview: with a generated verified original header at build time, `UR_MODERN_SOURCE_HERO_EXPERIMENTAL=1` paints the stock pose experiment on the 342-wide root and displays **ORIGINAL ART TEST**. At 256-wide / 4:3 it remains unavailable pending safe composition. Without a generated header the hook compiles out entirely, so no artwork is smuggled into the default build. This is an experimental original pixel hero, **not a finished showroom**.

## Source, duration and credibility

`analysis/generated/menu-visual-language.json` measures original 16-frame cursor spin at two ticks per tile (32 ticks), single-row source move steps `6,4,3,3,2,1,1,1,1,0,0,1` (12 ticks) and BG2 256px screen slide in 39 ticks. The pure model preserves these as values; it normalizes the 23px measured movement to the current Modern 21px row step. Modern's measured stock-grammar yellow/blue presentation roles come from `native/product/modern_stock_menu_palette.hpp`.

The provisional cursor ornament keeps the original OBJ's blue color constant. A one-pixel height/inset change twice per source 32-frame cycle supplies gentle idle feedback; **it is not a reconstructed 32×32 dimensional source cursor**. Source art and cursor-shape approval remain separate from the timing model.

The stock cursor evidence proves **cursor timing**, not unicycle pedalling/flip cadence. The one-shot pose cadence is now derived directly from original source-observed guest frames 1213..1220: one pose per 60Hz tick on root entry/selection change, then hold frame 1220 rather than fabricating a 1220→1213 loop. The low-amplitude 64-tick host bob and brief lean remain independently proposed composition animation and require visual approval. The verified clip is a real race pose window, **not verified title/idle actor movement**, so it stays visibly labelled experimental and opt-in. The entrance-distance value is available to title/screen agents but not currently applied to the on-screen root panel. Authentic mode and simulation/race animation remain untouched.

### Stock hero admission contract

Before binding even the smallest live hero sequence:

1. Extract registered **Original** composited 64x64 ARGB rasters via the existing `tools/extract_racer_presentation_family.py` / `analysis/data/racer-hd-replacement-prototype.json` original-corpus path, with source ROM identity, source registration, per-frame buffer hash and semantic frame ID. A `verified=true` field alone is not independent source proof.
2. Qualify the intended **ordered** pose sequence across adjacent original visible frames, including source OAM/PPU composition, palette and cadence. Never infer order from ascending semantic IDs or confuse a 4x authored pose for a stock frame.
3. Store a reviewable original pose sequence manifest plus provenance. Supply ARGB 64x64 buffers and digest to `ModernMenuStockHeroSequence`, with `original_raster_source_verified` and `original_pose_order_verified` only once established. The renderer prevalidates **all** pose buffers, semantic IDs and FNV integrity before touching the framebuffer and fails closed on any mismatch.
4. Obtain original-character art comparison and user approval on exact native screenshots. Pixel-perfect 1x stock drawing proves technical source identity, **not** artistic approval for new high-resolution art. The October 10 **4x procedural character-likeness veto** remains in full effect.
5. Wire that sequence only in a safe 16:9 / compact 4:3 region chosen by the screen owner. Do not paint a hero over controller reachability, selected option, records text or modal.

### Reproducible original-raster clip export (no repository art commit)

The new `tools/build_modern_menu_stock_hero.py` accepts only the canonical USA retail ROM SHA-256 `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`. It uses the already retained `analysis/data/racer-hd-replacement-prototype.json` P1 representation IDs for the *consecutive, source-observed* 1213–1220 clip and the existing `tools/prototype_racer_hd_replacement.py::build_stock_rgba` path. All exact composition guards, palette IDs, rendered original RGBA SHA-256, ARGB FNV, source frame IDs and extracted manifest are recorded. No invented pose order, synthetic asset, arbitrary palette, cycling or HD reconstruction.

Run from the repository root, only in an authorized private workspace:

```bash
python3 tools/build_modern_menu_stock_hero.py \
  --rom reference/roms/retail/Uniracers_USA.sfc \
  --header native/product/modern_menu_stock_hero_original.generated.hpp \
  --manifest /tmp/modern-original-hero-provenance.json \
  --frames-dir /tmp/modern-original-pose-review
UR_MODERN_SOURCE_HERO_EXPERIMENTAL=1 ./path/to/actual/native/game
```

Generate the header **before building** the native executable. Its exact pathname is ignored by git deliberately so a ROM-derived raster is not accidentally submitted. Optional review PNGs are genuine 64×64 original-raster pose plates with manifest-bound SHA-256, **not screenshots of the final native game**. The opt-in runtime experiment composes this source image at nearest-neighbour 4× on the 342px native root. Its alpha-safe overscan admits only fully transparent canvas padding outside the physical surface; an opaque pixel anywhere outside the safe rectangle in any registered pose refuses the entire draw. The original P1 source colour is fixed: this WIP is not yet a live profile/appearance preview, and no final acceptance may assume it matches the selected Modern racer. `tests/unit/test_build_modern_menu_stock_hero.py` independently rebuilds the true output in a disposable directory and compiles the resulting C++ on the precise source corpus when the ROM is available. No generated hero header or source pixels have been committed, and no native executable has yet been built from this optional generated header in this branch.

### Original 32×32 spinning OBJ cursor reconstruction (additional source work)

`tools/reconstruct_modern_menu_cursor.py` now consumes the **actual source PPU dumps** from the established `tests/input/menu-visual-language.script` capture, checks every one of its 64 chronological idle samples, OAM palette 7 arrow and palette 5 shadow, measured tile phase order `8,4,0,204,200,196,192,140,136,132,128,76,72,68,64,12`, two-frame holds, exact seven-pixel shadow displacement, original CGRAM colours and 32×32 OBJ tile geometry. It reconstructs a 16-phase 39×39 RGBA review atlas and SHA-bound dump manifest, rejecting missing or reordered captures and incomplete raster tiles. The regression test uses **clearly synthetic** VRAM/OAM to test decoder math and deliberate rejection paths; those test pixels never enter the product.

The required original 64 PPU source dumps are not retained as files in the git repository, so the tool cannot yet produce a source-qualified original OBJ atlas in this environment. To run on a real source capture:

```bash
python3 tools/reconstruct_modern_menu_cursor.py \
  --dump-dir /path/to/source-mvl-dumps \
  --out-dir /tmp/original-cursor-review \
  --manifest /tmp/original-cursor-evidence.json
```

The recovered sprite's actual appearance must be visually checked against original menu captures and native selection placement before it replaces the provisional two-pixel source-blue accent. The 32×32 source cursor, its +7px shadow and wide-screen layout are owned jointly with the shared visual grammar / root composition agents in #2038 / #2040. **No decoded original cursor is yet active in the native game.** This is source-reconstruction tooling only, not evidence of verified release artwork or final 4:3/16:9 screenshots.

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

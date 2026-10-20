# Modern shared menu visual grammar: original-derived native primitives

**Status: implemented bounded native host presentation primitive, not an approved finished title/menu skin.** This owns reusable appearance and timing vocabulary only. Title composition, root composition, individual modal information architecture, sprite art and finished UX reviews belong to their individual screen agents. Authentic/guest, route/controller, save/records, gameplay, HD racer and recruitment film are outside this lane.

## Source-first inventory (2026-10-20)

Primary source is the ROM-observed **canonical USA clean-boot menu capture** in [`analysis/generated/menu-visual-language.json`](../analysis/generated/menu-visual-language.json), independently described in [`UI-STATE-MAP.md`](UI-STATE-MAP.md). It samples original MAIN_MENU, OPTIONS_MENU, PLAYER_SELECT_P1, TOUR_SELECT and TRACK_SELECT; it is stronger than impressionistic modern redesign sketches.

| Role | Observed original | Shared implementation contract |
| --- | --- | --- |
| Main yellow font | BG2 priority above BG1; 16×16 uppercase tiles; glyph sheet omits O (zero used), custom left/right and course-type symbols | 16px letter cell, five-stage RGB yellow ramp `F8F800 → C8C800 → 989800 → 686800 → 303000`, black outline and grey shadow. Actual glyph atlas **pending**. |
| Small supporting font | 8×16, grey outline/edge ramp, numerals, small caps, limited punctuation | 8px pitch, 16px logical height; do not substitute large yellow heading where stock uses small supporting data. Atlas **pending**. |
| Cursor | 32×32 dimensional blue OBJ on palette 7; flat dark shadow at +7,+7; 16-tile spin, two frames/tile; eased x/y travel with same-frame input response | Exact 16 source CHR tile ids; 32-frame animation phase; integer quarter-distance easing; arrow atlas/palette compositing **pending**. Until real atlas, contrasting static focus remains. |
| Background | Fixed BG1 grey checkerboard with abstract leaf motif and large dimensional Uniracers logo; BG2 text strip moves independently | Checker module mirrors the measured repeat family using RGB grey steps; **not** a claim to reproduce leaf/logo or extract game imagery. Title/background agent owns the hero artwork. |
| List rhythm | Yellow headline characters 16px; 24px stock row pitch; menus centered, original main cursor location separate from text | Constants expose 16px/24px; screens decide how to rearrange for Modern. Existing native root still has legacy coordinates pending its owner's redesign. |
| Transitions | BG2 moves 256px over 39 frames (ease-in, 8px/frame cruise, ease-out), while BG1 stays fixed | 39 exact captured offsets and reversible lookup; do not scroll or alter stock guest UI. |
| Original feedback | Movement SFX id 3, forward 2, back 1, rider commit 4, name input 6 in source command evidence | Sound ids are **reference only**; routing, guest sound and new host SFX must be coordinated with input/audio owners, never triggered by a paint helper. |

The stock menu's regional **UNIRACERS/UNIRALLY** wordmark differs from arbitrary fonts or new brand marks. Preserve both names. These observations do **not** justify recreating the title art by stretching an existing sprite, pretending host ASCII is the original 16px font, or inventing an unrelated cursor.

Visual cross-checks outside the project's ROM capture: the [MobyGames original main menu](https://www.mobygames.com/game/8085/uniracers/screenshots/snes/46723/) and [tour selection](https://www.mobygames.com/game/8085/uniracers/screenshots/snes/46725/) show the large yellow/black type, dimensional pointer, grey checkerboard, whimsical pictorial context and contrast between heading and item data. These external images remain research references only; they are neither vendored nor legal permission to distribute assets.

**Contemporary reference, not a source of Uniracers conventions:** [Sonic Mania's photographed interface inventory](https://interfaceingame.com/games/sonic-mania/) demonstrates a practical 16:9 retro-original menu, title/entry and settings family, and [its 2017 review](https://www.seganerds.com/2017/08/14/review-sonic-mania/) discusses restrained modern rendering effects in an otherwise period-grounded 2D design. Borrow the *discipline* of a coordinated family, readable state hierarchy and intentional motion, not its Sega colours, round widgets, typefaces, icon shapes or screen layouts.

## Shared contract and native integration

`native/product/modern_menu_visual_grammar.hpp` provides:

- **Palette roles:** the measured five-step yellow and five-step neutral greys, dark and bright blue arrow stops. `modern_stock_menu_palette.hpp` remains the compatibility authority for currently published Modern components.
- **Type/layout:** measured 16×16/8×16/24px rhythm; single-column at narrow logical widths and genuine preview/detail column only from 320 logical pixels. For a 342-wide field, primary x0..167, secondary x184..333 (8px outer insets); for stock 256, one 240px content column. Per-screen composition remains outside this module.
- **Motion:** `modern_menu_cursor_chr_tile(frame)`, `modern_menu_cursor_ease_axis(current,target)`, `modern_menu_slide_pixels(elapsed,backwards)`; these are pure, ROM-observed specifications, **not** a second scheduler or a timing hook into guest physics. Reduced-motion owners can show static selected state.
- **Reusable raster painters:** `modern_menu_paint_checker_backdrop` and `modern_menu_paint_focus_band` take the **existing** narrow native painter callback ABI and accept only an already-clipped destination rectangle. They cannot accept input, mutate state, select menu destinations or manage the host surface. Invalid dimensions fail without a draw call. Focus uses source-sampled dark blue plus bright blue leading accent while the true 32×32 sprite is pending.

The shared Modern native presenter `native/product/modern_root_overlay_presenter.hpp` consumes these raster helpers in the existing five-destination root and native Options selected-row path; both the traditional Modern executor and integrated Baldosa host call the same presenter. The five settled destinations, prompts, modals, scores and controller semantics remain unchanged. All other screens can adopt these helpers incrementally after review instead of embedding different palette/selection/checker constants. The absence of a real sprite or font atlas is a blocker for claiming final visual polish.

## Decoded original-art reference path (no copyrighted assets committed)

The existing first-party `tools/extract_menu_visual_language.py` already decodes the original **40-slot 16×16** BG2 yellow type atlas from legitimate source PPU dumps. This lane extends that *same* extractor with all three missing complementary original raster references:

1. `--small-atlas-out` and optional `--small-atlas-manifest-out`: original **8×16 grey** character atlas, including zero reused for O, known punctuation and the H-flipped closing parenthesis. Glyph-to-VRAM-tile mappings, image dimensions and SHA256 are captured in the JSON manifest. No invented font face.
2. `--cursor-atlas-out` and optional `--cursor-manifest-out`: the actual **16-frame 32×32 palette-7 OBJ arrow plus palette-5 shadow displaced +7,+7**, decoded through `$2101` OBSEL VRAM name/base pages, source OAM size bits, original 4bpp palette and alpha transparency. The resulting image is 624×39, sixteen adjacent 39×39 cells. Pose order must match the captured 16 unique CHR tiles; missing or reordered phases fail closed, with source VRAM/CGRAM/OAM SHA256 receipts.
3. `--bg1-out` and optional `--bg1-manifest-out`: **actual fixed 256×224 8bpp BG1 art** showing the original static title/logo/checker/leaf motif as encoded in VRAM and CGRAM, rather than a substitute navy grid. Decode honours BG tile size, flipped tilemap entries and original scroll. This is BG1 only; BG2 menu lettering, OBJ arrow, colour math and final presentation remain outside the exported image. The manifest records the precise source and output hashes.

Run from a privately available canonical clean-boot `tests/input/menu-visual-language.script` capture and supply distinct local filenames, for example:

```sh
python3 tools/extract_menu_visual_language.py "$CAPTURE_DIR" \
  --out "$TMPDIR/menu-visual-language.json" \
  --atlas-out "$TMPDIR/stock-16px-font.png" \
  --atlas-manifest-out "$TMPDIR/stock-16px-font.json" \
  --small-atlas-out "$TMPDIR/stock-8px-font.png" \
  --small-atlas-manifest-out "$TMPDIR/stock-8px-font.json" \
  --cursor-atlas-out "$TMPDIR/stock-cursor-16poses.png" \
  --cursor-manifest-out "$TMPDIR/stock-cursor-16poses.json" \
  --bg1-out "$TMPDIR/stock-bg1-layer.png" \
  --bg1-manifest-out "$TMPDIR/stock-bg1-layer.json" \
  --bundle-manifest-out "$TMPDIR/stock-source-bundle.json"
```

The command is a **reproducible source-asset research route**, not a claim that this session executed it on an original ROM or delivered shippable game assets. It requires the separate authentic input capture; no binary atlas, ROM, game art or host screenshot is added to this PR. The original 16×16 font now also emits an optional `--atlas-manifest-out` receipt with all 40 source slots and original PPU VRAM/CGRAM hashes, making all four art exports independently source-bound; do not substitute a self-authored image with a copied receipt.

`--bundle-manifest-out` requires all four PNG outputs and verifies their **mutual** provenance: big font, BG1 and first cursor pose must have identical original idle-snapshot VRAM/CGRAM roots and tags; the small font must originate from a track-select source snapshot; every sheet must have its exact measured dimensions and the cursor must include all 16 ordered CHR phases. A mixed-capture bundle fails with an explicit error. The resulting JSON is a source research receipt and deliberately sets `asset_distribution_approved` and `native_render_and_visual_acceptance` to false. It contains hashes, not original art or redistribution permission.

A source-extracted image is eligible for artistic comparison and a **separately licensed/integrated renderer proposal**. It does not automatically grant redistribution rights, author approval, runtime native font/arrow rendering or packaged-Windows screenshot QA. RGB5-to-RGB8 sampling uses the existing shift-by-3 decoder: other PPU output-brightness/color-math effects are explicitly outside this reference layer.

The automated ROM-free checks in `tests/unit/test_extract_menu_visual_language.py` synthesize 8bpp BG1 tilemap H-flip and scroll, 8×16 punctuation/H-flip, OBJ second-page addressing, RGBA transparency, palette choice, 7px arrow/shadow displacement, phase enumeration and exact source hash receipts. Full output from original PPU frames remains a **pending real-domain acceptance step**.

## Native renderer seam for verified atlas rasters

`native/product/modern_menu_source_atlas.hpp` is a separate, dependency-free C++17 presentation adapter for **caller-supplied** pixel buffers. The shared `modern_menu_visual_grammar.hpp` re-exports it for title, root, destination and animation owners without creating another renderer or requiring any source graphics to be checked in.

- It recognizes **only** the recovered source atlas geometries: yellow heading **640×16** (40 16px cells), grey detail **360×16** (45 8px cells), cursor **624×39** (16 39px cells with shadow), and reference BG1 **256×224**.
- `modern_menu_paint_source_text` maps original uppercase/digit characters; title O reuses tile zero, small O uses its duplicated slot, the known original punctuation has explicitly indexed source cells. Its optional heading word gap matches the original measured **8px rider-title** or **16px main/options** spacing, while detail text stays at fixed 8px pitch. Unsupported characters or other heading gaps fail the entire text operation instead of displaying a guessed substitute. UI owners must provide supported copy or use a deliberately labeled host fallback for modern-only text.
- `modern_menu_paint_source_cell` paints a particular cursor animation frame, complete source BG1 layer, or font cell with 1×–4× nearest-neighbour scale. Transparent pixels preserve the host buffer and opaque pixels transfer verbatim. The adapter rejects unsupported translucent alpha, malformed allocation geometry, out-of-bounds destinations and cropped glyphs **before** touching output.
- Inputs are a pixel span in **host AARRGGBB** words, with stride, dimensions and allocated element count. Extractor PNGs store straight **RGBA bytes**; the host remains responsible for verified PNG decompression and source/asset digest admission. `modern_menu_pack_source_rgba` performs the exact RGBA-byte → AARRGGBB-word conversion after that verification, with full-buffer preflight for dimensions, length and 0/255 alpha, so an invalid later source pixel cannot corrupt the output partway through. Do not reinterpret file bytes as native `uint32_t` words, use a synthetic colour conversion or treat this packer as an image decoder.
- **Deliberate shipping hold:** there is no runtime source-art loader/manifest approval or bundled graphics in this PR. The original bitmap exports stay local, and this opt-in native painter does not activate without an explicitly supplied approved buffer. The existing ASCII/blue-band fallback stays visible and controller-readable. This is ready for visual and rights review, not an assertion that actual source fonts or cursors are already rendered in a packaged Windows build.

`tests/native/modern_menu_source_atlas_test.cpp` and `tests/unit/test_modern_menu_source_atlas_cpp.py` verify the real first-party native C++ header against exact pixels and negative cases. They are source-independent synthetic checks, not source-ROM capture or visual approval. Any later asset loader must validate the original source/PNG manifest and run the separate native final-frame/Authentic regression suite before being enabled.

## 4:3 and 16:9 design rules

| Layout | Native logical field | Shared compositor policy | Screen composition freedom |
| --- | --- | --- | --- |
| Stock-compatible 4:3 | **256×224**, 7:6 pixel aspect | Reserve at least 8 logical pixels horizontally for a 240px text panel; single vertical list; title and details legible without scissoring source glyphs | Rebalance vertical breathing room; do not shrink real 16px letters to pretend they are 8px. |
| Extended Modern 16:9 | **342×224**, 7:6 pixel aspect (~1.781:1) | Two columns only with >=320px actual available width; 168px initial navigation, 16px separation, remaining width for selected context and previews | Hero title art, important course/personal-best data, racer detail, etc. can occupy the added horizontal field. Do not stretch 256px stock art. |
| Narrow/modals | Less than 320px available content | One column, bounded text fit and no fake extra scroll or clipped selected item; existing validated modal dimensions win | Specific screen owner decides compact copy, fallback title pitch, modal placement and safe-area management. |

Use native resolution, 7:6 PAR and density authorities from [`DISPLAY-PRESENTATION-POLICY.md`](DISPLAY-PRESENTATION-POLICY.md) and [`modern_overlay_composition.hpp`](../native/product/modern_overlay_composition.hpp); do not assume host output 1920×1080 makes SNES logical pixels square. The layout helper consumes **available content width**, so passing the same 342px field after reserving HUD/insets is a misuse. The current root painter still uses its pre-existing 240/356 logical panel arguments; its screen owner must independently reconcile those against real 342-wide capture before final approval. Preserve keyboard and controller visibility and a visible static selected state under reduced motion.

## Three-project reuse preflight

Used the source-grounded [reuse register](../analysis/three-project-reuse-opportunities.json) and [capability matrix](../analysis/data/three-project-apparatus-capability-matrix-20261010.json), corresponding to the `modern-product` lane of `tools/select_three_project_reuse.py --lane modern-product --include-conditional`. **Execution limitation:** no local GitHub checkout in this session, so the Python preflight itself was not executed. Equivalent register/matrix entries were read directly; no conditional source-dependency pilot was activated.

- **UR-Recomp:** reuse existing shared `ModernRootOverlayPainter`, `modern_stock_menu_palette.hpp`, `modern_overlay_composition.hpp` and actual stock `menu-visual-language.json`. No new independent UI frontend or second presenter.
- **Baldosa USA:** reuse the already bound native guest/host frontend route and SDL pixel callback through the shared UR presenter. Pinned upstream core is a game execution dependency, not a reason to reimplement visuals in its source.
- **malmazuke PAL:** existing `src/app/frontend.cpp` is a cross-project semantic/reference candidate, not a matched USA menu art or shipping host component; PAL-native implementation and map cannot certify menu raster provenance. No code/assets imported.
- **Decision:** extend first-party host-presentation seam without new dependencies or copying game assets; stop at a small testable component family.

## Verification and explicit approval boundary

`tests/native/modern_menu_visual_grammar_test.cpp` compiles against the **actual shared C++ header** and asserts native source palette constants, all 39 scroll positions, 32-frame tile cycle, eased movement, logical geometries, raster clipping and sampled focus/checker pixels. Its `tests/unit/test_modern_menu_visual_grammar_cpp.py` runner uses C++17 pedantic warnings-as-errors and asserts the **native shipping root presenter** consumes the new helpers; existing `test_modern_root_overlay_presenter.py` exercises the actual linked presenter for both stock and wide host rectangles. A green ROM-free fixture proves code/raster contract only.

**Still open for screen/art/QA owners:** execution of the existing source-bound 16×16 font and newly added 8×16/cursor/BG1 atlas exporters against real original captures, artwork licensing and the actual native consumption/rendering of those verified pixels, source-faithful approved racer art, reduced-motion policy wired to the host, title and modal composition, final contrasting grey checker choice, original/Modern region split, real transition/SFX hookup, 4:3 and 16:9 output screenshots of the **packaged native Windows game**, motion/selection frames, 1×/4× density, real controller/keyboard, and a separate untouched Authentic capture. Source-only synthetic pixel tests are **not packaged-game screenshots** and grant no graphics/QA or human visual sign-off.

Coordinate integration by having each screen owner use this header, preserve current product models and submit its own screen screenshots/approval ledger; only the shared visual-grammar owner edits these common visual tokens in this PR.

# Modern shared menu visual grammar: original-derived native primitives

**Status: implemented bounded native host presentation primitive, not an approved finished title/menu skin.** This owns reusable appearance and timing vocabulary only. Title composition, root composition, individual modal information architecture, sprite art and finished UX reviews belong to their individual screen agents. Authentic/guest, route/controller, save/records, gameplay, HD racer and recruitment film are outside this lane.

## Fixed BG1-grid continuity in native Modern root (2026-10-21)

The original screen's checker/leaf **BG1 stays fixed** while the 39-frame menu
**BG2 text strip travels** (canonical source: `analysis/generated/menu-visual-language.json`).
The original shared checker fallback reset its 16px tile origin at every panel
rectangle, which could move the checker phase with panel bounds or create a
visible half-square discontinuity across adjacent cropped regions.

`modern_menu_paint_checker_backdrop(..., fixed_bg1_grid=true)` is a small
source-grounded presentation-only correction: it locks the checker squares to
the *actual destination framebuffer's* top-left pixel, even when a rectangle
starts at x/y offsets not divisible by 16 logical pixels. The existing
default remains local and byte-identical for other consumers. The actual
Modern root opts in; it still renders only its existing source-family
grey checker fallback, not an invented leaf/logo raster. No font, title
composition, menu state, routes, controller, guest pixels or Authentic mode
are changed. Both 256×224 (4:3) and 342×224 (16:9) use the same 16px SNES
logical grid at 1×, with integer 4× preservation.

The checked-in native C++ framebuffer oracle composes one full root-area
checker and four independently cropped quadrant panels split at *non-tile*
x/y boundaries and demands full-surface byte identity at both widths,
at 1× and 4×. It also checks global-origin phase, valid local default pixels
and fail-closed invalid rectangles. The existing root presenter source
contract asserts the fixed BG1 call is genuinely used by the shipping host.
This is **native shared-painter** evidence, not a packaged Windows SDL P7
capture, human art acceptance, leaf-pattern reconstruction or QA08 release
approval. The visual QA agent must independently inspect a newly compiled
combined native Windows SDL capture in 4:3 and 16:9 against stock BG1
references; the title/destination owners keep their screen-specific layouts.

Three-project reuse (registry `modern-product` with conditional entries):
UR's measured original PPU `menu-visual-language.json`, shared painter,
native product states and actual Windows capture route remain the source of
truth; Baldosa owns the integrated native framebuffer/SDL handoff; Malmazuke
is a PAL reference only. There is no justification for importing a second
runtime, painting engine or copied game artwork for this seam correction.

## Canonical transparent source pixels, direct-raster admission (2026-10-21)

The optional original-art adapter accepts two ingress paths: RGBA bytes
through `modern_menu_pack_source_rgba`, which already converts all alpha-zero
pixels to **literal ARGB zero**, and a direct caller-supplied AARRGGBB sheet
through `modern_menu_paint_source_cell/text`. The latter previously treated
an alpha-zero pixel with nonzero hidden RGB as valid heading, small-font or
BG1 art, even though the sixteen-pose cursor adapter rejected the identical
malformation. This is an internal provenance/canonicalization inconsistency,
not a visual difference in already-clean source buffers.

Both direct single-cell and whole-string preflights now refuse alpha-zero /
RGB-nonzero pixels, just as they already refuse fractional alpha, without
touching the destination. The whole-string path checks **all referenced
glyphs before the first write** so a malformed later P cannot leave the
earlier O painted. Source BG1 uses the same no-partial-paint rule. The
previously accepted real PNG-packer output and the separate all-pose cursor
contract remain unchanged. ROM-free C++ tests use deliberately malformed
synthetic 16px heading, 8px small font and 256×224 BG1 buffers, checking
literal buffer identity after rejection.

This protects the boundary for future *legally admitted* original font and
BG1 art. It does **not** supply those assets, certify any ROM/image rights,
prove source palette identity, or count as a new Windows SDL/human visual
acceptance. No layout, transition, hero, route, controller or Authentic
rendering changed.

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

## Contextual cursor palette is part of the source grammar

The original dimensional cursor is also a **two-OBJ composition**, not a
flat pointer: the palette-7 blue arrow and palette-5 dark maroon
`RGB(72,32,48)` shadow are offset by `(+7,+7)` original pixels. Shared
`kModernMenuSourceCursorShadow = 0xFF482030` preserves the real shadow
palette token; the verified original **39×39** source sheet already contains
both OBJs, so the native helper must not redraw the shadow or recolour the
combined atlas. Synthetic compiled C++ 4× raster tests verify separate
foreground/shadow pixels survive into the exact native buffer and preserve the
far bottom-right pixel and the following transparent boundary.

The original dimensional arrow is **not uniformly blue across stock menus**.
The captured USA `analysis/generated/menu-visual-language.json` separates:

| Original menu context | Source highlight RGB | Native ARGB token |
| --- | --- | --- |
| Main menu | (160, 208, 248), strongest blue OBJ palette stop | `0xFFA0D0F8` |
| Pick Your Uni / rider select | (136, 200, 240) | `0xFF88C8F0` |
| Pick Tour | (240, 160, 136) | `0xFFF0A088` |
| Pick Track | (240, 160, 136) | `0xFFF0A088` |

The publicly visible original *Pick Tour* screenshot corroborates the warm-coloured arrow: [MobyGames SNES screenshot 46725](https://www.mobygames.com/game/8085/uniracers/screenshots/snes/46725/). The repository capture, not that JPEG, is the authority for exact RGB values. These are source-state palettes, **not** automatic mappings from Modern destinations to original menus. A new Modern Practice view need not use the old Tour arrow colour merely because both offer courses.

The same clean-boot source captures **12 exact frame-to-frame vertical deltas** for the main-menu cursor's 70→93px move: `6,4,3,3,2,1,1,1,1,0,0,1`. `modern_menu_observed_first_row_move_y(elapsed_frames)` returns their clamped cumulative displacement, including both held frames and the final one-pixel settle, without allocating a second clock or altering any host route. The previously exposed `modern_menu_cursor_ease_axis` is still the general-purpose *approximation* for arbitrary distances, rather than a claim of frame-for-frame stock movement. A receiving motion/screen owner must decide when the exact first-row witness applies and must not transplant the curve into unrelated gameplay/guest coordinates.

Original big-font headings also have a context-specific **word gap**: the captured *PICK YOUR UNI* heading has 8px gaps, whereas the main/Options, *PICK TOUR* and *PICK TRACK* source examples use 16px. The pure `modern_menu_observed_heading_word_gap(context)` token supplies those measured advances for a legally cleared source glyph compositor; the provisional host ASCII fallback remains clearly identified as such. No screen is automatically reflowed.

A separate shared fallback-painter guard now preflights full **8px host glyph cells**, scaled width/height and the existing one-physical-pixel offset shadow before either text callback. It refuses missing, empty, oversized or edge-clipped headings atomically. Native tests cover too-wide words, bottom-edge overflow, a shadow that alone would cross the right edge, and an exactly fitting one-cell heading. This prevents future screen owners from turning a nominally safe 4:3 or 16:9 overlay into off-panel glyph writes; it does not substitute an original 16×16 raster glyph atlas or change stock pixels.

The shared C++17 header now exposes `ModernMenuSourceCursor` and `modern_menu_cursor_highlight(context)` and an optional final context argument on `modern_menu_paint_focus_band`. The existing root, destination and Options callers retain the **same default main-menu blue pixel values** without any API migration. An owning screen can select `Rider`, `Tour` or `Track` when an original-reference comparison justifies it; invalid values fail visibly to blue. The actual multi-shaded 32×32 spinning OBJ and its +7px shadow remain a separate rights-reviewed source-art asset, not a claim of completion by recolouring a three-pixel fallback marker. Tests exercise source constants and actual 256×224 framebuffer pixels in all four contexts without guest writes.

This patch follows the three-project reuse preflight for `modern-product`: keep UR's measured PPU `menu-visual-language.json`, existing native `ModernRootOverlayPainter` and typed menu state; reuse Baldosa's integrated host rather than adding another graphics/input path; use Malmazuke for comparative source research only. No framework pilot is justified without a reproduced failure. The last-mile independent screenshot comparison is still **HOLD**: acquire same-build native SDL final-drawable 342×224/256×224 context states, compare visually with original captures, check 1×/4× scaling and legibility, then obtain human art review. Synthetic native pixel tests do not constitute those screenshots or approval.

## Opt-in native source-asset adapters

A source-linked appearance primitive is only useful if a legitimately cleared
original raster can be passed through **the existing native painter** rather
than creating a second drawing pipeline. Two C++17 wrappers are now exposed
in `modern_menu_visual_grammar.hpp`:

- `modern_menu_paint_source_heading_context` forwards a user-local,
  independently verified **640×16** original heading sheet to the existing
  atomic `modern_menu_paint_source_text`, choosing the original 8px rider
  or 16px other-menu word gap. Unsupported characters, missing ink,
  cropped words or alpha errors reject without partial font writes.
- `modern_menu_paint_source_cursor_phase` forwards a source **624×39**
  atlas of sixteen 39×39 arrow-and-shadow phases to the already vetted
  `modern_menu_paint_source_cell` at index `(menu_frame / 2) % 16`. It first validates **all sixteen** source 39×39 poses for ink and strictly opaque/transparent pixels, so one broken late pose cannot vanish mid-spin after a seemingly successful first paint. The
  caller owns its 60Hz menu clock, focus fallback, location and reduced-motion
  choice. This function does not read or drive guest animation and does
  not replace the legitimate dimensional original arrow with the
  three-pixel host band.

ROM-free native C++17 tests use generated **single-pixel synthetic atlases**
to verify the real framebuffer receives correct rider/main word positioning,
all 16 cursor phases, two-frame holds, 32-frame wrap, rejection of empty, partial-alpha or nonblack-transparent *future* poses on frame zero, and **atomic no-write**
for invalid source or out-of-bounds target. No PNG, retail CHR, palette dump,
ROM bytes, or source-derived art is committed or loaded at game startup.
The source-bundle verifier, ownership/capture receipts, legally approved
distribution and integrated Windows SDL comparison remain independently
required before passing original art to these adapters. Visual acceptance
and release gates are still **HOLD**.

## Canonical USA PPU evidence-to-native token parity

`tests/unit/test_modern_menu_original_source_tokens.py` now checks the
**actual checked-in canonical USA PPU observation** against the native shared
C++ declarations, rather than merely comparing two copies of hardcoded
numbers. It independently verifies all five yellow glyph ramp stops, five
grey ramp stops, main blue light/dark and maroon cursor-shadow RGB, the +7px
shadow displacement, all 16 CHR spin tile IDs, all 39 stock scroll-frame
offsets, all 12 first-row cursor movement deltas, exact 32/39-frame periods,
and the original 8px/16px heading-gap and rider/tour/track highlight variants.
In-memory negative tests deliberately mutate a palette entry or replace its
C++ literal with a dynamic expression and require rejection. CI now triggers
these checks on changes to `analysis/generated/menu-visual-language.json`,
the shared grammar header and its native/pure tests.

This is a **source provenance guard for numerical tokens**. It does not
authenticate original ROM bytes anew, draw recovered art, prove correct
source/host raster parity or grant visual approval. The optional original
assets remain unbundled and source-manifest/rights-gated.

## Shared contract and native integration

`native/product/modern_menu_visual_grammar.hpp` provides:

- **Palette roles:** the measured five-step yellow and five-step neutral greys, dark and bright blue arrow stops. `modern_stock_menu_palette.hpp` remains the compatibility authority for currently published Modern components.
- **Type/layout:** measured 16×16/8×16/24px rhythm; single-column at narrow logical widths and genuine preview/detail column only from 320 logical pixels. For a 342-wide field, primary x0..167, secondary x184..333 (8px outer insets); for stock 256, one 240px content column. Per-screen composition remains outside this module.
- **Motion:** `modern_menu_cursor_chr_tile(frame)`, `modern_menu_cursor_ease_axis(current,target)`, `modern_menu_slide_pixels(elapsed,backwards)`; these are pure, ROM-observed specifications, **not** a second scheduler or a timing hook into guest physics. Reduced-motion owners can show static selected state.
- **Reusable raster painters:** `modern_menu_paint_checker_backdrop` and `modern_menu_paint_focus_band` take the **existing** narrow native painter callback ABI and accept only an already-clipped destination rectangle. They cannot accept input, mutate state, select menu destinations or manage the host surface. Invalid dimensions fail without a draw call. Focus uses source-sampled dark blue plus bright blue leading accent while the true 32×32 sprite is pending.

The shared Modern native presenter `native/product/modern_root_overlay_presenter.hpp` consumes these raster helpers in the existing five-destination root and native Options selected-row path; both the traditional Modern executor and integrated Baldosa host call the same presenter. The five settled destinations, prompts, modals, scores and controller semantics remain unchanged. All other screens can adopt these helpers incrementally after review instead of embedding different palette/selection/checker constants. The absence of a real sprite or font atlas is a blocker for claiming final visual polish.

## Changed-profile restart action remains readable in 4:3

The real native host stores one stale-profile state as racer identity text `PROFILE CHANGED - RESTART APP` when the active profile/SRAM authority changes. Prefixing this with `RACER: ` exceeded the actual **28 text cells available** in the compact 240-logical-pixel root, so an ordinary clipped/ellipsized identity lost the actionable `RESTART APP` suffix. When the original sentence does not fit, this sentinel renders as the complete `RACER: CHANGED - RESTART APP`, exactly 28 cells. A sufficiently wide root keeps the original longer `RACER: PROFILE CHANGED - RESTART APP` wording intact. The root's separate `RACER CHANGED - RESTART GAME` notice remains unchanged, and ordinary named players, anonymous profiles and genuinely long user-entered names retain their existing logic. The native test asserts the source action and real pixel bounds at 240px. No profile validity, save state, controller binding or reboot behaviour has changed.

## Controls help reports only real racer setup shortcuts

Independent review previously found a misleading root footer (`RACER SETUP NOT YET LINKED`) when the native host had no Create/Add/Switch action. The root footer was fixed earlier, but the deep **Options → Controls** modal still unconditionally rendered `X RACER SETUP`. It now shows this help row only if the host's product view advertises at least one genuine `racer_shortcuts_available`, `first_racer_shortcut_available`, `second_racer_shortcut_available` or `existing_profile_switch_available` capability. Existing hosts with an X/F2 racer route retain the original instruction. Unsupported hosts keep all keyboard/controller movement, select and back instructions but do not point users at an unavailable feature. Native C++ tests cover no available shortcut, legacy shortcut and independently offered first-racer creation. No menu routing, input policy, guest or persistence state has changed.

## Fail-closed root panel geometry at the native paint boundary

The shared `render_modern_root_overlay` now refuses a complete draw **before touching any pixel** unless both the integer display scale (1×–4×) and its assigned host rectangle can contain the full `panel_w × 204` logical menu. This closes an observed source-contract gap where a rectangle could be valid *within the framebuffer* but too narrow or short for its child controls, resulting in out-of-panel painter callbacks. The bounds check also constrains implausible source/stride inputs before multiplying drawing coordinates, including the existing 176px minimum required to fit source-sized fixed headings and controls (consistent with `modern_native_destination_canvas`). No valid existing compact root (240×204) or 16:9 root (320×204) changes size or pixel placement.

The standalone `render_modern_options_modal` entrypoint now independently rejects an absent painter/pixel buffer, invalid integer scales and requests whose 240px/320px panel or 180px-high modal region would extend outside the framebuffer. This protects future pause-screen callers even when they do not go through `render_modern_root_overlay`. A separate native test first asserts that malformed standalone calls produce no painter operations, then verifies that a valid compact modal draws all actual rectangles/text within its host panel. No valid Options menu or original source data is changed.

The native regression tests include 239px-wide and 203px-high 4:3 panels, a 319px instead of 320px widescreen root, unsupported 5× scale, excessively large panel width, and a full-size panel paired with an unscaled 4× host. They verify that malformed calls produce **no fill, border or text operations**. For valid compact and wide views they additionally record and bound every issued fill/stroke rectangle and actual 8px-cell text callback against the assigned panel, including checkerboard tiles and selected focus-band geometry. These are programmatic host paint contracts, not final physical-device artwork approval.

## Source detail-font special-slot integrity at the native painter

The separately verified original 8×16 detail-font PNG exporter creates three nonstandard glyph semantics: **O is a pixel-exact copy of numeral 0**, **')' is a horizontal mirror of '('**, and the designated **space is fully transparent**. The opt-in native `modern_menu_source_atlas.hpp` painter now checks these semantic slot relationships on its supplied 360×16 AARRGGBB atlas, including **every source row/pixel**, before issuing a **single cell or whole-string** paint. This is intentionally defensive even when another layer has already checked the standalone PNG manifest. A caller can no longer forge a nominally correct-size font image with extra space ink, a different O or unrelated closing parenthesis and have that bitmap mislabeled as original content. Any inconsistency fails without modifying the destination framebuffer. Existing zero/O/parenthesis text, source anti-clipping and 1×–4× scaling retain their behaviour on valid pixels.

`tests/native/modern_menu_source_atlas_test.cpp` uses synthetic rows rather than copied Nintendo/ROM font art and checks clean input plus three **separate negative mutations**, each preserving framebuffer bytes on refusal. It is a bounded *source-cell integrity invariant*, not original-image provenance, redistribution permission, integrated Windows font use or final visual approval.

## Optional original heading in the actual native root

The production-shared `render_modern_root_overlay` now accepts one **trailing, optional** `const ModernMenuSourcePixels* source_heading = nullptr`. All existing Modern/Baldosa call sites leave it unset and render exactly the same provisional host ASCII header; it does **not** change controller ownership, title composition, source asset policy, guest/Authentic state or any menu route. An independently verified and legitimately distributable **40-slot 640×16 original BG2 heading raster**, already decoded as host AARRGGBB and kept alive for the call, can be passed by a future native asset owner. The root then uses `modern_menu_paint_source_text` at the actual header coordinates with source 16px cells and nearest-neighbour 1×–4× scaling, including exact regional `UNIRACERS/UNIRALLY` names. It does **not** paint the provisional duplicate shadow over those pixels: the source atlas already contains original outline/shading.

The atlas painter **preflights the whole string** for bounds, alpha 0/255, valid source slots and nonempty ink before a write. A bad/undersized/translucent atlas fails atomically and the existing ASCII fallback remains visible. The actual shared-root native C++ test renders synthetic, non-game pixels into a real allocated 256×224 and 4× wide host buffer, asserts original-heading consumption, regional switch, default legacy behaviour and atomic invalid-atlas fallback. No source PNG/ROM bitmap or generated font is checked in or loaded automatically. `source_heading` is *not* an assertion that original assets are already shipping: **no current product host supplies that pointer**, and separate source attestation, licence/redistribution review, real Windows binding and independent final SDL/art approval remain required.

## Source-capture receipt is mandatory for local original-art checks

The first-party exporter `build_menu_source_art_bundle` includes its capture-script identity (`tests/input/menu-visual-language.script`), original main-frame tag `mvl-idle-000`, a numbered `mvl-track-XX` detail-frame tag, and **four original VRAM/CGRAM SHA-256 receipts** (`main_vram`, `main_cgram`, `detail_vram`, `detail_cgram`). Earlier versions of `verify_menu_source_art_bundle.py` checked PNG image digests and dimensions but did not require any of those source-capture fields, so a receipt missing *all* source PPU metadata could still be marked `source_bundle_verified`. The local admission verifier now rejects missing or malformed source fields, non-lowercase or non-64-digit digests, invented or missing original frame tags and surplus/unexpected digest names **before reading the images**. Synthetic tests include each absence and corruption, and still exercise the original four PNGs and special glyph/pose checks.

A new optional `--source-dumps /path/to/private-ppu-capture` flag can also verify those **actual local** original capture bytes. It reads only the exact four `mvl-idle-000.vram.bin` (65,536 bytes), `mvl-idle-000.cgram.bin` (512 bytes), `mvl-track-XX.vram.bin` (65,536 bytes) and `mvl-track-XX.cgram.bin` (512 bytes) paths named by the receipt, and recomputes SHA-256 of each against its declared `main_*/detail_*` digest. Wrong lengths, missing dumps, symlinks, unexpected SHA and nonexistent/redirected dump directories all fail **before any PNG is admitted**. Without the optional directory, no dump bytes are read and the explicit result field `local_ppu_dump_hashes_verified=false` remains visible; with all four exact matches it becomes true. Regardless, `rom_identity_verified=false` is always reported because the verifier does not independently authenticate the original retail game or capture apparatus. This is useful for private in-game original sprite/font comparison and never packages source files or the user's ROM.

For example, after creating a first-party local source bundle with the reference capture script:

```sh
python3 tools/verify_menu_source_art_bundle.py \
  --bundle /tmp/private-menu-art/bundle.json \
  --heading /tmp/private-menu-art/heading.png \
  --detail /tmp/private-menu-art/detail.png \
  --cursor /tmp/private-menu-art/cursor.png \
  --bg1 /tmp/private-menu-art/bg1.png \
  --source-dumps /tmp/private-menu-ppu-captures
```

The file layout and `--source-dumps` path are examples, not asserted existing or distributed files. All added automated tests generate fake PPU bytes in isolated temporary directories. No art, video, PPU snapshot or ROM bytes are included in the repository.

These fields are only a *completeness and format check of the declared capture evidence*. A caller able to invent all four hashes can still create a syntactically well-formed untrusted receipt. The verifier does **not** recompute PPU hashes from original VRAM/CGRAM dumps, authenticate a ROM or imply original-art redistribution permission. Independent capture/export provenance remains necessary before attaching any source original font/arrow/background data to a renderer; `distribution_approved` and `final_native_capture_approved` remain false unconditionally. No ROM/private source art or source atlas is distributed by this patch.

## Decoded original-art reference path (no copyrighted assets committed)

The existing first-party `tools/extract_menu_visual_language.py` already decodes the original **40-slot 16×16** BG2 yellow type atlas from legitimate source PPU dumps. This lane extends that *same* extractor with all three missing complementary original raster references:

1. `--small-atlas-out` and optional `--small-atlas-manifest-out`: original **8×16 grey** character atlas, including zero reused for O, known punctuation and the H-flipped closing parenthesis. Glyph-to-VRAM-tile mappings, image dimensions and SHA256 are captured in the JSON manifest. No invented font face.
2. `--cursor-atlas-out` and optional `--cursor-manifest-out`: the actual **16-frame 32×32 palette-7 OBJ arrow plus palette-5 shadow displaced +7,+7**, decoded through `$2101` OBSEL VRAM name/base pages, source OAM size bits, original 4bpp palette and alpha transparency. The resulting image is 624×39, sixteen adjacent 39×39 cells. The exporter now requires **all 64 consecutively tagged original idle captures**, not merely one example per pose, to verify the 16 source CHR tile phases repeat with exactly two frames per tile over both 32-frame cycles; any missing/reordered frame, drifted repeated source pixels/palette or incorrect phase fails closed. The atlas manifest records the 64-frame source-sample count plus the original 16-pose VRAM/CGRAM/OAM SHA256 receipts. Source OAM whole-sprite H/V flips and the real $2101 name-base word-address spacing of **0x2000 words (16 KiB bytes)** are decoded, not guessed.
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

The independently executable verifier `tools/verify_menu_source_art_bundle.py` accepts **only these four locally generated PNGs plus the bundle JSON**:

```sh
python3 tools/verify_menu_source_art_bundle.py \
  --bundle "$TMPDIR/stock-source-bundle.json" \
  --heading "$TMPDIR/stock-16px-font.png" \
  --detail "$TMPDIR/stock-8px-font.png" \
  --cursor "$TMPDIR/stock-cursor-16poses.png" \
  --bg1 "$TMPDIR/stock-bg1-layer.png"
```

It recomputes each SHA256 and decodes/validates the precise simple first-party **8-bit RGBA, unfiltered PNG** layout, CRCs, bounded scanlines, source dimensions and binary alpha. It independently checks the small font's identical zero/O glyphs, horizontally flipped parentheses and blank-space cell, plus a visible pixel in all sixteen source cursor phases. Corrupt or substituted images fail closed even when a caller has copied their new hashes into a synthetic receipt. The output explicitly denies asset distribution and final-screen approval. This is an additional integrity handoff, **not a cryptographic signature proving ownership of a captured original**, a native packaged-game screenshot or redistribution authority.

The command is a **reproducible source-asset research route**, not a claim that this session executed it on an original ROM or delivered shippable game assets. It requires the separate authentic input capture; no binary atlas, ROM, game art or host screenshot is added to this PR. The original 16×16 font now also emits an optional `--atlas-manifest-out` receipt with all 40 source slots and original PPU VRAM/CGRAM hashes, making all four art exports independently source-bound; do not substitute a self-authored image with a copied receipt.

`--bundle-manifest-out` requires all four PNG outputs, validates the full 64-idle-frame / 32-frame-cycle cursor proof, and verifies their **mutual** provenance: big font, BG1 and first cursor pose must have identical original idle-snapshot VRAM/CGRAM roots and tags; the small font must originate from a track-select source snapshot; every sheet must have its exact measured dimensions and the cursor must include all 16 ordered CHR phases. A mixed-capture bundle fails with an explicit error. The resulting JSON is a source research receipt and deliberately sets `asset_distribution_approved` and `native_render_and_visual_acceptance` to false. It contains hashes, not original art or redistribution permission.

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

## Image-level native SDL checker contrast admission

The independent `tools/verify_modern_root_sdl_contrast.py` tests the **captured output pixels**, not merely C++ palette definitions:

```sh
python3 tools/verify_modern_root_sdl_contrast.py \
  --receipt path/to/readback-receipt.json \
  --png path/to/actual-sdl-drawable.png \
  --p7 path/to/actual-sdl-drawable.pam \
  --native-log path/to/native-process.log \
  --out local-root-contrast-receipt.json
```

It accepts the independently archived **1024×768 / 1280×720** Windows SDL readbacks and additionally permits a **3840×2160 (4K) native SDL capture** when it is produced, with independently logged 256×224/root 240×204 (4:3) or 342×224/root 320×204 (16:9/4K) geometry. A 4K output with a forged or mismatched 256-wide source is rejected. The image parser's strict 4 MiB original-asset PNG default is unchanged; the pixel-audit consumer explicitly requests a 64 MiB bounded PNG cap for real high-resolution screenshots. The PNG, original unmodified P7 bytes and native process log must all match the receipt's SHA256 values; PNG pixels must **exactly equal the raw P7 RGBA bytes**. It checks the screen-captured racer-identity line at the observed 8px source cell band, requires real opaque foreground pixels above two checker tones, computes proper sRGB luminance for the worst background square, and rejects text below **4.5:1**. It rejects the old native #989898 and accepts the expected updated #C8C8C8 **only if it actually appears in the submitted native output**. Adversarial ROM-free tests cover old colours, forged hashes/P7, noncanonical source geometry, missing SDL readback logs, malformed trailing pixels and approval flags.

The 4K option is **prospective test infrastructure only**. Synthetic 3840×2160 pixel fixtures prove bounded parsing and geometry rejection, not that any Windows executable emitted 4K, a physical monitor displayed 4K, or the unapproved original art became shippable.

This verifier is deliberately narrower than #2041's full screenshot and native executable admission. It is an additional **bounded contrast discriminator** after QA has established real process/PE provenance, not an authority to certify that its untrusted local inputs truly came from a hardware renderer, that every selected/modal state is legible, or that artwork is polished. It emits `visual_approved=false`, `hardware_approved=false`, and `release_gate_credit=0` even when the pixels pass. An older pre-contrast capture is an intentional **negative fixture**; only a fresh exact integrated Windows PE after importing the new host color should pass.

## Host checkerboard contrast, source palette preserved

The real integrated Windows SDL root capture shows supporting racer text in neutral `#989898` over alternating `#303030` and `#505050` checker squares. In sRGB WCAG contrast calculations, the lighter squares give only **2.80:1**, which misses the ordinary small-text 4.5:1 target, even though `#989898` reaches 4.58:1 on the darker squares. The shared Modern root now uses **`kModernMenuCheckerLegibleGrey = #C8C8C8`** exclusively for its supporting identity and disabled-route/`SOON` labels drawn directly on the checker. The neutral colour retains the lighter-than-background stock-family hierarchy and reaches **4.82:1 on #505050** (7.89:1 on #303030), rather than redesigning the colour scheme. This is an explicitly modern accessibility adjustment, **not** a claim that retail CGRAM contains this RGB step. Original sprite/font source export data, all true source palettes, Authentic mode and game logic are untouched. The selected yellow text, white normal destinations, blue focus and already-contrasting title remain unchanged.

The native root painter regression records both actual text and colour callback values for the racer identity and disabled controls. It is not enough to establish the final on-device perceptual contrast: the integration rehearsal must recapture both 4:3 and 16:9 post-composition SDL pixels at an exact new Windows PE hash, while independent QA/human review checks character readability and faithful identity. Provenance: [integrated Windows SDL capture run 39518329126](https://github.com/gamesbyian/UR-Recomp/actions/runs/39518329126), comparison artifact `12311075191`. No release/accessibility certification is claimed without that recapture.

## Three native presentation defects corrected from independent QA

Independent QA identified three **reproducible** player-facing defects in the original shared root, not theoretical design concerns:

- **4:3 / 640×480:** with the stock anonymous rider, the 240px panel silently printed `RACER: STOCK RACER - NO PROF`. The semantic state is now shown as `RACER: NO PROFILE`. Long real profile names retain their distinguishable prefix but acquire an explicit `...` rather than pretending a truncated name is complete. Ordinary short names and the first-racer creation prompt are unchanged.
- **Modern 16:9 / 320px root panel:** the existing right-side detail starts at logical x+193, leaving a real 13-cell text budget. The previously drawn single line `TOUR AND CONTINUE` appeared as `TOUR AND CONT` in actual 1280×720 / 1024×768 Windows SDL pixels, and other destinations had equivalent risks. All five contexts now use two deliberately authored lines: **TOUR AND / CONTINUE**, **CHOOSE A / COURSE**, **LOCAL / TWO PLAYER**, **RUNS AND / BEST TIMES**, **DISPLAY AND / CONTROLS**. Disabled destinations render **NOT YET / AVAILABLE**. None is abbreviated in the 13-cell budget; the narrow one-column composition still uses its full single-line context. The preexisting `CONTINUE READY` status and route authority are unchanged.
- **Unavailable racer shortcut footer:** some valid racer/profile states have no Create/Add/Switch binding and the host correctly passes `racer_shortcuts_available=false`. The shared root falsely displayed `RACER SETUP NOT YET LINKED`, a temporary engineering message that reads as a broken feature. The no-shortcut default now deliberately paints **no footer text**, preserving the already visible racer identity and `A/ENTER SELECT  B/ESC QUIT` navigation legend. Real status/error messages and available shortcuts still take priority; no new button or execution capability is invented.

Evidence: independent QA [native 4:3 screenshot run 39411639620](https://github.com/gamesbyian/UR-Recomp/actions/runs/39411639620) and compiled four-PR [SDL capture artifact 12291806851](https://github.com/gamesbyian/UR-Recomp/actions/runs/39481197322/artifacts/12291806851). The updated `tests/native/modern_root_overlay_presenter_test.cpp` now checks every destination at the **real 320px root width**, anonymous status at 240px, long-name ellipsis, disabled preview semantics, exact 8px-cell framebuffer bounds at both widths, and absence of false or empty racer-footer draws. Tests are ROM-free exact presenter calls; **they are not fresh SDL output**. The integration rehearsal [draft #2053](https://github.com/gamesbyian/UR-Recomp/pull/2053) must cherry-pick these small shared-root changes and recapture the actual Windows output on its newly combined head before this is considered visually closed. No image/Authentic/hardware approval is implied.

## Verification and explicit approval boundary

`tests/native/modern_menu_visual_grammar_test.cpp` compiles against the **actual shared C++ header** and asserts native source palette constants, all 39 scroll positions, 32-frame tile cycle, eased movement, logical geometries, raster clipping and sampled focus/checker pixels. Its `tests/unit/test_modern_menu_visual_grammar_cpp.py` runner uses C++17 pedantic warnings-as-errors and asserts the **native shipping root presenter** consumes the new helpers; existing `test_modern_root_overlay_presenter.py` exercises the actual linked presenter for both stock and wide host rectangles. A green ROM-free fixture proves code/raster contract only.

**Still open for screen/art/QA owners:** execution of the existing source-bound 16×16 font and newly added 8×16/cursor/BG1 atlas exporters against real original captures, artwork licensing and the actual native consumption/rendering of those verified pixels, source-faithful approved racer art, reduced-motion policy wired to the host, title and modal composition, final contrasting grey checker choice, original/Modern region split, real transition/SFX hookup, 4:3 and 16:9 output screenshots of the **packaged native Windows game**, motion/selection frames, 1×/4× density, real controller/keyboard, and a separate untouched Authentic capture. Source-only synthetic pixel tests are **not packaged-game screenshots** and grant no graphics/QA or human visual sign-off.

Coordinate integration by having each screen owner use this header, preserve current product models and submit its own screen screenshots/approval ledger; only the shared visual-grammar owner edits these common visual tokens in this PR.

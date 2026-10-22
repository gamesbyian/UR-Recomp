# Modern UI accessibility primitives and visual diagnostics

Shared infrastructure only. Screen compositions, artwork and Authentic remain with their owners ([grammar](MODERN-MENU-SHARED-VISUAL-GRAMMAR.md), [fidelity gate](MODERN-UI-VISUAL-FIDELITY.md), [acceptance](MODERN-VISUAL-ACCEPTANCE.md)). Nothing here is human art approval, physical-display acceptance or original parity.

## Native primitives: `native/product/modern_ui_access.hpp`

Presentation-only (no SDL, input routing, profile or guest state); test: `tests/native/modern_ui_access_test.cpp`.

| Primitive | Contract |
|---|---|
| `modern_ui_contrast_x100`, `modern_ui_text_legible[_on_all]` | WCAG luminance/contrast on literal RGB; 4.50 text, 3.00 indicator floors. Pins the measured stock-grey 2.80:1 failure on the bright checker cell. |
| `modern_ui_focus_geometry` | Leading bar plus 1-logical-px outline; focus never relies on colour or the spinning cursor alone. |
| `modern_ui_title_safe` / `modern_ui_action_safe` | 5% / 2.5% insets (min 8px horizontally) for 342×224 and 256×224. |
| `modern_ui_integer_scale` | Integer overlay *density* on a surface, centred (720p→3×, 1080p→4×, 2160p→9×; 1024×768 4:3→3×). Not the final window mapping — see below. |
| `modern_ui_motion_frame` | Reduced motion resolves to the settled frame. |
| `modern_ui_next_enabled`, `modern_ui_may_activate` | Disabled rows stay visible with a reason, are skipped by navigation, refuse activation; inconsistent rows fail closed. |

## Capture diagnostics (final-SDL RGB_ALPHA P7)

`tools/qa_modern_visual_diagnostics.py` offers `clip`, `focus`, `contrast` (per-text-pixel local background), `compare` (undo the output mapping, require uniform block interiors, diff logical pixels across resolutions) and `detect` (which native logical width, 256 or 342, explains a frame). **Output mapping:** the shipped final-SDL path fits the logical canvas to the window with the 7:6 pixel aspect and nearest sampling, so blocks are fractional (342×224→1280×720 is ≈3.74×3.21 px per logical pixel). `--mode fit --par 7/6` (default) models that, verified on a real committed capture (true logical width: 0% non-uniform block interiors; a wrong width: several percent); `--mode integer` models whole-number density. `tools/qa_modern_visual_report.py` runs a JSON manifest and writes aggregate JSON plus a Markdown `$GITHUB_STEP_SUMMARY` table; missing, mis-hashed or malformed frames are `incomplete`, never `pass`. Pin each frame with `expect_sha256` from the independently qualified native run.

## Production-painter layout harness

`tests/native/modern_root_layout_dump.cpp` (run by `tests/unit/test_modern_root_legibility_audit.py`) renders the **real** root, native-destination and pause presenters at the 256 and 342 native logical widths, source-over blending their actual fill alphas. Text is a conservative solid glyph box per 8×8 cell (the real font lives in the external framework), so it verifies geometry and exact colours, never glyph art. `--audit` measures every text draw against the worst pixel already under its cells with `modern_ui_contrast_x100`, and also fails text outside the action-safe region or overlapping other live text (near-opaque panels mask text beneath them).

Policy encoded: body text and focused rows 4.5:1; intentionally dimmed unavailable pause rows and their `SOON` tag are disabled controls held to 3:1. Findings it already drove: root-modal supporting copy at 3.17/4.44:1 and focused unavailable pause rows at 1.76:1 (fixed, #2209). Rule of thumb for screen owners: never use the source-measured `secondary_grey` (#989898) for body text over a checker or translucent panel; use `kModernMenuCheckerLegibleGrey`. Destination presenter supporting copy (4.44–4.46:1) is reported to its owner on #2167.

Reduced motion resolves in `native/product/modern_reduced_motion_preference.hpp`: explicit `UR_REDUCED_MOTION=1|0` wins, otherwise the Windows "show animations" setting decides.

# Modern UI accessibility primitives and visual diagnostics

Shared infrastructure only. Screen compositions, artwork and Authentic remain with their owners ([grammar](MODERN-MENU-SHARED-VISUAL-GRAMMAR.md), [fidelity gate](MODERN-UI-VISUAL-FIDELITY.md), [acceptance](MODERN-VISUAL-ACCEPTANCE.md)). Nothing here is human art approval, physical-display acceptance or original parity.

## Native primitives: `native/product/modern_ui_access.hpp`

Presentation-only (no SDL, input routing, profile or guest state); test: `tests/native/modern_ui_access_test.cpp`.

| Primitive | Contract |
|---|---|
| `modern_ui_contrast_x100`, `modern_ui_text_legible[_on_all]` | WCAG luminance/contrast on literal RGB; 4.50 text, 3.00 indicator floors. Pins the measured stock-grey 2.80:1 failure on the bright checker cell. |
| `modern_ui_focus_geometry` | Leading bar plus 1-logical-px outline; focus never relies on colour or the spinning cursor alone. |
| `modern_ui_title_safe` / `modern_ui_action_safe` | 5% / 2.5% insets (min 8px horizontally) for 342×224 and 256×224. |
| `modern_ui_integer_scale` | Largest whole scale, centred letterbox (720p→3×, 1080p→4×, 2160p→9×; 1024×768 4:3→3×). |
| `modern_ui_motion_frame` | Reduced motion resolves to the settled frame. |
| `modern_ui_next_enabled`, `modern_ui_may_activate` | Disabled rows stay visible with a reason, are skipped by navigation, refuse activation; inconsistent rows fail closed. |

## Capture diagnostics (final-SDL RGB_ALPHA P7)

`tools/qa_modern_visual_diagnostics.py` mirrors the scale and safe-area formulas and offers `clip`, `focus`, `contrast` (per-text-pixel local background) and `compare` (undo integer scale/letterbox, require uniform blocks, diff logical pixels across resolutions). `tools/qa_modern_visual_report.py` runs a JSON manifest and writes aggregate JSON plus a Markdown `$GITHUB_STEP_SUMMARY` table; missing, mis-hashed or malformed frames are `incomplete`, never `pass`. Pin each frame with `expect_sha256` from the independently qualified native run.

# Windows Modern tour progress overview

Status: stacked follow-on to the Quick Practice picker (PR #734). Pending native acceptance and merge.

## Player-facing scope

At the settled Modern one-player main menu, **F7** or the live mapped **P1 L** semantic control opens a compact tour overview. Escape/F7, mapped P1 A/B/Start/L, or Enter closes it. The first-run F1 Help surface includes the shortcut. No stock guest cursor or progression bytes are modified, and Authentic ignores the surface.

The panel shows **all eight ordinary tour slots** in catalog order. Names and medal status are displayed only for tours admitted by the per-rider stock unlock tier. Locked slots are labeled generically `LOCKED TOUR`. Hunter and its medal, route, and eligibility never appear in the panel. The summary counts how many of those eight ordinary tours have at least Bronze/Silver/Gold medals, using read-only SRAM values.

## Authority

`native/title/uniracers_tour_progress_overview.hpp` projects the stock medal cells at `0x069C + 16*tour_option + rider` and reuses the title-owned `stock_practice_tour_option_mask` decoder introduced by the Practice picker. The identity and tier check therefore have one authority, including the clean-save selected-rider sentinel fallback and its zero-unlock safeguard. Eight ordinary course names are supplied by the canonical `quick_practice_catalog.hpp`. The presenter does not expose locked names, read the secret Hunter medal or update unlocks, SRAM, host profiles, race routing or replay state.

The host surface is exclusive during display and consumes keyboard/semantic-controller edges through the existing host-input release latch. It takes a read-only snapshot on open and closes automatically if the profile, mode, menu or race context changes. Rendering uses the existing 1x–4x Modern modal density/layout rule.

## Acceptance

- Strict C++17 unit acceptance proves four-, six-, and eight-tour visibility; all three stock medal tiers; no Hunter disclosure; clean-save fallback; and rejection of invalid SRAM, profile/rider mismatch, and malformed medal values.
- `tests/native/run_modern_tour_overview_acceptance.sh`, called by the existing independent Modern native acceptance shard, opens the real F7 modal on fresh-process clean SRAM, proves it is drawn, closes without racing, progressing or autosaving, and verifies Authentic mode is inert.
- Controller entry uses the live GamepadMap's semantic P1 L control rather than a hard-coded physical controller map; its source contract and user documentation accompany this slice.

This is a read-only frontend completion slice. It must not be conflated with speculative direct challenge-tier selection, Hunter discovery, Records aggregation, or pause presentation.


## Initial stock-derived visual hierarchy

The read-only Tour Progress screen now reuses a host-only source-measured palette from `analysis/generated/menu-visual-language.json` through `modern_stock_menu_palette.hpp`, shared with Quick Practice. Its header uses yellow stock title hierarchy and a dark offset; the read-only Bronze/Silver/Gold summary stays grey. Admitted tour rows are legible yellow, and unrevealed tours remain dimmed generic `LOCKED TOUR` labels. Because this panel does not select a tour, it deliberately does **not** draw a fake blue stock selection arrow. No medal tier, stock menu input or name/visibility policy changes.

At a 256-pixel 4:3 logical view, the modal stays 240 pixels wide. At widened Modern views it may expand up to 324 logical pixels, allowing complete tour names and medal summaries without horizontally stretching glyphs. The 13-character title uses 16-pixel logical glyph pitch where it fits, falling back to 8 pixels on narrow layouts. All dynamic summary/row/footer copy is clipped to the panel's actual glyph-cell budget, before the independent 1x–4x internal presentation-density transform.

This is a **first visual-hierarchy improvement**, not final art acceptance: the host still draws provisional ASCII glyph shapes instead of the recovered ROM BG2 title font, and no original arrow animation is grafted into this read-only surface. The native Tour Overview admission/exit acceptance and Authentic invariance remain authoritative for behavior; packaged-Windows screenshots and comparison with the stock menu remain the artistic release gate.

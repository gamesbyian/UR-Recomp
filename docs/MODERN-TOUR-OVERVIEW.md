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

## First stock-derived visual treatment

The player-facing Tour Progress panel now inherits the measured source menu's visual hierarchy. It uses the stock BG2 title-yellow role (#F8F800) at 16-pixel logical pitch where space allows, the documented grey data role (#989898), a dark offset under the heading, and a subdued section divider. Earned-medal rows use the title-yellow highlight, while unavailable and not-yet-started rows remain grey. The underlying raster glyphs and static frame remain provisional host artwork; the final original-derived font, movement and background treatment still require native screenshot/art-direction review.

At the ordinary 256px 4:3 logical width the modal stays 240px wide, retaining its original eight-row footprint and 1x–4x presentation density. Modern widened views can allocate up to 324 logical pixels for name and medal columns. The row formatter aligns medal labels to the right edge and shortens tour names before medal status rather than clipping or overwriting adjacent UI. Locked slots are formatted without consuming their hidden catalog names or medal tiers, preserving the existing Hunter and unlock policy. The strict C++ style test covers narrow/4:3/wide layouts, palette tokens, the eight-row vertical fit, earned/not-started status alignment, and suppression of locked names.

This is a presentation-only change. Tour eligibility, medal counts, stock SRAM, source profile identity, keyboard/controller entry, and Authentic mode remain under their existing authorities.

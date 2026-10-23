# Uniracers Windows Visual Atlas: approved visual concepts

**Date:** 2026-10-23 · **Purpose:** art direction and layout targets for `tools/visual_atlas_web/`.

These are the **four full-resolution, owner-selected revised concept images**, preserved as Git binary PNGs. The images were generated using user-provided Uniracers title/menu/gameplay/promotional references and the in-house pen-and-graph-paper architectural artwork. They are **design studies**, not native Windows captures, not verified reproductions of any particular route, and not a statement of canonical original game assets. They must never enter the capture intake pipeline, release ledger, or `analysis/windows-visual-atlas.json` as `captured`.

| View | Full-resolution artwork | Key UI objective |
|---|---|---|
| Desktop browsing | [2026-10-23-desktop-gallery.png](2026-10-23-desktop-gallery.png) | Search, presentation/family/status/evidence filters, source distinction, responsive gallery/list, direct agent copy |
| Desktop inspection | [2026-10-23-desktop-detail.png](2026-10-23-desktop-detail.png) | Large truthful pixels, receipt/source context, copyable stable ID, previous/next, source links |
| Mobile browsing | [2026-10-23-mobile-gallery.png](2026-10-23-mobile-gallery.png) | One-handed mobile search, compact genuine capture cards, filters, multi-reference clipboard action |
| Mobile inspection | [2026-10-23-mobile-detail.png](2026-10-23-mobile-detail.png) | Big fit/1:1 screenshot, first-class copy reference, semantic evidence distinction, keyboard/touch navigation |

## Translation rules

1. Keep **fine ink drafting and graph-paper texture as the identity**. Use a modest CSS grid, ruled borders, crop corners, hatching and an SVG drafting doodle. Real screenshots must not be painterly filtered or resampled in the actual 1:1 inspection view.
2. The colorful Uniracers wordmark and SNES-yellow chunky italic text are accents, not the primary body font. The mobile header is intentionally compact.
3. The decorative track must be a **genuinely cylindrical broad-banded Uniracers tube** with a physically contacting wheel atop it, not a rainbow ribbon or a floating wheel. `tools/visual_atlas_web/tube-header.svg` is a lightweight first production interpretation.
4. Favor truthful functionality over exact concept-art control labels. Existing catalog IDs are **`URV-*`**, not `URA-WIN-*` shown in some concepts. A generated image's sample entry, screenshots, status, capture counts, alternate crops, game scenes or annotations can be *fictional*. They are not evidence of existing product surfaces or implemented features.
5. Only show working `Copy ref`, `Copy link`, source link, filters, list/grid, current-image 1:1, next/previous and multi-copy controls. Don't add inert `Open route`, `Compare`, synthetic image carousels or `Capture now` controls without a real verified route/implementation.
6. Keep handwritten notes useful and few: **“Real frames, not guesses”**, **“Copy ID, brief agent”**, **“Original · Modern · QA”**. No generic slogans or claims of an approved build.
7. Preserve the original PNGs here as the review authority, not as runtime website assets. Production frontend remains simple CSS/JS and one small SVG, while the assembler copies existing in-house graph-paper plates for `COMING SOON`.

See [the mobile-first visual implementation contract](../../../docs/atlas/MOBILE-FIRST-VISUAL-IMPLEMENTATION.md) for tokens, breakpoints, interactions, regression checks, and future features.

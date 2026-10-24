# Windows Visual Atlas: mobile-first visual implementation contract
**Created:** 2026-10-23 · **Companion:** [Windows Visual Atlas](../WINDOWS-VISUAL-ATLAS.md) · **Owner:** visual atlas frontend only

## Purpose and source truth
Build the small static atlas that a remaster developer actually uses on a phone: locate a game surface, confirm whether there is a genuine Windows capture, inspect the correct pixels, copy a source-bound stable reference to an agent, and optionally inspect the owning original UI fixture or native capture route. The static assembler in `tools/windows_visual_atlas.py` owns data, status and screenshot provenance. The viewer never simulates implementation evidence.

Four revised, owner-reviewed concept views inform the target composition: desktop gallery, desktop inspection, mobile gallery, mobile inspection. These are **design references, not literal screen data, not authentic Windows captures, and not evidence of implemented buttons**. Sample case names, capture counts, screenshot labels, and additional features depicted by image-generation may be illustrative or factually wrong. The real catalogue currently has `URV-*` IDs; **do not silently rename them to the fictional `URA-WIN-*` shown in illustrations**.

## Visual direction: original department, 2026
The primary identity is **fine black pen + graph-paper architectural drawings**, not a traditional SNES-game skin. Build decoration as economical CSS/SVG, retaining generous space for actual screenshots. The original-game flavor is a highlight: chunky italic yellow titles with narrow ink outline and offset shade, cobalt-blue selection, warm red alerts, a blue/purple/pink/yellow/orange/red wordmark, yellow arrow tabs, hand-drawn scribble accents and tiny pencil construction marks. No animated mascot, faux load screen, giant marketing hero, textured raster backing every card, or heavyweight font download.

Palette/tokens (approximate, contrast to be rechecked in-browser): warm drafting paper `#faf8ef`, faint minor grid `#e9e5d8`, major grid `#d0cabb`, strong graphite `#202329`, ink-blue `#24537e`, SNES yellow `#f5da36`, sky-blue `#9de0f7`, pink `#f9b1d8`, green `#b4edbc`, warning coral `#ffc3ab`, planned violet `#e5d5fa`. Keep **semantic state labeling in text**, not solely color. Drafting texture: 8px minor and 40px major CSS gradients, light enough not to interfere with pixel inspection. Brackets, crop crosshairs, ruled section lines and hand-drawn hatching are subtle additive decoration, never behind the image when viewing native pixels.

### Critical geometry and illustration
A decorative header-only unicycle rides **on top of a genuinely cylindrical, broad-banded Uniracers tube**, with visible rounded edges, cross-section, highlight, shading, support posts and correct wheel-to-tube contact/tangent. It is **not** a rainbow ribbon or a wheel floating beside a tube. Keep illustration a small SVG; use no large binary asset for production. On narrow phones crop/hide decorative portions rather than steal room from search or screenshots. Fine graph-paper technical ink marks remain throughout.

Use small, relevant editorial notes only where there is room: `Real frames, not guesses`, `Copy ID, brief agent`, `Pixels have receipts`, `Original / Modern / QA`. No general slogans, generic lore, false authority, or invented project features. Keep these optional and hidden when space or assistive technology makes them distracting.

## Information architecture: current feature to design element
| Underlying actual capability | Visible UI and interaction | Grounding |
| --- | --- | --- |
| `atlas.json` with 199 stable IDs (subject to changes) | Searchable cards + filtered count + stable ID headline | Never assume the number in concept art |
| `mode`, `family`, `state`, `display` | Presentation and surface-family filters; description labels | Existing manifest fields |
| `captured`, `capture_pending`, `capture_failed`, `planned` | Strong distinct status ribbons: REAL CAPTURE / PENDING / FAILED / COMING SOON | Derived by assembler only |
| `source_inventory` | Original UI or Modern QA provenance category, linked to a source file | Distinct from current Windows capture evidence |
| `evidence` with source/EXE/PNG hashes | Explicit native Windows SDL evidence type, expandable receipt on detail | No visual/hardware release approval implied |
| Source routes in `entry.capture` and referenced manifest paths | `View source` URL to owning driver or source inventory, only if known | Never invent an executable launch / route action |
| Stable `#URV-*` hash | Copy link, copy full agent reference, browser back and forward | Existing link contract |
| Real PNG + graph-paper `assets` fallback | Pixel-faithful image / clearly labeled artist plate; never mix | No mock screenshot admitted as actual |
| Same surface, multiple screenshot candidates | Currently one selected capture; other captures require data schema extension | Do not show fake thumbnail count |
| Batch agent handoff | Checkbox select multiple IDs, copied references; sticky mobile control | New client-only UI, no backend storage |
| Exact image inspection | Mobile fit, desktop zoom 1:1, swipe and next/previous, image origin/geometry | No interpolation in native 1:1 mode |

## Responsive component inventory
**Phone-first at 360–430 CSS pixels / portrait:** small two-line wordmark and compact tube corner accent, no permanent sidebar; search and `Gallery/List` switch stay visible. Primary filters follow beneath in a flexible two-column arrangement or horizontally scrolling row; no forced horizontal viewport overflow. Result tally and clear-filters control present. Default view is legible, **single-column side-by-side thumbnail/list** with ID, title, exact evidence/status labels, and 44–48px tap targets; gallery grid optional for scanning thumbnails. Primary per-card action: click thumbnail/heading to open detail; `Copy ref` available without opening. Selection checkboxes and a sticky bottom `Copy N references` action appear only when selections exist, without hiding essential content. Respect safe-area insets, keyboard opening and reduced motion.

**Detail view on phone:** full-height modal/sheet with persistent close/back, one large image stage sized to available screen, source vs editorial label above it, title/ID and `Copy agent ref` above any secondary metadata. View 1:1 is an explicit scrollable state with no image resizing. Previous/next via 44px controls, arrow keys and horizontal swipe *only in fit mode*. Below: bounded relevant dimensions/route/provenance, source link where available, exact SHA in collapsible receipt. Note that original/UI or QA source anchors are not real screenshot captures.

**Tablet/desktop:** header art at upper right, optional slim visual legend rather than duplicate permanent filters, gallery uses 2–4 columns depending on available width; detail uses a two-column image/details arrangement. No need for marketing pages or extra application navigation. The drawing frame is ornamental; screenshot is presented as source pixels and must not be recolored/sketched by CSS.

## Implementation, in order
1. **Preserve the concepts:** `design/visual-atlas/mockups/` contains a manifest mapping each approved picture to the target UI state, a disclaimer about illustrative content and source image provenance; prefer original-resolution reference binaries if safe/available, with compressed web previews separately.
2. **Style foundation:** implement paper grid, ink line weights, visual tokens, accessible 44px controls, vector tube/wheel masthead and compact faithful retro wordmark. Make mobile layout the base CSS; desktop only through progressive `min-width` media rules. Prefer system font stack with heavy italic typography and ink outlines; inspect actual output before adding any third-party font.
3. **Functional gallery:** preserve catalog-driven statuses, implement evidence filter, ID/title search, sorting and list/grid toggle; add source-grounded category chips and genuine conditional `View source` link. Quick copy remains first class.
4. **Mobile inspection:** modal with source-bound image and 1:1 pixels, hash deep links, next/prev, copy exact agent text, meaningful original-ui or QA source-context section. Never show `Open route` unless a real route/source exists; URL targets open GitHub source, not the game.
5. **Agent selection:** batch select IDs, small sticky action bar only when populated, copy multiline references, clear selection. No private storage or hidden analytics.
6. **Responsive, accessibility and efficiency QA:** CSS/HTML/JS syntax, 320/360/393/430/768/1024/1440 px screenshots, no horizontal overflow, legible type, contrast, focus and native keyboard, reduced-motion, screen-reader names, clipboard fallback, offline-static served via HTTP, deep-link on reload, capture-not-approved disclaimers. Reuse cheap ROM-free atlas CI. **Do not run Windows AOT just to style the website**.
7. **Later only if data supports it:** screenshot-version tray, raw-vs-approved comparison, ROI annotations and copyable ROI codes, real sorting by capture time, provenance-rich crop comparison, capture failure drilldown. Those need real schema + verified screenshot data and must not be decorative buttons.

## Acceptance test for first implementation
- On a 393px phone, at least one real/candidate/planned card is visible without opening a menu; search, all 4 filters and copy ref work; a planned card is plainly **not a real screenshot**.
- No horizontal overflow on 320–430 px. 44px or larger interactive controls; pointer/touch/keyboard + Escape work; opening hash keeps focus and closing returns focus.
- Native Windows captures retain exact PNG pixel bytes at 1:1; no cosmetic overlay obscures critical HUD content.
- Every listed category and status is true of the same underlying `atlas.json` entry; mismatched source anchors cannot claim Windows SDL identity.
- With 199 manifest entries and zero captured images, UI remains useful, honest and attractive with sparse binary assets and no network frameworks.
- Publishing a revised UI does not perturb capture jobs, release gates, or native renderer files.

## Hand-off
This is design implementation on the **same atlas PR** (#2385) while that PR is open, not a competing capture/recomp branch. Avoid touching the Windows gameplay, production menu code, native acceptance matrix, archive intake or release ledger. Record a gallery thumbnail and screenshot detail from real browser validation when available; a generated concept image is not an implementation screenshot.

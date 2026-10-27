# Canonical promotional and screenshot-atlas artwork (owner decision, 2026-10-26)

These six owner-uploaded PNGs are the **only approved art family** for promotional video backgrounds/cards and noncaptured ("Coming Soon") Windows Screenshot Atlas slots. They were relocated losslessly from the repository root (Git blob SHA preserved).

| Purpose | Canonical file |
|---|---|
| Promo background 16:9, logo left | `blueprint-16x9-logo-left.png` |
| Promo background 16:9, logo right | `blueprint-16x9-logo-right.png` |
| Promo background 4:3, logo left | `blueprint-4x3-logo-left.png` |
| Promo background 4:3, logo right | `blueprint-4x3-logo-right.png` |
| Atlas unavailable screenshot, 16:9 | `atlas-coming-soon-16x9.png` |
| Atlas unavailable screenshot, 4:3 | `atlas-coming-soon-4x3.png` |

**Hard replacement:** Stop consuming all previously generated video card designs/backgrounds and all formerly generated atlas placeholders. Do not use `media/showcase/2026-10-20/graphpaper-final/cards/` for new video output or atlas placeholders. Historical files may remain as provenance, but they are obsolete, not alternate selections or fallbacks.

Video generation should compose footage, motion, dimensions, credits and recruitment copy over the appropriate approved clean blueprint file. Use the matching aspect ratio, and choose either approved left/right logo placement to avoid overlaps. Do not mutate source art. New promo videos should not inherit historical card textures or generated framing art.

Atlas generation MUST use the dedicated `atlas-coming-soon-*.png` by target aspect ratio for uncaptured and pending slots. Real source-verified Windows screenshots continue to supersede the placeholder only when captured according to the existing evidence contract. Preserve distinctions between planned, pending, failed and genuine captures. Do not label this illustration as a capture.

All asset selection and future artwork edits must respect this owner directive; any different card or placeholder family requires subsequent explicit owner approval.

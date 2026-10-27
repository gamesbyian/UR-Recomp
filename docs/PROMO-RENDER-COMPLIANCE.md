# Promotional video background compliance (2026-10-26)

**Owner's binding directive:** only the owner-uploaded canonical plates under `assets/promo/canonical` may be used for promotional video backgrounds. Portrait videos require `blueprint-9x16-portrait-2160x3840.png` exclusively. 16:9 and 4:3 videos use the matching approved left/right plates. Screenshot Atlas placeholders use only `atlas-coming-soon-*.png`. Never resurrect archived generated cards, blue/graph-paper procedural panels, dark/blurred mattes, or landscape-card crops as portrait backgrounds.

## Audited video entrypoints

| Script | Enforcement |
| --- | --- |
| `tools/showcase/graph_paper_trailer_art_direction.py` | Emits only approved plates, preserving historical output basenames; see merged #2675 |
| `tools/showcase/blue_trailer_art_direction.py` | Delegates to canonical plate exporter; old procedural blue panels retired |
| `tools/showcase/build_flagship_recruitment_20261019.py` | Canonical landscape frames and cards; complete portrait gameplay centered over exclusive portrait plate |
| `tools/showcase/upgrade_flagship_vertical_20261019.py` | Owner-approved portrait plate replaces blurred live-video matte |
| `tools/showcase/build_definitive_recruitment.py` | Canonical 16:9 CTA and approved portrait backdrops, with captured footage overlay |
| `tools/showcase/build_three_source_recruitment.py` | Canonical 16:9 CTA instead of generated black card |
| `tools/showcase/build_recruitment_teaser.py` | Portrait/wide scene templates start from approved corresponding plates; emits provenance with output hashes |
| `tools/showcase/build_continuous_recruitment_edits.py` | Uses portrait plate behind native content; refuses historical teaser inputs lacking matching approved-art receipt |

Historical rendered exports **are not retroactively approved**. Re-export from current scripts and confirm resulting video bytes/frames visually. The asset source may be scaled to delivery resolution preserving its whole composition; no arbitrary crop or new background illustration. Gameplay source remains independently evidence-verified. Text/footage compositing is allowed.

## Qualification limits

Static unit assertions prevent obvious regression but do not prove media outputs. CI must pass at the actual PR head. Full FFmpeg export acceptance needs real source clips, their provenance receipts, original soundtrack and precise dimensions/duration/frame-count verification. Use image inspection of several frames from each emitted video, especially 9:16 initial footage, transitions and final call to action, to confirm no stale cards or blank synthetic mattes. Preserve evidence with exact source SHA and output SHA; do not declare certification on static tests alone.

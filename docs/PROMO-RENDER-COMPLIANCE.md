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
| `tools/showcase/build_graphpaper_recruitment_20261020.py` | Legacy filename adapter delegates to current canonical exporter, blocks checkouts without approved portrait-art attestation; no original sketch JPEGs |
| `tools/showcase/build_flagship_dynamic_course_v2.py` | Intentionally retired with explicit error: its pinned historical 85s film bakes in disallowed generated cards |

Historical rendered exports **are not retroactively approved**. Re-export from current scripts and confirm resulting video bytes/frames visually. The asset source may be scaled to delivery resolution preserving its whole composition; no arbitrary crop or new background illustration. Gameplay source remains independently evidence-verified. Text/footage compositing is allowed.

## Qualification evidence and remaining limits (2026-10-27)

- Main integrated: [canonical exporter PR #2685](https://github.com/gamesbyian/UR-Recomp/pull/2685), [historical escape hatch retirement PR #2690](https://github.com/gamesbyian/UR-Recomp/pull/2690).
- Actual three-format (16:9, 4:3, 9:16) FFmpeg encode/readback smoke with real approved images, 6 frames per format and background-pixel comparison passed: [Actions run 40463248002](https://github.com/gamesbyian/UR-Recomp/actions/runs/40463248002).
- **First 80s/27s full encode was REJECTED after pixel inspection:** [run 40463247963](https://github.com/gamesbyian/UR-Recomp/actions/runs/40463247963) satisfied checksums and frame counts but the portrait CTA was incorrectly scaled to 1080×608 and padded dark. [Review run 40464854127](https://github.com/gamesbyian/UR-Recomp/actions/runs/40464854127) measured corner differences over 241 RGB levels. **Do not distribute its artifact as an approved export.**
- **Corrected complete source-pinned films:** [full encode run 40465519774](https://github.com/gamesbyian/UR-Recomp/actions/runs/40465519774), [corrected 80s landscape + 27s portrait MP4s and receipt](https://github.com/gamesbyian/UR-Recomp/actions/runs/40465519774/artifacts/12715888532). Verified 1920×1080/4,800 frames and 1080×1920/1,620 frames at 60 fps with source and output checksum matching.
- **Independent final MP4 pixel audit PASSED:** [frame review run 40466182743](https://github.com/gamesbyian/UR-Recomp/actions/runs/40466182743), [decoded PNG previews and measured pixel regions](https://github.com/gamesbyian/UR-Recomp/actions/runs/40466182743/artifacts/12716776319). Seven representative samples from actual compressed videos checked 16:9 card/CTA and 9:16 title/multiple CTA times against corresponding approved source pixels. Full-frame letterboxing was eliminated in [fix PR #2694](https://github.com/gamesbyian/UR-Recomp/pull/2694); required dark ink text and owner-provided contact are now applied as video overlays rather than changing canonical PNGs.
- Project tooling tests and repository hygiene passed on the complete-export PR head; the historical legacy retirement PR also passed those checks and the FFmpeg smoke.

**Limits:** The corrected 80s and 27s MP4s were encoded and independently pixel-sampled against actual artwork, but a human did not watch every frame in a media player. Other historical exporters have source/static regression and aspect-smoke coverage, not individual full-length release-quality exports. Source claims and gameplay parity remain governed by their independent receipts, not this aesthetic-policy audit. A future new media export needs inspection of sampled initial, transition, CTA and ending frames, preserving exact source and output hashes. Archived older MP4s do not become compliant retroactively.

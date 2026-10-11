# UR-Recomp: verified original sprite and 4× Remastered art showcase

**Classification: editorial, evidence-backed motion graphics.** These clips are not continuous native gameplay or an assertion that 342-wide Remastered rider compositing is shipping-ready. The source art is real and the Remastered poses are shipping-approved for their exact guarded first-family registrations. Camera motion, editorial playback timing, typography and crops belong solely to this showcase.

## Watch / handoff to recruitment-trailer assembly

| MP4 | Dimensions | Nominal FPS | Frames | Duration | Claim |
| --- | --- | --- | ---: | ---: | --- |
| `01-original-4x-remastered.mp4` | 1920×1080 | 30 | 210 | 7.000 s | One actual first-family racer pose, raw ROM source → exact nearest 4× → approved procedural 4× authored art |
| `02-animation-archaeology.mp4` | 1920×1080 | 30 | 210 | 7.000 s | Reconstructed original 1205–1220 ordered P1 pose strip plus matching approved 4× editorial animation |
| `03-remaster-progress.mp4` | 1920×1080 | 30 | 150 | 5.000 s | Approved original/4× racer art, showing both verified P1-red and P2-blue palette families |

All three are silent H.264 8-bit yuv420p with faststart. They are standalone editorial inserts, **not** a master recruitment-trailer edit.

The source assets are alongside the videos in `stock/` and `authored/`, with individual source manifests `inputs-p1.json` and `inputs-p2.json`, contact sheets named `<video-stem>-contact-sheet.png`, `provenance.json` and SHA256SUMS. Contact sheets are for editorial visual review, not a substitute for watching the actual video.

## Genuine source and approval

- Canonical USA ROM SHA-256: `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`.
- Original stock extraction: `tools/prototype_racer_hd_replacement.py::build_stock_rgba` uses exact registered composition with `tools/extract_racer_presentation_family.py` to reconstruct transparent 64×64 RGBA from ROM graphics and palette data.
- Exact semantic order: `analysis/data/racer-hd-replacement-prototype.json::motion_review_sequence.frames`, guest frames **1205–1220**, P1 and P2.
- Authored output: `tools/build_racer_hd_asset_dossier.py::authored_candidate_rgba_for_entry` mirrors the versioned procedural 4× implementation in `native/presentation/racer_hd_presenter.hpp`. It emits 256×256 RGBA.
- Art approval: `analysis/data/racer-hd-art-approval.json`, native approval review run **37248763308**, artifact **11319814239**, with exact `reviewed_authored_rgba_sha256` values. Other existing approval ledgers are discovered and checked by the tooling but this finished showcase is the retained first ordinary-race family only.
- Authored registration aliases are allowed **only** if the actual player, exact ROM-composed stock RGBA, and exact authored RGBA all match the same shipping-approved pose; that proof is recorded for each guest frame in the source manifests.

Original pixel close-ups are cropped from the exact same registered source coordinates in every presentation, without shifting the pose/contact. The 64×64 source is enlarged with nearest sampling; the 256×256 approved art is sampled at its own density. These close-ups use square-pixel editorial magnification for legibility; physical SNES 7:6 pixel aspect and finished game display placement are separate presentation contracts.

## Reproduction

```bash
python3 tools/verify_rom.py reference/roms/retail/Uniracers_USA.sfc
python3 tools/showcase/art_showcase/export_approved_strip.py \
  --player p1 --output media/showcase/art-reconstruction/2026-10-10
python3 tools/showcase/art_showcase/export_approved_strip.py \
  --player p2 --output media/showcase/art-reconstruction/2026-10-10
python3 tools/showcase/art_showcase/render_approved_art.py \
  --manifest media/showcase/art-reconstruction/2026-10-10/inputs-p1.json \
  --secondary-manifest media/showcase/art-reconstruction/2026-10-10/inputs-p2.json \
  --output media/showcase/art-reconstruction/2026-10-10
```

Requires Python Pillow and FFmpeg/FFprobe. The reproducible one-shot CI workflow is `.github/workflows/art-showcase-one-shot.yml` and runs only upon changing its own workflow definition on the dedicated art branch; it does not create a recurring CI trigger. The workflow verifies complete video decoding, exact 210+210+150 frames, 30/1 fps, 1080p dimensions, accompanying sheets and SHA256 receipts before committing. See `provenance.json` for file-specific hashes and source approval references and `SHA256SUMS` for a directory-wide manifest (the checksums file excludes itself).

## Claim limits

The first-family procedural authored art is hash-approved and has bounded native fixed-scene 4× replacement acceptance. This film does not independently demonstrate moving live native HDR/4K captures, wide-source OBJ occlusion fixes, full animation-family coverage, or a shipping beta. Nothing here modifies game state, PPU sprite visibility, guest rendering, menu code, acceptance ledgers or the master trailer.

# Verified Uniracers art-showcase tooling

**Status: three completed, visually inspected 1080p MP4 clips, with exact source PNGs, approval checks, SHA256 checksums, contact sheets, and retained CI proof.**

The final videos and full per-frame asset provenance live at [the art-showcase media README](../../../media/showcase/art-reconstruction/2026-10-10/README.md). The files were produced in [successful CI run 38107987386](https://github.com/gamesbyian/UR-Recomp/actions/runs/38107987386); its temporary one-shot workflow was intentionally removed so future pushes do not trigger redundant encodes.

## Source reconstruction

`export_approved_strip.py` obtains the actual P1 or P2 pose sequence for original guest frames 1205–1220 from `analysis/data/racer-hd-replacement-prototype.json::motion_review_sequence`. It reads the canonical ROM (SHA256 `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`), uses the repository's existing deterministic original sprite compositor (`tools/prototype_racer_hd_replacement.py::build_stock_rgba`) and 4× procedural authored generator (`tools/build_racer_hd_asset_dossier.py::authored_candidate_rgba_for_entry`).

Approved art is **not** an inferred PNG library. The actual authored RGBA bytes must match a shipping decision in `analysis/data/racer-hd-art-approval*.json`. A chronological alias is admitted only through same-player identical original RGBA AND identical authored RGBA, with the approved canonical representation recorded separately from the original guard. Unknown, blocked, or changed artwork fails closed. The first family's approval source is `analysis/data/racer-hd-art-approval.json`, native review run 37248763308, artifact 11319814239.

## Reproduce

Install Pillow, FFmpeg, and FFprobe; then, from the repository root:

```bash
OUT=media/showcase/art-reconstruction/2026-10-10
python3 tools/verify_rom.py reference/roms/retail/Uniracers_USA.sfc
python3 tools/showcase/art_showcase/export_approved_strip.py --player p1 --output "$OUT"
python3 tools/showcase/art_showcase/export_approved_strip.py --player p2 --output "$OUT"
python3 tools/showcase/art_showcase/render_approved_art.py \
  --manifest "$OUT/inputs-p1.json" \
  --secondary-manifest "$OUT/inputs-p2.json" \
  --output "$OUT"
```

The editor emits exactly three silent 1920×1080 / 30 fps MP4s (210 + 210 + 150 frames) and their visual contact sheets. It verifies frame count, dimensions, frame rate, complete decode, and file SHA256, recording per-pose source and ledger hashes in `provenance.json`. Recompute `SHA256SUMS` if any output changes.

The editorial magnification uses the **same object-local crop** for both original and authored pixels; original source uses nearest-neighbor sampling, approved 4× art uses its actual density. Animation-frame order is guest-derived but motion-graphics timing is editorial. All clips explicitly say they are verified art samples, **not** continuous native gameplay.

These assets cannot certify widescreen Remastered racer admission, split-screen OBJ source visibility, full-game HD coverage, or Windows beta readiness. Guest execution, presentation renderer, gameplay and art-approval decisions remain untouched.

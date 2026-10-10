# UR-Recomp: native-capture showcase (October 10, 2026)

This folder contains **development progress reels**, not a representation of a complete Windows beta or uninterrupted gameplay capture. The short clips are assembled from original Baldosa guest/PPU raster captures collected by a GitHub Actions native execution test.

## Files

- `ur-recomp-capture-reel-20261010.mp4`: 24-second 1280×720 silent horizontal recruitment/progress reel.
- `ur-recomp-342px-comparison-20261010.mp4`: 10-second excerpt featuring the Original/wide comparison and native 2P samples.
- `ur-recomp-capture-reel-poster.png`: editorial thumbnail extracted from the comparison segment.
- `native-widescreen-source-frame-1856.png`: **unaltered RGB source pixels**, 342×224, to permit direct inspection without decoding the movie.
- `provenance.json`: source run, exact artifact ZIP hash, selected frame numbers, image identity check and output checksums.

## Evidence and limitations

- Source: [Baldosa AOT core native experiment run 38083079741](https://github.com/gamesbyian/UR-Recomp/actions/runs/38083079741), artifact `baldosa-native-spike-evidence`, ID `11681138053`.
- Original fixed `256×224` and widened `342×224` captures at guest frame **1856** agree exactly on all RGB pixels in the centered 256×224 region (wide columns 43..298).
- Both P1/P2 split and 1P frame samples are real guest-driven captures; in each sequence samples are **16 guest frames apart**, rather than a full 60fps recorded video. Editorial holds, pans/caption transitions do not simulate gameplay between samples.
- The sequences include **pre-race countdown states**. These are not claims of a complete played race, independently accepted finish outcome, Remastered-wide sprites, or an approved physical 4K output mode. Development and product integration remain under QA.
- Soundtrack is intentionally absent rather than borrowing original commercial audio or inventing a source-audio demonstration.
- Game frames may be copyrighted. Avoid separate commercial redistribution or public release without an asset-rights review.

## Rebuild

Requires Python 3, Pillow, FFmpeg with libx264, and the authentic ZIP artifact from the linked Actions run.

```bash
python3 tools/showcase/build_capture_reel.py \
  --zip /path/to/baldosa-native-spike-evidence.zip \
  --outdir media/showcase/2026-10-10
```

The upstream Actions artifact has limited retention. The resulting video, key native frame, poster and provenance are committed here so the demonstration remains inspectable after artifact expiry. A newer, uninterrupted gameplay trailer should be recorded from a tested complete player journey when the integrated Windows candidate passes that acceptance.

The film and helper are supplementary contributor communication; they do **not** change the [official release-quality ledger](../../../docs/RELEASE-QUALITY-LEDGER.json).

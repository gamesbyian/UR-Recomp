# Contributor recruitment teaser (October 10, 2026)

This subdirectory contains a short **source-capture-backed recruitment video**, a social-vertical edit, a thumbnail, and the original late native screenshot. These are **development communications**, not a Windows beta demonstration.

## Deliverables
- `ur-recomp-recruitment-teaser-20261010.mp4` — 34 seconds, 1280×720, H.264/AAC, original editorial synth score, invite for contributors.
- `ur-recomp-recruitment-short-vertical-20261010.mp4` — 18 seconds, 720×1280, H.264/AAC.
- `ur-recomp-recruitment-poster-20261010.png` — landscape poster.
- `native-late-source-frame-2208.png` — unretouched 342×224 RGB native screenshot, preserved as a source image.
- `recruitment-provenance.json` — archive identity, frame claims and file checksums.

## Provenance and limitations

Source: [Baldosa native run 38083974528](https://github.com/gamesbyian/UR-Recomp/actions/runs/38083974528), artifact `baldosa-native-spike-evidence` ID `11681865494`. The ZIP archive is verified by SHA-256 `d3146b4d28e247530985826a7d2b321de8359b611c2b379a966397f6192381ad` before building.

The image at guest frame **2208** is a genuine later two-player Original-mode capture, with the race clock roughly 0:03, after the prominent early countdown/arrow captures. It is **one real observation, not a continuous video**. The original 256×224 frame at 1856 and the central 256 pixels of the real 342×224 frame match exactly. The native route reported 2,473/2,473 matching guest CRCs, which does not certify a whole race event or a Windows beta.

Captured game frames are not interpolated or reconstructed. Sequential samples 1808–1888 are 16 frames apart. Edited scene changes and held frames are editorial. The audio is independently synthesized original promotional music, **not claimed to be original Uniracers soundtrack or in-game audio**. The clips do not establish final 4K display, completed Remastered sprite integration, original/native 45-course acceptance, or a final product candidate.

## Rebuild

Download the linked GitHub Actions artifact (while retained), and run from the repository root after installing Pillow and FFmpeg:

```bash
python3 tools/showcase/build_recruitment_teaser.py \
  --zip /path/to/baldosa-native-spike-evidence.zip \
  --outdir media/showcase/2026-10-10/recruitment
```

`recruitment-provenance.json` records all four media output SHA-256 hashes. FFmpeg encoding bytes may vary across versions. The source frames' identity and central-pixel equality checks fail closed.

## Next shot list

A genuinely broader external recruitment trailer should be captured on **one nominated, independently validated Windows candidate** with a contiguous input-to-video recording: launch → Modern root → profile/racer selection → event → 1P and P2 split-screen movement through several course sections → pause/restart → result/Records persistence across fresh process → Original/Remastered world comparison. Show graphical QA defects honestly, and reserve evidence labels for confirmed frames. Obtain rights review before broad commercial-facing asset redistribution.

This media lane has **no release QA authority**. Release status stays in `docs/RELEASE-QUALITY-LEDGER.json`.

# Contributor recruitment teaser (October 10, 2026)

This subdirectory contains both the **original sampled-frame recruitment teasers** documented below and the **new verified continuous-gameplay recruitment campaign**. All are development communications, not a Windows beta demonstration.

**Definitive source-verified recruitment films:** [58-second 1920×1080/60-fps film](definitive-film/ur-recomp-definitive-recruitment-58s-1080p.mp4) · [20-second vertical 1080×1920/60-fps short](definitive-film/ur-recomp-recruitment-vertical-20s-1080x1920.mp4) · [HUD-safe authentic gameplay poster](definitive-film/ur-recomp-recruitment-final-poster.png) · [final SHA and exact source-clip timeline](definitive-film/definitive-trailer-provenance.json) · [18 independently decoded evidence frames](definitive-film/render-review-provenance.json). An original synthesized score accompanies genuine native game recordings; editorial engineering and approved 4× artwork sequences are explicitly labeled as demonstrations, not live remastered gameplay. The vivid stock 1994 title and checkerboard menu use two authentic source segments, with the intervening black game transition omitted. The complete release limitations and reproduction command appear in [the definitive media assembly notes](DEFINITIVE-TRAILER-ASSEMBLY.md). External asset-rights/public distribution review is a separate requirement.

**Previously accepted standalone 1080p presentation sequences:** [7-second animated widescreen reveal](presentation-edits/authentic-widescreen-reveal-7s.mp4) · [5-second equal-scale Original-centre crop versus full recorded world](presentation-edits/same-capture-centre-vs-wide-5s.mp4) · [source provenance and review witnesses](presentation-edits/presentation-provenance.json). Both are edits of the same validated 600-frame continuous native source. The Original-centre view is an editorial crop, not a second independently executed 256-wide capture. [Full review and reproducibility details](REVEAL-EDITING-NOTES.md).

**Latest videos:** [41-second 1080p continuous-gameplay-led trailer](continuous-edits/ur-recomp-recruitment-continuous-20261010.mp4) · [21-second vertical short](continuous-edits/ur-recomp-recruitment-continuous-vertical-20261010.mp4) · [10-second clean 600-frame native 2P race](continuous/ur-native-2p-clean-600f.mp4). Read the [source capture evidence](continuous/README.md) and [edited-source provenance](continuous-edits/README.md). The original teaser files listed next remain as honest historical sampled-frame media.

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

## Future shot list (beyond the accepted 600-frame recording)

A genuinely broader external recruitment trailer should be captured on **one nominated, independently validated Windows candidate** with a contiguous input-to-video recording: launch → Modern root → profile/racer selection → event → 1P and P2 split-screen movement through several course sections → pause/restart → result/Records persistence across fresh process → Original/Remastered world comparison. Show graphical QA defects honestly, and reserve evidence labels for confirmed frames. Obtain rights review before broad commercial-facing asset redistribution.

This media lane has **no release QA authority**. Release status stays in `docs/RELEASE-QUALITY-LEDGER.json`.

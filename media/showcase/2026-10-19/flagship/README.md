# October 19 flagship recruitment film: native, widescreen, reconstructed

## Finished media

- **[85-second flagship trailer (1920×1080/60fps)](ur-recomp-flagship-85s-1080p.mp4)**, SHA-256 `6b5015fb83cb6e6deaebb08b8adf55f86004918f4169da7a71e73e46bc23cd9c`.
- **[27-second redesigned social trailer (1080×1920/60fps)](ur-recomp-flagship-27s-social-ambient.mp4)**, SHA-256 `da3208ab71807542abc38a5fd89e460efeb39b827fd94c883fbb25310184e4ed`. Full genuine two-player frame centered above animated blurred editorial surroundings.
- **[27-second original matte portrait cut](ur-recomp-flagship-27s-vertical.mp4)**, SHA-256 `74785eb6bef6ae7b5ee007e60fd4a421b57c1b2a2e681cca7a3e18541e9a5ade`. Exact preceding video used to author the enhanced social variant.
- **[1920×1080 source-derived poster](ur-recomp-flagship-poster.png)**, SHA-256 `af85d31667800f67ab7a2112b3e8618a5dfc12e71299be6d05120699f239475e`.
- **[Final source/video identities and shot timeline](flagship-provenance.json)**, **[exact decoded output audit](flagship-output-review.json)** and [output contact sheet](flagship-output-contact-sheet.png), plus [ambient provenance and six decoded review witnesses](flagship-social-ambient-provenance.json).

Accepted media-only [flagship encode run 39339897759](https://github.com/gamesbyian/UR-Recomp/actions/runs/39339897759) and [ambient portrait run 39341026993](https://github.com/gamesbyian/UR-Recomp/actions/runs/39341026993) both completed successfully. Each single-use workflow self-deleted after passing and publishing its source-checked output. No native game builds or release gate changes were involved.

[Detailed model-assisted visual audit and restrictions](VISUAL-REVIEW.md).


This is a **separate media-only sequel** to the previously accepted October 10 recruitment film, not an assertion of a new Windows release. The baseline target is **85 seconds of 1920×1080/60fps video plus a 27-second vertical 1080×1920/60fps social cut**.

All source video is committed to `main` and pinned by exact SHA-256 inside `tools/showcase/build_flagship_recruitment_20261019.py`. The builder fails before rendering if any media source or its exact duration/fps/dimensions change. This edit neither executes a game nor regenerates missing game footage. The original native 600-frame split-screen race contributes two disjoint excerpts: first 240 and final 360 frames; both remain contiguous and in the original recorded order, and 600 other frames are neither synthesized nor duplicated. The animated widescreen reveal reuses a previously approved editorial side-masking edit of the same underlying native session. The standalone original-versus-wide comparison remains [here](../../2026-10-10/recruitment/presentation-edits/same-capture-centre-vs-wide-5s.mp4).

## Source-locked 85s narrative

| Film time | Duration | Actual visuals | Claim boundary |
| --- | ---: | --- | --- |
| 00:00–00:03 | 3s | Genuine colorful original title then genuinely recorded checkerboard menu; separately cut around an authentic black transition | 1994 game intro, 2 original source spans |
| 00:03–00:10 | 7s | Source-locked full-motion 256-centre → 342-world native racing reveal | Already-recorded 43 extra source columns each side |
| 00:10–00:14 | 4s | Actual first 240 consecutive native 2P frames | Original-mode wide 2P native recording, not new Windows capture |
| 00:14–00:24 | 10s | Genuine October 10 native Modern root navigation | Not footage of all new October 19 product features |
| 00:24–00:29 | 5s | **Editorial** Windows player journey diagram | Source-qualified scripted onboarding/race/result/Records work, not a live user recording |
| 00:29–00:38 | 9s | Genuine original 65816 MainLoop opcode + pinned generated native C and bounded actual native gameplay | Same-function mapping, not every instruction or total-game parity |
| 00:38–00:44 | 6s | Authentic single composited 342×224 source raster, with editorial guides | Raster source anatomy, not an extracted multilayer reconstruction |
| 00:44–00:50 | 6s | Editorial pixel-parity graphic | Only the bounded source-centre 0/57,344 difference observation |
| 00:50–00:55 | 5s | **Editorial** physical-4K evidence statistics | Exact 8,294,400-pixel SDL readback, **not 4K gameplay footage** |
| 00:55–01:10 | 15s | Three original-to-4× art/pose prototype reels | Historical exact source and procedural studies, now under explicit likeness veto |
| 01:10–01:16 | 6s | Actual final 360 native 2P frames, continuous within shot | Completes the original 600-frame source session |
| 01:16–01:25 | 9s | **Editorial** contribution invitation | C++ / reverse engineering / 3D character art / QA |

The 27-second social cut fits the **full recorded 16:9 race** inside 9:16; it never silently crops away P2. It uses genuine title (90f), menu (30f), 7s continuous reveal, 4s verified Modern navigation, 4s qualified code documentary, 6s native 2P race, and 4s editorial recruitment.

Every moving native frame comes from the committed captured videos, with 60fps source cadence unchanged and no temporal interpolation. Editorial 30fps clips are frame-duplicated to 60fps, rather than generating fictional guest frames. An animated synthetic score is authored in Python with no original or commercial game music.

## Research and release claims

The latest authoritative [active work queue](../../../../docs/WORK-QUEUE.md) and [release quality ledger](../../../../docs/RELEASE-QUALITY-LEDGER.json) still report **0/45 complete USA events independently accepted** and **0/12 Windows release gates accepted** as of October 19. Source-perfect Original centre, bounded 3840×2160 SDL readback, accepted 1P/2P user journeys and broader Modern menus are independent narrower accomplishments. The video depicts them accordingly.

The video **does not** show physical-controller hardware qualification, a human Windows new-player session recorded on October 19, finished Windows beta, complete original-vs-native event parity, shipping 4× racer likeness, or full-width Remastered art. The 4× procedural demonstration's earlier byte-level approvals do not override the October 10 artistic veto in `docs/HD-RACER-CHARACTER-RECONSTRUCTION.md`.

Evidence behind visible engineering claims:

- [Original/wide 0/57,344 exact centre differences](../../../../docs/QA08-NATIVE-STOCK-CENTER-PARITY-20261010.md)
- [Real 3840×2160 SDL readback, original native 2P, frame 2208](../../../../docs/QA08-REAL-4K-POST-GO-20261010.md)
- [Original source / real generated MainLoop code evidence](../../2026-10-10/technical-motion/README.md)
- [Modern scripted native Windows journeys, named racers, retained Records](../../../../docs/MODERN-FRONTEND-SHIPPING-STATUS.md)
- [New racer character likeness veto and reconstruction brief](../../../../docs/HD-RACER-CHARACTER-RECONSTRUCTION.md)
- [October 10 native continuous capture and source identities](../../2026-10-10/recruitment/continuous/README.md)
- [October 10 verified Original title and Modern front-end captures](../../2026-10-10/recruitment/README.md)

## Render

```sh
sudo apt-get install ffmpeg python3-pil
python3 tools/showcase/build_flagship_recruitment_20261019.py \
  --outdir media/showcase/2026-10-19/flagship
```

The script builds temporary intermediate source-locked segments, produces 85s and 27s H.264/AAC videos, an authentic original-gameplay poster and `flagship-provenance.json`. Every rendered video and the poster is SHA-256 recorded, with per-shot source ordinals, source identity and exclusions. Rendering requires no ROM, native executable, guest launch, shader changes or external network.

**Distribution rights remain separately unverified.** Packaging a promotional trailer is not clearance to distribute rights-controlled gameplay imagery or a ROM. A full human viewing pass has not been implied by tool-level verification; visual inspection is documented separately in the release review receipt.

## Portrait-first social edition

The base source-locked 27-second portrait cut preserves the full fitted 16:9 gameplay frame in a 1080×1920 matte. The optional **ambient social cut** in `ur-recomp-flagship-27s-social-ambient.mp4` keeps that same entire 1080×608 gameplay area at exactly (0,656) while filling only the background with a low-resolution, heavily blurred/colour-muted transform of its own recorded video pixels. Animated surrounding captions are editorial; the blurred matte is never represented as real additional track geometry. The short's score is copied unchanged.

```sh
python3 tools/showcase/upgrade_flagship_vertical_20261019.py \
  --outdir media/showcase/2026-10-19/flagship
```

The upgrade requires the *exact accepted* base portrait SHA and writes its own output SHA/provenance. The original 27-second vertical delivery remains available as the stable fall-back.

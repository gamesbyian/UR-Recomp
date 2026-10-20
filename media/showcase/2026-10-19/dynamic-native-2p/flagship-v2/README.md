# Dynamic course-topology flagship, second edition

This 90-second recruitment film replaces the two synchronized, visually flat native 2P shots in the first 85-second flagship with **three newly recorded authentic original 342-column two-player courses**.

## What changed

| New film window | Genuine source | What is visible / intended |
| --- | --- | --- |
| 0:00–0:10 | Original October 19 flagship | 1994 title/menu and authentic 256→342 world reveal |
| 0:10–0:15 | **MegaJump**, independent native 2P recording | Steep slopes, large-radius bowl-like transitions and different P1/P2 positions |
| 0:15–0:20 | **Jumps**, independent native 2P recording | Rising stunt terrain and airborne unicycle footage |
| 0:20–0:25 | **Looper**, independent native 2P recording | Rolling hills and independent racer locations; **complete closed loop not certified** |
| 0:25–1:21 | Original October 19 flagship | Modern navigation, source-level engineering, pixel tests and experimental art |
| 1:21–1:30 | Original October 19 flagship | Clear contributor invitation |

All 900 source frames in the middle 15-second montage are authored by the real native game with original 342-column world geometry. The montage is assembled from **three different genuine guest executions with explicit hard cuts**, not a continuous 15-second race, and no interpolation or racer-position compositing is performed.

The previously merged [85-second flagship](../../flagship/ur-recomp-flagship-85s-1080p.mp4) remains intact. This revision uses only independently checked MP4 source bytes, keyed SHA256, exact frame ranges and a film-only FFmpeg script.

## Verification boundary

The source [dynamic capture evidence ledger](../dynamic-racing-provenance.json) includes native course IDs, ROM hash, distinct full-WRAM guest position observations for both riders, guest-frame clocks, original lossless source hashes, control-vs-recorded full guest CRC checks and independent decoded course images. The [source reel receipt](../dynamic-three-course-reel-provenance.json) identifies every one of the three sessions and the 300 real frames selected from each. Each source course may contain geometry not visible in the specific chosen five seconds. Most importantly, **Looper's name is not verification that a complete loop is shown**.

The film's own `dynamic-flagship-provenance.json` identifies every retained/removed segment, source movie SHA256, exact frame ordinals, new output SHA256 and exclusions. The one-shot FFmpeg job checks 5,400 decoded 1920×1080/60fps output frames, retains 11 individually decoded output witnesses, and removes itself after publishing. Visual-frame review is a distinct gate before merge.

No finished-beta claim, physics/fidelity code change, approved final 4× character art or authentic physical 4K video is implied.

## Rebuild

```sh
python3 tools/showcase/build_dynamic_flagship_v2.py \
  --outdir media/showcase/2026-10-19/dynamic-native-2p/flagship-v2
```

This branch is stacked on [source capture PR #2002](https://github.com/gamesbyian/UR-Recomp/pull/2002). Do not merge a movie-only derivative into `main` without the authenticated native source being merged or made immutable and accessible.

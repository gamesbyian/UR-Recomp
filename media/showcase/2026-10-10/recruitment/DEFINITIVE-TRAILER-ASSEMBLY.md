# Evidence-gated definitive UR-Recomp recruitment assembly

**Status:** completed source-locked films with model-assisted representative-frame visual QA and independent CI video/SHA/frame verification. No human full-playback screening or external redistribution rights certification is claimed. This branch owns final media composition only; it does not modify the native emulator, renderer, guest gameplay, Modern frontend, HD art approval or source findings.

The full 58-second / 3480-frame horizontal 1920×1080 60-fps plan:

| Time | Source | Claim |
| --- | --- | --- |
| 00:00–00:04 | Verified native Original source ordinals 270–359 (title art) and 420–569 (checkerboard menu), two individually consecutive clips | Genuine title-to-menu editorial cut removes only the independently audited black transition |
| 00:04–00:14 | Verified native Modern root + original menu handoff, 600 frames | Real Modern frontend |
| 00:14–00:21 | Accepted independently reviewed native 2P moving reveal | Genuine 342-wide Original world behind animated side mattes |
| 00:21–00:25 | Accepted same-capture Original-centre/full-world comparison | **Editorial crop; not two WRAM-matched executions** |
| 00:25–00:34 | Agent 2 accepted full nine-second technical film | Clearly labeled editorial engineering visualization |
| 00:34–00:39 | Agent 3 accepted approved-art comparison | Approved 4× limited-pose work only |
| 00:39–00:44 | Agent 3 accepted animation archaeology | Editorial explanation, no new gameplay frames |
| 00:44–00:54 | Verified real 600 consecutive native 2P race frames | Actual Original source-backed widescreen play |
| 00:54–00:58 | Generated editorial final card | GitHub contribution invitation |

The accompanying 20-second 1080×1920 short uses 90 genuine title frames followed by 30 genuine checkerboard-menu frames, four seconds of real Modern frontend, six of uninterrupted moving widescreen reveal, five of genuine 2P gameplay and three of an editorial CTA. Both riders remain visible because the full 16:9 gameplay frame is fitted within the vertical canvas rather than vertically cropping one viewport.

## Runtime command

Dependencies: Python 3, FFmpeg (with libx264, AAC, drawtext), Pillow for the already committed original deterministic synthesized soundtrack generator.

```sh
root=media/showcase/2026-10-10/recruitment
python3 tools/showcase/build_definitive_recruitment.py \
  --title "$root/native-menu/ur-native-title-menu-900f.mp4" \
  --title-manifest "$root/native-menu/native-title-menu-provenance.json" \
  --modern "$root/modern-root/ur-modern-root-600f.mp4" \
  --modern-manifest "$root/modern-root/native-modern-root-provenance.json" \
  --race "$root/continuous/ur-native-2p-clean-600f.mp4" \
  --race-manifest "$root/continuous/native-continuous-provenance.json" \
  --reveal "$root/presentation-edits/authentic-widescreen-reveal-7s.mp4" \
  --comparison "$root/presentation-edits/same-capture-centre-vs-wide-5s.mp4" \
  --presentation-manifest "$root/presentation-edits/presentation-provenance.json" \
  --technical media/showcase/2026-10-10/technical-motion/04-machine-code-to-native.mp4 \
  --art media/showcase/art-reconstruction/2026-10-10/01-original-4x-remastered.mp4 \
  --archaeology media/showcase/art-reconstruction/2026-10-10/02-animation-archaeology.mp4 \
  --editorial-approval "$root/final-approval/approval.json" \
  --outdir /tmp/ur-final-recruitment
```

The editorial approval JSON must declare `schema: "UR-RECRUITMENT-MEDIA-APPROVAL/1"`, `accepted_by` (accountable reviewer identity, including explicit model-assisted review where applicable), and a `clips` dictionary for `technical`, `art`, `archaeology`. Each clip entry requires `kind: "editorial_graphic"`, `approved_for_trailer: true`, the exact `sha256` of the MP4, one or more `evidence_links` to authoritative docs or CI, and `review_frame_sha256` mapping at least three independently checked decoded review PNG *filenames relative to the approval manifest directory* to their content SHA-256. **Do not set approved_for_trailer before independent source and visual review.** The tool rejects missing media, altered video, unsupported 30/60-fps authoring, missing review frames or mismatched approval.

Both Agent 2's machine-code correspondence and Agent 3's art approval are independently gated; any insufficient technical demonstration is preferable to an impressive but unsupported one. Existing PRs: [technical #1300](https://github.com/gamesbyian/UR-Recomp/pull/1300), [art #1301](https://github.com/gamesbyian/UR-Recomp/pull/1301). Coordinate handoff in their own PR discussions.

The assembler performs exact SHA and FFprobe checks on all three native sources and the two media-only previously accepted presentation clips. It writes SHA-256, editorial source map, precise timeline and release-claim limitations into `definitive-trailer-provenance.json`. Source-recorded gameplay is not temporally interpolated; 30fps editorial motion graphics can be duplicated to 60fps but must retain their editorial labels. The soundtrack is the project's independently synthesized original promotional bed, never game music.

The final media passed the media-only verification in [run 38110782332](https://github.com/gamesbyian/UR-Recomp/actions/runs/38110782332), including 3480 horizontal frames, 1200 portrait frames, source video SHA checks, 18 independent PNG witnesses, authentic non-black openings and the HUD-safe poster. Selected final output frames were then visually checked by GPT-6; this is not a certification of a human full-film watch-through. No finished-beta, 4K continuous recording, complete 4× art coverage or Remastered widescreen gameplay claim is authorized. External public redistribution still requires asset-rights review.

**Completed media handoff:** all three agent input packages are now merged into `main`, and the final videos with provenance are ready for integration. These are promotional/recruitment media, not evidence of a finished game or an independently cleared commercial asset license.

## Original native title visual audit and exact edit points

[The 25-frame native title timing audit](final-approval/original-native-title-timing-audit.json) and [source-derived contact sheet](final-approval/original-native-title-timing-contact-sheet.png) independently verify that stock title art is visible across source ordinals 270–360, followed by an intentionally black transition at ordinals ~375–405. Real 1994 checkerboard menu art appears at source ordinal 420. The final horizontal film uses two true, unaltered source segments: title ordinals **270–359** (90 frames), then menu ordinals **420–569** (150 frames). The 20s mobile version uses title ordinals 270–359, then menu ordinals 420–449, making its first two seconds 120 native frames. Both are explicit editorial cuts within **the same independently accepted native execution**. The black transition is intentionally omitted, not restored, synthesized or interpolated. The final-source manifest records these exact ranges.

The earlier full-length render contained a black opening and was retained as a superseded review candidate, not as release-ready footage. The opening QA gate inspects frame 90 of both new cuts and **rejects** a black source image. No extra heavy gameplay CI is triggered for media edits.

## Final accepted candidate outputs

- [58s 1080p recruitment master](definitive-film/ur-recomp-definitive-recruitment-58s-1080p.mp4): SHA-256 `88f22b68f5aae5466923f315bf924a5f9107472a3dfd262cea258ee10738a2bc`; 3480 decoded frames / 60 fps.
- [20s vertical short](definitive-film/ur-recomp-recruitment-vertical-20s-1080x1920.mp4): SHA-256 `f1fc0b8ce1d6cb5383f8e6b63d9ed978d581941f352dede2ff982319c84024f7`; 1200 decoded frames / 60 fps.
- [Original-gameplay poster](definitive-film/ur-recomp-recruitment-final-poster.png): SHA-256 `d9bcbda5335a2656f81c79607be1fd540ca7403acba403111ad12f4b4270189a`; editorial typography sits in separate matte margins.
- [Full source/output SHA and shot ledger](definitive-film/definitive-trailer-provenance.json) and [output decoded witnesses](definitive-film/render-review-provenance.json), including **18 selected frames**, checked via independent decode and Pillow with actual image load/verification.

This resolves an initial failed edit whose 4-second opening contained the source game's intentional black transition. A 25-frame timing audit selected genuinely visible original title and menu ranges. A model-assisted visual review verified the corrected title, checkerboard menu, social-title treatment and poster; source segments elsewhere were previously inspected on the accepted original technical/art source clips. The film still makes explicit editorial cuts and includes original synthetic promotional audio, not game audio.

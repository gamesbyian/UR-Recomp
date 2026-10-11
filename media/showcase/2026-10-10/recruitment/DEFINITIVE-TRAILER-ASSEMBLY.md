# Evidence-gated definitive UR-Recomp recruitment assembly

**Status:** source-locked assembly and fully rendered media candidate; final visible-title cut and independent full-frame review pending. This branch owns final media composition only; it does not modify the native emulator, renderer, guest gameplay, Modern frontend, HD art approval or source findings.

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
  --technical /path/to/verified/technical.mp4 \
  --art /path/to/verified/approved-art.mp4 \
  --archaeology /path/to/verified/archaeology.mp4 \
  --editorial-approval /path/to/independently-reviewed/approval.json \
  --outdir /tmp/ur-final-recruitment
```

The editorial approval JSON must declare `schema: "UR-RECRUITMENT-MEDIA-APPROVAL/1"`, `accepted_by` (actual reviewer name), and a `clips` dictionary for `technical`, `art`, `archaeology`. Each clip entry requires `kind: "editorial_graphic"`, `approved_for_trailer: true`, the exact `sha256` of the MP4, one or more `evidence_links` to authoritative docs or CI, and `review_frame_sha256` mapping at least three independently checked decoded review PNG *filenames relative to the approval manifest directory* to their content SHA-256. **Do not set approved_for_trailer before independent source and visual review.** The tool rejects missing media, altered video, unsupported 30/60-fps authoring, missing review frames or mismatched approval.

Both Agent 2's machine-code correspondence and Agent 3's art approval are independently gated; any insufficient technical demonstration is preferable to an impressive but unsupported one. Existing PRs: [technical #1300](https://github.com/gamesbyian/UR-Recomp/pull/1300), [art #1301](https://github.com/gamesbyian/UR-Recomp/pull/1301). Coordinate handoff in their own PR discussions.

The assembler performs exact SHA and FFprobe checks on all three native sources and the two media-only previously accepted presentation clips. It writes SHA-256, editorial source map, precise timeline and release-claim limitations into `definitive-trailer-provenance.json`. Source-recorded gameplay is not temporally interpolated; 30fps editorial motion graphics can be duplicated to 60fps but must retain their editorial labels. The soundtrack is the project's independently synthesized original promotional bed, never game music.

The final media can be merged only after fresh output review and a media-only CI acceptance pass. No finished-beta, 4K continuous recording, complete 4× art coverage or Remastered widescreen gameplay claim is authorized. External public redistribution still requires asset-rights review.

**Important:** Do not merge this PR as finished footage until all three agent media outputs and their review witnesses exist and a final source audit accepts the resulting 58s and 20s binaries. This branch may remain open as a build contract without blocking standalone widescreen reveal PR #1299.

## Original native title visual audit and exact edit points

[The 25-frame native title timing audit](final-approval/original-native-title-timing-audit.json) and [source-derived contact sheet](final-approval/original-native-title-timing-contact-sheet.png) independently verify that stock title art is visible across source ordinals 270–360, followed by an intentionally black transition at ordinals ~375–405. Real 1994 checkerboard menu art appears at source ordinal 420. The final horizontal film uses two true, unaltered source segments: title ordinals **270–359** (90 frames), then menu ordinals **420–569** (150 frames). The 20s mobile version uses title ordinals 270–359, then menu ordinals 420–449, making its first two seconds 120 native frames. Both are explicit editorial cuts within **the same independently accepted native execution**. The black transition is intentionally omitted, not restored, synthesized or interpolated. The final-source manifest records these exact ranges.

The earlier full-length render contained a black opening and was retained as a superseded review candidate, not as release-ready footage. The opening QA gate inspects frame 90 of both new cuts and **rejects** a black source image. No extra heavy gameplay CI is triggered for media edits.

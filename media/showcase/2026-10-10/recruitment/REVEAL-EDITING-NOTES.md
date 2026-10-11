# Verified continuous widescreen presentation edits

**Accepted rendered standalone media.** This source-locked editing tool produces two independently inspected 1080p H.264 sequences from the validated 600-frame Baldosa two-player capture. These are not the unfinished definitive 58-second trailer.

Run from repository root:

```sh
root=media/showcase/2026-10-10/recruitment
python3 tools/showcase/build_definitive_reveal.py \
  --race "$root/continuous/ur-native-2p-clean-600f.mp4" \
  --manifest "$root/continuous/native-continuous-provenance.json" \
  --outdir /tmp/ur-recruitment-reveal
```

The tool fails before rendering unless the committed race file matches SHA-256 `182ef43ccf34f501dea4051312e71bf4d974a53dc6634cd98a5cbf3fae8ac130`, decoded frame count 600 at 60 fps, source resolution, guest-frame range 2100–2699, zero missing/duplicated frame IDs and the manifest's recording-on/off WRAM CRC identity.

**Widescreen reveal (seven seconds):** play the genuine moving 342-column world throughout; black opaque covers initially hide the 43 extra world columns on each side and slide away. The continuous raster is shown inside an editorial border so labels never obstruct the original game HUD. The fixed visible center is the canonical 256 original source columns, with their intended original-game display proportions (4:3 in a 16:9 delivery). The masked full game source is not a separate Original-mode recording.

**Comparison (five seconds):** precisely time-aligned centre crop and full view of the **same** native wide capture, horizontally paired **at equal displayed gameplay scale**. This is an *editorial same-capture crop*, explicitly not two separately executed, WRAM-matched Original/wide recordings. Do not call it independently verified gameplay parity. An independently matched guest-frame 256-mode capture can replace the left pane after separate evidence review.

Every generated video receives a machine-readable SHA-256/provenance report. The 1080p H.264 files have no fabricated racer motion, invented world content, temporal interpolation, game music, claims about finished Remastered graphics, or physical 4K host capture. Presentation overlays may hide source pixels; they never create pixels presented as gameplay.

**Accepted published files:**

- [7-second continuous widescreen reveal](presentation-edits/authentic-widescreen-reveal-7s.mp4), SHA-256 `92ea56611a18ee001ae101f36bc0f2600dc9ca117581edd8072df9535f831414`.
- [5-second same-capture centre-versus-wide comparison](presentation-edits/same-capture-centre-vs-wide-5s.mp4), SHA-256 `6291abda1f52f47425405757c049c70aa245133a39a138b263a2b4e2bf335e5f`.
- [Source and edit provenance](presentation-edits/presentation-provenance.json) and **six source-decoded output review frames** alongside the MP4s.

Both clips passed exact-source verification, frame-count/probe inspection (420 and 300 1080p/60-fps frames), manual review at beginning/midpoint/end, plus SHA-256 verification in [lightweight one-shot render CI run 38107826077](https://github.com/gamesbyian/UR-Recomp/actions/runs/38107826077). The first visual review detected HUD obstruction and scale-registration problems; both were corrected and the final frames re-reviewed. The temporary one-shot workflow self-removed in the media-commit transaction.

**Still pending for final film:** the 45–60-second master and new vertical edit require the evidence-reviewed Agent 2 technical sequence and Agent 3 approved 4× art/animation demonstrations. This standalone media is independently mergeable; it is not a finished recruitment-film certification. See [the separate final-assembly PR](https://github.com/gamesbyian/UR-Recomp/pulls?q=is%3Apr+is%3Aopen+definitive+assembly) for acceptance gates. No heavyweight native CI was used.

**Source:** [native continuous capture run 38089655141](https://github.com/gamesbyian/UR-Recomp/actions/runs/38089655141); [capture README](../continuous/README.md). Public redistribution still requires asset-rights review.

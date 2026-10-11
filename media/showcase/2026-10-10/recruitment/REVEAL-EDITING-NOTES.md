# Verified continuous widescreen presentation edits

This branch adds an **editing tool**, not a purported finished recruitment film. It makes two source-locked 1080p sequences from the already accepted genuine 600-frame Baldosa two-player capture.

Run from repository root:

```sh
root=media/showcase/2026-10-10/recruitment
python3 tools/showcase/build_definitive_reveal.py \
  --race "$root/continuous/ur-native-2p-clean-600f.mp4" \
  --manifest "$root/continuous/native-continuous-provenance.json" \
  --outdir /tmp/ur-recruitment-reveal
```

The tool fails before rendering unless the committed race file matches SHA-256 `182ef43ccf34f501dea4051312e71bf4d974a53dc6634cd98a5cbf3fae8ac130`, decoded frame count 600 at 60 fps, source resolution, guest-frame range 2100–2699, zero missing/duplicated frame IDs and the manifest's recording-on/off WRAM CRC identity.

**Widescreen reveal (seven seconds):** play the genuine moving 342-column world throughout; black opaque covers initially hide the 43 extra world columns on each side and slide away. The fixed visible center is the canonical 256 original source columns, with their intended original-game display proportions (4:3 in a 16:9 delivery). The masked full game source is not a separate Original-mode recording.

**Comparison (five seconds):** precisely time-aligned centre crop and full view of the **same** native wide capture, horizontally paired. This is an *editorial same-capture crop*, explicitly not two separately executed, WRAM-matched Original/wide recordings. Do not call it independently verified gameplay parity. An independently matched guest-frame 256-mode capture can replace the left pane after separate evidence review.

Every generated video receives a machine-readable SHA-256/provenance report. The 1080p H.264 files have no fabricated racer motion, invented world content, temporal interpolation, game music, claims about finished Remastered graphics, or physical 4K host capture. Presentation overlays may hide source pixels; they never create pixels presented as gameplay.

**Unfinished scope:** The definitive 45–60-second film, vertical short and Agent 2/3 archaeology/HD demonstrations require independently verified new material plus rendered media QA. This script is a deliberately independent building block and should be merged only after actually running FFmpeg and inspecting its first, midpoint and final frames. No automatic heavyweight native CI is needed.

**Source:** [native continuous capture run 38089655141](https://github.com/gamesbyian/UR-Recomp/actions/runs/38089655141); [capture README](../continuous/README.md). Public redistribution still requires asset-rights review.

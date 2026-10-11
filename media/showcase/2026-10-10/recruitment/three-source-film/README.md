# Three verified native sources: 30-second recruitment film

[Watch finished 1080p trailer](ur-recomp-three-source-recruitment-30s-1080p.mp4) · [Machine-readable edit provenance](three-source-recruitment-provenance.json)

This is the project's October 10 unified recruitment cut, assembled from **three separate actual native Baldosa recordings**, each already independently validated for exact frame IDs, guest WRAM CRC parity with recording disabled, FFV1 original-source capture, and permanent clean MP4 identity. It presents the original game title, integrated native Modern root and actual two-player 342-wide Original race.

| Trailer time | Frames | What is actually shown |
| --- | --- | --- |
| 0–5 s | 300 | Original stock title animation, genuine guest frames 180–479 |
| 5–15 s | 600 | Modern integrated root navigation, Records and stock handoff, guest frames 1–600 |
| 15–25 s | 600 | Real split-screen 342×224 logical widescreen Original race, guest frames 2100–2699 |
| 25–30 s | 300 | Clearly editorial contribution card with GitHub repository URL |

**Important distinction:** These are **three different recorded native sessions** joined by editorial cuts. The film makes no claim that the original title, Modern menu and two-player race constitute one uninterrupted guest session. No gameplay imagery or motion is invented, interpolated, repeated or substituted. The ending GitHub invitation is editorial typography, not a real in-game UI screen.

The title and underlying stock menus retain 256×224 original game geometry presented in a widescreen SDL window with sidebars. Only the racing sequence demonstrates the authentic 342×224 widened logical world. All original recordings were taken from 960×540 SDL physical drawables and then nearest-neighbor scaled to 1080p; this is **not a continuous 3840×2160 physical capture**, finished Remastered art mode or certified Windows beta.

**Provenance and production:** `tools/showcase/build_three_source_recruitment.py` independently verifies all three source video and manifest SHA-256 values, complete guest-frame counts, cadence, guest state parity and real video dimensions before joining their timelines. The edit uses the existing synthesized original promotional score, without commercial Uniracers audio. Final video and original-source manifest hashes are in `three-source-recruitment-provenance.json`. Representative decoded frames `review-frame-0180.png`, `review-frame-0420.png`, `review-frame-0720.png`, `review-frame-1100.png`, `review-frame-1490.png`, and `review-frame-1660.png` are retained for visual verification.

To reproduce the final film, from the repository root:

```bash
root=media/showcase/2026-10-10/recruitment
python3 tools/showcase/build_three_source_recruitment.py \
  --title "$root/native-menu/ur-native-title-menu-900f.mp4" \
  --title-manifest "$root/native-menu/native-title-menu-provenance.json" \
  --modern "$root/modern-root/ur-modern-root-600f.mp4" \
  --modern-manifest "$root/modern-root/native-modern-root-provenance.json" \
  --race "$root/continuous/ur-native-2p-clean-600f.mp4" \
  --race-manifest "$root/continuous/native-continuous-provenance.json" \
  --outdir /tmp/ur-three-source-recruitment
```

The temporary one-shot encoding workflow has been retired after the video was produced, leaving no permanent CI fanout.

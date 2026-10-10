# Continuous-gameplay recruitment campaign (October 10, 2026)

**Status: rendered and accepted media-source checks, pending final PR review.**

The first ten seconds of each production contain the same **600 unmodified-in-time consecutive genuine native Baldosa game frames**, guest frames 2100..2699, from the [separately recorded and verified lossless gameplay source](../continuous/README.md). These are actual SDL host presentations, not animation between extracted stills.

- [Watch 41-second 1920×1080 recruitment trailer](ur-recomp-recruitment-continuous-20261010.mp4)
- [Watch 21-second 720×1280 vertical recruitment short](ur-recomp-recruitment-continuous-vertical-20261010.mp4)
- [View source-moment ordinal 0](source-ordinal-000.png), [300](source-ordinal-300.png), [599](source-ordinal-599.png)
- [Open source-motion audit](visual-motion-review.json)
- [Open edit provenance](continuous-recruitment-edit-provenance.json)

## Actual recording versus editorial material

**00:00–00:10:** real 2P racing, genuine Original 342×224 widened game world, recorded from a real SDL 960×540 drawable, nearest-neighbor 1920×1080 delivery. 600 consecutive source IDs, no interpolation, no duplicated synthetic gameplay frames, and identical capture-enabled/disabled guest WRAM CRC traces. At 60 frames/s nominal the interval lasts 10 seconds. External display scanout timing was not separately certified.

**After 00:10:** existing October 10 source-backed editorial teaser scenes, including the actual 256-versus-342 comparison and older *sampled/held* authentic game frames. The source teaser's original sampled-frame labels and disclaimers remain visible. Its 24-fps authored editorial frame cadence was converted to 60 fps for this campaign; this is explicitly **editorial resampling**, not additional continuous game evidence.

**Audio:** the original deterministic synthesized promotional backing in `tools/showcase/build_recruitment_teaser.py`; no commercial game soundtrack.

The horizontal 41s edit is 1080p. The vertical 21s edit retains both 2P racers by fitting the full game image within the narrower layout rather than cropping one player away. Source SHA verification happens *before* rendering, and both output hashes are recorded.

## Independent multi-frame original-source review

The media-only CI run [38090216682](https://github.com/gamesbyian/UR-Recomp/actions/runs/38090216682) downloaded the **original** FFV1 artifact from native run 38089655141, checked exact SHA-256 against the first capture manifest, and decoded source ordinals 0, 150, 300, 450 and 599 independently. Measured source RGB pixels changed by **224,535**, **278,192**, **274,871** and **281,193** over the four 150/149-frame comparison intervals, at real source 960×540 output dimensions. These five actual decoded PNGs and their SHA256s are retained next to the edits. The original ordinal 300 decoded PNG checksum exactly matches the separately retained native-source poster (SHA-256 `d1a4116c5090c8e59cca58bdd2a7fea3a37570b552db020d527cbb3d89a8ce8f`).

Human inspection of ordinals 0/300/599 confirms source racers and course scroll are visible, with HUD progression approximately **0:01.8 → 0:06.8 → 0:11.8**. The two riders are often close together on this route, so a later more visually varied route will improve the promotional opening. The footage remains Original fallback and makes no claim of finished 4K HD replacement art, independent whole-game fidelity approval, or finished Windows beta.

## Reproduction

```sh
python3 tools/showcase/build_continuous_recruitment_edits.py \
  --clip ../continuous/ur-native-2p-clean-600f.mp4 \
  --provenance ../continuous/native-continuous-provenance.json \
  --teaser ../ur-recomp-recruitment-teaser-20261010.mp4 \
  --vertical ../ur-recomp-recruitment-short-vertical-20261010.mp4 \
  --outdir /tmp/ur-verified-recruitment-edit
```

Adjust the relative paths to your working directory, or supply absolute paths. This command fails closed unless the exact committed video matches its full provenance, guest IDs/CRC equality, 600 decoded frames, and 60-fps 1080p source delivery. The CI log/source-moment artifact and this directory retain sufficient evidence to independently inspect what the source footage actually contained.

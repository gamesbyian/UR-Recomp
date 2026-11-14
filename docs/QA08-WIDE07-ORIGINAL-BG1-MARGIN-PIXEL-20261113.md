# WIDE-07 original-USA-derived complete BG1/BG2 margin raster (2026-11-13)

**Result:** **38,528/38,528** native 342-wide margin pixels match a
source-only, independently decoded **original-USA Snes9x BG1/BG2 course-RAM,
VRAM, CGRAM and PPU raster prediction** in RGB5. This covers every pixel in
both 43-pixel margins for two real source checkpoints (race entry and after
900 input frames). It supersedes the initial BG1-only 2,403-pixel comparison
and the earlier 160/160 source tile-word crosswalk; it does **not** establish
a physical original-SNES 342-wide output, a complete game course, complete
WIDE-07 qualification or a Windows release gate.

## Actual executed producers

- Source Snes9x: [run 43539425650](https://github.com/gamesbyian/UR-Recomp/actions/runs/43539425650),
  artifact [14090194177](https://github.com/gamesbyian/UR-Recomp/actions/runs/43539425650/artifacts/14090194177),
  experiment source `b3ae92f0e587471674487921ea3c887bce06b3ac`,
  ZIP SHA256 `fd8faa2bf09fd2dcc89e860a9d0ff75edf5465380032361e176fc7e9ea3dad78`.
- Native fixed/342-wide: [run 43540488054](https://github.com/gamesbyian/UR-Recomp/actions/runs/43540488054),
  artifact [14091441914](https://github.com/gamesbyian/UR-Recomp/actions/runs/43540488054/artifacts/14091441914),
  experiment source `0c86c706b58f0f72969ceb9d0fa200d765bdf209`,
  ZIP SHA256 `4cdad8847df27145ba256494586ddddf9bccc13307356b9b8acac0fe408284d7`.

Both signed-by-receipt GHA archives were independently downloaded, hashed,
read and checked against the contained exact-source execution receipts.
No synthetic pixels, newly invented camera positions, unobserved ROM frames
or visually chosen pixel tolerances are used.

## Source-only method

`tools/wide07_original_margin_bg1.py` recovers source original bank-$7F
coarse/fine **16-bit tile words**, maps them into the original Snes9x live
VRAM BG1 32x32 tilemap and requires **a unique perfect 57,344/57,344
source-to-original-PPU word alignment** at each original 256x224 checkpoint.
The calibration tests 16-pixel world-cell offsets and never examines the
native margin image to select them. It returns world offsets `(0,+1)`
at race entry and `(-14,+1)` after 900 movement frames, derived from source
camera and original BG1 scroll. The actual source PPU write journal confirms
no BG1 scroll/character-map register changes over visible scanlines 1..224
for either captured frame.

The original VRAM character graphics are independently decoded as SNES Mode-1
**BG1 16x16 planar 4bpp**, with tile flips, and original CGRAM produces RGB5.
At BG1 palette-index-zero pixels, the source-only decoder then reconstructs
**BG2 8x8 4bpp**, including its 64x64 VRAM tilemap quadrant layout,
per-scanline-constant source PPU scroll, character base, tile flips and CGRAM
palette. BG2 has 100% opaque coverage of all BG1-transparent sampled margin
pixels at these two checkpoints. The original 256-wide centre is a separate
sanity check, complicated by source original OBJ/blue-arrow overlays. Neither
native margin colour nor native tilemap is used to calibrate source pixel
positions. Both BG1 and BG2 horizontal/vertical source PPU scroll/map write
journals have no visible V1..224 mutations for these checkpoints.

| Actual checkpoint | BG1 opaque margins | BG2 fills BG1-transparent | Complete margins |
|---|---:|---:|---:|
| Race entry | 1,199 / 1,199 | 18,065 / 18,065 | **19,264 / 19,264** |
| After 900 movement frames | 1,204 / 1,204 | 18,060 / 18,060 | **19,264 / 19,264** |
| **Both checkpoints** | **2,403 / 2,403** | **36,125 / 36,125** | **38,528 / 38,528** |

The original centre remains in the machine-readable report, including all
predicted-versus-observed differences; it is affected by OBJ, blue-arrow
rendering and other source overlay/priority decisions. Its transient
race-entry one-pixel blue arrow remains a separate timing/composition task.
Zero **offscreen margin** RGB5 mismatches does not establish absence of
offscreen OBJ/colour-math effects at other scene times or different courses.

## Reproduce from retained genuine artifacts

```bash
python3 -m unittest tests.unit.test_wide07_original_margin_bg1
python3 tools/wide07_original_margin_bg1.py \
  --original-zip /path/to/original-agent-hosted-script-evidence.zip \
  --native-zip /path/to/native-agent-hosted-script-evidence.zip \
  --require-margin-parity --out /tmp/wide07-source-bg1-margin.json
```

The report includes per-checkpoint source SHA, producer-archive SHA, source
WRAM/VRAM/CGRAM hashes, original-only world alignment, eligible pixel
denominators, actual RGB5 mismatches and explicit zero qualification credit.
Tests reject ambiguous source-only alignments, visible-scanline BG1/BG2
register changes, incorrect 4bpp palette/flip handling, wrong VRAM quadrant
addressing, and any unaccounted margin pixel. Any source-derived margin pixel
disagreement becomes a coordinate-level, source-bound failure.

## What is still missing

All 38,528 margin pixels are source-derived BG1/BG2 RGB5 matches at **two
checkpoints**, and source BG2 covers every source-BG1-transparent margin pixel.
Potential OBJ, window/HDMA colour-math, sprite priority and moving-frame
changes outside these captures remain unqualified. The original 256-wide
emulator did not literally rasterize 342 pixels, so this is a source-derived
counterfactual, not a second physical wide-renderer observation. Absolute
original/native guest-frame timing is not registered. The transient entry
arrow remains unresolved. Two original-derived frame predictions cannot
certify the remaining course journey or Windows visual acceptance.

**Next executable discriminator:** determine why the original/native
race-entry blue arrow differs by one pixel despite after-scroll exact
centre RGB5 agreement. Register its original PPU/OBJ raster phase with
native guest/display clocks using actual PPU journals. Then extend the
source-derived full-margin oracle from two frames into independently chosen
moving camera checkpoints, including an overlap or sprite/HDMA colour-effect
case, and rerun without reusing native colour to select source alignment.
In parallel finish the independently executable RF095 audio-onset and
complete-event criteria. Formal counters remain **0/45 and 0/12**.

# WIDE-07 original-USA-derived BG1 pixel oracle (2026-11-13)

**Result:** 2,403/2,403 native 342-wide opaque BG1 margin pixels match an
independently decoded **original-USA Snes9x course-RAM, VRAM, CGRAM and PPU**
prediction in RGB5. This is first bounded offscreen **pixel** evidence, beyond
the earlier 160/160 original-source course tile-word crosswalk. It is not full
widescreen qualification, a full USA course, or a Windows release gate.

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

The source original VRAM character graphics are decoded as SNES Mode-1 BG1
planar 4bpp, 16x16 cells, including tile flips and per-tile palette indices.
The original CGRAM words produce RGB5. Only **opaque BG1** samples are
compared, because palette index zero delegates visibility to BG2/OBJ and
colour composition, which this oracle does not implement. Original
256-wide central pixels are an independent raster sanity check; the native
margin BMP is read only after all source-only alignment is fixed.

| Actual checkpoint | Left 43px, opaque BG1 | Right 43px, opaque BG1 | Original-centre BG1 |
|---|---:|---:|---:|
| Race entry | 554/554 | 645/645 | 3,153/3,736 |
| After 900 right-held frames | 602/602 | 602/602 | 3,584/3,584 |
| **Margins total** | **1,156/1,156** | **1,247/1,247** | N/A |

The 583 original-centre BG1 mismatches at race entry are not omitted from
the report. The original/native framebuffer investigation already localized
the transient race-entry *blue directional arrow* overlay to a 1-pixel
boundary/phase difference. BG1 alone cannot be assumed to own those
occluded pixels; center differences require separate layer/OBJ accounting.

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
Tests reject ambiguous source-only alignments, visible-scanline BG1 register
changes and incorrect 4bpp palette/flip handling. Any margin pixel
disagreement becomes a coordinate-level, source-bound failure.

## What is still missing

The 2,403 samples are all opaque BG1 pixels at **two checkpoints**. Actual
transparent-BG1 margin output depends on BG2, OBJ, window/HDMA colour math,
sprite overlay and priority rules, which remain unqualified. The source's
256-wide emulator did not literally rasterize the offscreen area. Absolute
original/native guest-frame timing is not registered. The transient entry
arrow remains unresolved, and this observation cannot certify the remaining
43+ courses or Windows visual acceptance.

**Next executable discriminator:** extend the same source-only oracle to
original-derived BG2, OBJ and per-scanline window/colour composition in the
*same* two already retained archives. Before adding another instrumented
capture, check whether the original PPU journal, OAM, VRAM and CGRAM contain
all required inputs. If a first margin pixel differs, isolate the earliest
source layer/palette/priority discrepancy and repair the actual renderer.
In parallel finish the independently executable RF095 audio-onset and
complete-event criteria. Formal counters remain **0/45 and 0/12**.

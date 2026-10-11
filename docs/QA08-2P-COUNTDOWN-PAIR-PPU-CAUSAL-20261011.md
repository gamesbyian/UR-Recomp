# QA-08 native PPU causality: lower 2P racer under countdown

**Status: candidate pending native AOT.** This is a bounded source-faithful
Original PPU experiment, explicitly **not** a graphics product change,
new renderer, source removal in gameplay or approved 342-wide/4× HD art.

## Specific already-authenticated anomaly

The genuine moving native USA 2P Original at guest **1872**
shows the large blue countdown **“2”** across the bottom racer position.
Real separately source-isolated OAM slots **96 and97** still emit
**330+325** opaque pixels with **411 distinct emitted coordinates**
due to 244 overlapping positions. All **411/411** stock final PPU
pixels at those actual lower source coordinates are exactly
RGB `(57,57,255)` (numeral blue), not either rider's source colour.
The earlier frame1856 exposes the lower racer and has an already
successful single-slot96 removal counterfactual changing **305** actual
Original final pixels. The upper racer slot98 at1872 still has
**325/325** original source/final RGB matches.

Source-only observations explain why the pre-existing 2P overlap
report for1872 was `unproven`, but they cannot establish that source
slots96/97 have **no causal effect** on the actual final original
raster: RGB coincidence is not a hardware ownership bit.

## Narrow falsifiable native experiment

The existing `.github/workflows/baldosa-core-spike.yml` already builds
one pinned full Baldosa AOT guest and captures an unchanged Original
2P source image at1872. The only new native execution **reuses that
same compiled guest, the existing `race_2p_split.txt` route, stock
CRC and both separately accepted original OAM source planes** and
switches on diagnostic-only PPU `RemoveFromGame` for the single
contiguous original OAM pair **96-97** on **exactly frame1872**.
No guest write, changes to game/renderer, host-layer paint, new
CI workflow or new emulator harness.

`tools/check_baldosa_2p_covered_pair_causality.py` requires:

- Correct native Original, separately captured source slots96/97 and
  independent pair-removed **full** 342×224 RGBA raster at guest1872.
- Unchanged **all 2,473** native guest CRC entries across the four
  stock/source96/source97/pair-removed processes.
- Exactly **one** real native PPU `UR_RACER_HD_WIDE_REMOVE_PAIR
  frame=1872 slots=96-97 status=armed guest_unchanged=1` marker.
- Accepted independent original source SHA/bbox, full Original PPU
  unchanged-raster SHA, all six full previous stock raster controls,
  positive lower OBJ source and actual blue `411/411` coverage.
- Every one of the **76,608** final RGBA pixels compared between
  stock and actual paired-deletion native output. Changed pixels
  **outside** source96+97 alpha union reject; those inside are
  recorded with bounded exact examples.

Two valid observational outcomes are admitted rather than fabricated:
`native-covered-pair-final-unchanged` proves the pair deletion had
no distinguishable final Original effect at frame1872, or
`native-covered-pair-final-changed` proves the exact changed pixels
and demands further priority investigation. The validator does not
preassume which will happen; guest/process/provenance failures or
changed pixels outside the actual source union are not accepted.

The test module
`tests/unit/test_check_baldosa_2p_covered_pair_causality.py`
exercises true zero-delta cases, genuine source-bounded differences,
outside-source changes, false countdown RGB, mismatched/forged
2473-line CRC streams, missing native slot-arm markers, wrong source
SHA and aliased stock/removal input. The native workflow retains the
new raw counterfactual PPU image, log and bounded JSON report in the
**existing** evidence artifact.

Even a zero result will **not** identify the BG/OBJ/window layer
that drew the countdown “2”, certify the emulator versus original
hardware, generalize to other frames or authorize source OBJ erasure,
new HD/Remastered overlays, original character artistic likeness
approval or Windows release. It is one deeper piece of defensible
graphics archaeology, not a shortcut around Original fidelity.

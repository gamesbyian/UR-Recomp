# QA-08: three hidden original rear-racer source pixels before countdown

**Status: authentic native 2P original PPU observation with final-image
and causal front-slot removal, strictly at guest1856.** The
PPU-emitted lower racer image is not always visible in the final
Original, even at a coordinate where its front rival never emitted
a pixel. This is a small, useful counterexample to a tempting
but unsafe 2P HD compositing simplification.

## What the real PPU proves

Successful pinned original native AOT
[38119117927](https://github.com/gamesbyian/UR-Recomp/actions/runs/38119117927)
(artifact `11694649120`) retains separate complete 342×224 Original
stock, OAM lower **front slot96** and **rear slot97** PPU source
planes, independent source-provenance records and the original PPU
output after removing only slot96 at guest1856.

Compare all **76,608** full Original RGBA coordinates, but compare
their **RGB** to the separately extracted original OBJ source colours:
the final native 342-wide P7 image carries zero alpha across the
whole frame, so source-plane alpha and final-composite output alpha
must not be confused. The exact raster partition is:

| Original PPU phenomenon at frame1856 | Count |
| --- | ---: |
| Front96 independent opaque source pixels | 319 |
| Rear97 independent opaque source pixels | 321 |
| Front-only pixels, all changed after front96 removal | **162 / 162** |
| Different-RGB front/rear overlap, all changed to exact rear RGB | **143 / 143** |
| Same-RGB overlap, unchanged after front96 removal | **14 / 14** |
| Rear-only pixels, final stock RGB equals actual rear source RGB | **161 / 164** |
| **Rear-only pixels not visible in final Original RGB** | **3 / 164** |
| Rear-only pixels changed after removing front96 | **0 / 164** |
| Final changed outside actual front96 source | **0** |

The three real mismatches are:

| Original logical XY | Actual rear97 source RGB | Stock final Original RGB | After removing front96 RGB |
| --- | --- | --- | --- |
| (188,156) | (49,49,49) | (57,57,255) | (57,57,255) |
| (189,156) | (74,74,74) | (57,57,255) | (57,57,255) |
| (189,157) | (16,16,8) | (57,57,255) | (57,57,255) |

The exactly corresponding **upper viewport pixels**, translated
by the source-proven split-screen offset **−113 source rows**, tell a
particularly useful story: (188,43), (189,43) and (189,44) have
original stock **RGB equal to the actual rear source** colours
(49,49,49), (74,74,74) and (16,16,8), respectively. The very same
source colours fail to appear in the original lower screen at
(188,156), (189,156) and (189,157). This is strong
**viewport-dependent final-composite** evidence, not a malformed
or absent racer texture. The new validator fails if the stock
top counterpart does not reproduce each original colour.

These points belong to the **original rear97 source alone**.
Neither overlap with front96 nor deletion of front96 can explain
their final RGB mismatch. An independent Original presentation
stage already wins over their emitted source colour at those
coordinates. Its hardware layer/priority identity remains
unverified; source/final RGB colour cannot identify the
actual window, background or compositor bit that caused it.
The blue RGB also appears elsewhere in the Original, so this
must not be described as proving the later countdown numeral's
hardware implementation.

The actual independent front96 removal changes **305** pixels,
exactly the 162 front-only plus143 different-colour overlaps,
and the other 14 same-colour overlaps remain numerically
unchanged. This validates the expected 2P lower front/rear
ordering for almost the whole racer, with the **three
independent rear-only exceptions** retained, not silently waived.

## Reproducible bounded inspection

`tools/check_baldosa_2p_lower_rear_1856_gap.py` reuses the raw
native artifact's stock/source96/source97/same-frame-front96-
removal PAMs and its already accepted source/native removal
reports. It verifies exact original stock SHA, source slot/frame
metadata and source colours, six unmodified whole-Original
raster controls, the actual native front96 deletion report,
full 342×224 final delta, precise three pixel coordinates and
colours, and zero changes outside front96 source. There are
no guess-based rectangle masks and no new native guest process.

```sh
python3 tools/check_baldosa_2p_lower_rear_1856_gap.py \
  --native-artifact-root path/to/extracted-successful-AOT-11694649120 \
  --out path/to/qa08-lower-rear-source-gap-1856.json
python3 -m unittest tests.unit.test_check_baldosa_2p_lower_rear_1856_gap
```

Eight independent synthetic tests cover exact source partitions,
three-style rear-source-only gaps, native front-only and
different/same RGB overlap changes, out-of-source final changes,
invalid shapes, improper reveal after removing front, and
absence of genuine source alpha.

The copyright-safe numeric counts, original native SHA identities
and the exact three RGB coordinate exceptions are recorded at
[`analysis/data/qa08-original-2p-lower-rear-three-source-gaps-1856.json`](../analysis/data/qa08-original-2p-lower-rear-three-source-gaps-1856.json).

**Boundary:** These are literal Original source/final image observations,
not a new PPU renderer, full frame-accurate hardware layer oracle,
automatically permitted HD sprite paint, collision/character
model proof, 2P source deletion exception or Windows release
approval. They reinforce the policy to preserve unmodified
Original presentation whenever full 2P BG/window/OBJ ownership
is not independently settled.

# QA-08: original 2P countdown-foreground racer occlusion

**Status: authenticated native Original PPU pixel observation, not an HD
release mask or proof of winning hardware priority.** Real source slot96/97
racer imagery is emitted but obscured at two distinct two-player frames
during an onscreen countdown numeral.

## Genuine native source witness

The already **successful** pinned Baldosa AOT [38097914195](https://github.com/gamesbyian/UR-Recomp/actions/runs/38097914195)
(artifact `11686843233`) and a subsequent source-preserving successful
[38115756178](https://github.com/gamesbyian/UR-Recomp/actions/runs/38115756178)
(artifact `11693865103`) retain genuine 342×224 Original PPU image
sources and 12 independently emitted stock OBJ racer-slot planes across
native 2P guest frames 1856, 1872 and 1888. Their accepted per-source
reports prove original slot/frame identity, unchanged 6 full Original
frames in each source run and native guest CRC identity.

| Original guest frame | Lower slots96+97 emitted total | Distinct lower occupied source coordinates | Final Original RGB equals blue `57,57,255` at those coordinates | Lower slot96 / slot97 source-RGB matches |
| --- | ---: | ---: | ---: | --- |
| 1856 | 640 | 483 | 3 / 483 | 319/319 and 175/321 |
| **1872** | **655** | **411** | **411 / 411** | **0/330 and 0/325** |
| **1888** | **646** | **409** | **409 / 409** | **0/322 and 0/324** |

While *all* lower-racer emitted alpha positions are final blue on
1872 and 1888, the upper source **slot98 still matches Original
at all 325/325 and 324/324 positions**. The unmodified source picture
prominently shows the large blue countdown **“2”** over the bottom
racer position in precisely these two later frames. The earlier frame1856
shows both racers against their respective backgrounds. Native PPU has
**not ceased emitting lower racer imagery** in the countdown frames.

The prior ordinary source-overlap reports mark both frames1872 and1888
`unproven` rather than `passed` because they do not show the bottom
racer source colours in final Original. This investigation explains
the **observational discrepancy** and prevents prematurely calling it a
low-viewport renderer defect. It highlights a serious HD fidelity risk:
painting racer art above all final foreground/countdown elements would
make a hidden racer incorrectly visible through the numeral.

## Persistent countdown-colour foreground over moving racer sources

A stronger **temporal source/foreground observation**, using the same
unmodified Original PPU frames, records the full 342×224 binary mask
of all pixels whose final native RGB equals `57,57,255`. The entire
**16,770-pixel blue colour mask is byte-identical at both guest1872
and1888**, SHA256
`6c311efcd2377fcc40fdf76cff3d82e4b5926bbd9268b3d3f5feec7e282c3d36`
over 76,608 row-major occupancy bytes. Its inclusive logical
bounding box is `[103,8,260,200]`. At the earlier frame1856,
the blue mask differs (9,286 pixels; SHA256
`3dca34902e307495c64b1fbd87b4148e297b2052dff84dc0dca3ef258bcfcfdf`).
Both original lower OAM rider **source alpha masks demonstrably
change between1872 and1888**, independently of the stationary
final blue colour region, and both moving source instances remain
fully covered. That rules out a *frozen source racer* as the cause
of its invisibility in these exact samples.

The source-validated detector now fails if the full Original
blue-colour mask drifts even at a pixel **outside** the rider
silhouettes, or if lower rider alpha remains identical while it
claims movement. Full mask RGB identity is an observational frame
property, not an accepted hardware OBJ/BG layer ID or reusable
production occlusion mask. Treat its countdown-“2” interpretation
as supported by direct visual comparison, not proven compositor
priority.

## Actual PPU pair-removal counterfactual: no final effect at1872

A further **independent native PPU intervention** has now
completed at the same genuine original 2P guest1872 in the
already existing AOT workflow:
[run `38117375415`](https://github.com/gamesbyian/UR-Recomp/actions/runs/38117375415),
artifact **`11694242433`**. The native log authenticates an
exactly-armed `UR_RACER_HD_WIDE_REMOVE_PAIR frame=1872
slots=96-97 status=armed guest_unchanged=1` counterfactual, and
the workflow's stock-vs-removed-route full guest CRC comparison
completed successfully.

Independently reading every one of the **76,608 Original RGBA
pixels** in both archived stock and pair-deleted 342×224 PPU
images gives an **identical complete frame**, SHA256
`bdc3b13d2129e7fd7a20f4cf00539fc2976ba1b028f76386a395e6fdef4e2f2b`
in both. The lower source planes still emit 330 and325
pixels (655 counted with overlaps, **411 distinct coordinates**),
all covered by countdown-blue final Original RGB. Removing **both**
lower original slots together causes **zero** final Original pixel
change in this authenticated frame. This is stronger than the
earlier source/final-colour observation and closes the specific
*causal* 2P countdown pixel-effect question.

The AOT workflow itself remained **red** solely because its new
checker mistakenly required 5,447 **one-player** guest CRC records
on this **2,473-frame two-player** route. The native execution and
`cmp` had already succeeded. That validator-count defect was
corrected on [PR #1330](https://github.com/gamesbyian/UR-Recomp/pull/1330)
(commit `164ca851815300f596e1aad382cc38360f13b2da`);
do not claim its corrected exact-head native job is already
accepted until confirmed. The independently recovered
source/image/marker provenance and zero-result count are retained
at [`analysis/data/qa08-original-2p-countdown-pair-native-causal-zero-1872.json`](../analysis/data/qa08-original-2p-countdown-pair-native-causal-zero-1872.json)
without redistributing ROM graphics. This single-frame zero
result cannot identify which SNES layer painted the blue numeral,
or justify disabling the original two racers outside an explicit
native diagnostic. Any normal HD overpaint would still risk a
countdown fidelity defect.

## Already-retained 4× Original density parity

The **same authentic native AOT artifact** also retains complete
`1368×896` Original 4× fallback frames1856,1872,1888. An independent
full-RGBA comparison against every corresponding original `342×224`
stock pixel expanded to one `4×4` square measured **zero physical
pixel differences across all 3,677,184 output pixels**. In particular,
the large countdown-blue lower-racer covering stays intact in all
three 4× source-density captures. The exact three 1× and 4× source
image SHA pairs and zero-difference counts are retained at
[`analysis/data/qa08-2p-countdown-original-4x-density-parity-1856-1888.json`](../analysis/data/qa08-2p-countdown-original-4x-density-parity-1856-1888.json).
This reinforces the existing Original 4× nearest-raster contract; it
does **not** test separately captured physical `3840×2160`, native
guest correctness, replacement HD sprite priority or rendered 4K art.

## Offline reproducibility

Run **without recompiling, replaying guest routes, downloading tools
or generating any new images**:

```sh
python3 tools/check_baldosa_2p_countdown_source_occlusion.py \
  --native-artifact-root path/to/extracted-existing-native-AOT \
  --out path/to/qa08-original-countdown-occlusion.json
python3 -m unittest tests.unit.test_check_baldosa_2p_countdown_source_occlusion
```

The strict source checker reads exact native P7 original RGBA,
validates independent per-slot source SHA, absolute raster-band placement,
slot/frame provenance, complete unmodified stock raster SHA, 12 accepted
original source reports with six matching original captures and
guest-CRC parity attestations, and three different final Original
frame hashes. It rejects a one-byte blue colour mutation, missing
or forged source records, stale main frames and cross-band OBJ alpha.
The bounded machine-readable raw artifact-derived results appear in
`analysis/data/qa08-original-2p-countdown-source-colour-1856-1888.json`;
**no copyrighted source graphics bytes are checked in**.

**Explicit non-claims:** The large “2” is visually identifiable in
the captured Original PPU, but identical blue final pixels **do not prove
the exact responsible OBJ/BG/window layer or its causal priority**. No
lower-slot removal experiment is asserted at frames1872/1888.
The analysis cannot license per-pixel destructive Original OBJ erasure,
a general occlusion mask, authored 4× character geometry or any current
Remastered/4K product/release certification. Conservative original
presentation remains mandatory until the exact full moving visibility
and approved-character-art requirements are met.

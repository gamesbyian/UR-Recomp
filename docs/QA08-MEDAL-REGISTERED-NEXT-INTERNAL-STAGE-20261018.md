# QA08: correct video callback versus following 2014 medal-painter stage

18 October 2026 | **source-only temporal discriminator, not a renderer fix**

The original 2014 Snes9x sprite painter [#1839](https://github.com/gamesbyian/UR-Recomp/pull/1839) and callback registration [#1846](https://github.com/gamesbyian/UR-Recomp/pull/1846) show that an internal painter field and an archived callback field sharing a nearby number cannot be substituted indiscriminately. Separately compiled and source-authenticated Modern+HDMA/V0 Windows PPU [#1867](https://github.com/gamesbyian/UR-Recomp/pull/1867) still reproduces the real **890,205** original/native RGB5 differences on 263 frames, including a fixed **296-pixel result-medal mask on 25** samples. This witness investigates **five selected coordinates** in that region, with two independently observed result fields. It does *not* infer the winner from native OAM, apply a frame shift, edit source pixels, or claim 296/296 pixel ownership.

## Three different genuine source stages

Each row below uses exact original callback at label **4031** or **4175** (human one-based output 4032 or 4176), genuine native guest output at **4032** or **4176**, and, as a deliberately **invalid replacement for the video callback**, the following internally executed original Snes9x render-stage field labeled 4032 or 4176. The genuine 2014 original painter at label 4031/4175 **does agree with its own registered callback at all ten samples**. All these are real source-visible pixels.

| Coordinates | Genuine original callback RGB5 | Genuine native final RGB5 | Following internal original painter RGB5 | Following painter owner |
| --- | --- | --- | --- | --- |
| (207,91) | (14,7,9) | (14,14,14) | (14,14,14) | BG0 |
| (205,115) | (14,7,9) | (16,5,2) | (16,6,3) | OBJ113 |
| (205,139) | (16,16,16) | (14,7,9) | (14,7,9) | OBJ114 |
| (225,96) | (25,23,17) | (16,15,13) | (16,15,13) | OBJ97 |
| (225,120) | (25,23,17) | (16,15,13) | (16,15,13) | OBJ96 |

The same values repeat at 4032 and 4176 (ten source-registered observations). Thus **0/10 actual original callbacks equal the native pixel**, but **8/10 native pixels numerically equal the following original internal painter stage**. The other two are identical (205,115) samples with a strictly bounded native-minus-painter RGB5 delta **(0,-1,-1)**. This is evidence of a *possible localized source/raster phase relationship*, **not proof of a specific NMI clock error, native consumed button timing, or PPU bug**. It also does not turn painter-stage RGB565 into native post-colour-math final pixels: the stage distinction is retained, and native RGB5 green is compared after correctly truncating Snes9x's six-bit green. Frame+1 matching would be a failed original acceptance test; it is recorded solely as a counterfactual discriminator.

The real source-original callback archive is 90-day artifact **12075111053** (outer SHA256 `3475ee87b5b20768f9377d8d1c787927955c33ee6d4388dae008f5486a81370e`; nested original.zip SHA256 `72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e`). The independently captured actual original painter archive **12150037795** SHA256 is `8387c413d42cf8d2da2a61ba3ec67e8375394f938171dc4d73a3e4ba567920e4` (252 original sprite calls and 360 stage observations). Their **actual 26 source-original logged input transitions** match SHA256 `9c9072123a8eadceb7af228088a51bf074e362f81772500daf3ac83a382aa4f0`. The real compiled integrated Windows PPU observer archive **12151839452** SHA256 is `832c08263e2d3013d5b15df82b2b0574fabfd3114194b7cbef9f6bb1b2959727`, with inner 263-source-image ZIP SHA256 `c36fdd0238735e739219b013d25665e42a008a7827ee97631a322217c9f4f0cd` and unchanged authentic 5484 guest CRC SHA256 `b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568`.

## Independent recurring source-image crosscheck, all 25 result medal appearances

The same two SHA-pinned original/native full-image archives contain **every 48th sampled result source** from native guest **4032 through 5184 inclusive**, 25 genuinely captured images and 25 distinct independently captured 2014 Snes9x callback images at original labels guest−1. Comparing the same five pixel coordinates (without any alternate source-frame registration or synthesized image), **all 125/125 original/native RGB5 pixel comparisons disagree**.

Four color-bearing selected medal coordinates reproduce the **same registered original/native color pair at all 25** samples. The fifth point, (205,139), is different: the genuine original **final callback** grayscale cycles through **(15,15,15), (16,16,16), (17,17,17), (20,20,20)**, while native retains **(14,7,9)** at every one of these 25 frames. The original source painter proves BG0 ownership at this coordinate for callbacks **4031 and 4175 only**; its ownership in the other 23 periodic fields was not instrumented and is deliberately unclaimed. The underlying four-state source gray cycles and the stable medal silhouette therefore overlap spatially here, rather than becoming a single new shading phenomenon. This recurrence extends the **registered negative** to 125/125 real samples; the **counterfactual original internal painter-stage comparison remains limited to the ten genuinely instrumented points in two frames**. There are no original painter-stage captures for the other 23 periodic fields, so their actual winning original OBJ numbers remain unproved.

This supports two separately actionable next discriminators: source-authenticated original versus native medal tile/OAM publication at a common consumed-input/beam boundary, and separately the genuine CPU palette/CGRAM ingestion history at source field (205,139). It does not show that changing either native sprite priority or grayscale brightness would repair the other. No global frame offset, guessed draw-order change or output recolor is allowed by either observation.

## Reproduce and reject unsafe conclusions

```sh
python3 tools/qa08_verify_original_medal_next_internal_stage.py \
  --original-outer /private/original-artifact-12075111053.zip \
  --painter /private/original-painter-12150037795.zip \
  --native-outer /private/native-integrated-source-12151839452.zip \
  --out /private/qa08-medal-original-next-stage.json
python3 -m unittest tests.unit.test_qa08_verify_original_medal_next_internal_stage
```

The stdlib-only verifier refuses altered outer/nested source SHA256s, false painter/original actual input identity, missing/cropped 2014 callback and 256×224 P7 sample, unexpected native fourth channel, wrong 2014 BG/OBJ stage or duplicate source observations, and a change to the **0/10 vs 8/10** original/next-painter counts. Two independent snapshot locations are necessary but insufficient to prove causal frame phase. This tool does **not** touch renderer/CPU/APU, compile a new emulator, change Modern profiles or start a broad Actions research factory. The remaining 296-pixel mask needs true source-registered source-original/native guest NMI, final CGRAM, actual per-line OAM and post-colour-math raster evidence. Do not promote #1807 brightness, recolour a medal, globally re-time video or assert graphics QA acceptance on this diagnostic.

**Disposition:** source-only counterfactual instrument, no gameplay/presentation fix; original/native acceptance remains held.

Durable compact, ROM-art-free result summary: [QA08 25-field medal source histogram](../analysis/data/qa08-medal-recurring-registered-source-20261018.json). It retains exact counts and SHA provenance after 90-day Actions image retention expires; full per-frame capture validation remains in the executable verifier and its original artifacts.

# QA08: actual 112-field grayscale pixel budget across full-size Snes9x/Win32 source

19 October 2026 | **Read-only graphics causality prioritization, not a PPU correction or release acceptance.**

This result isolates a measurable part of the original/native 2P 2014-Snes9x result-screen mismatch from the same **authenticated 263-frame full-raster** experiment already archived by [QA08 integrated Windows source](QA08-MODERN-CLEAN-FULL263-ORIGINAL-WIN32-20261018.md). It reuses real original Snes9x callbacks f−1 and actual native Windows guest frames f at the *only registered video alignment*, without shifting frames, recolouring a pixel, manufacturing an image or starting another emulator. The 2014 callback source is inner ZIP SHA256 `72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e` from artifact **12075111053**. The actual compiled integrated PPU source is outer ZIP SHA256 `832c08263e2d3013d5b15df82b2b0574fabfd3114194b7cbef9f6bb1b2959727` from artifact **12151839452**, 263-image inner ZIP SHA256 `c36fdd0238735e739219b013d25665e42a008a7827ee97631a322217c9f4f0cd`, unchanged 5,484-frame guest CRC SHA256 `b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568`.

## Actual full-frame pixel census

At native guest 4064,4176,4288,4400,4512,4624,4736,4848,4960,5072,5184,5296,5408, the independent source archives contain **13 genuinely captured 256×224 images**. These labels are spaced by precisely 112 guest frames. At every source pixel we compared the original callback's BGRX, native P7 RGB channels and **all three five-bit channels**. A mismatch means *any* RGB5 component differs, not only differences larger than one.

| Full-size measured population | Mismatched RGB5 pixels |
| --- | ---: |
| Complete 263 registered original/native source frames, previously authenticated | **890,205** |
| All mismatches in these 13 actual 112-spaced captures | **359,013** |
| Both original and native were grayscale at a mismatching pixel | **342,086** |
| Exact four-state gray-value substitutions below | **318,775** |

The actual four recurring grayscale pairs are:

| Original final RGB5 gray | Native final RGB5 gray | Genuine pixel occurrences in these 13 captures |
| --- | --- | ---: |
| (15,15,15) | (20,20,20) | 53,658 |
| (16,16,16) | (15,15,15) | 107,868 |
| (17,17,17) | (16,16,16) | 52,716 |
| (20,20,20) | (17,17,17) | 104,533 |
| **Total** | | **318,775** |

This **four-state class alone represents 35.8% of every original/native RGB5 mismatch across all 263 sampled frames** (318,775/890,205), or 88.8% of the 359,013 errors on those 13 source frames. Across the 13 samples, **95.3% of all mismatched pixels are gray in both original and native** (342,086/359,013). Each of the 13 individual source frames retains more than 20,000 exact four-state mismatches. Separately, the forced-black guest4016, recurring medal/OBJ, non-gray result colours, early countdown and other transitions remain errors; this census does not attribute their causes to the same cycle.

The **exact per-frame wrong/gray/cycle populations**, 2014 source identities and fail-closed release-negative flags are committed as [machine-readable summary](../analysis/data/qa08-real-112field-13frame-grayscale-error-budget-20261019.json). No copyrighted ROM/source raster bytes enter Git. Unlike a visual mask at a single medal coordinate, this identifies the **dominant, independently recurring full-frame grayscale *presentation symptom*** and tells a CPU/CGRAM timing investigation where its highest pixel impact lies.

## Independent rerun on immutable archives

```sh
python3 tools/qa08_verify_112field_grey_pixel_budget.py \
  --original /private/original-2014-inner.zip \
  --native /private/compiled-integrated-ppu-artifact-12151839452.zip \
  --out /private/QA08-gray-cycle-counts.json

python3 -m unittest tests.unit.test_qa08_verify_112field_grey_pixel_budget
```

The stdlib-only validator refuses incorrect outer/nested ZIP identity, missing or duplicate real callback labels, wrong full-route guest CRC, altered original/native per-image SHA256, non-256×224 source geometry, forged fourth channels, changed source component ordering, wrong registered f−1 label, changed old 890,205 total or a changed measured 13-field grayscale census. It produces numbers only and does not execute a new emulator.

## Engineering interpretation and strict hold

The prior [source-verified $2121/$2122 original/native four-word writer join](QA08-RESULT-GREY-PHASE-112-CYCLE-20261017.md) already established matching original/native values at **six of six** genuine CPU palette packets with a two-field native writer-label lead, but did not prove equivalent guest instruction/beam times. This new pixel budget is a separate **final displayed raster** observation. It does not prove that a particular writer instruction, DAC, output brightness operation, NMI entry, palette-ingestion order or native renderer implementation caused the four-state RGB5 relationship. Joining the exact original/native consumed input, executed writer-PC, scanline H/V and the final CGRAM/main/sub state remains a CPU↔PPU source-bound research responsibility.

**Do not** globally remap gray15/16/17/20, shift the comparison by 112 or 32 frames, copy original raster data into the native game, activate the experimental brightness trial [#1807](https://github.com/gamesbyian/UR-Recomp/pull/1807), discount medal errors, or mark any QA08/release gate as accepted. [Issue #1774](https://github.com/gamesbyian/UR-Recomp/issues/1774) and independent [graphics QA #974](https://github.com/gamesbyian/UR-Recomp/issues/974) retain unresolved causality and acceptance. Original 342×224 7:6 PAR, Original 1×–4×, real Windows UHD and rejected HD racer likeness remain separate.

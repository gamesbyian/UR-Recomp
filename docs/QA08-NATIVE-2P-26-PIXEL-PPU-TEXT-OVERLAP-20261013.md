# QA-08: complete 26-pixel original 2P racer/BG3 text composition witness

**Status: proposed real pinned native AOT experiment, not yet accepted.**

The accepted [two-pixel original-native source proof](QA08-ORIGINAL-PPU-MAIN-SUB-PIXEL-DISCRIMINATOR-20261013.md) in merged #1433 identified BG3 red13 as main and OBJ as subscreen at both (133,50) and (133,162), with live fixed colour RGB5 red15 in the upper field and green19 below. The older [26-pixel source-registration/counterfactual evidence](QA08-2P-NATIVE-BG3-COLOUR-CONSTRAINTS-20261013.md) recorded **13 exact overlapping source positions in each viewport**, all with unchanged green and blue and +13 red5 in the final output. The **other 24 main/sub source owners have not yet been measured**. This bounded discriminator closes exactly that gap.

## New source probe, exact geometry

`tools/qa08_patch_ppu_text26_source.py` derives a second purely read-only native PPU observer from the exact already accepted two-point source emitter. It patches only the pinned throwaway `baldosa/snesrecomp@075fbe4c` AOT checkout and refuses source drift, duplicate patching or an absent original two-point witness. Requires `UR_QA08_PPU_TEXT26_FRAME=2208`. Selects only these unmodified native coordinates, measured in a real original source:

| Native output Y | Original X positions |
| --- | --- |
| 47 and 159 | 133 |
| 48 and 160 | 132, 133, 135, 136 |
| 49 and 161 | 132, 133, 135 |
| 50 and 162 | 132, 133 |
| 51 and 163 | 132, 133 |
| 52 and 164 | 132 |

At these 13+13 pixels only, the source patch reads the **live actual PPU main/sub priority tags, CGRAM-derived colour RGB15, fixed15, math gate, window clip and finished Original RGB**. No state, timing, OAM, BG buffers, ROM, guest WRAM, renderer decisions or host graphics modes are modified. The patch is never used in shipping.

## Strict integrated native acceptance

The existing single pinned Baldosa AOT job already executes and independently checks three original/native USA 2P complete guest processes at frame2208: untouched stock Original, only upper front OBJ98 removed, only lower front OBJ96 removed. Each compares the **full 2,473 guest CRC records**, captures stock and removed 342×224 PPU original rasters and runs the preexisting causal and two-pixel colour source checks.

The new `check_qa08_native_text26.py` reads the **same** real three logs and P7 rasters, plus the independent complete 26-pixel causal report and source colour field journal. It requires exact stock/removal SHA256, all 26 distinct original source coordinates, exact cross-viewport (0,+112) source pairing, exactly **78 native PPU source records**, per-pixel final RGB equality, authentic BG3-main red13 plus OBJ-subscreen racer colour at all 26 stock source positions, absent subscreen and correct **live HDMA fixed colour** at precisely the 13 deleted-front positions per respective process, preservation of opposite viewport OBJ and exact 5-bit additive colour-math arithmetic. A missing or surprising source owner is a **genuine red native acceptance gate**, not a reason to manufacture an art overlay or weaken the comparator.

Because the original native two-point source probe is kept intact and checked separately, there are no additional emulator processes, artifact families or expensive new runner factories. The new result `ws342_native_text26_2208.json` is retained in the existing native artifact when the exact-head job passes. Synthetic unit fixtures reject source drift, tampered z-buffer layer, incomplete registers, wrong 5-bit colours, missing samples and unequal corresponding viewports; those fixtures do **not** constitute native game acceptance.

**Limits:** Source proof at these 26 text-covered rider pixels, even if fully accepted, does not certify the other ~600 combined racer source alpha pixels, true event completion, original physical hardware midscanline timing, licensed art likeness or approval of the procedural HD racer. Preserve native 256×224 and 7:6 PAR, authentic 342×224 widened world, unmodified Original fallback and independent QA authority.
# QA-08: first native PPU main/sub per-pixel ownership discriminator

**Status: proposed source experiment pending pinned Baldosa AOT.** Reuse the already required true Original USA 2P route and its two independently repeated guest2208 diagnostic front-slot removals. Do not run an additional factory, alter the guest or change shipped PPU composition.

## Why these two pixels

The authenticated [native colour constraint investigation](QA08-2P-NATIVE-BG3-COLOUR-CONSTRAINTS-20261013.md) finds upper front slot98 and lower front slot96 both have red5 +13 at 13 original source/text overlap coordinates. Normal Original at **(133,50)** and **(133,162)** has the same underlying isolated racer RGB and red-only +13. The real PPU register journal is uniformly CGADSUB=0x04, CGWSEL=0x02 and fixed RGB5 (0,19,0) at every visible row. Deleting slot98 changes the upper output to RGB5 (28,0,0); deleting slot96 changes the lower to RGB5 (13,19,0).

## Exact instrumentation seam and default safety

`tools/qa08_patch_ppu_pixel_compose_probe.py` adds an opt-in read-only local block after the pinned `baldosa/snesrecomp@075fbe4c` compositor writes each final native raster RGB pixel. It reads the **actual** existing main and subscreen `bgBuffers`, source-layer codes, palette indices, RGB15, CGADSUB/CGWSEL/fixed colour, the current clip/math eligibility and final RGB at the two selected source points. It neither writes the arrays nor changes timing decisions, OAM, VRAM, guest memory, colour arithmetic, widescreen materialization or host rendering. The patch is scoped to the disposable AOT copy, fail-closed on source drift, not a production PPU modification.

Enable only via `UR_QA08_PPU_PIXEL_FRAME=2208` in the already-existing 2P stock process and two guest2208 source-removal processes. Only SNESRecomp emulator-frame counter 2208 and source-space X133/native rows 50 and162, with exactly +43 logical side margins, can emit a diagnostic record. If the emulator counter and guest frame differ, the strict witness **fails**, rather than quietly treating an approximate neighbouring frame as authentic.

`tools/check_qa08_native_main_sub_pixel_probe.py` accepts two original per-pixel records in each process only if all six exactly match their independently hashed original P7 stock/removed source raster pixels, native register states, exact guest frame and per-slot original-native counterfactual receipts. The existing journal and guest CRC acceptance must already pass. It emits `ws342_native_main_sub_pixel_2208.json` in the normal existing native AOT artifact. Exact-head unit and full native checks must pass before the report gains factual status.

## Decision from actual source

If stock top and bottom have actual main-layer=BG3 and sub-layer=OBJ with math permitted and the palette colours consistent with their native RGB outputs, the BG3-main/sub-OBJ hypothesis receives its first directly observed source witness **at those two pixels only**. Compare how the exposed sub tag changes after deleting just the upper or lower front OBJ and whether the fixed RGB5 (0,19,0) replaces an empty subscreen. Any contradictory result remains useful, with the actual raw tags preserved; do not force a success flag.

Neither the 26-pixel arithmetic check nor two directly observed source-layer pixels establish every racer pixel’s PPU winner, physical SNES subscanline timing, a new 3D character likeness, true 2P complete-event progression, nor a release gate. Retain the original source PPU, 256×224, 7:6 PAR, 4× Original fallback and real 342 logical-world margins. The procedural HD racer remains artistically vetoed.

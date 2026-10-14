# QA-08: first native PPU main/sub per-pixel ownership discriminator

## First exact native PPU pixel capture: successful source witness, checker correction pending

**Native AOT [run 38498698636](https://github.com/gamesbyian/UR-Recomp/actions/runs/38498698636), artifact 11864599802, 2026-10-13.**
Unit/hygiene passed and native Original 2P guest2208, 2,473 guest CRCs,
full original pixel SHA and both independent front-slot-removal causality
tests all passed; the new QA pixel checker failed at its **incorrect
assumption that fixed15 must equal the saved field baseline 0x0260 at
every rendering row**. The actual native PPU logged all six requested
records in the three full native processes:

| Native PPU pixel (x=133) | Main z-buffer | Sub z-buffer | Main RGB15 | Sub RGB15 | *Live* fixed RGB15 | Final RGB24 |
| --- | --- | --- | --- | --- | --- | --- |
| Stock y50 | F21B BG3 | A6B3 OBJ palette group6 | 000D | 18C6 | **000F** | **9C3131** |
| Stock y162 | F21B BG3 | A4C3 OBJ palette group4 | 000D | 18C6 | **0260** | **9C3131** |
| Remove front98 y50 | F21B BG3 | 0500 empty | 000D | 0000 | **000F** | **E70000** |
| Remove front98 y162 | F21B BG3 | A4C3 OBJ | 000D | 18C6 | 0260 | 9C3131 |
| Remove front96 y50 | F21B BG3 | A6B3 OBJ | 000D | 18C6 | 000F | 9C3131 |
| Remove front96 y162 | F21B BG3 | 0500 empty | 000D | 0000 | **0260** | **6B9C00** |

At both stock pixels main is **BG3 text red5=13** and a real
OBJ is the **subscreen colour operand RGB5=(6,6,6)**. The PPU
colour-math gate is on, CGADSUB=04, CGWSEL=02, subscreen is
rendered, and the main pixel is not clipped. Thus red13 plus
sprite grey6 yields RGB5=(19,6,6), final RGB24=(156,49,49).
When the front OBJ is removed, the subscreen tag 0500 has an
**empty palette index** and native PPU source uses its *live* fixed
operand: top RGB5=(15,0,0), yielding (28,0,0); bottom
RGB5=(0,19,0), yielding (13,19,0). The two viewports use distinct
underlying OBJ palette group codes 6 and4; **do not require group4
in both**.

The journal captured the PPU's saved field-start fixed RGB15=0260,
but that baseline does **not** incorporate subsequent render-time
HDMA writes. The pinned source runs `dma_doHdma` during line
replay and the CPU-side register journal intentionally excludes
render-generated HDMA writes; source observations prove the
effective per-line switch, but **do not yet attribute it to a
particular HDMA channel or table**.

The checker correction must preserve the saved field-baseline gate
while validating the **actual per-row live fixed15**,
independent native main/sub buffers, palette RGB15 and calculated
final RGB24 at all six samples. It must **not** replace the
accurate native trace with a synthetic expected state.
The first red native job is valuable *source evidence* but not
a successful strict-accepted new per-pixel report until that
corrected exact-head job passes.

**Status: proposed source experiment pending pinned Baldosa AOT.** Reuse the already required true Original USA 2P route and its two independently repeated guest2208 diagnostic front-slot removals. Do not run an additional factory, alter the guest or change shipped PPU composition.

## Why these two pixels

The authenticated [native colour constraint investigation](QA08-2P-NATIVE-BG3-COLOUR-CONSTRAINTS-20261013.md) finds upper front slot98 and lower front slot96 both have red5 +13 at 13 original source/text overlap coordinates. Normal Original at **(133,50)** and **(133,162)** has the same underlying isolated racer RGB and red-only +13. The recorded CPU journal has CGADSUB=0x04, CGWSEL=0x02 and **saved field-baseline** fixed RGB5 (0,19,0), but a later real PPU probe observed different **live** fixed RGB5 at the upper rendering row. Deleting slot98 changes the upper output to RGB5 (28,0,0); deleting slot96 changes the lower to RGB5 (13,19,0).

## Exact instrumentation seam and default safety

`tools/qa08_patch_ppu_pixel_compose_probe.py` adds an opt-in read-only local block after the pinned `baldosa/snesrecomp@075fbe4c` compositor writes each final native raster RGB pixel. It reads the **actual** existing main and subscreen `bgBuffers`, source-layer codes, palette indices, RGB15, CGADSUB/CGWSEL/fixed colour, the current clip/math eligibility and final RGB at the two selected source points. It neither writes the arrays nor changes timing decisions, OAM, VRAM, guest memory, colour arithmetic, widescreen materialization or host rendering. The patch is scoped to the disposable AOT copy, fail-closed on source drift, not a production PPU modification.

Enable only via `UR_QA08_PPU_PIXEL_FRAME=2208` in the already-existing 2P stock process and two guest2208 source-removal processes. Only SNESRecomp emulator-frame counter 2208 and source-space X133/native rows 50 and162, with exactly +43 logical side margins, can emit a diagnostic record. If the emulator counter and guest frame differ, the strict witness **fails**, rather than quietly treating an approximate neighbouring frame as authentic.

`tools/check_qa08_native_main_sub_pixel_probe.py` accepts two original per-pixel records in each process only if all six exactly match their independently hashed original P7 stock/removed source raster pixels, native register states, exact guest frame and per-slot original-native counterfactual receipts. The existing journal and guest CRC acceptance must already pass. It emits `ws342_native_main_sub_pixel_2208.json` in the normal existing native AOT artifact. Exact-head unit and full native checks must pass before the report gains factual status.

## Decision from actual source

If stock top and bottom have actual main-layer=BG3 and sub-layer=OBJ with math permitted and the palette colours consistent with their native RGB outputs, the BG3-main/sub-OBJ hypothesis receives its first directly observed source witness **at those two pixels only**. Compare how the exposed sub tag changes after deleting just the upper or lower front OBJ and whether the fixed RGB5 (0,19,0) replaces an empty subscreen. Any contradictory result remains useful, with the actual raw tags preserved; do not force a success flag.

Neither the 26-pixel arithmetic check nor two directly observed source-layer pixels establish every racer pixel’s PPU winner, physical SNES subscanline timing, a new 3D character likeness, true 2P complete-event progression, nor a release gate. Retain the original source PPU, 256×224, 7:6 PAR, 4× Original fallback and real 342 logical-world margins. The procedural HD racer remains artistically vetoed.

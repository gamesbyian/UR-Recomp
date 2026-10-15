# QA-08: native countdown all-channel HDMA PPU-register source census

**Read-only disposable instrumentation staged, not yet an executed
original/native register comparison.** The exact real 2P countdown
global-prime scene reproduces genuine Snes9x original callback1855 at
57,344/57,344 RGB5 pixels. Both channel7-only and combined
channel5+7 remain 460 pixels wrong in two verified upper/lower
window-contour components. Correcting channel5 alone as well as
channel7 changes none of those residual pixels (merged #1595).

The existing source-accepted native Baldosa 2P HDMA probe previously
logged channel5/7 at *post-GO guest2208*. It cannot establish which
other actual HDMA source channels or registers are active at
*countdown guest1856*. The next narrow action is therefore a
comprehensive **read-only transfer census before another blind
first-line DMA prime experiment**.

New tools/qa08_patch_hdma_all_channels_source.py only patches the
already instrumented **disposable** pinned Baldosa SNESRecomp
runner/src/snes/dma.c, after the independently accepted
qa08_patch_hdma_coldata_source.py observer. It keys off the exact
source read-only marker and the real after-BBUS snes_writeBBus call,
rejecting uninstrumented, duplicated or otherwise modified source.

An explicit environment variable UR_QA08_HDMA_ALL_CHANNELS_FRAME
selects at most **one actual guest frame**; default is disabled.
On each real HDMA PPU B-bus write in that frame, the observer records:
true native guest frame, read-only PPU journal frame and line,
source channel 0..7, B-bus address and actual written byte, A-bus
bank/address, mode, direct/indirect, descriptor table pointer and
channel repetition state. The 16,384-event cap emits an overflow
marker instead of silently truncating. It must be checked by
the eventual parser and source-bound CI job.

No PPU, DMA, guest, ROM or host frame value is modified by the
observer. The previously established channel5 COLDATA/CGADSUB and
channel7 INIDISP independent source watchers remain intact and
separately gated. The probe is intended to execute at **guest1856**
within the already existing authentic USA 2P workflow after the
separate moving 37-frame source experiment is reconciled, so
additional expensive AOT builds are not started unnecessarily.

Evidence required before naming a causal other channel: actual
original USA executed 65816 producer PC/source table; source bytes
and completed native B-bus register writes; effective per-output-row
PPU window/BG/OBJ/math state; and a deliberate single-channel
or bounded subset counterfactual with the original full 57,344-pixel
RGB5 raster as oracle. The spatial 460-pixel components are
important observational constraints, not a proven register owner.

Do not promote a changed framework globally: Gundam Wing's
non-consuming first-line behavior is a real pinned upstream
compatibility reason. No Original 256x224/7:6, true 4×,
authentic 342-wide world, P1/P2 visibility, procedural
Remastered art, gameplay/Modern, CPU/APU, QA ledger or
cumulative scheduler changes.

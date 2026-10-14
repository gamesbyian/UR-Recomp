# QA-08: real native source-pixel test of HDMA first-line consumption

**October 14 experiment, deliberately nonproduction.** Prior original and
native source executions proved exact channel-7 mode0 direct bytes
`0F/00/0F`, original header bytes `6F/02/60`, and native live counts
`111/2`. The preceding native renderer repeats initial `$2100=0F` at
write-log tag2 and emits a two-row brightness-zero band one row later
than original Snes9x. Those are independent source observations, not a
license to apply a global DMA timing change.

This bounded counterfactual uses a **single pinned Baldosa checkout**
with two **separate full native AOT guest executions** of the identical
original USA retail 2P route. It first retains the original fixed
256x224 source pixel framebuffer at guest2208 plus the entire
2,473-frame guest WRAM CRC transcript. The baseline P7 **must hash** to
the independently accepted unmodified original-source P7
`a946c9ebb54775639b8fd87a6861af0408cceed4896e58be05908c4a4491c67f`.
An unmatched baseline is a failed input precondition, not a usable new
native raster. The read-only `$2100` DMA source logger is installed
*before both native runs* and is never given the authority of final pixels.

Only after the complete unmodified baseline has succeeded does the
workflow explicitly apply the opt-in disposable native framework
`qa08_patch_hdma_prime_counterfactual.py` and recompile the identical
native game. That mutation consumes the first transfer in every active
HDMA channel instead of restoring the channel table pointer and count.
This is intentionally dangerous to production behaviour and therefore
**never alters UR-Recomp's product framework or recorded upstream pins**.

`qa08_compare_native_hdma_prime_trial.py` checks the full unmodified
source-sized P7 arrays, no cropping, no lossy normalisation, no image
repair and no line mask. A positive native-to-native seam-placement
observation requires exactly 512 changed real RGBA source pixels,
256 on output y111 and 256 on y113, baseline black y112-113 and
experimental black y111-112, unchanged y112 and all other rows, plus
unaltered alpha and complete matching 2,473-record CRC streams.
Unexpected changes or no displacement produce **explicit negative**
result reports, not a hidden tolerance or claim of success.

**Still required even after a positive result:** compare the actual
experimental P7 directly to the hash-bound genuine original Snes9x
callback2207 frame (`tools/qa08_check_hdma_prime_candidate.py`),
record all relevant channel5 CGADSUB/COLDATA and window/OBJ effects,
ensure top/bottom source-alpha and priority survive on several actual
moving-race frames, test 1P and other games against the known upstream
Gundam Wing first-line workaround, and retain the 342-wide
source-world/true 4x Original contracts. All original physical SNES,
shipping visual, HD rider and independent Windows release claims remain
unverified here.

Existing artifact authority remains the accepted original and native
source provenance, with no reused CI screenshot guessed into an original
SNES screenshot. This new one-shot workflow is pull-request-invalidated
only on exact experiment files, and can be explicitly dispatched if
needed; it is not a recurring research factory.

Run local adversarial checker tests:

```sh
python3 -m unittest tests.unit.test_qa08_compare_native_hdma_prime_trial
```

## Actual 2P source PPU execution and independently read original video result

**Executed original/native source proof, 2026-10-14, experimental renderer only.**
The real bounded native test emitted the full raw P7 and guest-CRC artifact
[native experiment 38625005621](https://github.com/gamesbyian/UR-Recomp/actions/runs/38625005621),
artifact `11924132279`, independently downloaded ZIP SHA256
`4a3d9af21f509e8b5daeb17e4ba27932ba8a3dcd4bb167832ff4d33fd6bf3df7`.
The unmodified native baseline P7 is SHA256
`a946c9ebb54775639b8fd87a6861af0408cceed4896e58be05908c4a4491c67f`,
identical to the earlier independent native accepted source.
The disposable consumed-prime trial P7 is SHA256
`bf8b4218fb72f94338b19da5c1386bd5ce09c0dc0c767093286e80895fa3353c`.

All **2,473 guest WRAM CRC lines were bytewise identical** across
these two native emulator processes. There are 2,292 distinct CRC
values; repeated early and stationary frames are genuine source
observations, not missing records. The first run's appended CI pixel
checker mistakenly required all CRC values unique and therefore its
job was red **after both runs completed and produced full artifacts**.
The erroneous constraint has been removed. Changed native pixels were
exactly 512 RGBA source pixels, all 256 pixels on y111 and y113;
every other pixel in the full 256x224 Original raster is unchanged.
Native brightness0 moves from y112–113 to y111–112. The trial's
real channel7 `$2100` writes change from tags 0,2,113,115 to
0,112,114, eliminating the duplicated initial `0F`.

Independently fetched accepted original Snes9x reference archive
[38543766102](https://github.com/gamesbyian/UR-Recomp/actions/runs/38543766102),
artifact `11884155561`, ZIP SHA256
`6e5d488230c11d3dfcd144b6a7cbc8c25d7acfcb4f95b776a85071dd3487f5e3`.
The actual source callback frame2207 BGRX8888 image SHA256 is
`e76c6010b3fb339ecbdae2fec985a00019345723cdff122d9bbc78d71481c8aa`.
Using only the previously justified Snes9x RGB565 expanded green6
to native 5-bit green reduction, baseline native was 56,832/57,344
identical RGB pixels while the **experimental native image was
57,344/57,344 exactly identical** to real independent original.
No tolerance, scanline ignore mask, alternate sprite image or
colour-bias correction is used. The separate source-grade receipt is
`analysis/data/qa08-original-native-hdma-prime-exact-2p-rgb5-20261014.json`.

**Shipping boundary remains closed.** The counterfactual changes
global HDMA priming for *every* active channel, although this one
frame ended with only the 512 visible seam pixels changing. The
pinned SNESRecomp source explicitly documents why the non-consuming
prime was introduced for Gundam Wing. Before any production merge,
run unchanged-input original/native comparisons on several separated
active 1P and 2P frames, scanline112 effective OAM/P1/P2 alpha,
channel5 effective CGADSUB/COLDATA, window/mosaic, genuine 342px
world and 4x Original presentation, and a cross-game first-line
regression. The source-original one-frame 100% RGB5 result proves
this specific timing discrepancy, not whole-title hardware fidelity.

## Follow-on: exact native-source three-scene experiment

The accepted original/native source-frame comparison achieved genuine
57,344/57,344 pixel RGB5 equality. To test the global first-line HDMA
counterfactual for unwanted other-scene effects, the same two independent
2,473-frame native guest processes now also capture actual original-size
256x224 PPU source at guest400 (2P frontend) and guest1856 (countdown),
in addition to the proven 2208 (post-GO) source frame. These use the
three already-existing read-only Original capture selectors, preserving
the exact accepted baseline 2208 SHA and unchanged full guest CRC.

The new qa08_compare_native_prime_multiframe.py scans every unaltered
RGBA pixel in both captures for all three guest frames, reports row
locations, bounded changed-pixel examples and alpha changes, and checks
that the authentic 2208 two-row seam fix remains exact. Unexpected
differences in the early scenes are retained as potential regressions,
not hidden by tolerant thresholds, gamma correction or line masking.
A result showing no other changes is only three-frame native evidence;
it cannot establish equivalence for every game frame or other games.

Important: the reference original Snes9x archive contains 37 consecutive
PPU callbacks around 2207, but Baldosa's normal host presents frames
sparsely. Selected host source images are not a contiguous 37-frame
native PPU source capture. Any future multi-frame original/native
comparison requires its own correctly timed per-guest PPU observer.

Cross-game Gundam Wing HDMA startup, full channel5 colour math, window
and line112 effective OAM, true 342-wide source geometry and 4x fallback
remain separate blocking proof before production HDMA code changes.

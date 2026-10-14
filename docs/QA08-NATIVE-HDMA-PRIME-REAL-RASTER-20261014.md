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

# QA-08: narrower channel-7-only first-line prime discriminator

**October 14, 2026: unexecuted experimental branch, not a production patch.**
The accepted genuine 2P source comparison from #1567 proved
57,344/57,344 original Snes9x-native RGB5 equality for one finished
post-GO source frame, using a disposable renderer which consumed the
first transfer of **every active HDMA channel**. The native source
archive from action 38626620186, artifact 11924945566, independently
recorded after-BBUS channel5 and channel7 register writes alongside
the full source pixels. Those source journals are not themselves
effective per-scanline PPU output.

## Real observed registers: why discriminate channel7 from global

| Real native HDMA register | Existing nonconsuming-prime tags | All-channel consumed-prime tags |
| --- | --- | --- |
| channel7 / $2100 INIDISP | 0, 2, 113, 115 | 0, 112, 114 |
| channel5 / $2131 CGADSUB | 0, 2, 3, 4, 113, 114, 115 | 0, 2, 3, 112, 113, 114 |
| channel5 / $2132 COLDATA | 0, 2, 3, 4, 113, 114, 115 | 0, 2, 3, 112, 113, 114 |

All raw transmitted channel7 brightness values match original 0F,00,0F.
Channel5 COLDATA values also retain source order 2F,40,80,20,53,80;
CGADSUB remains 04. Thus applying global prime consumption
changed the channel5 BBUS *timing* as well, even though only the
expected two brightness-seam rows changed in the true completed frame.
Importantly, that single final RGB result cannot prove equivalent
channel5/window composition in every race state.

The pinned Baldosa SNESRecomp header explicitly documents why its
global nonconsuming-prime scheme was chosen to repair a first-line
Gundam Wing visual defect. A title-specific exception may pose less
compatibility risk, but the source-faithful solution must ultimately
derive from authentic SNES line timing across all active channels.

## Proposed opt-in controlled discriminator

The narrowly anchored
tools/qa08_patch_channel7_only_prime_counterfactual.py
applies to a **disposable copy only** of pinned
SNESRecomp 075fbe4c8e0d97b0013be541795c39cb644a9709.
It validates the same original byte transfer and first-line source
anchors as the existing global prime experiment. It leaves the pinned
saved DMA descriptor/counter untouched in **every channel other than**
channel7 when explicitly in direct mode0 with destination $2100.
Only that source-observed brightness channel advances its first descriptor.
Dry run is default; an explicit --apply-experiment is required.

Next discriminator: start with the exact authentic original USA 2P route,
reuse the unchanged before/after #1567 guest CRC and image hash guards,
then run *three actual independent native processes*: baseline,
all-channel consumed-prime, channel7-only consumed-prime. Demand
unmodified guest CRC and exact full-PPU 256x224 RGBA/RGB5 comparisons
for the accepted post-GO frame and earlier 400/1856 frames. Measure
channel5 effective register timing and original Snes9x windows, not
only channel7 write timestamps; if source images disagree, retain
the negative. This result cannot be asserted until the real native
candidate is built and executed.

**No production framework change, shipping art, controller/save/gameplay
mutation, independent QA ledger or HD rider approval is authorized.**
World geometry stays genuine 342 logical pixels when Widescreen is
selected; fixed Original remains 256x224 at 7:6 PAR with genuine 4x.

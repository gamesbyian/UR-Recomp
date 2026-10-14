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


## Prepared three-process real-source discriminator (not yet an executed result)

The next bounded iteration extends the **existing** manual/PR-invalidated
`qa08-native-hdma-prime-counterfactual.yml`, rather than commissioning
a second emulator runner or accepting a synthetically shifted image.
It runs the same original-USA 2P input and pinned Baldosa guest three
times, each through the actual source PPU and distinct complete 2,473
guest-CRC transcript:

1. Unmodified native HDMA priming (with the already accepted unchanged
   guest2208 stock source hash).
2. Global consumed-prime reference, independently original-pixel exact at
   post-GO guest2208 and countdown guest1856.
3. **Channel-7-only** consumed-prime counterfactual after exact inversion
   of the global patch, preserving all prior read-only instrumentation.

The third execution must retain real source-sized 256×224 P7 bytes
at guest400/1856/2208, actual channel7 `$2100` after-BBUS write
receipts, **unchanged channel5 `$2131` source journal**, and CRC streams
identical to both controls. The inversion validates by reapplying the
global patch in memory and demanding byte-for-byte reconstruction of
the formerly patched source; it never resets unrelated host adapters.

`tools/qa08_compare_channel7_native_prime.py` requires full exact
original Snes9x archives for callback1855 (countdown) and callback2207
(post-GO), with original ZIP SHA256s and the accepted 2P native
controls. Its output records all three candidate P7 identities,
the complete pixel-difference row census, alpha differences, and
the channel-7-only RGB5 comparison to both *genuine* original images.
The 2P frontend lacks an independently paired original scene and is
only a bounded **native-versus-native** regression control.

A channel-7-only trial that fails original pixel equality is valuable
negative evidence. A trial that agrees with both original frames
remains **experimental source-frame agreement only**: neither scenario
proves later moving race poses, 1P, results, effective scanline-112
OAM/window/OBJ layer causality, physical SNES correctness, widened
342-world output, physical 4× Original, or Gundam Wing regression
safety. Both selective and global source mutations stay entirely in a
disposable pinned framework checkout. No production runtime change.

**Reuse disposition:** preflight `rider-oam-hdma` and
`dma-entry-provenance` remain conditional existing-tool reuse;
`candidate-evidence-envelope` and `agent-work-packets` favor
binding the already captured ROM/route/native source identities.
Current Baldosa DMA/PPU probes and existing UR source comparators
are sufficient for this measurement. Malmazuke PPU/OAM interpretation
remains advisory until genuine USA executed source/finished pixels
distinguish a specific unresolved layer.


## Executed: real channel-7-only original/native result (2026-10-14)

**The unexecuted status above is superseded for this exact experimental
trial.** [PR #1586](https://github.com/gamesbyian/UR-Recomp/pull/1586)
merged after genuine successful pinned native
[workflow run 38640211633](https://github.com/gamesbyian/UR-Recomp/actions/runs/38640211633).
Artifact ID **11929639588**, complete archive SHA256
**9df4d909c7ee2277af86593f38b409925da8fddd58203b33f898cbd247b73ce9**.
Strict source report SHA256
102f25ab7f996b4447e8f8acbeab76532828c4a412cd7a89080991c17a644f74.
All three entire 2,473-frame native guest CRC streams are identical,
each with file SHA256
4280056aef50acde83ca9ce82d0a12f8a5b7190a18e42a5d24401b65c44e205d.
The original Snes9x ZIPs remain source-hash pinned. The native PPU source
alpha never changes between the three source experiments.

| Actual guest + paired original callback | Stock wrong RGB5 | Channel7-only wrong RGB5 | Global-prime wrong RGB5 |
| --- | ---: | ---: | ---: |
| Frontend guest400, no paired original | Original not checked | Native delta 0 | Native delta 0 |
| Countdown guest1856 ↔ original1855 | 971 | **460** | **0** |
| Post-GO guest2208 ↔ original2207 | 512 | **0** | **0** |

Thus channel7-only actually corrects the **entire 512-pixel split
brightness difference** in the tested post-GO scene and is exact
against the independently genuine original callback2207 there.
At countdown guest1856 it corrects the *same two entire 256-wide
split rows* relative to the stock native framebuffer, but **460
original RGB5 pixels still disagree**. This negative result
**falsifies channel7-only as a generally pixel-exact correction
for the two tested real 2P scenes**. The global consumed-prime
trial remains exactly equal at both original-size callbacks, but
still is not a shipping renderer/hardware correctness certificate.

The residual has 226 incorrect pixels in upper rows0–110 and
234 in lower rows113–223. **459** are contour/window-shaped
off-split pixels. The other **one is a three-way difference** at
logical original pixel **(223,113)**: original Snes9x BGRX
\`FF 38 39 00\`, corresponding to global native RGBA
\`39 39 FF 00\` after justified green6→5 conversion; stock
native RGBA \`00 00 00 00\`; selective native RGBA
\`84 A5 A5 00\`. The 512 stock→channel7 native changes and
971 stock→global changes overlap on this point, so simply
subtracting 512 from 971 would incorrectly infer 459 remaining
instead of the measured **460**. All residual pixels and alpha
are unmasked full original-size source observations.

Exactly seven genuine channel-5 \`$2131 CGADSUB\` after-BBUS
write records at **guest2208** were retained, byte-identical
between stock and channel7-only (journal SHA256
f4fa82fec7aca2ac22feb96cb718bfd9e23f320d2b00b615cfd86225f6f1a37d).
Selective channel-7's real \`$2100 INIDISP\` writes were
0F at native line0, 00 at line112 and 0F at line114.
The source demonstrates that the selective experiment preserves
**observed channel5 control at 2208** while fixing the seam.
It does NOT yet prove that *channel5 alone* caused the 460
countdown differences: other channels' prime state, scanline
window/colour math, OBJ/BG ordering and the original executed
65816 table writers remain to be isolated.

Next discriminator: an independently executed disposable
**combined channel5+7 first-line consumption** (and if needed
channel5-only), compared against the same source-hashed
original callbacks and additional moving original frames.
Instrument actual channel5 per-line BBUS writes at countdown
1856, effective CGADSUB/COLDATA/colour window state,
channel7 brightness and final output pixels. Fail on
unexplained changes, capture source alpha, preserve full
guest CRC and avoid assuming 2P OAM winner solely from
sprite rectangles. The *proposed* additional post-GO moving
original callbacks2191 and2223 are quantified in
[the authentic motion census](QA08-ORIGINAL-2P-37-FRAME-PIXEL-ALIGNMENT-20261014.md).

Permanent compact source receipts:
[\`analysis/data/qa08-selective-channel7-real-original-native-outcome-20261014.json\`](../analysis/data/qa08-selective-channel7-real-original-native-outcome-20261014.json).
No production HDMA, wide/4x pixel-art, authored-remaster,
gameplay, Modern or independent release acceptance changed.

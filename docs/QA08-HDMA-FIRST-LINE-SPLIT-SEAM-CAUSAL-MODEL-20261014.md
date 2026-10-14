# QA-08: first-line HDMA consumption and the 2P seam

**2026-10-14 status: source-code causal model; corrected native binary NOT run or accepted.**
This experiment neither fixes production PPU nor changes any independent release gate.

## Decision-bearing evidence

Accepted original Snes9x versus native Baldosa RGB5 source comparison is
56,832/57,344 pixels identical. Precisely two full-width rows differ:
y111 and y113, 256 pixels each. Original brightness-zero output rows are
111–112; native rows are 112–113. No visual masking or colour correction
is defensible. The original RGB565 green6 to native RGB5 conversion is
the separately justified video-format normalization.

The independently executed original Snes9x channel7/direct/mode0 register
writes, and source locations, are V0 at 7E:2065/0F,
V111 at 7E:2067/00, V113 at 7E:2069/0F. Original actual
PPU brightness 15 to 0 to 15, never bit7 forced blank. Native real
after-BBUS PPU INIDISP writes are: tag0/7E:2065/0F,
tag2/7E:2065/0F, tag113/7E:2067/00, tag115/7E:2069/0F.
Full source ZIP SHA values, original USA/guest ROM/input receipts and
source image hashes remain in
[paired brightness source evidence](../analysis/data/qa08-original-native-2p-brightness-split-channel7-handoff-20261014.json)
and [exact 512-pixel seam](QA08-ORIGINAL-NATIVE-2P-RGB5-SPLIT-BAND-PIXEL-20261014.md).

## Native source control-flow candidate

Pin: [Baldosa SNESRecomp commit 075fbe4c](https://github.com/baldosa/snesrecomp/blob/075fbe4c8e0d97b0013be541795c39cb644a9709/runner/src/snes/dma.c).

- dma.c lines373–381: dma_initHdma loads the A-bus table descriptor.
- dma.c lines400–418: dma_primeHdmaFirstLine copies DmaChannel, transfers
  the first real value to PPU, then **restores the entire channel copy**.
  The PPU byte persists, but tableAdr, repCount and doTransfer rewind.
- beam_frame_driver.c lines236–258: prime once, then for line=1..224,
  replay CPU writes, draw the line, and run dma_doHdma **after** drawing.
- ppu.c lines767–772 and PpuDrawWholeLine: the line cursor is updated
  to line+1 before HDMA, and actual RGB pixels go to row=line-1.
  Thus an after-draw transfer logged as native tag N first affects
  output row N-1. The prime event is logged at tag0.
- dma.c lines420–455: the normal path consumes the descriptor through
  repCount decrement, doTransfer and next-header loading. Prime does
  not do so because it restores the previous channel state.

The source model shows a precise falsifiable relationship:

| Real register event | Original V | Native observed tag | Consumed-prime model tag |
|---|---:|---:|---:|
| Initial brightness 15 | 0 | 0, then duplicate 2 | 0 |
| Brightness zero | 111 | 113 | 112 |
| Brightness 15 restore | 113 | 115 | 114 |
| Black output rows | 111–112 | 112–113 | 111–112 |

The model's first two *nonrepeating* durations 111 and 2 are
**inferred from original transition distances**; actual original
channel7 header bytes at 7E:2064/2066/2068 have NOT been separately
read in these retained reports. Its final duration is illustrative.
The predicted corrected transfer tags are NOT native measurements,
nor does the source model establish physical SNES HBlank behaviour.

Execute the self-contained analytical replay and tests:

    python3 -m unittest tests.unit.test_qa08_hdma_prime_counterfactual
    python3 tools/qa08_model_hdma_prime.py --out /tmp/qa08-hdma-prime.json

## Experimental correction, deliberately not in production

The anchored, fail-closed
[prime consumption patch](../tools/qa08_patch_hdma_prime_counterfactual.py)
modifies only a *disposable* pinned Baldosa framework checkout. Dry
run is the default. Explicit --apply-experiment removes save/restore
and applies repCount/doTransfer/descriptor progression after the
genuine initial BBUS transfer, matching the ordinary HDMA path.
This affects potentially **every HDMA channel**, not just channel7.
It therefore requires more than the single-row explanation to ship.

    python3 tools/qa08_patch_hdma_prime_counterfactual.py --framework /tmp/disposable-baldosa/snesrecomp
    python3 tools/qa08_patch_hdma_prime_counterfactual.py --framework /tmp/disposable-baldosa/snesrecomp --apply-experiment

Reuse the existing genuine unchanged-input 2P route and exact source
guest2208 PPU capture. Record real header bytes and live per-channel
state before/after prime, read after-write INIDISP, CGADSUB, COLDATA,
window/OBJ/OAM transfer state and finished source pixels.
Do not use CPU journals as a proxy for final PPU rendering.

[Strict full-source-pixel checker](../tools/qa08_check_hdma_prime_candidate.py)
demands original accepted archive checksum, exact original callback2207
image checksum, original-size 256x224 native trial P7, **57,344/57,344**
normalized RGB5 equality, and equal 2,473-record unmodified/native-trial
guest CRC transcripts. It neither ignores rows nor accepts a guessed
visual correction. Its caller-supplied baseline CRC transcript remains
externally authenticated, so keep the exact accepted artifact/route SHA
with any prospective result.

    python3 tools/qa08_check_hdma_prime_candidate.py --original-zip /path/original.zip --candidate-p7 /path/candidate.pam --original-crc /path/unmodified-native.crc.txt --candidate-crc /path/trial-native.crc.txt --out /tmp/seam-experiment.json

Before production promotion also require source/final acceptance over
several moving post-GO frames, channel5 real colour-math and window
behaviour, the **26 independent BG3/OBJ composite witnesses**,
correct actual split line112 OAM high-table switching and upper/lower
source-alpha/culling, centre equality and 342-wide true-world plus
4x Original fallback. The established
[OAM shadow/projection model](QA08-2P-OAM-SHADOW-PROJECTION-20261013.md)
for $1599 and $1501..$150E forbids assuming a constant
$0DDB/$121B/$121D is a hidden rider. Even exact isolated sprite
alpha does not establish final winner at occluded pixels.

**Stop rule:** if corrected actual per-line register values or output
pixels disagree with the prediction, reject the hypothesis; inspect
descriptor semantics and cross-core beam timing, not a black-row mask.
Original 256x224 logical, 7:6 PAR, world-space Widescreen, and
owner-vetoed Remastered procedural rider art remain untouched.

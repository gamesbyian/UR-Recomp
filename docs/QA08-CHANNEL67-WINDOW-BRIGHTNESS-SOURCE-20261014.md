# QA-08: window-HD​MA channel6 and brightness channel7, four original-source scene discriminator

**Status: new fifth real guest 2P AOT experiment, not a production PPU change.**

## Real source qualified motivation

The genuine USA native [run 38666654931](https://github.com/gamesbyian/UR-Recomp/actions/runs/38666654931),
artifact 11942930136 (SHA256 fa70b6675009a924ebfff2b41403acda9113d022cf1a4061fbaad1538bec9c65),
ran four full authentic 2P guest processes and captured *all actual HDMA
PPU B-bus register writes* on countdown guest1856. Every process retained
all 2473 unchanged guest CRC records and earlier strict RGB5 source images.

Actual source register activity appears on channels1..7. Most
importantly, channel6 reads ROM bank15 and uses **direct mode4**
to transfer four consecutive bytes to **$2126..$2129 window
boundaries** every source scanline. Its first genuine A-bus byte
is $15:9513; the other three first-line bytes come from
$15:9514..9516. Native stock, ch7-only and combined5+7
each produced **900** channel6 register writes (225 rows times 4),
whereas consumed-prime global produced **896** (224 rows times 4).
Actual late channel6 tags are 225 in stock and 224 under global
first-line consumption.

The independently original-source-matched countdown image exhibits
a large blue right-pointing arrow, RGB8 (57,57,255). Its entire
**460-pixel mismatch** between global-prime and ch7-only/ch5+7
is the XOR of blue arrow coverage. The selective image's arrow is
displaced by **one source-output scanline**, apart from the black
2P split seam. Thus the source channel6 window boundary and its
duplicate first-line transfer are a strong *causal candidate*,
but direct B-bus transfers do not alone prove completed-window
state, original game producer PC or actual source layer winner.

Post-GO at guest2192,2208,2224, by contrast, both ch7-only and
global-prime now agree with the original Snes9x at all 57,344
RGB5 source pixels in **three distinct moving 2P original views**.
The original countdown guest1856 remains exact only with global
prime; selective ch7/ch5+7 retain 460 incorrect blue arrow pixels.

## Narrow experimental implementation

tools/qa08_patch_channel67_prime_counterfactual.py changes only a
**disposable pinned SNESRecomp DMA source copy** after reproducing
the exact pre-existing global first-line source guard. It consumes
the already transferred prime descriptor solely when the real
channel configuration is:

- channel 6, direct mode4, PPU BBUS base $26, ROM bank $15
- channel 7, direct mode0, PPU BBUS base $00, INIDISP

All other channels use the pinned untouched snapshot/restore
first-line prime. The experiment never alters generated guest C,
gameplay, inputs, on-disk save, any production binary or the Snes9x
original video oracle. Reversible patch staging is mandatory.

The existing one-shot native 2P graphics workflow, not another
emulator-runner factory, now builds a **fifth independently executed
2473-frame real USA guest process** and captures exact 256x224
source P7 at guest1856,2192,2208,2224 alongside authentic
channel6/7 B-bus transfer records and unchanged guest CRC.

tools/qa08_compare_channel67_native_prime.py compares all **57,344
RGB5 pixels** of four independent original Snes9x callbacks
1855,2191,2207,2223 with actual native stock/global/ch7/ch57/ch67
PPU rasters. It requires all five full CRC streams byte-identical,
independently accepted original archival ZIPs, complete source pixels,
previous four global-prime exact-P7 digests and positive global
original/native RGB5 source controls. Every candidate pixel
mismatch, row and source-alpha change is reported. An image
inequality is scientific negative evidence; damaged credentials,
missing source or guest divergence fail the experiment.

### Interpretation and production stop rule

A positive ch6+7 result would establish only **four specified
source-size frames** can be rendered exactly by that disposable
configuration after justified Snes9x green6-to-green5 normalization.
It would narrow causal candidates and support more broad testing;
it would **not authorize** changing general production first-line
HDMA: the pinned upstream's non-consuming first-line behavior
was introduced for Gundam Wing, so cross-title SNES/HBlank
compatibility still needs representative source evidence.

Full original/native moving event phase and actual 65816
writer-state alignment, results and 1P scenes, scanline112
active OAM/high-table sprite ownership, BG/OBJ final pixels,
original world-centred 256x224 7:6 PAR, true Original 4x
fallback, authentic 342-wide world margins and Remastered
rider owner likeness review remain independently gated.
Do not infer a general renderer fix from a special-purpose
source prime experiment.

The permanent source-qualified all-channel evidence register
is analysis/data/qa08-countdown-real-seven-HDMA-channel-source-census-20261014.json.

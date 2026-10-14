# QA-08: combined channel5+7 first-line prime, original-source discriminator

**Status: fourth real native AOT source experiment, pending execution.**
No production code or gameplay changes.

## Why an independently controlled channel5+7 trial

Accepted merged #1586 / native run 38640211633 establishes full
original/native source RGB5 pixel comparisons:

| Genuine USA 2P scene | Stock wrong pixels | Consume ch7 first HDMA line | Consume all channels' first HDMA lines |
| --- | ---: | ---: | ---: |
| Countdown guest1856 ↔ original callback1855 | 971 | **460** | **0** |
| Post-GO guest2208 ↔ original callback2207 | 512 | **0** | **0** |

The channel7-only counterfactual repairs the post-GO split brightness
band but does not close countdown, including 459 off-seam contour/window
pixels and the unique three-way source pixel (223,113). The native
channel5 CGADSUB after-BBUS source journal was byte-identical stock
versus ch7-only at 2208 (seven records); the same has not yet been
directly recorded for countdown1856. Therefore channel5 alone has
**not** been demonstrated causal for the missing 460.

The smallest next controlled distinction consumes the first transferred
HDMA descriptor on only these genuine native source-qualified channels:
- Channel 7: direct mode0 to PPU INIDISP at $2100, real source
  WRAM $7E:2065/2067/2069.
- Channel 5: direct mode1 to $2131 CGADSUB and $2132 COLDATA,
  real $2131 source WRAM $7E:2085–2094 at postGO2208.

Other channels retain the pinned non-consuming-first-line behavior.
This experiment deliberately refuses to assume that channels5/7
explain all original pixels until compared with the actual PPU.

## Genuine four-process source acceptance

The previously accepted one-shot native QA08 workflow executes three
full unchanged-route guests (stock, global prime, selective ch7). The
fourth stage requires exact reversible inversion of the channel7-only
patch, validates the pinned DMA A-bus source and reuses all observers,
then applies only the combined channel5+7 disposable DMA patch.

It rebuilds the same pinned guest, runs the authentic USA 2P 2473-frame
input, captures real 256x224 Original PPU P7 frames400/1856/2208,
and requires fourth guest CRC byte-for-byte identical to all previous
native processes. The real channel5 $2131 after-BBUS source journal at
postGO2208 must match the global-prime control; native ch7
INIDISP output remains separately retained.

The independent fourth-process source comparator rechecks all prior
strict original/native controls and exact-SHA original Snes9x ZIPs.
It reports every raw RGB5 mismatch and actual source alpha change at
original callbacks1855/2207, including negative results. Invalid
images, missing original archive frames, foreign ROM/route CRC or
source register drift fail closed. The true result belongs to an
exact-head GitHub Actions artifact, not these proposed tests.

**No pixel-exact outcome is claimed before native execution.**
Even positive two-scene results cannot certify physical SNES HDMA,
all effective scanline registers, additional moving gameplay,
results/transitions, 1P, 342-wide sprite visibility, 4x Original
fallback, cross-title SNESRecomp compatibility or production renderer
promotion. The user-vetoed procedural HD racer remains unapproved.

The already source-verified genuine 37-frame original motion census
identifies callback2191 and callback2223 as substantial other 2P
motion candidates. Native guest2192/2224 are proposed only; their
actual source-frame presentation and independent frame phase remain
unproven. Do not invent those additional source samples.

Preflight reuse: UR native original PPU source capture, existing
Baldosa pinned renderer, accepted QA08 comparator, and actual
source-observed DMA channel selectors; Malmazuke PPU/OAM external
knowledge remains advisory only. No gameplay, Modern/storage,
Claude CPU/APU, research scheduler, independent release ledger,
production HD, Widescreen or Original presentation changed.

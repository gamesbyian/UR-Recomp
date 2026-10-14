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


## Genuine four-process executed result: combined 5+7 is still insufficient

The pending status above is now superseded by real source execution.
[PR #1595](https://github.com/gamesbyian/UR-Recomp/pull/1595)
was accepted and merged with successful one-shot native
[run 38642367882](https://github.com/gamesbyian/UR-Recomp/actions/runs/38642367882),
artifact **11930109109**; independently downloaded artifact SHA256
**a6aae4f82644c93b43f98f336d72c21d24846fea5f8377e18cbc54e37c1b3040**.
Its strict complete original/native source comparator JSON SHA256 is
2bb604274276a00e580635bbd31211749a6ef32e9f48f2e2396b25bbec956426.
Four genuine 2473-entry native guest CRC transcripts are *identical*
(SHA256 4280056aef50acde83ca9ce82d0a12f8a5b7190a18e42a5d24401b65c44e205d).
All comparison source alpha bytes remain unchanged.

| Real original/native scene | Stock original RGB5 wrong | Ch7-only wrong | Combined ch5+7 wrong | Global prime wrong |
| --- | ---: | ---: | ---: | ---: |
| Frontend native guest400 | No original paired | Native unchanged | Native unchanged | Native unchanged |
| Countdown original1855/native1856 | 971 | **460** | **460** | **0** |
| Post-GO original2207/native2208 | 512 | **0** | **0** | **0** |

More strongly than the scalar counts, the entire actual 256x224 native
combined-ch5+7 P7 source framebuffer is **byte-for-byte identical**
to the ch7-only framebuffer in **all three native scenes**.
At countdown1856 both images retain the same exact **460**
original source wrong RGB5 pixels, including the three-way
split coordinate (223,113). Source alpha also remains identical.
Thus adding consumed prime for channel5 does not close *any* of
the remaining countdown output differences under this precise
intervention.

The source-qualified **global-prime vs combined-ch5+7**
after-BBUS channel5 CGADSUB journal at guest2208 is identical
(journal SHA256
deedf392710bbe2ab7148ff824382b3e8f9bc08b13c4dba4309e1b4842f70ef4).
That establishes the trial applied channel5's observed source
control as intended at post-GO2208, but does not expose its
source PPU write effects at countdown1856. Channel7 live
INIDISP values remain the genuine consumed-prime 0F/00/0F.

**Disposition:** combined channel5+7 is falsified as a sufficient
general first-line fix across the two tested 2P scenes.
The missing 460 source pixels depend on additional channel(s),
their first-line interactions, or downstream per-line BG/window/
colour-math state which differs when those channels are also
primed. Neither source layer ownership nor a specific other
channel has yet been identified. Avoid conjecturally changing
channel5 again.

**Next executable experiment** should *read*, without modifying
the actual renderer, the first-line/descriptor A-bus data and
genuine active HDMA channel registry for **countdown frame1856**,
then observe effective per-output-row window/colour math and
source RGB at the 460 mismatches. Only after qualifying
the actual active channels should one choose a single-channel
or minimal subset consumption discriminator, and recheck
same original 57,344 pixels, 26 BG3/OBJ intersections,
split-112 OAM, authentic moving 2P source, original 1P and
cross-title compatibility.

Long-lived compact receipt:
[qa08-combined-channel57-real-original-native-negative-20261014.json](../analysis/data/qa08-combined-channel57-real-original-native-negative-20261014.json).
No production change and no released Original, Widescreen or HD art approval.

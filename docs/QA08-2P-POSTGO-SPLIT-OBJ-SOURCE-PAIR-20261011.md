# QA-08: post-GO original 2P paired racer-source symmetry check

**Status: source-backed post-GO original native AOT ACCEPTED**
[38120828291](https://github.com/gamesbyian/UR-Recomp/actions/runs/38120828291),
artifact `11695173178`. Four independent source planes and
seven unchanged whole-Original frame controls passed. Exact
per-pixel split-source identity at the **new post-GO transform**
is independently verified below, but final PPU winner is NOT.

The original/native 2P racer OAM source mapping, traced in earlier
accepted moving pre-race captures, is P1 top **slot98** and lower
**slot97**; P2 top **slot99** and lower **slot96**. The earlier
original frames1856,1872,1888 showed pixel-exact replicated
upper/lower **RGBA source** under `(dx,dy)=(0,+113)` original
raster-pixel shift. At genuine **post-GO** frame2208, the original
source bboxes already reveal a different offset, which this
tool independently verifies: **`(-13,+112)`** for both racers,
not the pre-race shift. This is a measured source-registration
difference across phases, not proof which 2P camera or game
WRAM instruction caused it.

New native source route [#1340](https://github.com/gamesbyian/UR-Recomp/pull/1340)
reuses four existing independent slot-isolation processes and
captures every 2P source slot at guest2208, while independently
matching at least **seven** unchanged whole original 342×224
raster controls and full 2P guest CRCs.

`tools/check_baldosa_2p_postgo_source_pairs.py` consumes only
those original PPU PAMs, stock Original frame2208 and four exact
native source validation records. It derives a *candidate* upper/lower translation from the
two independently validated actual source **alpha bboxes**,
then independently compares **every occupied source RGBA
pixel and all source-support coordinates**. A shared bbox alone
never proves that source pixels match; every RGBA value is
verified. It does not assume the earlier **(0,+113)** shift.

## Accepted source-pair and final-Original observations

At authenticated native USA 2P guest2208, the two complete
independently isolated Original upper/lower source pairs match
pixel-for-pixel at the **same inferred raster transform
`x−13,y+112`**:

| Original source pair | Upper emitted | Lower emitted | Alpha mismatch | RGBA mismatch |
| --- | ---: | ---: | ---: | ---: |
| P1 slot98→slot97 | 317 | 317 | **0** | **0** |
| P2 slot99→slot96 | 313 | 313 | **0** | **0** |

The full source raster outside their translated opaque
pixels is also equal (zero unused RGBA image data), but
the accepted invariant checks actual **visible** RGBA and
alpha. This proves that a fixed global **(0,+113)**
translation is wrong after GO. It does not imply a
camera geometry, physical 3D rig or product-space transform.

The same accepted unmodified native full Original
342×224 raster at2208 lets us record **RGB equality**
at source-alpha coordinates without falsely treating
colour matches as hardware priority bits:

| Original source | Emitted | Original final RGB matches | RGB differs |
| --- | ---: | ---: | ---: |
| Upper slot98 | 317 | 304 | 13 |
| Upper slot99 | 313 | 265 | 48 |
| Lower slot96 | 313 | 300 | 13 |
| Lower slot97 | 317 | 291 | 26 |

## Screen-fixed text/OBJ RGB interaction: repeated 13-pixel signature

The genuine native 342×224 final PPU screenshot at guest2208 has
large original on-screen **“GIVE YOU”** glyphs crossing both
unicycles. At exactly **13 source-positive positions** in
original upper OAM slot98, and **13 in lower slot96**, the final
Original RGB differs from the authentic isolated OBJ source
in one remarkably specific way: **(final minus source RGB) =
(+107, 0, 0)**. Both 13-position mismatch sets are identical
after **a screen-space offset of (0,+112)**; the actual
underlying source RGB and final RGB also match at each paired
screen position. The upper exceptions occupy source coordinates
x132–136/y47–52; the lower exceptions occupy the same X
at y159–164. This is **not** the 2P racer source-pair
translation (−13,+112): those are two distinct phenomena.
The screenshot visually places the mismatches directly beneath
text glyphs, supporting a foreground/text interaction rather
than missing racer source artwork.

### Original SNES 5-bit channel arithmetic, not just an 8-bit RGB delta

Checking all source-positive original bytes against the
standard SNES 5-bit-to-8-bit channel conversion,
`expand5(n) = (n << 3) | (n >> 2)`, yields a much
stronger numeric invariant. Across **48** original
source-positive slot positions, the final Original PPU
red value is exactly **13 native 5-bit red levels
above** the isolated source red value while the
underlying 5-bit green and blue remain unchanged.
The source palettes and final composite colours are
all legal 5-bit-expanded values in these samples:

| Original source slot | Exact native +13 red5 | Other source/final RGB differences |
| --- | ---: | ---: |
| Upper front98 | **13** | 0 |
| Upper rear99 | **22** | 26 (normal differently coloured racer overlap) |
| Lower front96 | **13** | 0 |
| Lower rear97 | **0** | 26 (normal differently coloured racer overlap) |

Within upper rear slot99's 22 red-only pixels, **19**
appear as **+107** in expanded 8-bit red and **3**
appear as **+108**, because `expand5(3)=24`
and `expand5(16)=132` differ by108 even though
their underlying SNES red5 values differ by13.
For example, `49 → 156` and `74 → 181`
each correspond to exactly +13 original red5.

This is strong evidence for a **red-channel-addition
signature consistent with SNES PPU colour math**,
not a demonstrated value of `CGADSUB`, `CGWSEL`,
the fixed-colour register or any particular BG/window
priority stage. Identical output arithmetic is not
proof of the hardware implementation. The analyser
checks 5-bit-exact rather than assuming every
8-bit output offset must be numerically +107;
tests reject malformed/non-palette RGB and changed
green/blue. The accepted machine-readable 5-bit
histograms and source hashes are archived in
[`analysis/data/qa08-original-2p-postgo-native5-red-add13-2208.json`](../analysis/data/qa08-original-2p-postgo-native5-red-add13-2208.json).

The read-only comparer now reports both 13-pixel RGB delta
histograms, the coordinate translation, and distinct checks for
identical support versus identical per-pixel delta. Four
adversarial tests alter a colour channel, remove one affected
source pixel, erase the entire effect, or preserve it exactly.
The exact upper affected XY list and image/source hashes are
preserved in
[`analysis/data/qa08-original-2p-postgo-text-source-rgb-delta-2208.json`](../analysis/data/qa08-original-2p-postgo-text-source-rgb-delta-2208.json).
This is **observational**, not proof whether hardware PPU
colour addition, text BG priority, window or other raster
compositing logic owns the effect. The measured pattern
must not be transformed into a general hard-coded text
occlusion mask or used to authorize HD racer painting.

The upper and lower sources each have **35** overlapping
source coordinates, of which **9** have the same source
RGB and **26** have different source RGB. These are
source/final colour facts, NOT proven front/back pixel
causality after GO, nor permission to paint the remaining
visible pixels in HD. In particular, 13 source/final RGB
nonmatches occur on each of the nominal front
source planes, and 22 nominal upper rear-only source
coordinates do not match the final Original colour.
A later native targeted removal may identify which layer
owns those coordinates; this report alone does not.

The actual stock/frame and four source SHA/count witnesses,
observed `(-13,+112)` pairs, four independent final-RGB
comparisons and overlap partition live at
[`analysis/data/qa08-original-2p-postgo-source-registration-2208.json`](../analysis/data/qa08-original-2p-postgo-source-registration-2208.json).
No copyrighted source graphics are committed.

## Source-registered final-viewport RGB difference: shared source is not shared final pixels

The successful original native 2P post-GO **full Original final raster**
was compared at corresponding racer-source support positions using the
**independently verified** `(-13,+112)` upper-to-lower OAM source transform,
without assuming the finished viewports are identical. Each viewport
contains **595 distinct opaque racer-source coordinates** (630 combined
source emissions minus 35 overlaps). At that shared source support,
the two **final Original RGB rasters** agree at **527** positions and
differ at **68**:

| Source-position category | Final RGB differences, upper vs lower |
| --- | ---: |
| Upper slot98-only source support | **13** |
| Upper slot99-only source support | **29** |
| Both emit distinct original source RGB | **26** |
| Both emit exactly equal original source RGB | **0** |
| **Total** | **68** |

Every one of the **42 single-source final-viewport differences**
has identical green/blue channels and an absolute **13-quanta red
difference in source-native 5-bit colour** (8-bit differences
`107` or `108` depending on quantized channel). The other 26
differences are exactly at the actual distinct-colour racer
source-overlap positions, consistent with each viewport presenting
a different original source colour. This is a bounded **raster
relationship**, not causal proof of PPU priority, a COLDATA
write, CGADSUB mode or a physical 3D camera model.

The newly added fail-closed comparison tool only performs
this *final-Original viewport* analysis when **both** independent
source-pair RGBA aliases have passed and inferred the **same**
translation. Source-empty, mismatched source/alpha or separate
translations remain valid source observations but produce
no invented final-viewport comparison. The original source
bytes and final RGB are never changed. Adversarial tests
check exact source copy with different final colours,
different-colour source overlap and divergent source
attestations. The numeric counts and source/frame SHA
are retained in
[`analysis/data/qa08-original-2p-postgo-registered-final-viewport-rgb-2208.json`](../analysis/data/qa08-original-2p-postgo-registered-final-viewport-rgb-2208.json).
The crucial negative rule for any later Remastered art is
**do not blindly translate finished upper-viewport racer
pixels into the lower viewport**. Identical source OAM
does not imply identical final presentation.

## Four-frame native original 2P registration and visibility matrix

A bounded retrospective review of the **same successfully validated
native AOT artifact**, using original frame/source SHA identities from
all four independent source-isolation processes, confirms **both
P1 and P2 source RGBA planes are exact viewport-translated copies
at each of four separate moving frames**. The actual source
translation is **not constant over time**:

| Original 2P guest frame | Exact source shift (upper → lower), dx/dy | Upper-source RGB matching final Original | Lower-source RGB matching final Original |
| --- | --- | ---: | ---: |
| 1856 | **0 / +113** | 497 / 640 emitted | 494 / 640 emitted |
| 1872 | **0 / +113** | 448 / 655 emitted | **0 / 655** emitted |
| 1888 | **0 / +113** | 444 / 646 emitted | **0 / 646** emitted |
| **2208 (after GO)** | **−13 / +112** | 569 / 630 emitted | **591 / 630** emitted |

All **eight independently captured source pairs** have zero
source-support (alpha) disagreement and zero actual visible
RGBA disagreement after applying the *frame-specific* measured
translation. Fractions here **count per-source emission**,
including source overlap counted twice; they are deliberately
**not** numbers of independent final output pixels or unique
PPU priority winners. During the blue countdown, the
separately accepted real pair-deletion counterfactuals
confirm zero final lower-racer contribution at 1872
and1888. By2208, most source RGB coincides with
final Original, but no equivalent post-GO deletion has yet
established causality.

This establishes **at least two different spatial
registrations across these sampled original 2P phases**.
It does not establish *which* intervening guest frame,
camera instruction, WRAM selector, OAM scroll write or
window/priority change produced the transition.
A fixed +113Y/0X transform is unsuitable for post-GO
source-faithful 2P reconstruction, but an equally fixed
−13X/+112Y transform is *not* automatically justified for
all later courses, motions and cameras.

The full 4-frame numeric source emission/RGB comparison,
transform, original-stock SHA and no-HD-admission record
is retained in
[`analysis/data/qa08-original-2p-source-registration-phase-matrix-1856-2208.json`](../analysis/data/qa08-original-2p-source-registration-phase-matrix-1856-2208.json).
This is a definitive source-backed **sampled** graphics
fact, not a generalized 3D camera model.

## Separately accepted native physical 4K Original source parity

The **same authenticated native frame2208** also has a
separately accepted **3840×2160 software physical-output
Original** record
`baldosa-evidence/ws342_physical_4k_frame2208.json`,
from successful native AOT
[38120828291](https://github.com/gamesbyian/UR-Recomp/actions/runs/38120828291).
The physically captured raster was checked against the
complete Original logical 342×224 PPU frame (SHA256
`f9ca59c19dc3e8d51c7ca1dbce25d5dc14e56ba36011128abbadee8cec0e7b4a`),
through the exact 1368×896 4× internal-density image
(SHA256 `776963ddc3c50f8824a0b026251aee5ae05296a841a135c1ff55eff119cec108`)
and the host's expected 7:6 source pixel-aspect nearest
resampling to a full-screen 3840×2160 target.
The independently recorded physical-output RGBA SHA256
is `29f6ef1f9b5965d32818228182922e337a0570433b5929c89e285af2969a0fac`.
The native report status is **`exact-native-capture-pixel-parity`**;
its original full 224 logical rows are retained, and the
horizontal 3840-wide mapping uses the recorded fixed-point
nearest integer fit.

This is exact **supplied software-output capture parity**,
not evidence that a particular user's SDL display can
successfully request/use that drawable, that a real monitor
was connected, that 4K authored sprite/text assets are
present, or that General 2P PPU foreground/camera priority
is reconstructed. The numeric 1×/4×/physical provenance
is preserved at
[`analysis/data/qa08-original-2p-postgo-text-physical-4k-parity-2208.json`](../analysis/data/qa08-original-2p-postgo-text-physical-4k-parity-2208.json).
The file retains no source screenshot or copyrighted sprite
bytes. The actual GUI and release 4K-capable product
gates remain independent.

## Next discriminator: the actual SNES colour-math register path

To determine whether this exact +13 native red5 signature
really came from original PPU colour addition, collect
**read-only native PPU register and scanline evidence**,
not another colour-match heuristic. The historically
imported independent MAME reference
`reference/imported/emulators/mame/snes_ppu.cpp`
identifies the required CPU-visible addresses:
`CGWSEL=$2130`, `CGADSUB=$2131`,
`COLDATA=$2132`. The independent imported bsnes
`third_party/src/beetle-bsnes-libretro/mednafen/snes/src/ppu/bppu/render/addsub.cpp`
implements saturating five-bit addition/subtraction
and half-brightness as separate computations.
Use these as **reference candidate semantics**,
not evidence that our pinned native guest exercised
any particular register setting.

A future narrow source-only capture should distinguish
register state and final PPU window/colour-math
selection on the **13 upper and 13 lower front**
source-supported pixels and on adjacent **unchanged
source-colour control pixels**, using exactly the
same independently verified original guest2208 and
four native source planes. Compare whether red
addition is enabled at those exact locations, what
the sub-screen or fixed RGB operands are, and if
`+13 red5` follows the real operand/half mode
without altering any guest state. For any claim of
layer ownership, retain an independent PPU removal
and source-overlay negative control and do not
infer from `CGADSUB` register values alone.
The ongoing exact native front98/front96 causal
counterfactual in [#1344](https://github.com/gamesbyian/UR-Recomp/pull/1344)
provides the immediate *final-pixel effect*
discriminator. Do not launch a new native colour
register investigation merely to repeat this already
running AOT.

The read-only tool distinguishes:

- **Exact +113 RGBA source alias**: actual nonempty upper/lower
  image support, exact visible RGBA match on every registered
  coordinate, no opaque source on the unpaired edge row and no
  source alpha leaking into the wrong viewport.
- **Actual divergence**: alpha or RGB differences, unmatched
  top or bottom edge emissions, or visible source bytes
  in unexpected split-screen bands. It retains bounded
  exact logical-pixel disagreements, not hypothetical
  geometry.
- **Source empty**: both paired source planes genuinely
  contain no opaque pixels. This is valid evidence of
  unobserved OAM source emission, not proof of no racers
  anywhere or authority to fill an HD slot.

```sh
python3 tools/check_baldosa_2p_postgo_source_pairs.py \
  --native-artifact-root path/to/extracted-postgo-AOT-artifact \
  --out path/to/qa08-native-postgo-source-pairs.json
python3 -m unittest tests.unit.test_check_baldosa_2p_postgo_source_pairs
```

Adversarial synthetic tests verify exact translated copy,
per-slot final Original RGB matches, source overlap and nonmatching
RGBA colour, missing per-pixel alpha, source-only unpaired edge,
a fully empty genuine pair, short/mismatched rasters, altered
stock Original provenance, stale seven-frame reports without
the true 2208 witness, changed original source SHA and
source-file substitution across slots.

This is a **follow-on, stacked independent docs/tool/tests PR**
based on the exact source schema from #1340. No additional
workflows, guest routes, AOT recompilation or renderer
changes are needed: the original post-GO source four-plane
artifact itself is the only required missing input.

**Crucial scope:** Identical pre-priority OBJ source bytes
do not establish which hardware BG/window/OBJ layer wins
final Original pixels, collision pivot, actual original
3D rig or HD art likeness; divergent source bytes do not
alone prove an emulator bug. The result cannot authorize
normal source-slot removal, 2P HD repainting or wider
Windows release certification. This code observes actual
pixels and leaves the Original fallback intact.

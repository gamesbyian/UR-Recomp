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

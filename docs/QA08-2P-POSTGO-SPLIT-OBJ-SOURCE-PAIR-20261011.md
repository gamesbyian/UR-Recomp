# QA-08: post-GO original 2P paired racer-source symmetry check

**Status: offline characterization ready; native original post-GO
slot96–99 source still pending successful [#1340](https://github.com/gamesbyian/UR-Recomp/pull/1340).
Do not claim exact alias, source positivity or final visibility yet.**

The original/native 2P racer OAM source mapping, traced in earlier
accepted moving pre-race captures, is P1 top **slot98** and lower
**slot97**; P2 top **slot99** and lower **slot96**. The earlier
original frames1856,1872,1888 showed pixel-exact replicated
upper/lower **RGBA source** using an absolute +113 original
raster-row shift. That result is real but not sufficient to
infer behaviour **after the countdown**, particularly while
the lower racers can be masked by other PPU presentation.

New native source route [#1340](https://github.com/gamesbyian/UR-Recomp/pull/1340)
reuses four existing independent slot-isolation processes and
captures every 2P source slot at guest2208, while independently
matching at least **seven** unchanged whole original 342×224
raster controls and full 2P guest CRCs.

`tools/check_baldosa_2p_postgo_source_pairs.py` consumes only
those original PPU PAMs, stock Original frame2208 and four exact
native source validation records. It then compares the real
upper/lower slot pairs at explicit **+113 raster rows**, checking
all visible source RGBA and alpha, *not* assuming equal sprites.

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

Ten adversarial synthetic tests verify exact copy, nonmatching
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

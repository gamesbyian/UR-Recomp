# QA-08: exact 2P upper racer front/rear native Original PPU reveal

**Bounded accepted underlying native inputs.** A new dependency-free
read-only analysis tool reinterprets *already completed* first-party
Original PPU counterfactuals. No new native AOT, ROM, gameplay, renderer,
HD artwork, Windows product or release gate is involved.

## Genuine PPU causal source observation

Use accepted pinned native AOT [38115756178](https://github.com/gamesbyian/UR-Recomp/actions/runs/38115756178)
(artifact `11693865103`; the earlier source work is present in
[38097914195](https://github.com/gamesbyian/UR-Recomp/actions/runs/38097914195),
artifact `11686843233`). The retained two moving 2P guest frames
**1856 and 1872** include the complete Original stock 342×224 raster,
actual isolated racer OBJ slots98 and99, exact stock/source-probe
metadata and full unchanged Original frame proofs, and a native
diagnostic PPU screenshot with only **slot98 removed at that same
guest frame**. The native single-slot proof reports include genuine
slot98 removal markers and complete matched guest CRCs.

The exact original final-screen source contribution partition is:

| Source/PPU observation | Guest1856 | Guest1872 | Total |
| --- | ---: | ---: | ---: |
| Top/front slot98 emitted source pixels | 321 | 325 | **646** |
| Top/rear slot99 emitted source pixels | 319 | 330 | **649** |
| Slot98-only pixels, all final changed when 98 removed | 164 | 81 | **245** |
| Shared coordinates with **different RGB**, all final changed to slot99 RGB after removing 98 | 143 | 207 | **350** |
| Shared coordinates with **identical RGB**, final unchanged on removing 98 | 14 | 37 | **51** |
| Slot99-only pixels, unaffected by slot98 removal | 162 | 86 | **248** |
| Changed full Original pixels outside actual slot98 source | 0 | 0 | **0** |
| Unexpected pixels under the exact original source/PPU relationship | 0 | 0 | **0** |

In these two real 2P frames, the original top racer slot98 is a
front-colour contributor at every one of its source coordinates,
but its independent **observable final-removal delta is not the
same as its emitted source extent**. The 51 identical-RGB
overlaps show why RGB equality and no visible change cannot
establish unique hardware pixel ownership. In the other **350**
overlaps, actual native PPU deletion reveals the exact RGB
of original separately exported source slot99, confirming the
specific compositing relationship for those source coordinates.
Slot99-only pixels remain unaffected by slot98 removal. This
is a strong causal, **frame-bounded** graphics regression invariant.

## Reproducibility

`tools/check_baldosa_2p_top_racer_ordinary_priority.py`
reconstructs this directly from the existing raw PPU PAMs; it
requires each accepted per-slot source report, source SHA/bbox,
six matching whole Original raster captures, same-guest-frame
stock SHA, the accepted single-slot98 deletion report and
that report's recorded exact changed pixels/CRC/arm state.
Each of all 76,608 Original RGBA pixels is classified with
a bounded disagreement example. It requires *both* native
frames be distinct. There is no new captured screenshot or
new guest process.

```sh
python3 tools/check_baldosa_2p_top_racer_ordinary_priority.py \
  --native-artifact-root path/to/extracted-native-AOT-evidence \
  --out path/to/qa08-top-racer-reveal.json
python3 -m unittest tests.unit.test_check_baldosa_2p_top_racer_ordinary_priority
```

Test coverage includes source-only front/rear, different-colour and
same-colour overlaps, deliberately incorrect revealed rear RGB,
a false delta in an identical-colour overlap, unexpected changes
outside source, altered native deletion/full Original/source
hash proof, and an independently sourced rear-only pixel hidden
despite otherwise self-consistent provenance.

The compact numeric and native SHA record
[`analysis/data/qa08-original-2p-upper-front-rear-native-reveal-1856-1872.json`](../analysis/data/qa08-original-2p-upper-front-rear-native-reveal-1856-1872.json)
contains no copied copyrighted sprite imagery.

**Strict limit:** The native PPU interventions demonstrate the
2P upper-layer colour relationship at exactly these two source
frames. They do **not** generally identify OBJ hardware owners at
same-RGB overlap, infer BG/window priority, certify the historic
SNES emulator's CPU/PPU parity, approve destructive slot removal
in the 342-wide Modern host, prove final 2P countdown lower-layer
priority (a separate #1330 investigation), approve current owner-vetoed
HD character likeness, or authorize a Windows beta.

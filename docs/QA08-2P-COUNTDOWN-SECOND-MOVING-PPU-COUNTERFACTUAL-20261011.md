# QA-08: independent moving 2P countdown lower-OBJ PPU counterfactual

**Status: PASSED second moving guest frame on exact-head native AOT
[38119117927](https://github.com/gamesbyian/UR-Recomp/actions/runs/38119117927),
artifact `11694649120` (tested commit
`3afaec0bffc5729687806cfe047442c6fc182caa`).**
Stacked directly on the accepted first-frame native counterfactual
[#1330](https://github.com/gamesbyian/UR-Recomp/pull/1330).
The later documentation/data commit does not alter its accepted
native executable or validator.
This preserves the accepted 1872 branch/head and does not replace it.

## Accepted starting point: first genuine countdown frame

Successful original native [AOT 38118239801](https://github.com/gamesbyian/UR-Recomp/actions/runs/38118239801)
(artifact `11694303573`) established original guest **1872**
source96/97 PPU emission of **330+325** opaque pixels (**411** distinct
source coordinates). Removing the pair *only on guest1872* in an
independent PPU execution left the complete **342×224** Original
unchanged, exactly **0 final RGBA changes**, despite real original
source emission. Four entire **2,473-frame** genuine 2P guest CRC
streams matched byte-for-byte; the actual native report records
the PPU pair removal and all source/frame SHA identities.

An **independent later Original source image** is already available
at guest **1888**, not merely a retimed or cached copy of 1872:
original lower slots96 and97 have **322+324** opaque source pixels
with **409 distinct occupied coordinates**, a **different 78-pixel
symmetric-difference alpha footprint** compared to source at 1872.
The entire final countdown-blue colour mask, however, remains
unchanged between1872 and1888 (exactly the same **16,770**
native original blue-coordinate positions). All 409 original
source coordinates at1888 still have final countdown-blue RGB.

Those are **observational** facts. They cannot prove that deleting
both lower source slots at1888 will also leave the final unchanged:
two different source layers or background/window priority conditions
could by chance produce the same final blue.

## Real native results: two source-moving countdown moments

Both frame-specific native PPU interventions **passed** at the exact
tested branch head. Their actual source and final-output facts are:

| Exact guest frame | Source96+97 opaque emission | Source union | Original full-frame changed by genuine pair removal | Full guest CRC |
| --- | ---: | ---: | ---: | --- |
| 1872 | 330 + 325 = **655** | **411** | **0 / 76,608** RGBA pixels | Four identical 2,473-line streams |
| **1888** | 322 + 324 = **646** | **409** | **0 / 76,608** RGBA pixels | Four identical 2,473-line streams |

The native run explicitly reports
`UR_QA08_2P_COVERED_PAIR_PPU native-covered-pair-final-unchanged
frame=1888 emitted=646 union=409 final_changed=0
changed_outside=0 release_hd=0`. Both frames have one genuine
`UR_RACER_HD_WIDE_REMOVE_PAIR` armed log marker, source-report
attestations, unchanged guest CRC routes and complete stock-vs-
removed PPU SHA identity. The second frame's complete Original
and pair-removed hashes are both
`7de0e805f07234d0b7b6c4c526eea79b5c6c523ff594c09ddc9970de238eede7`.

This proves **two independent native causal zero-effect results**,
while the lower OBJ source union has genuinely shifted at 78
logical coordinates, including 409 current alpha positions under
a full-frame stationary countdown-blue colour mask. It rejects
the competing explanation of a trivially cached/frozen racer source
at the second checkpoint. It does **not** prove all intervening
frames or recover the exact BG/window hardware priority.

The accepted two-frame hash and count witness is preserved at
[`analysis/data/qa08-native-original-2p-countdown-moving-pair-causal-1872-1888.json`](../analysis/data/qa08-native-original-2p-countdown-moving-pair-causal-1872-1888.json).
The raw PAM source graphics remain in the native GHA artifact.

## Single useful new experiment

This stacked change reuses the **identical pinned Baldosa AOT
executable and `race_2p_split.txt` deterministic route** already
built and driven by the existing graphics native workflow. Exactly
one additional original guest route arms diagnostic
`UR_RACER_HD_WIDE_REMOVE_PAIR=96-97` only at
`UR_RACER_HD_WIDE_REMOVE_FRAME=1888`, capturing the actual
frame1888 native PPU final Original output. No emulator framework,
host renderer or guest gameplay code is changed.

The existing `tools/check_baldosa_2p_covered_pair_causality.py`
now accepts an **explicit restricted `--frame 1872|1888`**
parameter, keeping default1872 and its proven existing contract.
The selected frame requires real native stock/source96/source97/
removed96+97 full P7 RGBA, exact source and Original
SHA/frame/slot reports, six independent Original frame-control
witnesses, precisely one frame-matched native removal arm marker,
and **all four complete 2,473-frame guest CRC streams identical**.
It compares *every* original output pixel and rejects any changed
pixel outside those actually source-positive slots.

Both outcomes are scientifically informative and neither is
prematurely forced to pass as zero:

- `native-covered-pair-final-unchanged`: zero effect after deleting
  both moving racer sources despite nonempty 409-coordinate union.
- `native-covered-pair-final-changed`: actual source-bounded native
  final differences exist; report counts/examples and prioritize
  fresh PPU-depth investigations.

A changed pixel outside the source union, tampered metadata,
wrong frame/slot, missing genuine source or unequal guest CRC
remains a strict failure. The existing artifact uploader retains
the new native log, raw Original removed-pair framebuffer and
`ws342_pair96_97_countdown_causal_1888.json` report.

New synthetic unit cases confirm both real native diagnostic
outcome classes are representable at frame1888, old 1872
acceptance is unchanged, stale native frame arm markers fail and
unapproved other frames cannot be used as a release shortcut.

**Interpretation limit:** Even two consecutive source-motion
samples with zero final PPU change do not establish a universal
BG/OBJ/window owner, permit production sprite erasure, fix
character mesh design or authorize any Remastered 2P/4K output.
The owner-rejected procedural HD unicycles remain unapproved;
the product keeps its Original fallback and release authority
stays with independent QA.

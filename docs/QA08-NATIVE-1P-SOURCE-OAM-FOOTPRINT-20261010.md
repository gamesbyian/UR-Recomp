# QA-08: native authored 1P pixel locality versus actual source OAM

**Status: independent read-only graphical QA candidate.** No change to racer painter, source OBJ admission, guest CPU/PPU or shipping graphics.

## Accepted source

Merged #1228 native AOT run 38089648874, artifact 11683487886, demonstrates 5,447 identical original/host guest CRCs and two genuine fixed-width P1-only HD captures.

| Frame | P1 source bottom | P1 top source | Changed 4x pixels | 4x changed-pixel bounding box |
| --- | --- | --- | --- | --- |
| 1728 | slot97 X96,Y96; 315 opaque | zero | 3,422 bottom, zero top | X448..523, Y448..531 |
| 1744 | slot97 X96,Y96; 316 opaque | zero | 3,526 bottom, zero top | X448..523, Y448..531 |

The bbox was examined directly using real native 1024x896 captures and independently retained 256x224 PPU underlay taken AFTER source OBJ removal. Original countdown overlay is still on both images. This does not establish polished racing, 342-wide authored HD or exact stock foreground/background priority.

## Spatial safety oracle

The new tools/check_baldosa_1p_hd_placement.py independently compares every dense pixel to native post-OBJ PPU output. It requires:

- exact signed OAM X and hardware-wrapped Y, slot98 for top / slot97 for bottom, native 64x64 dimensions, split clip at scanline112;
- same-frame authorized HD present, actual original isolated-OBJ opaque count, both native PAM source files, and native host changed-pixel counters;
- no changed pixels anywhere without source admission, nor beyond that rider's original 64x64 source OBJ footprint;
- matching 5,447-frame independent guest CRC evidence and no unsafe fixture from the separately accepted native classifier.

Reports exact 4x changed bounding rectangles and SHA256s. Adversarial tests cover top-band phantom paint, out-of-footprint bottom paint, frame provenance, and wrapped source Y.

**Limit:** This only validates authoring locality relative to post-removal PPU pixels, not untouched stock Original foreground priority, 1P continuous art coverage, 2P P2 foreground ownership, or integrated Windows Remastered release.

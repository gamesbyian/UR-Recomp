# QA-08: exact current native medal pixel physical 4bpp winner (one-shot)
18 October 2026 | **read-only original PPU source experiment; never merge the runtime instrument**

## Decision

The original 2014 Snes9x / RF017 Windows 263-frame census has a fixed
296-position medal silhouette disagreement repeated at 25 sampled result frames.
At guest 4032, the actual current native pixel-owned layers are already known:
(x207,y91) BG1; (x205,y115/139) OBJ; (x225,y96/120) OBJ.
Actual native OAM slot112/113/114 tile names are A0/A2/A4 while the
source original field4032 OAM contains A2/A4/A6. Earlier source
[#1788](https://github.com/gamesbyian/UR-Recomp/pull/1788) additionally
found complete original-2014 544-byte OAM payloads entered the genuine
current RF017 Windows PE two host fields earlier (4030/4174), but that
does not prove which tile actually won a *current* raster pixel.

**Smallest missing witness:** At three to four of these *already wrong*
coordinates, identify the physical current native SNESRecomp sprite fetch
which last wrote OBJ: original OAM slot, actual tile name/attribute,
decoded 4bpp VRAM tile address, row, plane bits, nonzero pixel nibble,
CGRAM palette base and priority. Compare the resulting OBJ zbuffer word
against the existing same-source native effective pixel owner probe.
Do not infer a source-original effective pixel owner from an adjacent OAM
entry or from a full OAM DMA input alone.

## Exact scope and controls

This is an additive **read-only** patch to the pinned
RetroPortingToolKit/snesrecomp `runner/src/snes/ppu.c` commit
`075fbe4c8e0d97b0013be541795c39cb644a9709`, in
the exact disposable gamesbyian/uniracers-recomp
`10b864b9d14a7b7416dd909eb7b054c88faef101`
title checkout only. The marker is inserted next to the real SNES
sprite fetch `dst[0] = z + pixel`, after transparent/clipped pixels are
rejected; it retains *all* same-pixel candidate writes in their actual
execution order so a later lower-numbered OAM slot can be the winner.
This is **not** a second sprite renderer or a replacement for
`ppu_render_pixel`; actual composer and OAM probes from closed research
[#1782](https://github.com/gamesbyian/UR-Recomp/pull/1782) remain active
in this disposable experiment as independent per-pixel controls.

The already archived source original/PPU comparison and the full real
Windows current native 2P route are the controls. The exact USA retail
ROM SHA256 is
`859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`;
the literal existing controller script SHA256 is
`ef74ec51fa585aa76652f4a14d2727f0074434b3925522ab2607e3bd29aa0194`.
**Require all 5,484 true guest CRC entries** and exact SHA256
`b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568`;
the comparison is invalid without that source identity.

Five sampled genuine native result guests:
4032,4048,4064,4080,4176. Each probes original logical coordinates
(207,91), (205,115), (205,139), (225,96), (225,120), with native internal
`ppu_line=raster_y+1`. Our already-proven native 25 effective PPU
pixel witnesses and 175 OAM candidates are required, along with current
real source CGRAM port writers. One new source witness is emitted only
when an actual nontransparent in-bounds sprite writes one of those
coordinates: tagged `UR_QA08_WIN_OBJ_FETCH`. The compact parser
recomputes its actual pixel nibble from the physical VRAM plane
bits, OAM flip, sub-tile column and sprite priority, and verifies the
last writer at every native OBJ-main pixel against that same guest's
already observed OBJ zbuffer word.

## Outcomes and stop rule

- **Exact last native fetch equals current native PPU OBJ pixel:** native
  OAM tile/slot/VRAM winner proven. Compare it to independently archived
  original source **only after** original same-epoch sprite ownership is
  separately qualified; the remaining medal shift may still originate in
  CPU/NMI OAM publication, not PPU graphics.
- **Different last fetch than effective native OBJ:** real extra-object,
  sprite-buffer poststage or source-frame registration must be located;
  no source tile reindex is authorized.
- **Missing/incomplete source or changed CRC:** retain logs and mark
  NOT ADJUDICATED. Never reconstruct invisible samples.
- **Non-OBJ BG1 points:** preserve them explicitly as negative controls;
  do not assign a medal sprite winner where an independent BG pixel won.

Exactly one decision-bearing current RF017 Windows run. Save actual
compiled PE, run/candidate identity, raw bounded source trace and
machine receipt for independent QA. Do not merge instrumentation into
shipping. **No guest clock/CPU/APU, native Modern SRAM, palette LUT,
final pixel painter, guessed frame shift, UHD scaling, HD racer or release
ledger edit is permitted.** The owner of the original/native CPU source
must adjudicate guest publication/NMI causality before any renderer patch.

## Current-head execution branch

Current diagnostic built as an insertion-only child of production graphics
source `6e77b097803da6c6812f6e661ac82f36fff24267`, whose first parent already incorporates RF050 main
`9e697cd071c8f9a18e077e8a91ea380d3af26b9f`.
This branch imports the proven old #1782 pixel/OAM/CGRAM read-only logger
and adds only the new genuine physical 4bpp tile-fetch observer. The entire
existing Windows workflow remains an ordered untouched subsequence.
The actual source route is still RF017 with 5484 original native frames.
This experimental branch is never a release candidate; the previously
accepted graphics #1780 remains unchanged and explicitly held.

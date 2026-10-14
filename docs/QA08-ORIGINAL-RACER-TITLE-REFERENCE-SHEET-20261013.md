# Original-source HD racer reference contact sheet

**Source-first reconstruction input, not remastered art approval.**

The reproducible tool `tools/art/build_qa08_original_contact_sheet.py` consumes
the existing verified Baldosa native graphics AOT artifact ZIP from
[run 38492408817](https://github.com/gamesbyian/UR-Recomp/actions/runs/38492408817),
artifact **11863045863**. It requires exact source bytes, sizes and SHA256
digests for the original USA title's guest-frame400 256×224 PPU raster,
post-GO guest-frame2208 authentic 342×224 split-screen raster, and
four independently native-extracted original OAM slot source layers
96, 97, 98 and 99 from that same 2P guest frame.

These six inputs are independently hash-checked against the original
native evidence. Slot source nonzero-alpha counts must match the accepted
**317, 313, 313, 317** pixels for slots98, 99, 96, 97 respectively.

```sh
python3 tools/art/build_qa08_original_contact_sheet.py \
  --artifact /path/to/baldosa-native-spike-evidence.zip \
  --out /tmp/qa08-original-reference.html
```

The resulting **self-contained HTML** embeds lossless PNGs made from the
original native raw RGBA. No ROM, original copyrighted image, custom font
or generated image asset is committed. A JSON provenance sidecar with the
same base name contains exact source hashes, crop native coordinates and
alpha counts. The HTML viewer applies the authentic **7:6** SNES physical
pixel aspect by changing the *display width only*, never upsampling or
altering raw source pixels. An additional title preview uses **CSS-only
brightness(4)** and is conspicuously labelled an inspection aid, because
the native frame400 original is in a dark title fade (largest RGB8=51).
That filtered view is **not** an accurate full-bright colour reference.

These views make the relative saddle, frame, fork, wheel silhouette and
dynamic game OAM poses accessible together in one repeatable briefing.
The two title unicycles overlap and are in perspective. OAM isolated
source alpha is not a finished-composite pixel owner; the dimensions
of its sparse 30-ish pixel shape are not a recovered three-dimensional
character model. The sheet is a source-contact tool, **not**
shipping Remastered approval or a justification for overpainting
Original pixels. The owner veto on procedural HD character likeness
remains fully active.

Two precise follow-on art tasks: add an independently verified
non-fading title/reference screenshot when available, and register
measurements from multiple poses against genuinely independent period
packaging/press artworks without mistaking duplicated box images for
multiple independent artist perspectives. A human artist must accept
the coherent candidate design before promoting any source-family HD
assets. This tool adds no original/emulator/gameplay/Modern/QA release
path or GitHub Actions campaign.


## Period-source intake correction (2026-10-14)

The proposed DMA Design press archive was **inspected by the project
owner** and contains only one Uniracers-related PDF, **already present
in the repository from its first research days**. This is a completed,
duplicate lead: no additional authentic model view or new visual
reference came from it. Do not download the archive again or promote it
into the title/OAM reference contact sheet. The
[period-source research ledger](HD-RACER-PERIOD-PR-ART-SOURCES-20261014.md)
records the explicit retirement and the independent remaining sources.
Previously SHA-authenticated original PPU/OAM atlas references are unchanged,
and current procedural 4× art still lacks aesthetic approval.

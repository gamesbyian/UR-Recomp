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


## Newly located period-source archive, pending actual image inspection

The [HD racer period press research ledger](HD-RACER-PERIOD-PR-ART-SOURCES-20261014.md)
records an independently catalogued original DMA Design press-material
collection, an original 1995 German magazine advertisement and sources for
regional print imagery. The archive is catalogued as containing Uniracers/
Unirally material, but its individual images are **not inspected yet**;
no external artwork is admitted into the reference contact sheet or
presented as a third verified pose. Human likeness approval remains
mandatory. Existing SHA-verified title PPU and multi-pose OBJ source
images remain authoritative for original projected game pixels.

# Original racer palette-index audit

This source-only experiment addresses a known limitation of RGB-threshold studies. The original ROM-composed 41 colour images represent 35 binary source silhouettes; six silhouettes have two original colour variants, whose high-chroma fractions inside the wheel ring can differ by up to 5.82 percentage points with unchanged alpha geometry.

The existing original USA-ROM source compositor already decodes planar 4bpp pixel indices before applying a BGR555/8bit palette. The new bounded audit replays the SAME composition inputs, preserving transparent-index-zero overwrites and original 64x64 tile geometry. It reconstructs each index raster, then rebuilds its RGBA pixels from the exact ROM palette. It requires exact equality with the existing original RGBA composer and the source image SHA256 from the authenticated 59-representation original corpus. The exact original ROM hash, source manifest, registry bytes and all original PNG/RGBA/alpha/binary mask hashes are independently gated by existing validators.

The producer emits a write-once NUMERIC JSON report: original palette-index maps by digest; per-index pixel counts; ROM-derived RGBA colours; the existing red/blue chroma indicator for each index; and min/max count inside the seven-pixel original source wheel disk across EVERY tied source rim centre. All 59 authored-registry representations are preserved, with exactly 41 original RGBA and 35 binary silhouette groups. Same-RGBA different-index maps are explicitly reported rather than silently called the same source observation.

The mapping is from ROM source 4bpp index to rendered RGBA; no 4bpp index is independently proved to correspond to one anatomical 1994 3D part. Multiple pieces can use the same index, and original image ordering is a curated registry rather than live captured original PPU timing. This is evidence for a future semantic material/OBJ attribution experiment, not source geometry recovery or approval of the existing 2026 GLB.

Use the original source ZIP from previous verified run #41396846120 and a historical registry whose exact bytes match the SHA in that ZIP. The repo may have changed that registry since it was captured; in that case a newer registry must not be substituted. Pillow is needed only for source PNG authentication, with no new workflow. Standard library synthetic tests cover 4bpp decoding, transparent tile overwrite, source H/V reflection, palette index and wheel-ring bounds.

    python3 -m unittest tests.unit.test_audit_original_racer_palette_indices
    python3 tools/art/audit_original_racer_palette_indices.py \
      --rom reference/roms/retail/Uniracers_USA.sfc \
      --registry analysis/data/racer-hd-replacement-prototype.json \
      --source-zip /private/original-source-corpus.zip \
      --out /private/new/original-source-palette-indices.json

No changed GLB, pose viewer, new emulator, source sprite redistribution or shipping-art approval. The next independent discriminator remains source PPU/OAM palette/OBJ attribution and real animation chronology.


## Source index-zero transparency ambiguity and exact-byte correction

Independent source review found an important edge: the canonical original RGBA composer starts a 64x64 image as true black-transparent 0,0,0,0, while a source tile explicitly writing palette index 0 produces the exact ROM palette-zero RGB with alpha 0. If that palette entry happens to have nonblack RGB, equal index-zero values alone cannot reconstruct identical PNG RGBA bytes.

The new producer therefore retains BOTH an index raster AND a second tile-written/visited raster. Its RGBA rehydrator outputs true 0,0,0,0 for untouched pixels and the exact palette byte tuple for explicitly written positions, including transparent index-zero overdraw. The numeric ledger includes the tile-written mask SHA and counts of explicit-zero versus untouched background pixels. A synthetic negative/positive regression uses an original-like nonblack transparent palette-zero entry and demands byte identity against the preexisting original ROM rasterizer. This fix does not invent physical 3D part labels; the tile-written raster is one more authentic 2D source-provenance boundary.

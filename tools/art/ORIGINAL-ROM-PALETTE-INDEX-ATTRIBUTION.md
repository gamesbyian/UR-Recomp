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

## Authenticated real-ROM result (November 2, 2026)

[Exact source run #41537961500](https://github.com/gamesbyian/UR-Recomp/actions/runs/41537961500) **passed** on draft source head `68dada6346c3243013e658f615174f27dca8b719`. The producer checked the pinned USA-ROM SHA, recovered the exact historical registry SHA from source commit `7ba8295e966c8b2c959cfeb12ae82f8c701772e0`, and verified the archived 41 original RGBA PNGs, source alpha/mask and all 59 registered 4bpp RGBA reconstructions. Run artifact `13183968725` contains the full numeric report, file SHA-256 `b6f59fc5f9030b44ca9345bf308e5df83901f8b9534a6f33b215fa39f8e3079e`. The action artifact expires November 9, 2026; a compact durable summary is at `analysis/data/racer-original-4bpp-index-census-summary-20261102.json`.

All 35 unique binary silhouettes correspond to exactly 35 original 4bpp index planes. There are **zero** cases of identical RGBA images with different index planes, and **zero** cases of identical binary masks with different index planes. Therefore, in this frozen corpus, all six same-silhouette colour variants use **identical index placements**; their visible differences arise from the palette mapping. This supports testing index-stable material-colour hypotheses without treating red/blue RGB threshold masks as source authority.

For each of the 15 nontransparent index values, the summary reports pixel counts and bounded inside-wheel-disc counts across the **35 distinct index planes**, avoiding false independence from 59 registered descriptions. All tied 2D ring-centre hypotheses are retained. These counts do **not** establish the source anatomical identities of wheel, rim, fork, crank or hub, nor any independent original PPU/OAM timing or source camera. No rig/GLB was modified and no owner likeness approval is implied.

The temporary source-workflow invocation used to obtain the report was removed from the final PR diff. This retains the opt-in workflow's original targeted triggers and avoids a permanent dependency on the expiring archived ZIP.

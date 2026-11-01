# First-family original racer colourway census (source-authenticated 2D)

**Scope:** 32 original ROM-composed P1/P2 observations from guest frames 1205–1220, 14 retained first-family PNG filenames, **ten independent binary silhouette groups**. Exact input provenance is authenticated by the existing `build_racer_source_pixel_corpus.py` source hashes. This report measures source-raster pixel colour and does **not** infer original 3D material parameters, camera, lighting or 2026 blockout pose identity.

## Why this matters to the current single blue model

The current source-owned experimental five-part GLB from draft [#2832](https://github.com/gamesbyian/UR-Recomp/pull/2832) is primarily blue on the coloured fork/frame material: the actual verified published `upright` GLB in the viewer's [real-asset Actions evidence](https://github.com/gamesbyian/UR-Recomp/actions/runs/41259476190) contains `fork_and_frame__material_0` with vertex colour **RGB 28,89,222**, and a blue-gray base. That is a valid experimental *one-colourway blockout*. The game's authentic P1 source-raster samples have **red** chromatic accents while P2 samples have **blue** accents. A viewer selection of P1 sprite beside that single GLB is therefore visually diagnostic, **not** a source-matched original P1 palette reconstruction. 3D silhouette metrics remain colour-independent.

Reconstructing the original's recognisable colour identity will require distinct, traceable P1/P2 material parameters on the **same canonical rig geometry**, with validation against original source pixels under appropriate lighting and pixel aspect. Do not duplicate the rig, apply an unverified client-side recolour, or treat exact 1994 raster palette RGB as linear PBR albedo. The viewer agent owns whether/how to show a clearly marked provisional source-colour switch in the existing Pages site.

## The actual raster evidence

The existing source PNGs contain predominantly low-chroma tire/saddle grays plus a relatively small high-chroma racer accent. The new `tools/art/audit_original_racer_colourway.py` applies the following *heuristic descriptive RGB indicator*, explicitly **not a 3D mesh-part segmenter**:

```text
Red accent indicator:  R >= 64 and R > 2*G and R > 2*B
Blue accent indicator: B >= 64 and B > 2*G and B > 2*R
```

| Exact original group (equal weight per 64×64 binary silhouette) | Independent source silhouettes | Mean red-indicator pixels / shape | Mean blue-indicator pixels / shape |
| --- | ---: | ---: | ---: |
| P1 | 6 | **54** | 0 |
| P2 | 4 | 0 | **67** |

All 32 original source frames are authenticated and represented in these ten shape groups. Identical repeated sprite frames do **not** add another vote. If a future original frame has the exact same binary mask but different source RGB palette, the auditor retains that as an explicit independent **colour variant within the one source shape**, giving equal weight to each variant rather than frame-hold length.

## Reproduce

```sh
# From repository root, no original ROM, OpenSCAD or graphical dependencies:
python3 tools/art/audit_original_racer_colourway.py

# Immutable, private output (will never replace existing paths):
python3 tools/art/audit_original_racer_colourway.py \
  --out /private/ur-art4k/original-colourway-1205-1220.json

python3 -m unittest tests.unit.test_audit_original_racer_colourway
```

The report provides per-source-shape original PNG identities, exact source decoded-RGBA and original binary-mask hashes, full **opaque RGB frequency counts** (not redistributed source images), chroma indicator counts/fractions, per-player equal-shape-weighted means and falsely asserted 3D/material/owner/shipping approval flags. Existing independently verified source manifests remain authoritative. Test cases include changed colour at unchanged mask, duplicate/absent frame, fake ROM/registry SHA, wrong original player, altered decoded PNG SHA and nonbinary alpha, with positive integration on the real original retained first-family PNGs.

**Suggested next art review:** display original P1 and P2 source palettes alongside *explicitly provisional and separately configurable* material variants from the unchanged five-part 3D rig, at authentic 64px and 7:6 physical aspect. Keep colour fidelity and source-silhouette/3D-pose correspondence as separate acceptance gates. This evidence does not make the blue blockout a source-approved racer.

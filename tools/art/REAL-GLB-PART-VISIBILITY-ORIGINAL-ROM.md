# ART-4K: source-owned 3D part alpha attribution against real original sprites

**Problem:** The original-USA-ROM static silhouette studies were treating each of the 35 original binary sprite shapes as if the single experimental 2026 **upright** GLB had the correct source animation pose. That assumption is not established. A source-owned five-part leave-one-out projection can quantify which *2026* parts' uniquely visible pixels help or harm overlap, but cannot label which corresponding 1994 sprite pixels belong to a saddle, wheel or fork.

## Actual-source result

The original USA ROM, source PNGs and 35 unique alpha-mask hashes are rechecked. The input GLBs are **actual verified OpenSCAD→GLB exports** of the same 2026 source: unmodified upright `ffa14324c10c50b68400fbfab4285d893b248d081a50361c01d09937dd03bc04` and original-source fork1.4 `5531438b95c97dc0508790247aa3f5889f7c0d96d9079ba2970529cb1e05fa53`, with the same previously verified +10% tire/rim X span applied *in memory* to the latter. The fixed provisional P1-1205 orthographic 7:6 source camera, original registered visible lowest-alpha anchor and exact 4× pixel-center source rasterization are held unchanged.

For each candidate, the real five-part/16-material GLB is baked into world coordinates. Six authentic 3D projections are rendered: the whole model and five otherwise-identical projections omitting exactly one of `tire`, `rim_and_hub`, `pedals`, `saddle`, `fork_and_frame`. Every source sprite contributes exactly one vote per binary-mask SHA. For each part, `full & ~without_part` identifies only the uniquely visible 2D model pixels lost by omission. Comparison against each real original alpha classifies those pixels as original true positives or false positives. **Overlapping/occluded pixels cannot be assigned to a part by this method.** The original missing alpha pixels remain non-attributable; the experiment does not identify the original 1994 3D mesh's part segmentation.

The locally executed independent exact 4× raster reproduces the complete original-ROM crossed-study full-model IoU **per original mask exactly** (maximum difference 0.0 across all 35 shapes) and all-35 means **0.46002071** for unchanged, **0.49816283** for the optional combined fork1.4/wheel1.1. The full numeric 35-shape/5-part/two-model report was generated as `UR-Art4K-source-3D-part-ablation-real-ROM-20261101.json`, SHA-256 `1ca267e60bec48872bf048a546d77a1ba7f880fa7d6c0d0287f601987e0e1ca9`, from the original source ZIP and two retained real GLBs. The compact report is checked into `analysis/data/racer-art4k-original-ROM-real-GLB-part-attribution-20261101.json`. This locally verified source result is **not yet a fresh GHA real-ROM acceptance check of the new script**, so do not confuse it with hosted CI.

### The decisive diagnostic: original animation family matters

| Real 2026 upright part omitted | First original fit-connected family, 16 mask mean IoU change | 19 other SHA-disjoint source masks, mean IoU change |
| --- | ---: | ---: |
| Saddle, default GLB | **−0.064458** | **+0.052917** |
| Fork/frame, default GLB | −0.013380 | +0.015293 |
| Saddle, combined GLB | −0.054151 | +0.052966 |
| Fork/frame, combined GLB | −0.022149 | +0.011418 |

**Positive** means omitting the part improves overlap. The otherwise unchanged 2026 upright saddle is helpful on the source family most similar to the original upright, but harmful on other original source presentation families: among those 19 additional original 2D masks, it contributes just **one** uniquely visible true-positive pixel versus **987** false-positive pixels with the unmodified upright. The combined variant similarly produces 1 true positive versus 930 false positives. These are *cumulative across 19 masks*, not pixels in one 64×64 image.

The tire and rim/hub removal, by contrast, worsens full overlap on **all 35 source masks** for both model variants. The fork/frame and saddle contribute many extra pixels in the other source families, though this may reflect wrong 3D pose, wrong original camera, occluded authentic artwork, or incorrect geometry. There is insufficient evidence to assign a unique cause.

**Decision:** do not delete, shrink or redesign the saddle based on this static-upright, unpaired-source raster result. First establish source-original frame/semantic pose grouping and a source-bound relationship to the *same* 2026 rig's authored ride/stunt poses, then compare corresponding whole-source silhouettes under independently justified camera/contact constraints. Preserve full-model and per-part metrics, renderer checks, model SHA, source family connected-component exclusions, and the existing sole Pages viewer. No new model or shipping art.

## Reproduce

    python3 tools/art/evaluate_original_racer_part_ablation.py \
      --corpus /real/original-US-ROM-source-corpus.json \
      --unchanged-glb /sha-pinned/upright-default.glb \
      --combined-glb /sha-pinned/source-fork1.4.glb \
      --camera analysis/data/racer-inverse-side-provisional-1205.json \
      --out /new/part-attribution.json

The final `--combined-glb` input is the **source-fork-only** actual GLB. The script applies the +10% source tire/rim X factor in memory as already tested in #2978/#3009. Require a freshly generated original-ROM corpus with its PNGs adjacent, exact historical two GLB SHA identity, and a new no-replace output path. Source script and unit tests are ROM-free in ordinary GHA tooling; full genuine source reproducibility requires OpenSCAD outputs and the authenticated original source corpus. If exact source hashes change, produce a **new versioned** evidence report, not a fake historical match.

This is research-only. No original 1994 3D geometry/camera or physical contact, original game→2026 articulated pose registration, owner character likeness or shipping art is proven, and no gameplay/release acceptance is earned.

# Original ROM 2D wheel-anchored 3D frame-hinge fit

**Experimental 2026 blockout only, no source-3D likeness acceptance.** This experiment is stacked on wheel-candidate PR #3035 and retains the ONE existing 2026 five-parent / sixteen-material GLB and fixed provisional 7:6 side camera. Source wheel-ring candidate centres are independently obtained from the 41 authentic ROM-composed colour PNGs (35 unique binary silhouettes). The tool revalidates the original source raster hashes, alpha mask identities, and all palette variants before using their 2D ring centres; no target GLB overlap is used to select a translation.

It compares exactly the original upright GLB (SHA256 efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5) with a −40° axle-centred FORK+SADDLE parent-only variant. The wheel, rim and already-baked cranks are untouched. It calls the existing fourfold render_racer_glb_projection triangulation, locks camera SHA 1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028, and projects the existing source axle to the exact fourfold pixel coordinate. Each authentic source ring centre proposes a possible integer, nonclipping raster translation. ALL tied one-pixel positions yield an uncertainty interval of model IoU scores, without selecting the best-shape-overlap shift.

Independent local original-ROM and actual GLB execution established:

| 35 authentic binary source silhouettes, equal mask weights | Earlier source lowest-alpha alignment | Source ring alignment, lowest tied IoU | Source ring alignment, highest tied IoU |
|---|---:|---:|---:|
| Existing upright model | 0.46002071 | 0.41237579 | 0.42198267 |
| Fixed −40° fork/saddle | 0.47955889 | 0.43118927 | 0.43382268 |
| Previously explored source painted-axis pose rule (angle above +20° selects −40°, otherwise original) | 0.54715522 | 0.49514691 | 0.50339133 |

Source-family controls from the previous exact binary SHA-disjoint grouping:

- First connected 16: upright ring worst/best 0.50548473 / 0.52533087; fixed hinge 0.37556948 / 0.38133007; painted-axis-conditioned 0.51487815 / 0.53291282.
- Additional 19: upright 0.33396827 / 0.33495260; fixed hinge 0.47802699 / 0.47802699; painted-axis-conditioned 0.47853113 / 0.47853113.

This is a deliberately useful **negative/robustness result**: switching from whole-source lowest alpha alignment to source grey-ring centre *lowers* absolute overlap by roughly 0.04–0.05 under the existing uncalibrated camera. However, the previously observed difference between source orientation families and the benefit of an independently selectable frame hinge persist under a translation source that does not consult the projected model silhouette. Tied centre bounds are NOT a sampled posterior or calibrated confidence interval.

The −40° candidate, +20° source-colour threshold, camera hypothesis and grey wheel-ring detector were all chosen after prior inspection of these same source images. There is **no independent unseen 3D viewpoint, source pose registration, physical axle, author 1994 camera or live gameplay cadence**. These scores cannot approve new geometry or shipping art. The next discriminator is source-painted semantic fork/saddle landmarks and independently captured emulator PPU/OAM observation chronology, with the same camera held fixed.

Reproduce against the original retained source-corpus ZIP from run #41396846120, extracted privately as source-corpus.json and stock/*.png, the pinned historical upright GLB from run #41259476190, and the optional authentic chroma and source-family JSON reports from run #41398486394:

    python3 tools/art/evaluate_original_racer_wheel_anchor_registered_hinge.py \
      --corpus /private/source/source-corpus.json \
      --glb /private/model/upright-efdc8425f252b4a0.glb \
      --camera analysis/data/racer-inverse-side-provisional-1205.json \
      --chroma /private/source-chroma-axes.json \
      --split /private/wheel-holdout.json \
      --out /private/new/wheel-centred-3d-pose-comparison.json

The code requires optional NumPy/Trimesh for actual GLB rendering but only basic Python for numerical unit tests (NumPy-dependent raster tests skip if unavailable). The output is an immutable write-once numeric report; it does not copy ROM, PNGs or GLBs into the repo, mutate the unified rig or deploy a separate viewer or workflow.

# ART-4K experimental articulated blockout

**Unapproved candidate, not shipping artwork.** This is a recovered 2026-10-18 OpenSCAD study from closed PR #1826, plus a new offline exporter. The original owner rejection of the procedural character likeness remains in force. No production presenter, guest gameplay, original sprite, ROM, Windows packaging, or release ledger is changed.

The old flat STL/GLB export fused the whole character. The new optional tool creates **five separately selectable GLB nodes**: tire, rim/hub, fork/frame, pedals and saddle. The saddle mesh is rebased to its **source-owned** mount, extracted from the canonical `saddle(lean=0)` OpenSCAD definition. A malformed, duplicated or no-longer-recognizable mount fails closed instead of silently misregistering a pivot. Wheel, rim and pedals use the wheel hub as their node pivot. These are editable assembly parts, **not a skeletal rig**, source-timed animation or approved model. The five editable parent pivots now retain **16 independently colored child meshes**, extracted by source-owned OpenSCAD color passes (tire 2, rim/hub 5, frame 4, pedals 3, saddle 2). Each child is watertight, has its own material RGBA and stays attached to the correct pivot across named blockout poses. These are the **2026 procedural source palette**, not recovered original-game materials or approved art.

From the repository root with `openscad`, `numpy` and `trimesh` installed:

```sh
python3 tools/art/export_articulated_unicycle.py tools/art/candidates/unicycle_shared_rig.scad /tmp/ur-art4k
python3 -m unittest discover -s tests/unit -p 'test_export_articulated_unicycle.py'
```

**Two actual source-module pose studies:** The exporter now permits bounded, explicitly experimental `--pedal-phase` (−360..360 degrees, default 18) and `--saddle-lean` (−30..30 degrees, default 0). For the existing blockout's named `pedal` pose, use a separate output directory and the **same** OpenSCAD source:

```sh
python3 tools/art/export_articulated_unicycle.py tools/art/candidates/unicycle_shared_rig.scad /tmp/ur-art4k-pedal --pedal-phase 88 --saddle-lean -5
```

These values are copied from the recovered blockout's `rig("pedal")` branch, **not from a measured original game pose**. Each GLB independently evaluates the OpenSCAD `pedals(phase)` and `saddle(lean)` modules, preserving the pedal platforms' unrotated orientation. Rotating the entire fused pedals node in a GLB would be incorrect: the cranks move with phase, while the pedal bodies remain level in the source module. The other three components retain the same source geometry. The output receipt and atomic success pointer record both control values; both outputs remain explicitly unapproved. These are separate static poses, not glTF animation channels, original source cadence, a physically rigged crank/pedal hierarchy, or a replacement for registered native gameplay.

**Named source-blockout pose transforms:** `--rig-pose upright|pedal|wheelie|stunt|bank` reads the existing pose's crank phase, saddle lean and *outer translation/rotation* directly from the unchanged OpenSCAD `rig(p)` branch. It applies that transform to each of the five GLB nodes, preserving individual selection and the transformed world-space pivots. For example:

```sh
python3 tools/art/export_articulated_unicycle.py tools/art/candidates/unicycle_shared_rig.scad /tmp/ur-art4k-wheelie --rig-pose wheelie
```

The original blockout has only these five static named branches; continuous `ride` and `stunt_cycle` are **not** imported as source-timed animation. Named poses cannot also receive manual phase/lean overrides; use `--rig-pose custom` (default) for arbitrary exploratory controls. Unsupported/ambiguous source transforms fail closed. The receipt records both the local part pivots and the named pose's transformed world pivots, plus the actual source-derived transform matrix. These are **2026 procedural blockout** poses, not authenticated 1994 animation poses or owner-approved likeness. A matching 3D bounding box validates transform implementation, not original fidelity.

**Publication contract:** Every invocation writes `articulated_blockout_last_attempt.json` with `running`, `failed` or `succeeded` status and the exact source SHA-256. Successful exports stage the GLB and receipt privately, then publish both together into a **unique immutable** `attempts/<id>/` directory. `articulated_blockout_current.json` is atomically replaced only after both files are complete and identifies their relative paths and SHA-256 digests. A failed or interrupted rerun leaves an earlier successful attempt and pointer intact, **but does not represent that earlier asset as the current run**. Inspect `last_attempt.status` and its `attempt_id` against `current.attempt_id` before trusting the latest command's result. Do not infer success from the existence of an old GLB or receipt. A failed run intentionally leaves the previous good files available for recovery; no automatic deletion occurs. Filesystem atomic rename is scoped to one local filesystem, not networked/SMB transactional durability.

The exporter rejects empty/nonfinite/nonwatertight component meshes and emits source/GLB SHA-256, part pivots and explicitly false likeness, cadence and shipping approval. OpenSCAD and Trimesh are **optional offline authoring dependencies**, never runtime or CI prerequisites.

**Remaining work:** authenticate a high-detail original title/packaging view and adjacent genuine original gameplay poses; measure perspective-tagged landmarks with the existing `measure_unicycle_reference.py`; fit wheel/fork/saddle and original contact/pivots; reconstruct source cadence, original-faithful materials, lighting and motion; compare at 32/64px and 4× in 1P/2P; obtain explicit independent owner likeness approval. No ART-02..ART-10 or Windows/USA event credit from this technical export.

## Source-owned optional 1.4× fork A/B (experimental, NOT default artwork)

A real source-ROM OpenSCAD experiment selected **1.4× fork/frame source `frame_member` mass** on ten original binary silhouettes and then separately retested it on **19 SHA-disjoint original 2D silhouettes** from other registered original-ROM windows. On the 19 masks, complete IoU increased **0.38192089 → 0.38824958 (19/19 wins)**; the more aggressive 2.0 mass lost all 19 shape overlaps. Mean physical boundary Chamfer at 1.4 became slightly **worse**, 3.07819813 → 3.08501689. This is worth **visual review**, not an accepted source character shape or 1994 independent 3D pose proof. See [main research PR #3007](https://github.com/gamesbyian/UR-Recomp/pull/3007), actual ROM/OpenSCAD source producer #41360120641 and pinned `analysis/data/racer-art4k-source-frame-mass-original-19-mask-20261101.json`.

The **same** five-part, 16-material source-owned exporter now supports:

```sh
python3 tools/art/export_articulated_unicycle.py tools/art/candidates/unicycle_shared_rig.scad /tmp/ur-default --rig-pose upright
python3 tools/art/export_articulated_unicycle.py tools/art/candidates/unicycle_shared_rig.scad /tmp/ur-fork-review --rig-pose upright --frame-mass 1.4
```

The default 1.0 does not add OpenSCAD overrides. For 1.4, the exporter requires the **exact historically authenticated source SCAD SHA-256** `e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984` and passes `-D rig_frame_mass=1.4` to both the uncoloured source sentinel and all source-material OpenSCAD passes, rather than generating a second model or modifying a source file. The atomic full GLB receipt and current pointer independently declare source SHA, frame-mass value and false original 1994/likeness/shipping flags. Only **1.0 and 1.4** are allowed until a new source-bound review explicitly qualifies further values.

`.github/workflows/art4k-real-fork-mass-review.yml` runs on source exporter/test changes and creates **both actual source GLBs**. A separate independent Trimesh loader verifies two five-part, 16-material GLBs, immutable source hashes, pivot transforms, color/material identity, unchanged tire, rim, pedals and saddle geometry/normal/triangle signatures, and at least one changed fork source geometry signature. Both source GLBs and their receipts are uploaded for direct use in the **existing** Pages 3D model reviewer via its local GLB upload. No new rig, no automatically published model variant, no original sprite-to-pose mapping and no shipping or title-game art acceptance is implied.

**Next art question:** compare the two real source GLBs at source gameplay size and with the existing authentic P1/P2 sprites, checking saddle shape and wheel/frame contact as well as surface fullness. If the thicker fork does not look more faithful, keep it experimental regardless of the positive whole-image IoU. Original character visual veto and owner likeness approval remain binding.

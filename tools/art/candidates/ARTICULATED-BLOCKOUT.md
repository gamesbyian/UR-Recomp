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

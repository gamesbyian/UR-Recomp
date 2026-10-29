# ART-4K experimental articulated blockout

**Unapproved candidate, not shipping artwork.** This is a recovered 2026-10-18 OpenSCAD study from closed PR #1826, plus a new offline exporter. The original owner rejection of the procedural character likeness remains in force. No production presenter, guest gameplay, original sprite, ROM, Windows packaging, or release ledger is changed.

The old flat STL/GLB export fused the whole character. The new optional tool creates **five separately selectable GLB nodes**: tire, rim/hub, fork/frame, pedals and saddle. The saddle mesh is rebased to its mount, while wheel, rim and pedals use the wheel hub as their node pivot. These are editable assembly parts, **not a skeletal rig**, source-timed animation or approved model. The mesh colors are review-only placeholders; original OpenSCAD subcomponent material separation is not recovered in the GLB.

From the repository root with `openscad`, `numpy` and `trimesh` installed:

```sh
python3 tools/art/export_articulated_unicycle.py tools/art/candidates/unicycle_shared_rig.scad /tmp/ur-art4k
python3 -m unittest discover -s tests/unit -p 'test_export_articulated_unicycle.py'
```

The exporter runs OpenSCAD for each part, rejects empty/nonfinite/nonwatertight meshes and emits a SHA-256 receipt with explicitly false likeness, cadence and shipping approval. OpenSCAD and Trimesh are **optional offline authoring dependencies**, never runtime or CI prerequisites.

**Remaining work:** authenticate a high-detail original title/packaging view and adjacent genuine original gameplay poses; measure perspective-tagged landmarks with the existing `measure_unicycle_reference.py`; fit wheel/fork/saddle and original contact/pivots; reconstruct source cadence, per-material geometry, lighting and motion; compare at 32/64px and 4× in 1P/2P; obtain explicit independent owner likeness approval. No ART-02..ART-10 or Windows/USA event credit from this technical export.

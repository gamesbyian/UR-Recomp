#!/usr/bin/env python3
"""Export an unapproved OpenSCAD unicycle blockout as a part-addressable GLB.

Offline authoring only: not a replacement sprite, shipping model or original
animation reconstruction. Requires OpenSCAD and the optional trimesh package.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

PARTS = {
    "tire": ("tire();", (27, 29, 31, 255)),
    "rim_and_hub": ("rim_and_hub();", (173, 190, 204, 255)),
    "fork_and_frame": ("fork_and_frame();", (29, 89, 222, 255)),
    "pedals": ("pedals(18);", (125, 138, 151, 255)),
    "saddle": ("saddle(0);", (27, 29, 34, 255)),
}
END_MARKER = "rig(rig_pose);"
# The original saddle module contains its own local mounting translation.
# Rebase the exported mesh so its GLB node pivots at that mounting point.
SADDLE_MOUNT = (0.04, 0.0, 2.27)


def source_without_entrypoint(source: str) -> str:
    stripped = source.rstrip()
    if not stripped.endswith(END_MARKER) or stripped.count(END_MARKER) != 1:
        raise ValueError("source must end with exactly one canonical rig entrypoint")
    return stripped[:-len(END_MARKER)].rstrip() + "\n"


def component_source(base: str, name: str) -> str:
    if name not in PARTS:
        raise ValueError("unknown component")
    return source_without_entrypoint(base) + "\n" + PARTS[name][0] + "\n"


def part_translation(name: str) -> tuple[float, float, float]:
    if name not in PARTS:
        raise ValueError("unknown component")
    if name == "saddle":
        return (SADDLE_MOUNT[0], SADDLE_MOUNT[1], 1.0 + SADDLE_MOUNT[2])
    return (0.0, 0.0, 1.0)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def export(source: Path, out_dir: Path, *, timeout: int = 90) -> dict:
    import numpy as np
    import trimesh

    openscad = shutil.which("openscad")
    if not openscad:
        raise RuntimeError("OpenSCAD executable is required for offline authoring")
    source_bytes = source.read_bytes()
    base = source_bytes.decode("utf-8")
    source_without_entrypoint(base)
    out_dir.mkdir(parents=True, exist_ok=True)
    scene = trimesh.Scene()
    report = {"schema": "ur-art4k-articulated-blockout/1",
              "source_sha256": sha256_bytes(source_bytes),
              "original_character_likeness_approved": False,
              "shipping_art_approved": False,
              "animation_cadence_source_registered": False,
              "components": []}
    with tempfile.TemporaryDirectory(prefix="ur-art4k-") as tmp:
        work = Path(tmp)
        for name, (_, rgba) in PARTS.items():
            scad = work / f"{name}.scad"
            stl = work / f"{name}.stl"
            scad.write_text(component_source(base, name), encoding="utf-8")
            run = subprocess.run([openscad, "-o", str(stl), str(scad)],
                                 capture_output=True, text=True,
                                 timeout=timeout, check=False)
            if run.returncode != 0 or not stl.is_file():
                raise RuntimeError(f"OpenSCAD failed for {name}: {run.stderr[-1000:]}")
            mesh = trimesh.load_mesh(stl, file_type="stl", process=True)
            if not isinstance(mesh, trimesh.Trimesh) or mesh.is_empty:
                raise ValueError(f"invalid empty mesh for {name}")
            if not np.isfinite(mesh.vertices).all() or not mesh.is_watertight:
                raise ValueError(f"nonfinite/nonwatertight component: {name}")
            if name == "saddle":
                mesh.apply_translation(-np.array(SADDLE_MOUNT))
            mesh.visual.vertex_colors = np.array(rgba, dtype=np.uint8)
            transform = np.eye(4)
            transform[:3, 3] = part_translation(name)
            scene.add_geometry(mesh, node_name=name, geom_name=name,
                               transform=transform)
            report["components"].append({"name": name,
                "triangles": int(len(mesh.faces)),
                "watertight": bool(mesh.is_watertight),
                "pivot_translation": list(part_translation(name)),
                "editable_node": True})
    # A GLB node hierarchy makes tire/rim/cranks/saddle independently selectable.
    # It does NOT reconstruct original game animation or material separation.
    output = out_dir / "unicycle_articulated_blockout.glb"
    output.write_bytes(scene.export(file_type="glb"))
    report["glb_sha256"] = sha256_bytes(output.read_bytes())
    report["glb_size"] = output.stat().st_size
    (out_dir / "articulated_blockout_receipt.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()
    if args.timeout < 1 or args.timeout > 600:
        parser.error("timeout must be 1..600 seconds")
    print(json.dumps(export(args.source, args.out_dir, timeout=args.timeout),
                     indent=2))


if __name__ == "__main__":
    main()

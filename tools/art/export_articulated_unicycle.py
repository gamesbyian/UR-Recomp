#!/usr/bin/env python3
"""Export an unapproved OpenSCAD unicycle blockout as a part-addressable GLB.

Offline authoring only: not a replacement sprite, shipping model or original
animation reconstruction. Requires OpenSCAD and the optional trimesh package.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import uuid
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
# The saddle mounting translation is owned by the actual OpenSCAD source.
# Reject ambiguous/changed structure rather than silently exporting a
# misleading pivot when the model is refitted.
SADDLE_TRANSLATE = re.compile(
    r"module\s+saddle\s*\(\s*lean\s*=\s*0\s*\)\s*\{\s*"
    r"translate\s*\(\s*\[\s*([+-]?\d+(?:\.\d+)?)\s*,\s*"
    r"([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*\]\s*\)\s*"
    r"rotate\s*\(\s*\[\s*0\s*,\s*lean\s*,\s*0\s*\]\s*\)"
)


def saddle_mount_from_source(source: str) -> tuple[float, float, float]:
    matches = SADDLE_TRANSLATE.findall(source)
    if len(matches) != 1:
        raise ValueError("expected one source-owned saddle mount translation")
    return tuple(float(v) for v in matches[0])


def source_without_entrypoint(source: str) -> str:
    stripped = source.rstrip()
    if not stripped.endswith(END_MARKER) or stripped.count(END_MARKER) != 1:
        raise ValueError("source must end with exactly one canonical rig entrypoint")
    return stripped[:-len(END_MARKER)].rstrip() + "\n"


def component_source(base: str, name: str) -> str:
    if name not in PARTS:
        raise ValueError("unknown component")
    return source_without_entrypoint(base) + "\n" + PARTS[name][0] + "\n"


def part_translation(name: str, saddle_mount: tuple[float, float, float]) -> tuple[float, float, float]:
    if name not in PARTS:
        raise ValueError("unknown component")
    if name == "saddle":
        return (saddle_mount[0], saddle_mount[1], 1.0 + saddle_mount[2])
    return (0.0, 0.0, 1.0)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json_atomic(path: Path, payload: dict) -> None:
    """Replace a single status/pointer document without exposing partial JSON."""
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def export(source: Path, out_dir: Path, *, timeout: int = 90) -> dict:
    source_bytes = source.read_bytes()
    base = source_bytes.decode("utf-8")
    source_digest = sha256_bytes(source_bytes)
    out_dir.mkdir(parents=True, exist_ok=True)
    attempt_id = uuid.uuid4().hex
    last_attempt = out_dir / "articulated_blockout_last_attempt.json"
    current = out_dir / "articulated_blockout_current.json"
    attempts_dir = out_dir / "attempts"
    # An interrupted run remains visibly 'running', never masquerades as a
    # completed export. A failed rerun leaves the prior success intact.
    state = {"schema": "ur-art4k-export-attempt/1", "attempt_id": attempt_id,
             "source_sha256": source_digest, "status": "running",
             "current_output_usable": False}
    _write_json_atomic(last_attempt, state)
    try:
        source_without_entrypoint(base)
        saddle_mount = saddle_mount_from_source(base)
        openscad = shutil.which("openscad")
        if not openscad:
            raise RuntimeError("OpenSCAD executable is required for offline authoring")
        import numpy as np
        import trimesh
        scene = trimesh.Scene()
        report = {"schema": "ur-art4k-articulated-blockout/1",
                  "attempt_id": attempt_id, "source_sha256": source_digest,
                  "source_saddle_mount": list(saddle_mount),
                  "original_character_likeness_approved": False,
                  "shipping_art_approved": False,
                  "animation_cadence_source_registered": False,
                  "components": []}
        # Build and validate privately. Only complete, immutable attempts are
        # exposed via the success pointer; never publish half of a GLB/receipt.
        with tempfile.TemporaryDirectory(prefix=".ur-art4k-staging-", dir=out_dir) as tmp:
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
                    mesh.apply_translation(-np.array(saddle_mount))
                mesh.visual.vertex_colors = np.array(rgba, dtype=np.uint8)
                transform = np.eye(4)
                transform[:3, 3] = part_translation(name, saddle_mount)
                scene.add_geometry(mesh, node_name=name, geom_name=name,
                                   transform=transform)
                report["components"].append({"name": name,
                    "triangles": int(len(mesh.faces)),
                    "watertight": bool(mesh.is_watertight),
                    "pivot_translation": list(part_translation(name, saddle_mount)),
                    "editable_node": True})
            stage = work / "published"
            stage.mkdir()
            glb = stage / "unicycle_articulated_blockout.glb"
            glb.write_bytes(scene.export(file_type="glb"))
            report["glb_sha256"] = sha256_bytes(glb.read_bytes())
            report["glb_size"] = glb.stat().st_size
            receipt = stage / "articulated_blockout_receipt.json"
            receipt.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
            receipt_sha = sha256_bytes(receipt.read_bytes())
            attempts_dir.mkdir(exist_ok=True)
            destination = attempts_dir / attempt_id
            # Same-filesystem rename publishes a complete immutable pair.
            os.rename(stage, destination)
        pointer = {"schema": "ur-art4k-export-current/1",
                   "attempt_id": attempt_id, "source_sha256": source_digest,
                   "glb_path": f"attempts/{attempt_id}/unicycle_articulated_blockout.glb",
                   "receipt_path": f"attempts/{attempt_id}/articulated_blockout_receipt.json",
                   "glb_sha256": report["glb_sha256"],
                   "receipt_sha256": receipt_sha}
        _write_json_atomic(current, pointer)
        _write_json_atomic(last_attempt, {**state, "status": "succeeded",
                                         "current_output_usable": True,
                                         "glb_sha256": report["glb_sha256"]})
        return report
    except Exception as exc:
        # The last successful pointer and immutable outputs are deliberately
        # retained. Callers must inspect last_attempt before treating them as
        # the result of *this* invocation.
        _write_json_atomic(last_attempt, {**state, "status": "failed",
                                         "error_type": type(exc).__name__,
                                         "error": str(exc)[-1000:]})
        raise


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

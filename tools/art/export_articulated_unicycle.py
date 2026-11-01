#!/usr/bin/env python3
"""Export an unapproved OpenSCAD unicycle blockout as a part-addressable GLB.

Offline authoring only: not a replacement sprite, shipping model or original
animation reconstruction. Requires OpenSCAD and the optional trimesh package.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import os
import re
import uuid
import shutil
import subprocess
import tempfile
from pathlib import Path

try:
    from tools.art.glb_roundtrip_guard import validate_glb_roundtrip, geometry_signature, normal_signature, bind_source_normals
except ModuleNotFoundError:
    from glb_roundtrip_guard import validate_glb_roundtrip, geometry_signature, normal_signature, bind_source_normals

# Support both repo-root unit imports and direct offline script execution.
try:
    from tools.art.scad_materials import materials_for_part, material_pass_source, uncolored_probe_source, UNCOLORED_PROBE_MIN
except ModuleNotFoundError:
    from scad_materials import materials_for_part, material_pass_source, uncolored_probe_source, UNCOLORED_PROBE_MIN

try:
    from tools.art.continuous_pose_recipe import continuous_pose_recipe
except ModuleNotFoundError:
    from continuous_pose_recipe import continuous_pose_recipe

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
POSES = ("upright", "pedal", "wheelie", "stunt", "bank")
_NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)"
_VECTOR = re.compile(r"(translate|rotate)\s*\(\s*\[\s*(" + _NUMBER +
                     r")\s*,\s*(" + _NUMBER + r")\s*,\s*(" + _NUMBER +
                     r")\s*\]\s*\)")
_RIG_BRANCH = re.compile(r'(?:^|\s)(?:else\s+)?if\s*\(\s*p\s*==\s*"([a-z_]+)"\s*\)', re.M)
_RIG_CALL = re.compile(r"shared_rig\s*\(\s*pedal\s*=\s*(" + _NUMBER +
                       r")\s*,\s*seat_lean\s*=\s*(" + _NUMBER + r")\s*\)\s*;\s*\Z")


def _matmul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(4))
                       for j in range(4)) for i in range(4))


def _identity():
    return ((1., 0., 0., 0.), (0., 1., 0., 0.),
            (0., 0., 1., 0.), (0., 0., 0., 1.))


def _transform(kind, xyz):
    x, y, z = xyz
    if kind == "translate":
        m = [list(row) for row in _identity()]
        for i, value in enumerate(xyz):
            m[i][3] = value
        return tuple(tuple(row) for row in m)
    # OpenSCAD's vector Euler form applies X, then Y, then Z rotations.
    def axis(which, degrees):
        c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
        if which == "x":
            return ((1,0,0,0),(0,c,-s,0),(0,s,c,0),(0,0,0,1))
        if which == "y":
            return ((c,0,s,0),(0,1,0,0),(-s,0,c,0),(0,0,0,1))
        return ((c,-s,0,0),(s,c,0,0),(0,0,1,0),(0,0,0,1))
    return _matmul(_matmul(axis("z", z), axis("y", y)), axis("x", x))


def pose_recipe(source: str, name: str):
    """Read named blockout pose from SCAD, fail closed on changed syntax.

    These are *source-owned blockout* transforms, not registered 1994 poses.
    Every numeric control and outer transform is extracted, not duplicated.
    """
    if name not in POSES:
        raise ValueError("unknown source blockout pose")
    matches = list(_RIG_BRANCH.finditer(source))
    found = [i for i, match in enumerate(matches) if match.group(1) == name]
    if len(found) != 1:
        raise ValueError("expected one source-owned pose branch")
    i = found[0]
    start = matches[i].end()
    end = matches[i+1].start() if i + 1 < len(matches) else source.find("}", start)
    if end < 0:
        raise ValueError("unterminated source-owned pose branch")
    body = source[start:end].strip()
    call = _RIG_CALL.search(body)
    if call is None:
        raise ValueError("source-owned pose must end in one shared_rig call")
    phase, lean = map(float, call.groups())
    validate_pose_controls(phase, lean)
    prefix = body[:call.start()]
    matrix = _identity()
    pos = 0
    for op in _VECTOR.finditer(prefix):
        if prefix[pos:op.start()].strip():
            raise ValueError("unsupported source-owned pose transform")
        matrix = _matmul(matrix, _transform(op.group(1), tuple(map(float, op.groups()[1:]))))
        pos = op.end()
    if prefix[pos:].strip():
        raise ValueError("unsupported source-owned pose transform")
    return phase, lean, matrix


SADDLE_TRANSLATE = re.compile(
    r"module\s+saddle\s*\(\s*lean\s*=\s*0\s*\)\s*\{\s*"
    r"translate\s*\(\s*\[\s*([+-]?\d+(?:\.\d+)?)\s*,\s*"
    r"([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*\]\s*\)\s*"
    r"rotate\s*\(\s*\[\s*0\s*,\s*lean\s*,\s*0\s*\]\s*\)"
)


# Count all saddle module declarations, including those with changed bodies.
# The mount regex alone would silently accept a second, differently formed
# definition and could publish a pivot for the wrong OpenSCAD module.
SADDLE_DECLARATION = re.compile(r"\bmodule\s+saddle\s*\(")
SCAD_COMMENTS = re.compile(r"/\*.*?\*/|//[^\n]*", re.S)
MODULE_DECLARATION = re.compile(r"\bmodule\s+([A-Za-z_]\w*)\s*\(")


def assert_unique_module_declarations(source: str) -> None:
    """Reject silently overridden OpenSCAD modules before part-only export.

    OpenSCAD accepts duplicate module definitions and renders the later one.
    A refit could therefore replace a tire/frame/helper without invalidating
    the saddle mount or the five-component GLB shape contract.
    """
    names = MODULE_DECLARATION.findall(SCAD_COMMENTS.sub("", source))
    duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
    if "saddle" in duplicates:
        raise ValueError("expected one source-owned saddle module declaration")
    if duplicates:
        raise ValueError("duplicate OpenSCAD module declaration: " + ", ".join(duplicates))




def saddle_mount_from_source(source: str) -> tuple[float, float, float]:
    code = SCAD_COMMENTS.sub("", source)
    if len(SADDLE_DECLARATION.findall(code)) != 1:
        raise ValueError("expected one source-owned saddle module declaration")
    matches = SADDLE_TRANSLATE.findall(code)
    if len(matches) != 1:
        raise ValueError("expected one source-owned saddle mount translation")
    return tuple(float(v) for v in matches[0])


def assert_no_extra_top_level_geometry(source: str) -> None:
    """Reject extra top-level geometry in a part-only OpenSCAD export.

    A second top-level module call would otherwise be rendered into *every*
    exported STL, even after the canonical rig(rig_pose) call is stripped.
    This conservative scanner permits module declarations, functions,
    assignments and plain asserts; unsupported source grammar fails closed.
    """
    def plain_assert(statement: str) -> bool:
        m = re.match(r"assert\s*\(", statement)
        if m is None:
            return False
        parens = 1
        quote = False
        escape = False
        for i in range(m.end(), len(statement)):
            c = statement[i]
            if quote:
                if escape:
                    escape = False
                elif c == '\\':
                    escape = True
                elif c == '"':
                    quote = False
                continue
            if c == '"':
                quote = True
            elif c == "(":
                parens += 1
            elif c == ")":
                parens -= 1
                if parens == 0:
                    return not statement[i+1:].strip()
        return False

    code = SCAD_COMMENTS.sub("", source)
    depth = 0
    start = 0
    in_string = False
    escaped = False
    for i, char in enumerate(code):
        if in_string:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            if depth == 0:
                header = code[start:i].strip()
                if not re.fullmatch(r"module\s+[A-Za-z_]\w*\s*\(.*\)", header, re.S):
                    raise ValueError("unexpected top-level geometry block")
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                raise ValueError("unbalanced OpenSCAD braces")
            if depth == 0:
                start = i + 1
        elif char == ";" and depth == 0:
            statement = code[start:i].strip()
            if statement and not (
                    re.match(r"^[$A-Za-z_]\w*\s*=", statement)
                    or re.match(r"^function\s+[A-Za-z_]\w*\s*\(", statement)
                    or plain_assert(statement)):
                raise ValueError("unexpected top-level geometry call")
            start = i + 1
    if depth or in_string or code[start:].strip():
        raise ValueError("unterminated top-level OpenSCAD statement")


def source_without_entrypoint(source: str) -> str:
    stripped = source.rstrip()
    if not stripped.endswith(END_MARKER) or stripped.count(END_MARKER) != 1:
        raise ValueError("source must end with exactly one canonical rig entrypoint")
    body = stripped[:-len(END_MARKER)].rstrip() + "\n"
    assert_unique_module_declarations(body)
    assert_no_extra_top_level_geometry(body)
    return body


def validate_pose_controls(pedal_phase: float, saddle_lean: float) -> None:
    """Limit experimental pose probes to the existing blockout's local axes."""
    if not math.isfinite(pedal_phase) or not -360 <= pedal_phase <= 360:
        raise ValueError("pedal phase must be finite and within -360..360 degrees")
    if not math.isfinite(saddle_lean) or not -30 <= saddle_lean <= 30:
        raise ValueError("saddle lean must be finite and within -30..30 degrees")


def component_source(base: str, name: str, *, pedal_phase: float = 18,
                     saddle_lean: float = 0) -> str:
    if name not in PARTS:
        raise ValueError("unknown component")
    validate_pose_controls(pedal_phase, saddle_lean)
    call = PARTS[name][0]
    if name == "pedals":
        call = f"pedals({pedal_phase:g});"
    elif name == "saddle":
        call = f"saddle({saddle_lean:g});"
    return source_without_entrypoint(base) + "\n" + call + "\n"


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


def export(source: Path, out_dir: Path, *, timeout: int = 90,
           pedal_phase: float | None = None, saddle_lean: float | None = None,
           rig_pose: str = "custom", rig_time: float | None = None) -> dict:
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
        continuous_meta = None
        if rig_pose in ("ride", "stunt_cycle"):
            if pedal_phase is not None or saddle_lean is not None or rig_time is None:
                raise ValueError("continuous source pose requires --rig-time and no manual overrides")
            pedal_phase, saddle_lean, pose_matrix, continuous_meta = continuous_pose_recipe(
                base, rig_pose, rig_time)
            validate_pose_controls(pedal_phase, saddle_lean)
        elif rig_pose == "custom":
            if rig_time is not None:
                raise ValueError("custom pose cannot accept --rig-time")
            pedal_phase = 18.0 if pedal_phase is None else pedal_phase
            saddle_lean = 0.0 if saddle_lean is None else saddle_lean
            validate_pose_controls(pedal_phase, saddle_lean)
            pose_matrix = _identity()
        else:
            if pedal_phase is not None or saddle_lean is not None or rig_time is not None:
                raise ValueError("named source pose cannot override its authored controls")
            pedal_phase, saddle_lean, pose_matrix = pose_recipe(base, rig_pose)
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
                  "rig_pose": rig_pose,
                  "source_pose_transform": [list(row) for row in pose_matrix],
                  "pose_controls": {"pedal_phase_degrees": pedal_phase,
                                    "saddle_lean_degrees": saddle_lean},
                  "continuous_pose": continuous_meta,
                  "pose_source_registered_to_original_game": False,
                  "original_character_likeness_approved": False,
                  "shipping_art_approved": False,
                  "animation_cadence_source_registered": False,
                  "components": []}
        # Build and validate privately. Only complete, immutable attempts are
        # exposed via the success pointer; never publish half of a GLB/receipt.
        with tempfile.TemporaryDirectory(prefix=".ur-art4k-staging-", dir=out_dir) as tmp:
            work = Path(tmp)
            for name in PARTS:
                # Keep the same five independently editable part pivots. The
                # authored colors now survive as child material meshes rather
                # than being flattened into one STL color per entire part.
                transform = np.eye(4)
                transform[:3, 3] = part_translation(name, saddle_mount)
                node_transform = np.array(pose_matrix) @ transform
                scene.graph.update(frame_to=name, frame_from=scene.graph.base_frame,
                                   matrix=node_transform)
                part_source = component_source(base, name, pedal_phase=pedal_phase,
                                               saddle_lean=saddle_lean)
                materials = materials_for_part(base, name)
                # A source refit can add geometry outside color(). That geometry
                # survives EVERY material pass and silently duplicates in GLB.
                # Render the uncolored remainder with one remote sentinel cube;
                # only that exact cube may survive. Fail before publishing.
                probe_scad = work / f"{name}-uncolored-probe.scad"
                probe_stl = work / f"{name}-uncolored-probe.stl"
                probe_scad.write_text(uncolored_probe_source(part_source), encoding="utf-8")
                probe_run = subprocess.run([openscad, "-o", str(probe_stl), str(probe_scad)],
                                           capture_output=True, text=True,
                                           timeout=timeout, check=False)
                if probe_run.returncode != 0 or not probe_stl.is_file():
                    raise RuntimeError(f"OpenSCAD uncolored probe failed for {name}: "
                                       + probe_run.stderr[-1000:])
                probe_mesh = trimesh.load_mesh(probe_stl, file_type="stl", process=True)
                expected_bounds = np.array([[UNCOLORED_PROBE_MIN] * 3,
                                            [UNCOLORED_PROBE_MIN + 1] * 3])
                if (not isinstance(probe_mesh, trimesh.Trimesh) or probe_mesh.is_empty
                        or not np.isfinite(probe_mesh.vertices).all()
                        or not np.allclose(probe_mesh.bounds, expected_bounds,
                                           rtol=0, atol=1e-4)
                        or not probe_mesh.is_watertight
                        or abs(probe_mesh.volume - 1.0) > 1e-4
                        or len(probe_mesh.faces) != 12):
                    raise ValueError(f"uncolored geometry leaks into material passes: {name}")
                material_rows = []
                for index, rgba in enumerate(materials):
                    scad = work / f"{name}-{index}.scad"
                    stl = work / f"{name}-{index}.stl"
                    scad.write_text(material_pass_source(part_source, rgba),
                                    encoding="utf-8")
                    run = subprocess.run([openscad, "-o", str(stl), str(scad)],
                                         capture_output=True, text=True,
                                         timeout=timeout, check=False)
                    if run.returncode != 0 or not stl.is_file():
                        raise RuntimeError(
                            f"OpenSCAD failed for {name} material {index}: {run.stderr[-1000:]}")
                    mesh = trimesh.load_mesh(stl, file_type="stl", process=True)
                    if not isinstance(mesh, trimesh.Trimesh) or mesh.is_empty:
                        raise ValueError(f"invalid empty mesh for {name} material {index}")
                    if not np.isfinite(mesh.vertices).all() or not mesh.is_watertight:
                        raise ValueError(f"nonfinite/nonwatertight: {name} material {index}")
                    if name == "saddle":
                        mesh.apply_translation(-np.array(saddle_mount))
                    mesh.visual.vertex_colors = np.array(rgba, dtype=np.uint8)
                    child = f"{name}__material_{index}"
                    bind_source_normals(mesh)
                    scene.add_geometry(mesh, node_name=child, geom_name=child,
                                       parent_node_name=name)
                    material_rows.append({"node": child, "rgba": list(rgba),
                                          "geometry_sha256": geometry_signature(mesh),
                                          "normals_sha256": normal_signature(mesh, source=True),
                                          "triangles": int(len(mesh.faces)),
                                          "watertight": bool(mesh.is_watertight)})
                report["components"].append({"name": name,
                    "triangles": sum(row["triangles"] for row in material_rows),
                    "watertight": all(row["watertight"] for row in material_rows),
                    "pivot_translation": list(part_translation(name, saddle_mount)),
                    "world_pivot_translation": [float(v) for v in node_transform[:3, 3]],
                    "editable_node": True, "material_count": len(material_rows),
                    "materials": material_rows})
            stage = work / "published"
            stage.mkdir()
            glb = stage / "unicycle_articulated_blockout.glb"
            glb.write_bytes(scene.export(file_type="glb"))
            report["glb_roundtrip"] = validate_glb_roundtrip(glb, report)
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
                   "rig_pose": rig_pose,
                   "pose_controls": report["pose_controls"],
                   "continuous_pose": continuous_meta,
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
    parser.add_argument("--rig-pose", choices=("custom",) + POSES + ("ride", "stunt_cycle"), default="custom",
                        help="source-owned BLOCKOUT pose, never original-game cadence")
    parser.add_argument("--rig-time", type=float, default=None,
                        help="authored continuous blockout sample 0..1; not 1994 frame cadence")
    parser.add_argument("--pedal-phase", type=float, default=None,
                        help="blockout crank phase in degrees (-360..360), not original cadence")
    parser.add_argument("--saddle-lean", type=float, default=None,
                        help="blockout saddle pitch in degrees (-30..30), not original motion")
    args = parser.parse_args()
    if args.timeout < 1 or args.timeout > 600:
        parser.error("timeout must be 1..600 seconds")
    print(json.dumps(export(args.source, args.out_dir, timeout=args.timeout,
                            pedal_phase=args.pedal_phase, saddle_lean=args.saddle_lean,
                            rig_pose=args.rig_pose, rig_time=args.rig_time),
                     indent=2))


if __name__ == "__main__":
    main()

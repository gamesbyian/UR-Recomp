#!/usr/bin/env python3
"""Offline fixed-camera 4x silhouette projection of an ART-4K part-addressable GLB.

Requires optional numpy/trimesh/Pillow, not installed by default product CI.
Projects GLB world transforms, no auto-fit, no host/gameplay code and no
art-approval verdict. The view is a declared camera hypothesis, not recovered
1994 3D geometry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import uuid

try:
    import numpy as np
    import trimesh
    from PIL import Image
except ImportError:
    np = trimesh = Image = None

CAMERA_SCHEMA = "UR-RACER-FIXED-ORTHOGRAPHIC-CAMERA/1"
PARTS = ("tire", "rim_and_hub", "fork_and_frame", "pedals", "saddle")


def _require_optional():
    if np is None or trimesh is None or Image is None:
        raise RuntimeError("offline projection requires numpy, trimesh and Pillow")


def camera_config(camera: dict):
    _require_optional()
    if camera.get("schema") != CAMERA_SCHEMA or camera.get("source_pixel_aspect") != "7:6":
        raise ValueError("camera schema or 7:6 source pixel-aspect mismatch")
    for key in ("right_world", "up_world", "origin_world"):
        v = camera.get(key)
        if (not isinstance(v, list) or len(v) != 3 or
                not all(type(n) in (float, int) and math.isfinite(n) for n in v)):
            raise ValueError("camera requires finite basis " + key)
    right = np.asarray(camera["right_world"], dtype=float)
    up = np.asarray(camera["up_world"], dtype=float)
    if (abs(np.linalg.norm(right)-1) > 1e-5 or
            abs(np.linalg.norm(up)-1) > 1e-5 or
            abs(float(right @ up)) > 1e-5):
        raise ValueError("camera right/up must be orthonormal")
    scale = camera.get("logical_pixels_per_model_unit_vertical")
    anchor = camera.get("source_anchor_x2_y2")
    if type(scale) not in (float, int) or not math.isfinite(scale) or not 0 < scale <= 100:
        raise ValueError("invalid fixed camera world scale")
    if (not isinstance(anchor, list) or len(anchor) != 2 or
            not all(type(n) is int and -256 <= n <= 256 for n in anchor)):
        raise ValueError("invalid source alpha anchor x2/y2")
    status = camera.get("camera_calibration_status")
    if status not in ("provisional", "source-calibrated"):
        raise ValueError("explicit provisional/source-calibrated status required")
    # A hexadecimal string alone cannot establish source calibration.
    # Enable this status only when an actual calibration receipt validator
    # is implemented, not when a caller can simply invent a digest.
    if status == "source-calibrated":
        raise ValueError("source-calibrated camera requires implemented evidence validator")
    return right, up, np.asarray(camera["origin_world"], dtype=float), float(scale), anchor


def model_mesh(path: Path, expected_sha256: str):
    _require_optional()
    raw = path.read_bytes()
    measured = hashlib.sha256(raw).hexdigest()
    if expected_sha256 != measured:
        raise ValueError("GLB content SHA256 mismatch")
    if raw[:4] != b"glTF":
        raise ValueError("candidate model must be a GLB")
    # The exact offline authoring runner pins Trimesh 4.5.3, which predates
    # the modern convenience load_scene() and Scene.to_geometry() methods.
    # Preserve world-transform baking on both old and new APIs, rather than
    # silently changing the package pin or flattening GLB parent transforms.
    scene = (trimesh.load_scene(path, file_type="glb", process=False)
             if callable(getattr(trimesh, "load_scene", None))
             else trimesh.load(path, file_type="glb", force="scene", process=False))
    if not isinstance(scene, trimesh.Scene):
        raise ValueError("GLB loader did not preserve articulated scene")
    if not set(PARTS).issubset(set(scene.graph.nodes)):
        raise ValueError("GLB lacks five required articulated parent nodes")
    mesh = (scene.to_geometry() if callable(getattr(scene, "to_geometry", None))
            else scene.dump(concatenate=True))  # Bake all world transforms.
    vertices = np.asarray(mesh.vertices)
    faces = np.asarray(mesh.faces)
    if (len(vertices) == 0 or len(faces) == 0 or
            not np.isfinite(vertices).all() or
            np.min(faces) < 0 or np.max(faces) >= len(vertices)):
        raise ValueError("GLB has empty, invalid or nonfinite geometry")
    return vertices, faces, measured, len(scene.graph.nodes)


def render_mask(vertices, faces, camera):
    right, up, origin, scale, anchor = camera_config(camera)
    points = np.asarray(vertices, dtype=float) - origin
    if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
        raise ValueError("nonfinite mesh vertices")
    # Logical source-pixel index centres map to 4*x+2, 4*y+2.
    # The SNES 7:6 physical pixel aspect means X has 6/7 logical
    # pixels per equivalent physical Y distance. No source pose is moved.
    projected = np.column_stack((
        (points @ right) * (scale * 4 * 6 / 7) + 2*anchor[0] + 2,
        -(points @ up) * (scale * 4) + 2*anchor[1] + 2,
    ))
    # Reject a camera/view that silently cuts off model geometry. A clipped
    # render can score artificially well against cropped source art.
    if (np.any(projected < 0) or np.any(projected > 255)):
        raise ValueError("fixed-camera model geometry clips the 256x256 canvas")
    alpha = np.zeros((256, 256), dtype=np.uint8)
    for face in np.asarray(faces):
        a, b, c = projected[face]
        if not np.isfinite([*a, *b, *c]).all():
            raise ValueError("nonfinite projected mesh triangle")
        x0 = max(0, int(math.floor(min(a[0], b[0], c[0]))))
        x1 = min(255, int(math.ceil(max(a[0], b[0], c[0]))))
        y0 = max(0, int(math.floor(min(a[1], b[1], c[1]))))
        y1 = min(255, int(math.ceil(max(a[1], b[1], c[1]))))
        if x0 > x1 or y0 > y1:
            continue
        det = (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
        if abs(det) < 1e-11:
            continue
        yy, xx = np.mgrid[y0:y1+1, x0:x1+1]
        dx, dy = xx-a[0], yy-a[1]
        u = (dx*(c[1]-a[1]) - dy*(c[0]-a[0]))/det
        v = (dy*(b[0]-a[0]) - dx*(b[1]-a[1]))/det
        inside = (u >= -1e-9) & (v >= -1e-9) & (u+v <= 1+1e-9)
        alpha[y0:y1+1, x0:x1+1] |= inside.astype(np.uint8)
    if not alpha.any():
        raise ValueError("GLB completely outside declared fixed camera")
    return alpha


def render_to_png(mask, dest: Path) -> str:
    _require_optional()
    rgba = np.zeros((256, 256, 4), dtype=np.uint8)
    rgba[:, :, 3] = mask * 255
    # Complete the file before replacing any earlier path. A failed
    # rasterization cannot publish a partially completed PNG.
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=".racer-", suffix=".png", dir=dest.parent, delete=False
    ) as stream:
        staged = Path(stream.name)
    try:
        Image.fromarray(rgba, "RGBA").save(staged)
        digest = hashlib.sha256(staged.read_bytes()).hexdigest()
        os.replace(staged, dest)
        return digest
    finally:
        staged.unlink(missing_ok=True)


def project(glb: Path, glb_sha: str, camera_path: Path, output: Path) -> dict:
    source_bytes = camera_path.read_bytes()
    camera = json.loads(source_bytes)
    camera_config(camera)
    verts, faces, model_sha, nodes = model_mesh(glb, glb_sha)
    mask = render_mask(verts, faces, camera)
    png_sha = render_to_png(mask, output)
    return {
        "schema": "UR-RACER-FIXED-GLB-PROJECTION/1",
        "source_model_glb_sha256": model_sha,
        "camera_manifest_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "camera_calibration_status": camera["camera_calibration_status"],
        "candidate_png_sha256": png_sha,
        "candidate_density": 4,
        "4x_opaque_alpha_pixels": int(mask.sum()),
        "glb_node_count": nodes,
        "source_camera_auto_fit": False,
        "render_contains_only_binary_silhouette": True,
        "source_1994_model_recovered": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--glb", type=Path, required=True)
    ap.add_argument("--glb-sha256", required=True)
    ap.add_argument("--camera", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--receipt", type=Path, required=True)
    args = ap.parse_args()
    if args.receipt.resolve() == args.out.resolve():
        raise ValueError("receipt cannot overwrite image")
    result = project(args.glb, args.glb_sha256, args.camera, args.out)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    # The receipt is the specific invocation's result and source digest, not
    # an assertion that some pre-existing output was generated this time.
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=args.receipt.parent,
        prefix=".racer-receipt-", delete=False
    ) as stream:
        staged = Path(stream.name)
        stream.write(text)
    try:
        os.replace(staged, args.receipt)
    finally:
        staged.unlink(missing_ok=True)
    print(text, end="")


if __name__ == "__main__":
    main()

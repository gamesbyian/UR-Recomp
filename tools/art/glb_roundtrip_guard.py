"""Fail-closed GLB round-trip integrity check for the unapproved ART-4K blockout.

Checks serialized scene structure, source-derived part transforms and material
geometry before the exporter publishes its immutable success pointer. This
is mechanical integrity only, never original-game likeness/art approval.
"""
from __future__ import annotations

from pathlib import Path
import hashlib


def geometry_signature(mesh) -> str:
    """Hash oriented local triangles at GLB float32 precision.

    Canonicalize cyclic vertex rotations and face order while preserving
    winding. A reversed triangle has the opposite normal and must never pass
    the material digest even when its coordinates and watertightness agree.
    """
    import numpy as np

    triangles = np.asarray(mesh.triangles, dtype="<f4").copy()
    if (triangles.ndim != 3 or triangles.shape[1:] != (3, 3)
            or not len(triangles) or not np.isfinite(triangles).all()):
        raise ValueError("invalid source material geometry")
    triangles[triangles == 0] = 0  # normalize IEEE negative zero
    vertex_dtype = np.dtype([("x", "<f4"), ("y", "<f4"), ("z", "<f4")])
    vertices = np.ascontiguousarray(triangles).view(vertex_dtype).reshape(-1, 3)
    # The three cyclic rotations preserve orientation. Swapping any two
    # vertices reverses it and therefore must produce a different digest.
    rotations = np.stack((vertices, np.roll(vertices, -1, axis=1),
                          np.roll(vertices, -2, axis=1)), axis=1)
    face_options = np.ascontiguousarray(rotations).view(np.dtype("V36")).reshape(-1, 3)
    faces = np.sort(face_options, axis=1)[:, 0].copy()
    faces.sort()
    return hashlib.sha256(faces.tobytes()).hexdigest()



def normal_signature(mesh, *, source: bool = False) -> str:
    """Bind GLB corner normals to source-derived float32 geometry shading.

    The current OpenSCAD/STL blockout has no separately authored normals.
    Recompute its expected vertex normals from float32 positions, matching
    the precision serialized by GLB. At validation read the actual imported
    normal attribute, so an inverted/shading-altered GLB cannot pass merely
    because its oriented triangles are unchanged. Canonicalize face order
    and cyclic vertex rotations, not reversed winding.
    """
    import numpy as np
    if source:
        import trimesh
        normalized = trimesh.Trimesh(
            vertices=np.asarray(mesh.vertices, dtype="<f4"),
            faces=mesh.faces, process=False)
        vertex_normals = normalized.vertex_normals
    else:
        vertex_normals = mesh.vertex_normals
    triangles = np.asarray(mesh.triangles, dtype="<f4").copy()
    normals = np.asarray(vertex_normals[mesh.faces], dtype="<f4").copy()
    if (triangles.ndim != 3 or triangles.shape[1:] != (3, 3)
            or not len(triangles) or normals.shape != triangles.shape
            or not np.isfinite(triangles).all()
            or not np.isfinite(normals).all()):
        raise ValueError("invalid material normals")
    lengths = np.linalg.norm(normals.astype(np.float64), axis=2)
    if not np.allclose(lengths, 1, rtol=0, atol=1e-4):
        raise ValueError("invalid material normal magnitude")
    corners = np.concatenate((triangles, normals), axis=2)
    corners[corners == 0] = 0
    vertices = np.ascontiguousarray(corners).view(np.dtype("V24")).reshape(-1, 3)
    rotations = np.stack((vertices, np.roll(vertices, -1, axis=1),
                          np.roll(vertices, -2, axis=1)), axis=1)
    face_options = np.ascontiguousarray(rotations).view(np.dtype("V72")).reshape(-1, 3)
    faces = np.sort(face_options, axis=1)[:, 0].copy()
    faces.sort()
    return hashlib.sha256(faces.tobytes()).hexdigest()



def bind_source_normals(mesh) -> None:
    """Emit the float32-derived normals that the source receipt signs."""
    import numpy as np
    import trimesh
    normalized = trimesh.Trimesh(
        vertices=np.asarray(mesh.vertices, dtype="<f4"),
        faces=mesh.faces, process=False)
    mesh.vertex_normals = normalized.vertex_normals


def require_explicit_glb_normals(path: Path, expected_nodes) -> None:
    """Reject absent or unbacked glTF NORMAL data before Trimesh synthesizes it."""
    import json
    import struct

    with path.open("rb") as handle:
        header = handle.read(20)
        if len(header) != 20:
            raise ValueError("GLB normal accessor header missing")
        magic, version, total, json_size, chunk_type = struct.unpack("<4sIIII", header)
        if (magic != b"glTF" or version != 2 or total != path.stat().st_size
                or chunk_type != 0x4E4F534A or json_size <= 0
                or json_size > total - 20):
            raise ValueError("GLB normal accessor header invalid")
        payload = handle.read(json_size)
        if len(payload) != json_size:
            raise ValueError("GLB normal accessor JSON truncated")
        bin_header = handle.read(8)
        if len(bin_header) != 8:
            raise ValueError("GLB normal accessor BIN chunk missing")
        bin_length, bin_type = struct.unpack("<II", bin_header)
        if bin_type != 0x004E4942 or 20 + json_size + 8 + bin_length > total:
            raise ValueError("GLB normal accessor BIN chunk invalid")
    try:
        gltf = json.loads(payload)
        meshes = gltf["meshes"]
        accessors = gltf["accessors"]
        views = gltf["bufferViews"]
        buffers = gltf["buffers"]
        if (not isinstance(meshes, list) or not isinstance(accessors, list)
                or not isinstance(views, list) or not isinstance(buffers, list)
                or len(buffers) != 1):
            raise ValueError("invalid mesh/accessor/buffer arrays")
        # This exporter emits dense accessors only. Sparse overrides change
        # the glTF-defined vertex data, but Trimesh currently reads the base
        # buffer values and can silently accept a source-different GLB.
        # Reject every sparse accessor before trusting imported signatures.
        if any(not isinstance(accessor, dict) or "sparse" in accessor
               for accessor in accessors):
            raise ValueError("GLB sparse accessor unsupported")
        buffer_bytes = buffers[0]["byteLength"]
        if type(buffer_bytes) is not int or buffer_bytes <= 0 or buffer_bytes > bin_length:
            raise ValueError("GLB normal buffer exceeds BIN chunk")
        found = set()
        for mesh in meshes:
            name = mesh["name"]
            primitives = mesh["primitives"]
            if (not isinstance(name, str) or name in found
                    or not isinstance(primitives, list) or len(primitives) != 1):
                raise ValueError("invalid mesh identity/primitives")
            found.add(name)
            attributes = primitives[0]["attributes"]
            normal_index, position_index = attributes["NORMAL"], attributes["POSITION"]
            if (type(normal_index) is not int or type(position_index) is not int
                    or normal_index < 0 or normal_index >= len(accessors)
                    or position_index < 0 or position_index >= len(accessors)):
                raise ValueError("invalid NORMAL/POSITION indices")
            normal, position = accessors[normal_index], accessors[position_index]
            if (normal.get("type") != "VEC3" or normal.get("componentType") != 5126
                    or type(normal.get("count")) is not int
                    or normal["count"] <= 0 or normal["count"] != position.get("count")):
                raise ValueError("invalid NORMAL accessor format/count")
            # An accessor can declare VEC3/FLOAT without backing storage.
            # Downstream loaders may supply default/synthetic normals; require
            # the actual source-signed float32 bytes inside this GLB BIN.
            view_index = normal.get("bufferView")
            if type(view_index) is not int or not 0 <= view_index < len(views):
                raise ValueError("NORMAL accessor has no valid bufferView")
            view = views[view_index]
            if not isinstance(view, dict) or view.get("buffer") != 0:
                raise ValueError("NORMAL accessor uses invalid BIN buffer")
            offset = view.get("byteOffset", 0)
            length = view.get("byteLength")
            accessor_offset = normal.get("byteOffset", 0)
            stride = view.get("byteStride", 12)
            if (any(type(v) is not int for v in (offset, length, accessor_offset, stride))
                    or offset < 0 or length <= 0 or accessor_offset < 0
                    or stride < 12 or stride % 4 != 0 or accessor_offset % 4 != 0
                    or offset + length > buffer_bytes
                    or accessor_offset + (normal["count"] - 1) * stride + 12 > length):
                raise ValueError("NORMAL accessor bytes absent or outside BIN view")
        if found != set(expected_nodes):
            raise ValueError("GLB normal accessor mesh identities differ from receipt")
    except (KeyError, TypeError, IndexError, ValueError) as exc:
        raise ValueError("GLB material NORMAL accessor missing or invalid") from exc


def validate_glb_roundtrip(path: Path, report: dict) -> dict:
    """Reopen a staged GLB and reject missing, altered or detached part meshes."""
    import numpy as np
    import trimesh

    scene = trimesh.load(str(path), file_type="glb", force="scene")
    if not isinstance(scene, trimesh.Scene):
        raise ValueError("GLB did not reopen as a scene")
    components = report["components"]
    names = [part["name"] for part in components]
    if len(names) != 5 or len(set(names)) != 5:
        raise ValueError("GLB receipt must contain five distinct parts")
    expected_children = {}
    for part in components:
        children = part["materials"]
        if not children or part["material_count"] != len(children):
            raise ValueError("GLB receipt has missing material entries")
        for child in children:
            node = child["node"]
            if node in expected_children or node in names:
                raise ValueError("GLB receipt has duplicate material nodes")
            expected_children[node] = (part["name"], child)
    require_explicit_glb_normals(path, expected_children)
    expected_nodes = {scene.graph.base_frame, *names, *expected_children}
    if set(scene.graph.nodes) != expected_nodes:
        raise ValueError("GLB scene node set differs from receipt")
    if set(scene.graph.nodes_geometry) != set(expected_children):
        raise ValueError("GLB material geometry nodes differ from receipt")
    if set(scene.geometry) != set(expected_children):
        raise ValueError("GLB material mesh names differ from receipt")

    source_pose = np.asarray(report["source_pose_transform"], dtype=float)
    if source_pose.shape != (4, 4) or not np.isfinite(source_pose).all():
        raise ValueError("invalid source pose matrix")
    total_faces = 0
    for part in components:
        name = part["name"]
        if scene.graph.transforms.parents.get(name) != scene.graph.base_frame:
            raise ValueError(f"GLB parent node detached: {name}")
        local = np.eye(4)
        pivot = np.asarray(part["pivot_translation"], dtype=float)
        if pivot.shape != (3,) or not np.isfinite(pivot).all():
            raise ValueError(f"invalid part pivot: {name}")
        local[:3, 3] = pivot
        expected_world = source_pose @ local
        world, geometry = scene.graph.get(name)
        if geometry is not None or not np.allclose(world, expected_world, rtol=0, atol=1e-5):
            raise ValueError(f"GLB part transform changed: {name}")
        part_faces = 0
        for child in part["materials"]:
            node = child["node"]
            if scene.graph.transforms.parents.get(node) != name:
                raise ValueError(f"GLB material node detached: {node}")
            child_world, child_geom = scene.graph.get(node)
            if child_geom != node or not np.allclose(child_world, world, rtol=0, atol=1e-5):
                raise ValueError(f"GLB material transform changed: {node}")
            mesh = scene.geometry[node]
            if (not isinstance(mesh, trimesh.Trimesh) or mesh.is_empty
                    or not np.isfinite(mesh.vertices).all() or not mesh.is_watertight):
                raise ValueError(f"GLB material geometry invalid: {node}")
            if len(mesh.faces) != child["triangles"]:
                raise ValueError(f"GLB material triangle count changed: {node}")
            expected_geometry = child.get("geometry_sha256")
            if (not isinstance(expected_geometry, str) or len(expected_geometry) != 64
                    or any(c not in "0123456789abcdef" for c in expected_geometry)
                    or geometry_signature(mesh) != expected_geometry):
                raise ValueError(f"GLB material geometry digest changed: {node}")
            expected_normals = child.get("normals_sha256")
            if (not isinstance(expected_normals, str) or len(expected_normals) != 64
                    or any(c not in "0123456789abcdef" for c in expected_normals)
                    or normal_signature(mesh) != expected_normals):
                raise ValueError(f"GLB material normal digest changed: {node}")
            rgba = np.asarray(child["rgba"])
            if (rgba.shape != (4,) or mesh.visual.kind != "vertex"
                    or not np.all(mesh.visual.vertex_colors == rgba)):
                raise ValueError(f"GLB material color changed: {node}")
            part_faces += len(mesh.faces)
        if part_faces != part["triangles"]:
            raise ValueError(f"GLB part triangle count changed: {name}")
        total_faces += part_faces
    return {"validated_parts": len(names),
            "validated_material_meshes": len(expected_children),
            "validated_triangles": total_faces}

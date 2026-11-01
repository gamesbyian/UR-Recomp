#!/usr/bin/env python3
"""Produce P1/P2 provisional colourways from the SAME five SHA-verified GLBs.

One source geometry, no OpenSCAD rerender, no new 3D pose, no art approval.
P2 preserves its original GLB byte-for-byte; P1 changes exactly one COLOR_0
accessor's bytes and its metadata min/max. Everything else is fingerprinted.
"""
from __future__ import annotations

import argparse
import copy
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import tempfile
import uuid

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / "model-review"))
from stage_pages import POSES, validate

SCHEMA = "ur-art4k-provisional-colourways/1"
SLOT = "fork_and_frame__material_0"
P2_BLUE = (28, 89, 222, 255)  # Actual baseline GLB material.
P1_RED = (211, 43, 47, 255)   # Explicit 2026 proposal, NOT original 3D albedo.
SHA = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_glb(data: bytes):
    if len(data) < 28:
        raise ValueError("truncated GLB")
    magic, version, length = struct.unpack_from("<4sII", data)
    if magic != b"glTF" or version != 2 or length != len(data):
        raise ValueError("invalid GLB header")
    json_len, json_tag = struct.unpack_from("<I4s", data, 12)
    if json_tag != b"JSON" or not json_len or json_len % 4:
        raise ValueError("invalid GLB JSON chunk")
    bin_header = 20 + json_len
    if bin_header + 8 > len(data):
        raise ValueError("truncated GLB BIN chunk")
    bin_len, bin_tag = struct.unpack_from("<I4s", data, bin_header)
    if (bin_tag != b"BIN\x00" or bin_len % 4 or
            bin_header + 8 + bin_len != len(data)):
        raise ValueError("unsupported extra/malformed GLB chunks")
    doc = json.loads(data[20:bin_header].decode("utf-8"))
    if (doc.get("asset", {}).get("version") != "2.0" or
            len(doc.get("buffers", [])) != 1 or
            type(doc["buffers"][0].get("byteLength")) is not int or
            not 0 < doc["buffers"][0]["byteLength"] <= bin_len or
            "skins" in doc or "animations" in doc):
        raise ValueError("unsupported GLB structural form")
    return doc, bytearray(data[bin_header + 8:])


def encode_glb(doc: dict, binary: bytes) -> bytes:
    raw = json.dumps(doc, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    raw += b" " * (-len(raw) % 4)
    if len(binary) % 4:
        raise ValueError("unaligned GLB binary")
    size = 12 + 8 + len(raw) + 8 + len(binary)
    return (struct.pack("<4sII", b"glTF", 2, size) +
            struct.pack("<I4s", len(raw), b"JSON") + raw +
            struct.pack("<I4s", len(binary), b"BIN\x00") + binary)


def colour_layout(doc: dict, binary: bytes, receipt: dict):
    """Check all 16 original material slots, then isolate one writable buffer."""
    parts = receipt.get("components")
    if not isinstance(parts, list) or len(parts) != 5:
        raise ValueError("source receipt has no five-part rig")
    expected = {material["node"]: tuple(material["rgba"])
                for part in parts for material in part["materials"]}
    if (len(expected) != 16 or SLOT not in expected or expected[SLOT] != P2_BLUE or
            any(len(c) != 4 or c[3] != 255 for c in expected.values())):
        raise ValueError("source receipt material contract changed")
    meshes = doc.get("meshes")
    if (not isinstance(meshes, list) or len(meshes) != 16 or
            {m.get("name") for m in meshes} != set(expected)):
        raise ValueError("GLB has missing, duplicate or alien material meshes")
    accessors = doc["accessors"]
    views = doc["bufferViews"]
    target = None
    for mesh in meshes:
        primitives = mesh["primitives"]
        if (len(primitives) != 1 or
                primitives[0].get("mode", 4) != 4 or "targets" in primitives[0]):
            raise ValueError("unsupported material mesh primitives")
        attrs = primitives[0]["attributes"]
        idx, pos = attrs.get("COLOR_0"), attrs.get("POSITION")
        if (type(idx) is not int or type(pos) is not int or
                not 0 <= idx < len(accessors) or not 0 <= pos < len(accessors)):
            raise ValueError("source material lacks explicit colours/positions")
        acc = accessors[idx]
        if (acc.get("componentType") != 5121 or acc.get("type") != "VEC4" or
                acc.get("normalized") is not True or "sparse" in acc or
                type(acc.get("count")) is not int or acc["count"] <= 0 or
                acc["count"] != accessors[pos].get("count")):
            raise ValueError("unsupported GLB colour accessor")
        view_idx = acc.get("bufferView")
        if type(view_idx) is not int or not 0 <= view_idx < len(views):
            raise ValueError("unbacked GLB colour accessor")
        view = views[view_idx]
        voff, aoff = view.get("byteOffset", 0), acc.get("byteOffset", 0)
        size = acc["count"] * 4
        if (view.get("buffer") != 0 or view.get("byteStride", 4) != 4 or
                any(type(x) is not int for x in
                    (voff, aoff, size, view.get("byteLength"))) or
                voff < 0 or aoff < 0 or
                aoff + size > view["byteLength"] or
                voff + aoff + size > doc["buffers"][0]["byteLength"] or
                voff + aoff + size > len(binary)):
            raise ValueError("GLB colour view outside contiguous binary")
        offset = voff + aoff
        if binary[offset:offset + size] != bytes(expected[mesh["name"]]) * acc["count"]:
            raise ValueError("source GLB colour differs from authenticated receipt")
        if mesh["name"] == SLOT:
            target = idx, view_idx, offset, size, acc["count"]
    if target is None:
        raise ValueError("missing paintable fork material")
    target_idx, target_view, offset, size, count = target
    # A single accessor index can be referenced by unrelated semantics.
    # Its byte range being unique is insufficient if NORMAL, POSITION, UV,
    # mesh indices or an attribute of another primitive reuses that index.
    for mesh in meshes:
        primitive = mesh["primitives"][0]
        attributes = primitive["attributes"]
        if not isinstance(attributes, dict):
            raise ValueError("invalid primitive attribute mapping")
        uses = list(attributes.items())
        if "indices" in primitive:
            uses.append(("indices", primitive["indices"]))
        for semantic, accessor_index in uses:
            if accessor_index == target_idx and (
                    mesh["name"] != SLOT or semantic != "COLOR_0"):
                raise ValueError("fork colour accessor aliased by unrelated primitive semantic")
    # Different accessor/view IDs can still alias *the same BIN range*.
    # A recolour must not modify positions, indices or another colourway.
    for other_index, accessor in enumerate(accessors):
        if other_index == target_idx:
            continue
        view_index = accessor.get("bufferView")
        if type(view_index) is not int or not 0 <= view_index < len(views):
            raise ValueError("unbacked/invalid GLB attribute accessor")
        other = views[view_index]
        start, length = other.get("byteOffset", 0), other.get("byteLength")
        if (other.get("buffer") != 0 or type(start) is not int or
                type(length) is not int or start < 0 or length <= 0 or
                start + length > len(binary)):
            raise ValueError("invalid GLB attribute storage")
        if start < offset + size and offset < start + length:
            raise ValueError("fork colour bytes overlap another attribute's storage")
    return target_idx, offset, size, count, expected


def neutral_fingerprint(doc: dict, binary: bytes, layout) -> str:
    """Identical digest means every NON-target source byte/rig field is intact."""
    idx, offset, size, _, _ = layout
    clean_doc = copy.deepcopy(doc)
    clean_doc["accessors"][idx].pop("min", None)
    clean_doc["accessors"][idx].pop("max", None)
    clean_bin = bytearray(binary)
    clean_bin[offset:offset + size] = b"\x00" * size
    return digest(json.dumps(clean_doc, sort_keys=True, separators=(",", ":")).encode() + clean_bin)


def variants(source: bytes, receipt: dict):
    doc, binary = read_glb(source)
    layout = colour_layout(doc, binary, receipt)
    idx, offset, size, count, _ = layout
    reference = neutral_fingerprint(doc, binary, layout)
    new_doc = copy.deepcopy(doc)
    new_bin = bytearray(binary)
    new_bin[offset:offset + size] = bytes(P1_RED) * count
    for bound in ("min", "max"):
        if bound in new_doc["accessors"][idx]:
            new_doc["accessors"][idx][bound] = list(P1_RED)
    p1 = encode_glb(new_doc, new_bin)
    p1_doc, p1_binary = read_glb(p1)
    if neutral_fingerprint(p1_doc, p1_binary, layout) != reference:
        raise ValueError("geometry, rig or unrelated GLB data drifted")
    return {"p1": p1, "p2": source}, reference


def publish_directory(source: Path, destination: Path) -> None:
    """Atomically publish a directory without replacing any existing entry.

    POSIX os.rename can replace an existing empty directory. Linux therefore
    requires kernel RENAME_NOREPLACE; unsupported platforms fail closed.
    """
    if os.name == "nt":
        os.rename(source, destination)
        return
    if sys.platform != "linux":
        raise OSError(errno.ENOTSUP, "atomic no-replace directory rename unavailable")
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        renameat2 = libc.renameat2
    except AttributeError as exc:
        raise OSError(errno.ENOSYS, "renameat2 unavailable") from exc
    renameat2.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                          ctypes.c_char_p, ctypes.c_uint)
    renameat2.restype = ctypes.c_int
    if renameat2(-100, os.fsencode(source), -100, os.fsencode(destination), 1) != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), os.fspath(destination))


def build(exports: Path, out: Path, source_commit: str) -> dict:
    if not COMMIT.fullmatch(source_commit):
        raise ValueError("exact lowercase 40-character rig source commit required")
    checked = {pose: validate(exports, pose) for pose in POSES}
    source_sha = {ptr["source_sha256"] for ptr, _ in checked.values()}
    if len(source_sha) != 1 or not SHA.fullmatch(next(iter(source_sha))):
        raise ValueError("mixed/invalid canonical rig source")
    if out.is_symlink():
        raise ValueError("redirected output path")
    out.mkdir(parents=True, exist_ok=True)
    result = {"schema": SCHEMA, "source_commit": source_commit,
              "source_commit_verified": False,
              "source_model_sha256": next(iter(source_sha)),
              "original_colour_evidence": "tools/art/ORIGINAL-RACER-COLOURWAY-SOURCE.md (#2965)",
              "source_raster_colour_to_3d_material_proven": False,
              "original_3d_camera_identified": False,
              "original_sprite_to_blockout_pose_mapped": False,
              "heldout_source_pose_family_verified": False,
              "original_character_likeness_approved": False,
              "shipping_art_approved": False,
              "colourways": {
                  "p1": {"source_player": "P1", "fork_rgba": list(P1_RED), "provisional": True},
                  "p2": {"source_player": "P2", "fork_rgba": list(P2_BLUE), "provisional": True}},
              "poses": {}}
    with tempfile.TemporaryDirectory(prefix=".art4k-colourways-", dir=out) as tmp:
        temp = Path(tmp)
        for pose, (ptr, paths) in checked.items():
            source = paths["glb"].read_bytes()
            receipt_bytes = paths["receipt"].read_bytes()
            # The preflight can precede this read: recheck actual bytes here,
            # not merely the paths that were valid a moment earlier.
            if (digest(source) != ptr["glb_sha256"] or
                    digest(receipt_bytes) != ptr["receipt_sha256"]):
                raise ValueError(f"{pose}: source changed since SHA preflight")
            report = json.loads(receipt_bytes)
            outputs, neutral = variants(source, report)
            row = {"source_glb_sha256": digest(source),
                   "non_colour_payload_sha256": neutral, "outputs": {}}
            for player, data in outputs.items():
                name = f"{pose}-{player}-{digest(data)[:16]}.glb"
                (temp / name).write_bytes(data)
                row["outputs"][player] = {
                    "filename": name, "sha256": digest(data), "bytes": len(data)}
            result["poses"][pose] = row
        (temp / "colourways.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        destination = out / ("art4k-colourways-" + uuid.uuid4().hex)
        publish_directory(temp, destination)
    return {"directory": str(destination), "receipt": str(destination / "colourways.json"),
            "source_model_sha256": next(iter(source_sha)), "poses": list(POSES)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exports", required=True, type=Path,
                        help="five verified #2832 exporter pose directories")
    parser.add_argument("--out", required=True, type=Path,
                        help="immutable output parent directory")
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.exports, args.out, args.source_commit), indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Publish one source-registered ART-4K GLB projection+score as an atomic packet.

Consumes the existing #2832 exporter's immutable current/last-attempt receipts.
Never guesses a GLB from filenames, retries a failed export, or promotes an
unregistered 2026 procedural pose to original-1994 likeness approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import uuid

try:
    from tools.art.render_racer_glb_projection import project, camera_config
    from tools.art.score_racer_candidate import score_retained_original
    from tools.art.build_racer_source_pixel_corpus import REGISTRY
except ModuleNotFoundError:
    from render_racer_glb_projection import project, camera_config
    from score_racer_candidate import score_retained_original
    from build_racer_source_pixel_corpus import REGISTRY

SCHEMA = "UR-RACER-SOURCE-RIG-EVIDENCE-PACKET/1"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    return json.loads(raw), _sha(raw)


def _write_atomic(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent,
        prefix=".ur-racer-packet-", delete=False
    ) as f:
        staging = Path(f.name)
        json.dump(value, f, indent=2, sort_keys=True)
        f.write("\n")
    try:
        os.replace(staging, path)
    finally:
        staging.unlink(missing_ok=True)


def validate_current_export(export_dir: Path, source_scad: Path) -> dict:
    """Fail closed if the last attempt failed or the current pointer is stale."""
    pointer, _ = _read(export_dir / "articulated_blockout_current.json")
    last, _ = _read(export_dir / "articulated_blockout_last_attempt.json")
    if (pointer.get("schema") != "ur-art4k-export-current/1" or
            last.get("schema") != "ur-art4k-export-attempt/1"):
        raise ValueError("unrecognized ART-4K export pointer schema")
    attempt = pointer.get("attempt_id")
    if not isinstance(attempt, str) or not re.fullmatch(r"[0-9a-f]{32}", attempt):
        raise ValueError("invalid immutable ART-4K attempt ID")
    if (last.get("attempt_id") != attempt or last.get("status") != "succeeded" or
            last.get("current_output_usable") is not True):
        raise ValueError("last ART-4K export did not succeed; refuse stale current pointer")
    source_sha = _sha(source_scad.read_bytes())
    if (pointer.get("source_sha256") != source_sha or
            last.get("source_sha256") != source_sha):
        raise ValueError("ART-4K model source hash changed since export")
    glb_rel = Path(f"attempts/{attempt}/unicycle_articulated_blockout.glb")
    receipt_rel = Path(f"attempts/{attempt}/articulated_blockout_receipt.json")
    if pointer.get("glb_path") != glb_rel.as_posix() or pointer.get("receipt_path") != receipt_rel.as_posix():
        raise ValueError("current ART-4K paths do not belong to this immutable attempt")
    glb_path = export_dir / glb_rel
    receipt_path = export_dir / receipt_rel
    if (not glb_path.resolve().is_relative_to(export_dir.resolve()) or
            not receipt_path.resolve().is_relative_to(export_dir.resolve())):
        raise ValueError("export path escapes source directory")
    glb_hash = _sha(glb_path.read_bytes())
    receipt, receipt_hash = _read(receipt_path)
    if (pointer.get("glb_sha256") != glb_hash or
            last.get("glb_sha256") != glb_hash or
            pointer.get("receipt_sha256") != receipt_hash or
            receipt.get("glb_sha256") != glb_hash or
            receipt.get("schema") != "ur-art4k-articulated-blockout/1" or
            receipt.get("attempt_id") != attempt or
            receipt.get("source_sha256") != source_sha or
            receipt.get("rig_pose") != pointer.get("rig_pose")):
        raise ValueError("ART-4K GLB/receipt/current pointer do not agree")
    if (receipt.get("shipping_art_approved") is not False or
            receipt.get("original_character_likeness_approved") is not False or
            receipt.get("pose_source_registered_to_original_game") is not False):
        raise ValueError("this pipeline supports only an unapproved blockout pose")
    return {
        "attempt_id": attempt,
        "source_scad_sha256": source_sha,
        "source_glb_sha256": glb_hash,
        "source_art4k_receipt_sha256": receipt_hash,
        "glb_path": glb_path,
        "rig_pose": pointer["rig_pose"],
    }


def validate_source_camera(camera_path: Path, player: str, frame: int) -> dict:
    camera, camera_sha = _read(camera_path)
    camera_config(camera)
    witness = camera.get("source_witness")
    if not isinstance(witness, dict) or witness.get("player") != player or witness.get("guest_frame") != frame:
        raise ValueError("camera belongs to another source frame or player")
    registry, _ = _read(REGISTRY)
    sequence = next((r for r in registry["motion_review_sequence"]["frames"] if r["frame"] == frame), None)
    if sequence is None:
        raise ValueError("requested authentic source frame is not registered")
    identity = sequence[player + "_representation_id"]
    if witness.get("source_representation_id") != identity:
        raise ValueError("camera source representation is unverified")
    entry = next((x for x in registry["entries"] if x["representation_id"] == identity), None)
    if entry is None:
        raise ValueError("authentic registry entry missing")
    anchor = entry["registration"]["semantic_anchors"]["wheel_contact_x2_y2"]
    if camera.get("source_anchor_x2_y2") != anchor:
        raise ValueError("camera anchor conflicts with source-verified geometry")
    return {"sha256": camera_sha, "representation_id": identity, "camera": camera}


def run_packet(export_dir: Path, source_scad: Path, camera_path: Path,
               player: str, frame: int, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    attempt = uuid.uuid4().hex
    last_path = out_dir / "racer_inverse_last_attempt.json"
    current_path = out_dir / "racer_inverse_current.json"
    _write_atomic(last_path, {"schema": SCHEMA, "attempt_id": attempt, "status": "running"})
    stage = Path(tempfile.mkdtemp(prefix=".ur-racer-inverse-", dir=out_dir))
    try:
        export = validate_current_export(export_dir, source_scad)
        camera = validate_source_camera(camera_path, player, frame)
        candidate = stage / "candidate-4x.png"
        projection = project(export["glb_path"], export["source_glb_sha256"], camera_path, candidate)
        score = score_retained_original(player, frame, candidate, projection["candidate_png_sha256"], 4)
        packet = {
            "schema": SCHEMA,
            "attempt_id": attempt,
            "source_art4k_attempt_id": export["attempt_id"],
            "source_art4k_rig_pose": export["rig_pose"],
            "source_scad_sha256": export["source_scad_sha256"],
            "source_glb_sha256": export["source_glb_sha256"],
            "source_art4k_receipt_sha256": export["source_art4k_receipt_sha256"],
            "source_camera_manifest_sha256": camera["sha256"],
            "source_original_representation_id": camera["representation_id"],
            "candidate_png_sha256": projection["candidate_png_sha256"],
            "projected_alpha": projection,
            "silhouette_score": score,
            "source_1994_3d_camera_verified": False,
            "owner_likeness_approved": False,
            "shipping_art_approved": False,
        }
        _write_atomic(stage / "packet.json", packet)
        packet_sha = _sha((stage / "packet.json").read_bytes())
        attempts = out_dir / "attempts"
        attempts.mkdir(exist_ok=True)
        final = attempts / attempt
        os.rename(stage, final)
        current = {
            "schema": SCHEMA, "attempt_id": attempt,
            "packet_path": f"attempts/{attempt}/packet.json",
            "packet_sha256": packet_sha,
            "candidate_path": f"attempts/{attempt}/candidate-4x.png",
            "candidate_png_sha256": projection["candidate_png_sha256"],
        }
        _write_atomic(current_path, current)
        _write_atomic(last_path, {"schema": SCHEMA, "attempt_id": attempt, "status": "succeeded",
                                 "current_output_usable": True})
        return packet
    except Exception as exc:
        _write_atomic(last_path, {"schema": SCHEMA, "attempt_id": attempt, "status": "failed",
                                 "current_output_usable": False, "error_type": type(exc).__name__,
                                 "error": str(exc)[-500:]})
        raise
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--export-dir", type=Path, required=True)
    ap.add_argument("--source-scad", type=Path, required=True)
    ap.add_argument("--camera", type=Path, required=True)
    ap.add_argument("--player", choices=("p1", "p2"), required=True)
    ap.add_argument("--frame", type=int, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    result = run_packet(
        args.export_dir, args.source_scad, args.camera,
        args.player, args.frame, args.out_dir
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
